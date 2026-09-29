import { apiRequest } from "./client";

export function register(name, email, username, password) {
  return apiRequest("/api/auth/register", {
    method: "POST",
    body: { name, email, username, password },
    auth: false,
  });
}

export function login(email, password) {
  return apiRequest("/api/auth/login", { method: "POST", body: { email, password }, auth: false });
}

export function getMe() {
  return apiRequest("/api/me");
}

export function updateMe(updates) {
  return apiRequest("/api/me", { method: "PATCH", body: updates });
}
