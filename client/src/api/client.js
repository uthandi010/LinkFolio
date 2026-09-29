const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const TOKEN_KEY = "linkfolio_token";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function extractErrorMessage(data, status) {
  if (data) {
    // Our own HTTPException(status, "message") calls land here as a string.
    if (typeof data.detail === "string") return data.detail;
    // FastAPI's automatic Pydantic validation errors land here as a list.
    if (Array.isArray(data.detail) && typeof data.detail[0]?.msg === "string") {
      return data.detail[0].msg;
    }
    if (typeof data.message === "string") return data.message;
  }
  return `Request failed with status ${status}`;
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export async function apiRequest(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (auth && token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) {
    return undefined;
  }

  const text = await response.text();
  const data = text ? JSON.parse(text) : undefined;

  if (!response.ok) {
    throw new ApiError(response.status, extractErrorMessage(data, response.status));
  }

  return data;
}
