// Thin wrapper around the backend REST API.
// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js).

const BASE = "/api/v1";

export async function listRuns() {
  const res = await fetch(`${BASE}/trajectories`);
  if (!res.ok) throw new Error(`listRuns failed: ${res.status}`);
  const data = await res.json();
  return data.run_ids ?? [];
}

export async function getTrajectory(runId) {
  const res = await fetch(`${BASE}/trajectories/${runId}`);
  if (!res.ok) throw new Error(`getTrajectory failed: ${res.status}`);
  return res.json();
}

export async function runTask(task) {
  const res = await fetch(`${BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task }),
  });
  if (!res.ok) throw new Error(`runTask failed: ${res.status}`);
  return res.json();
}
