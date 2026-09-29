import { apiRequest } from "./client";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function getPublicProfile(username) {
  return apiRequest(`/api/public/profiles/${username}`, { auth: false });
}

// The click-tracking redirect is a plain link, not a fetch call - the
// browser needs to actually navigate (and follow the 302) rather than have
// JS read the response.
export function clickUrl(linkId) {
  return `${API_BASE_URL}/api/public/links/${linkId}/go`;
}
