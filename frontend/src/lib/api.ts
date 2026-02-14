/** Custom error for API responses */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  params?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

const BASE_URL = "/api/v1";

function buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
  const url = `${BASE_URL}${endpoint}`;
  if (!params) return url;

  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value));
    }
  }
  const qs = searchParams.toString();
  return qs ? `${url}?${qs}` : url;
}

async function request<T>(method: string, endpoint: string, options?: RequestOptions & { body?: unknown }): Promise<T> {
  const url = buildUrl(endpoint, options?.params);
  const init: RequestInit = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    signal: options?.signal,
  };

  if (options?.body !== undefined) {
    init.body = JSON.stringify(options.body);
  }

  const res = await fetch(url, init);

  if (!res.ok) {
    let body: unknown;
    const text = await res.text();
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
    throw new ApiError(res.status, res.statusText, body);
  }

  return res.json() as Promise<T>;
}

/** Generic API client */
export const api = {
  get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>("GET", endpoint, options);
  },
  post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>("POST", endpoint, { ...options, body });
  },
  put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>("PUT", endpoint, { ...options, body });
  },
  delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>("DELETE", endpoint, options);
  },
};
