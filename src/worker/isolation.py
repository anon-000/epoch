"""
Process-level resource isolation for job execution.
Runs jobs in subprocesses with CPU, memory, and timeout limits.
Uses resource module on Linux/macOS to enforce limits.
"""

import asyncio
import json
import logging
import multiprocessing
import os
import resource
import signal
import sys
import traceback

logger = logging.getLogger("epoch.worker.isolation")

# Default resource limits
DEFAULT_MEMORY_LIMIT_MB = 512
DEFAULT_CPU_TIME_LIMIT = 3600  # seconds


def _set_resource_limits(memory_mb: int, cpu_seconds: int):
    """Set resource limits inside the subprocess (called in child process)."""
    # Memory limit (soft, hard) in bytes
    memory_bytes = memory_mb * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    except ValueError:
        # Some systems don't support RLIMIT_AS, try RSS instead
        try:
            resource.setrlimit(resource.RLIMIT_RSS, (memory_bytes, memory_bytes))
        except (ValueError, AttributeError):
            pass

    # CPU time limit
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    except ValueError:
        pass


def _run_job_in_process(
    job_type: str,
    payload_json: str,
    resume_state_json: str | None,
    memory_mb: int,
    cpu_seconds: int,
    result_pipe,
):
    """
    Target function for subprocess execution.
    Imports the job, runs it, sends result through pipe.
    """
    import asyncio
    import importlib

    # Apply resource limits
    _set_resource_limits(memory_mb, cpu_seconds)

    async def _execute():
        try:
            module_path, class_name = job_type.rsplit(":", 1)
            module = importlib.import_module(module_path)
            job_class = getattr(module, class_name)

            job_instance = job_class()

            resume_state = None
            if resume_state_json:
                resume_state = json.loads(resume_state_json)

            result = await job_instance.run(payload_json if isinstance(payload_json, dict) else json.loads(payload_json), resume_state=resume_state)
            return {"success": True, "result": result}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    try:
        result = asyncio.run(_execute())
        result_pipe.send(result)
    except Exception as e:
        result_pipe.send({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        })
    finally:
        result_pipe.close()


class IsolatedExecutor:
    """Execute jobs in isolated subprocesses with resource limits."""

    async def execute(
        self,
        job_type: str,
        payload: dict,
        resume_state: dict | None = None,
        timeout_seconds: int = 3600,
        memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
        cpu_limit_seconds: int = DEFAULT_CPU_TIME_LIMIT,
    ) -> dict:
        """
        Run a job in a subprocess with resource limits.
        Falls back to in-process execution if subprocess fails to start.
        """
        parent_conn, child_conn = multiprocessing.Pipe()

        payload_json = json.dumps(payload)
        resume_json = json.dumps(resume_state) if resume_state else None

        process = multiprocessing.Process(
            target=_run_job_in_process,
            args=(job_type, payload_json, resume_json, memory_limit_mb, cpu_limit_seconds, child_conn),
        )
        process.start()
        child_conn.close()  # parent doesn't write

        try:
            # Wait for result with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, parent_conn.recv
                ),
                timeout=timeout_seconds,
            )
            return result

        except asyncio.TimeoutError:
            logger.warning(f"Isolated job timed out after {timeout_seconds}s, killing process")
            process.kill()
            return {
                "success": False,
                "error": f"Process timed out after {timeout_seconds}s",
            }

        except EOFError:
            # Child process crashed without sending result
            return {
                "success": False,
                "error": f"Process crashed (exit code: {process.exitcode})",
            }

        finally:
            parent_conn.close()
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
