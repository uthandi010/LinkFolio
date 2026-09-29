import { apiRequest } from "./client";

export function listLinks() {
  return apiRequest("/api/links");
}

export function createLink(title, url) {
  return apiRequest("/api/links", { method: "POST", body: { title, url } });
}

export function updateLink(linkId, updates) {
  return apiRequest(`/api/links/${linkId}`, { method: "PATCH", body: updates });
}

export function deleteLink(linkId) {
  return apiRequest(`/api/links/${linkId}`, { method: "DELETE" });
}

export function reorderLinks(linkIds) {
  return apiRequest("/api/links/reorder", { method: "POST", body: { link_ids: linkIds } });
}
