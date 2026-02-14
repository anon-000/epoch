"""Entry point for the API server."""

import uvicorn

from src.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
