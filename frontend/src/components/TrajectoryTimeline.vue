<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as echarts from "echarts";

const props = defineProps({ steps: { type: Array, required: true } });

const ROLE_META = {
  planner: { label: "Planner", color: "#8b5cf6", icon: "🧭" },
  executor: { label: "Executor", color: "#3b82f6", icon: "⚙️" },
  critic: { label: "Critic", color: "#10b981", icon: "🔍" },
};

function roleOf(step) {
  return ROLE_META[step.agent_role] ?? { label: step.agent_role, color: "#8b93a7", icon: "❓" };
}

function fmtTokens(step) {
  return `${step.token_in}+${step.token_out}`;
}

// ===== ECharts: per-step tokens + latency =====
const chartEl = ref(null);
let chart = null;

const chartOption = computed(() => {
  const labels = props.steps.map((s) => `#${s.step_id} ${roleOf(s).label}`);
  return {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    legend: { data: ["tokens in", "tokens out", "latency (ms)"], textStyle: { color: "#8b93a7" } },
    grid: { left: 50, right: 50, top: 40, bottom: 30 },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { color: "#8b93a7", fontSize: 11 },
      axisLine: { lineStyle: { color: "#2a2f3e" } },
    },
    yAxis: [
      { type: "value", name: "tokens", axisLabel: { color: "#8b93a7" }, splitLine: { lineStyle: { color: "#22273600" } } },
      { type: "value", name: "ms", axisLabel: { color: "#8b93a7" }, splitLine: { show: false } },
    ],
    series: [
      {
        name: "tokens in",
        type: "bar",
        stack: "tok",
        data: props.steps.map((s) => s.token_in),
        itemStyle: { color: "#3b82f6" },
      },
      {
        name: "tokens out",
        type: "bar",
        stack: "tok",
        data: props.steps.map((s) => s.token_out),
        itemStyle: { color: "#60a5fa" },
      },
      {
        name: "latency (ms)",
        type: "line",
        yAxisIndex: 1,
        data: props.steps.map((s) => s.latency_ms),
        smooth: true,
        itemStyle: { color: "#f59e0b" },
        lineStyle: { color: "#f59e0b", width: 2 },
      },
    ],
  };
});

function renderChart() {
  if (!chartEl.value) return;
  if (!chart) chart = echarts.init(chartEl.value);
  chart.setOption(chartOption.value);
}

function onResize() { chart?.resize(); }

onMounted(() => {
  renderChart();
  window.addEventListener("resize", onResize);
});
watch(() => props.steps, renderChart, { deep: true });
onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  chart?.dispose();
});
</script>

<template>
  <div class="timeline">
    <h2 class="section-title">Step-by-step trajectory</h2>

    <ol class="steps">
      <li v-for="step in steps" :key="step.step_id" class="step" :class="step.agent_role">
        <div class="rail">
          <span class="badge" :style="{ background: roleOf(step).color }">
            {{ roleOf(step).icon }} {{ roleOf(step).label }}
          </span>
        </div>

        <div class="card">
          <div class="head">
            <span class="step-id">Step {{ step.step_id }}</span>
            <span class="metrics">
              📊 {{ fmtTokens(step) }} tok · {{ (step.latency_ms / 1000).toFixed(1) }}s
            </span>
          </div>

          <p v-if="step.thought" class="thought">
            <span class="k">💭 thought</span>
            {{ step.thought }}
          </p>

          <p v-if="step.action" class="action">
            <span class="k">🔧 action</span>
            <code>{{ step.action.tool_name }}({{ step.action.tool_input }})</code>
          </p>

          <p v-if="step.observation" class="observation">
            <span class="k">📥 observation</span>
            {{ step.observation }}
          </p>
        </div>
      </li>
    </ol>

    <h2 class="section-title">Tokens &amp; latency per step</h2>
    <div ref="chartEl" class="chart"></div>
  </div>
</template>

<style scoped>
.timeline { margin-top: 8px; }
.section-title { font-size: 15px; color: var(--muted); margin: 26px 0 12px; font-weight: 600; }

.steps { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }

.step { display: flex; gap: 14px; align-items: flex-start; }
.rail { width: 118px; flex-shrink: 0; padding-top: 10px; }
.badge {
  display: inline-block; color: #fff; font-size: 12px; font-weight: 600;
  padding: 4px 10px; border-radius: 999px; white-space: nowrap;
}

.card {
  flex: 1; background: var(--panel); border: 1px solid var(--border);
  border-radius: 10px; padding: 12px 16px;
}
.step.planner .card { border-left: 3px solid var(--planner); }
.step.executor .card { border-left: 3px solid var(--executor); }
.step.critic .card { border-left: 3px solid var(--critic); }

.head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.step-id { font-size: 12px; color: var(--muted); font-weight: 600; }
.metrics { font-size: 12px; color: var(--muted); }

.thought, .action, .observation { margin: 6px 0; font-size: 13.5px; line-height: 1.55; }
.k { display: inline-block; min-width: 106px; color: var(--muted); font-size: 12px; }
.action code {
  background: var(--panel-2); padding: 2px 8px; border-radius: 6px;
  font-size: 12.5px; color: #93c5fd;
}
.observation { color: #c3cad9; }

.chart { width: 100%; height: 280px; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; }
</style>
