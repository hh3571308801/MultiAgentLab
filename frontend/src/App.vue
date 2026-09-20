<script setup>
import { onMounted, ref, watch } from "vue";
import { listRuns, getTrajectory } from "./api.js";
import TrajectoryTimeline from "./components/TrajectoryTimeline.vue";

const runIds = ref([]);
const selectedRun = ref("");
const trajectory = ref(null);
const loading = ref(false);
const error = ref("");

async function refreshRuns() {
  try {
    runIds.value = await listRuns();
    if (runIds.value.length && !selectedRun.value) {
      // Backend returns runs newest-first; default to the most recent one.
      selectedRun.value = runIds.value[0];
    }
  } catch (e) {
    error.value = "Cannot reach backend — is `python -m backend.main` running on :8000?";
  }
}

async function loadTrajectory(runId) {
  if (!runId) return;
  loading.value = true;
  error.value = "";
  try {
    trajectory.value = await getTrajectory(runId);
  } catch (e) {
    error.value = String(e.message || e);
    trajectory.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  // Support deep-linking: http://localhost:5173/#run=<run_id>
  const hashRun = window.location.hash.replace("#run=", "");
  await refreshRuns();
  if (hashRun && runIds.value.includes(hashRun)) {
    selectedRun.value = hashRun;
  }
});
watch(selectedRun, loadTrajectory);
</script>

<template>
  <div class="page">
    <header class="topbar">
      <div class="brand">
        <span class="logo">🧪</span>
        <div>
          <h1>MultiAgentLab</h1>
          <p class="tagline">Trajectory Viewer</p>
        </div>
      </div>
      <div class="controls">
        <select v-model="selectedRun" class="run-select">
          <option value="" disabled>Select a run…</option>
          <option v-for="id in runIds" :key="id" :value="id">{{ id.slice(0, 8) }}</option>
        </select>
        <button class="refresh" @click="refreshRuns" title="Refresh run list">⟳</button>
      </div>
    </header>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading" class="loading">Loading trajectory…</p>

    <template v-if="trajectory">
      <section class="summary">
        <div class="task">
          <span class="label">Task</span>
          <span class="value">{{ trajectory.task }}</span>
        </div>
        <div class="stats">
          <div class="stat">
            <span class="label">Status</span>
            <span class="value" :class="trajectory.status">{{ trajectory.status }}</span>
          </div>
          <div class="stat">
            <span class="label">Steps</span>
            <span class="value">{{ trajectory.steps.length }}</span>
          </div>
          <div class="stat">
            <span class="label">Tokens</span>
            <span class="value">{{ trajectory.total_tokens.toLocaleString() }}</span>
          </div>
          <div class="stat">
            <span class="label">Latency</span>
            <span class="value">{{ (trajectory.total_latency_ms / 1000).toFixed(1) }}s</span>
          </div>
        </div>
      </section>

      <section v-if="trajectory.final_answer" class="answer">
        <span class="label">Final Answer</span>
        <span class="value">{{ trajectory.final_answer }}</span>
      </section>

      <TrajectoryTimeline :steps="trajectory.steps" />
    </template>

    <p v-else-if="!error && !loading" class="hint">
      Pick a run from the dropdown (run the backend first, or add one via
      <code>python scripts/run_real_demo.py "…"</code>).
    </p>
  </div>
</template>

<style>
:root {
  --bg: #0f1117;
  --panel: #171a23;
  --panel-2: #1e2230;
  --border: #2a2f3e;
  --text: #e5e9f0;
  --muted: #8b93a7;
  --planner: #8b5cf6;
  --executor: #3b82f6;
  --critic: #10b981;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}
.page { max-width: 1080px; margin: 0 auto; padding: 24px 20px 60px; }

.topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 16px; border-bottom: 1px solid var(--border); margin-bottom: 20px;
}
.brand { display: flex; align-items: center; gap: 12px; }
.logo { font-size: 30px; }
.brand h1 { margin: 0; font-size: 20px; }
.tagline { margin: 2px 0 0; color: var(--muted); font-size: 12px; }

.controls { display: flex; gap: 8px; }
.run-select, .refresh {
  background: var(--panel-2); color: var(--text);
  border: 1px solid var(--border); border-radius: 8px;
  padding: 8px 12px; font-size: 14px;
}
.refresh { cursor: pointer; }

.error { color: #f87171; }
.loading, .hint { color: var(--muted); }
.hint code { color: var(--executor); }

.summary { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; margin-bottom: 14px; }
.task { display: flex; gap: 12px; align-items: baseline; }
.task .value { font-size: 15px; }
.stats { display: flex; gap: 32px; margin-top: 12px; flex-wrap: wrap; }
.stat .label { display: block; }
.label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }
.value { font-size: 16px; font-weight: 600; }
.value.completed { color: var(--critic); }
.value.failed { color: #f87171; }

.answer { background: var(--panel); border: 1px solid var(--border); border-left: 3px solid var(--critic); border-radius: 12px; padding: 14px 20px; margin-bottom: 14px; }
.answer .value { display: block; margin-top: 6px; }
</style>
