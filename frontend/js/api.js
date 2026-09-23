/**
 * API client for CWA Temperature Broadcast Service
 */

const API_BASE_URL = window.location.origin.includes(":8000") || window.location.origin.includes(":3000") || window.location.origin.includes(":5173")
  ? window.location.origin
  : "http://localhost:8000";

export async function fetchLatestTemperatures(forceRefresh = false) {
  const url = `${API_BASE_URL}/api/temperature/latest${forceRefresh ? "?force_refresh=true" : ""}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch temperature data: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}

export async function fetchTemperatureGeoJSON(forceRefresh = false) {
  const url = `${API_BASE_URL}/api/temperature/geojson${forceRefresh ? "?force_refresh=true" : ""}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch GeoJSON: ${response.status} ${response.statusText}`);
  }
  return await response.json();
}

export async function fetchStationDetail(stationId) {
  const url = `${API_BASE_URL}/api/temperature/stations/${encodeURIComponent(stationId)}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch station ${stationId}: ${response.status}`);
  }
  return await response.json();
}

export async function fetchHealthStatus() {
  const url = `${API_BASE_URL}/api/health`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return await response.json();
}
