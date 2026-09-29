import { apiRequest } from "./client";

export function getAnalyticsSummary() {
  return apiRequest("/api/analytics/summary");
}
