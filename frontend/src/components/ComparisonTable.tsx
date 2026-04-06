import { useState } from "react";
import type { ComparisonRow } from "../types";

const COLS: { key: keyof ComparisonRow; label: string }[] = [
  { key: "model", label: "Model" },
  { key: "feature_set", label: "Layer" },
  { key: "roc_auc", label: "AUC" },
  { key: "spearman_ic", label: "IC" },
  { key: "precision_at_k", label: "P@30" },
  { key: "f1", label: "F1" },
  { key: "accuracy", label: "Acc" },
  { key: "precision", label: "Prec" },
  { key: "recall", label: "Rec" },
  { key: "ndcg_at_k", label: "NDCG" },
  { key: "n_folds", label: "Folds" },
];

const layerBg: Record<string, string> = {
  A: "bg-[var(--color-layer-a)]",
  B: "bg-[var(--color-layer-b)]",
  C: "bg-[var(--color-layer-c)]",
};

function fmt(v: unknown): string {
  if (v == null) return "–";
  if (typeof v === "number") return v >= 1 ? v.toFixed(0) : v.toFixed(4);
  return String(v);
}

export default function ComparisonTable({ data }: { data: ComparisonRow[] }) {
  const [sortKey, setSortKey] = useState<keyof ComparisonRow>("feature_set");
  const [asc, setAsc] = useState(true);

  const sorted = [...data].sort((a, b) => {
    const va = a[sortKey] ?? 0, vb = b[sortKey] ?? 0;
    const cmp = va < vb ? -1 : va > vb ? 1 : 0;
    return asc ? cmp : -cmp;
  });

  const toggleSort = (key: keyof ComparisonRow) => {
    if (sortKey === key) setAsc(!asc);
    else { setSortKey(key); setAsc(true); }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-[var(--color-border)]">
            {COLS.map(({ key, label }) => (
              <th key={key} onClick={() => toggleSort(key)}
                className="px-3 py-2 text-left text-[var(--color-text-dim)] font-medium cursor-pointer hover:text-[var(--color-text)] select-none whitespace-nowrap">
                {label} {sortKey === key ? (asc ? "↑" : "↓") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => {
            const layer = row.feature_set[0];
            return (
              <tr key={i} className={`border-b border-[var(--color-border)]/50 ${layerBg[layer] || ""}`}>
                {COLS.map(({ key }) => (
                  <td key={key} className="px-3 py-1.5 whitespace-nowrap">{fmt(row[key])}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
