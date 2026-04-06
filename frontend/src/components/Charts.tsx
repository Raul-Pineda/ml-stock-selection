import _Plotly from "plotly.js-dist-min";
import _factory from "react-plotly.js/factory";
import type { ComparisonRow, FeatureImportance, PerQuarterRow } from "../types";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const resolve = (m: any) => m.default ?? m;
const Plot = resolve(_factory)(resolve(_Plotly));

const DARK = { paper_bgcolor: "transparent", plot_bgcolor: "transparent", font: { color: "#C5CDD9", family: "JetBrains Mono, monospace", size: 11 } };
const GRID = { gridcolor: "#1E2330", zerolinecolor: "#1E2330" };
const COLORS = ["#2563EB", "#ED7D31", "#70AD47", "#FFC000"];
const PLOT = { config: { displayModeBar: false, responsive: true }, style: { width: "100%" } } as const;

export function MetricBars({ data }: { data: ComparisonRow[] }) {
  const metrics = ["roc_auc", "spearman_ic", "precision_at_k", "f1"] as const;
  const labels = ["AUC", "Spearman IC", "Precision@30", "F1"];
  const x = data.map((r) => `${r.model}\n${r.feature_set}`);

  return (
    <Plot
      data={metrics.map((m, i) => ({
        type: "bar" as const, name: labels[i], x, y: data.map((r) => r[m] ?? 0),
        marker: { color: COLORS[i] },
      }))}
      layout={{ ...DARK, barmode: "group", xaxis: { ...GRID }, yaxis: { ...GRID, title: "Score" },
        margin: { t: 30, b: 80, l: 50, r: 20 }, height: 320, legend: { orientation: "h", y: 1.12 } }}
      {...PLOT}
    />
  );
}

export function ICTimeseries({ data }: { data: PerQuarterRow[] }) {
  const layerC = data.filter((r) => r.feature_set === "C_All_features");
  const models = [...new Set(layerC.map((r) => r.model))];

  return (
    <div className="space-y-4">
      {models.map((name) => {
        const rows = layerC.filter((r) => r.model === name).sort((a, b) => a.quarter.localeCompare(b.quarter));
        const ics = rows.map((r) => Number(r.spearman_ic) || 0);
        const mean = ics.reduce((a, b) => a + b, 0) / ics.length;
        return (
          <div key={name}>
            <p className="font-mono text-xs text-[var(--color-text-dim)] mb-1">{name} — IC per quarter (mean: {mean.toFixed(4)})</p>
            <Plot
              data={[{
                type: "bar" as const, x: rows.map((r) => r.quarter), y: ics,
                marker: { color: ics.map((v) => v >= 0 ? "#2563EB" : "#EF4444") },
              }, {
                type: "scatter" as const, mode: "lines" as const, x: rows.map((r) => r.quarter),
                y: Array(rows.length).fill(mean), line: { color: "#EF4444", dash: "dash", width: 1 },
                name: "Mean", showlegend: false,
              }]}
              layout={{ ...DARK, xaxis: { ...GRID, tickangle: -45, tickfont: { size: 8 } },
                yaxis: { ...GRID, title: "IC" }, margin: { t: 10, b: 60, l: 50, r: 20 },
                height: 220, showlegend: false }}
              {...PLOT}
            />
          </div>
        );
      })}
    </div>
  );
}

export function FeatureImportanceChart({ data }: { data: Record<string, FeatureImportance> }) {
  const entries = Object.entries(data);
  if (!entries.length) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {entries.map(([name, { features, importances }]) => {
        const idx = importances.map((_, i) => i).sort((a, b) => importances[a] - importances[b]);
        return (
          <div key={name}>
            <p className="font-mono text-xs text-[var(--color-text-dim)] mb-1">{name}</p>
            <Plot
              data={[{
                type: "bar" as const, orientation: "h" as const,
                y: idx.map((i) => features[i]), x: idx.map((i) => importances[i]),
                marker: { color: "#2563EB" },
              }]}
              layout={{ ...DARK, xaxis: { ...GRID, title: "Gini Importance" },
                yaxis: { ...GRID, tickfont: { size: 9 } },
                margin: { t: 10, b: 40, l: 120, r: 20 }, height: Math.max(200, features.length * 24) }}
              {...PLOT}
            />
          </div>
        );
      })}
    </div>
  );
}
