import type { ModelRoster, TrainProgress } from "../types";

interface Props {
  roster: ModelRoster[];
  progress: Record<string, TrainProgress>;
}

export default function Progress({ roster, progress }: Props) {
  if (roster.length === 0) return null;

  return (
    <div className="space-y-2">
      {roster.map(({ model, layer }) => {
        const key = `${model}|${layer}`;
        const evt = progress[key];
        const pct = evt?.total ? Math.round(((evt.fold || 0) / evt.total) * 100) : 0;
        const done = pct === 100;

        return (
          <div key={key} className="border border-[var(--color-border)] bg-[var(--color-surface)] rounded-sm p-3">
            <div className="flex justify-between font-mono text-xs mb-1.5">
              <span className={done ? "text-[var(--color-positive)]" : "text-[var(--color-text)]"}>
                {model} — {layer}
                {done && " ✓"}
              </span>
              <span className="text-[var(--color-text-dim)]">
                {evt ? `Fold ${evt.fold}/${evt.total} · AUC ${(evt.auc || 0).toFixed(3)}` : "Waiting..."}
              </span>
            </div>
            <div className="h-1.5 bg-[var(--color-border)] rounded-sm overflow-hidden">
              <div
                className={`h-full transition-all duration-200 ${done ? "bg-[var(--color-positive)]" : "bg-[var(--color-accent)]"}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
