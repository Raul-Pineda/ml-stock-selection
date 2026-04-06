import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { downloadXlsx, fetchComparison, fetchFeatures, fetchPerQuarter, trainModels } from "../api/client";
import { FeatureImportanceChart, ICTimeseries, MetricBars } from "../components/Charts";
import ComparisonTable from "../components/ComparisonTable";
import Layout from "../components/Layout";
import Progress from "../components/Progress";
import type { ComparisonRow, FeatureImportance, ModelRoster, PerQuarterRow, Schema, TrainProgress } from "../types";

function Section({ title, padded, children }: { title: string; padded?: boolean; children: ReactNode }) {
  return (
    <section>
      <h2 className="font-mono text-xs text-[var(--color-text-dim)] font-medium mb-2 uppercase tracking-wider">{title}</h2>
      <div className={`border border-[var(--color-border)] rounded-sm ${padded ? "p-2 bg-[var(--color-surface)]" : "overflow-hidden"}`}>
        {children}
      </div>
    </section>
  );
}

export default function Dashboard({ schema }: { schema: Schema | null }) {
  const [roster, setRoster] = useState<ModelRoster[]>([]);
  const [progress, setProgress] = useState<Record<string, TrainProgress>>({});
  const [training, setTraining] = useState(true);
  const [comparison, setComparison] = useState<ComparisonRow[]>([]);
  const [perQuarter, setPerQuarter] = useState<PerQuarterRow[]>([]);
  const [features, setFeatures] = useState<Record<string, FeatureImportance>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    const close = trainModels(async (evt) => {
      if (evt.event === "roster") {
        setRoster(evt.models as ModelRoster[]);
      } else if (evt.event === "complete") {
        setTraining(false);
        try {
          const [comp, pq, feat] = await Promise.all([
            fetchComparison(), fetchPerQuarter(), fetchFeatures(),
          ]);
          setComparison(comp);
          setPerQuarter(pq);
          setFeatures(feat);
        } catch (e) {
          setError(`Failed to load results: ${e instanceof Error ? e.message : e}`);
        }
      } else if (evt.event === "progress") {
        const key = `${evt.model}|${evt.layer}`;
        setProgress((prev) => ({ ...prev, [key]: evt as TrainProgress }));
      }
    });
    return close;
  }, []);

  return (
    <Layout right={!training ? (
      <button onClick={downloadXlsx}
        className="font-mono text-xs px-3 py-1 border border-[var(--color-border)] hover:border-[var(--color-accent)] text-[var(--color-text-dim)] hover:text-[var(--color-text)] rounded-sm transition-colors">
        Export XLSX
      </button>
    ) : undefined}>
      {schema && (
        <div className="flex gap-6 font-mono text-xs text-[var(--color-text-dim)] mb-4">
          <span>{schema.rows.toLocaleString()} rows</span>
          <span>{schema.quarters} quarters</span>
          <span>{schema.quarter_range}</span>
          <span>{schema.features.length} features</span>
        </div>
      )}

      {training && <Progress roster={roster} progress={progress} />}

      {error && <p className="mt-3 font-mono text-xs text-[var(--color-negative)]">{error}</p>}

      {!training && comparison.length > 0 && (
        <div className="space-y-6">
          <Section title="Model Comparison">
            <ComparisonTable data={comparison} />
          </Section>
          <Section title="Key Metrics" padded>
            <MetricBars data={comparison} />
          </Section>
          {perQuarter.length > 0 && (
            <Section title="IC Over Time — Layer C" padded>
              <ICTimeseries data={perQuarter} />
            </Section>
          )}
          {Object.keys(features).length > 0 && (
            <Section title="Feature Importance — Layer C" padded>
              <FeatureImportanceChart data={features} />
            </Section>
          )}
        </div>
      )}
    </Layout>
  );
}
