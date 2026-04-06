import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listFiles, selectFile, uploadCSV } from "../api/client";
import FileUpload from "../components/FileUpload";
import Layout from "../components/Layout";
import type { Schema } from "../types";

export default function Upload({ onSchema }: { onSchema: (s: Schema) => void }) {
  const [files, setFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [filesLoading, setFilesLoading] = useState(true);
  const [schema, setSchema] = useState<Schema | null>(null);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    listFiles()
      .then((r) => setFiles(r.files))
      .catch((e) => setError(`Failed to load files: ${e.message ?? e}`))
      .finally(() => setFilesLoading(false));
  }, []);

  const load = async (name: string, fetch: () => Promise<Schema>) => {
    setLoading(true);
    setError("");
    setSelected(name);
    try {
      const s = await fetch();
      setSchema(s);
      onSchema(s);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto mt-16">
        <h1 className="font-mono text-lg font-semibold mb-1">Select Data</h1>
        <p className="text-xs text-[var(--color-text-dim)] mb-6">Choose a file from data/processed/ or drop your own CSV</p>

        {filesLoading ? (
          <p className="font-mono text-xs text-[var(--color-text-dim)] mb-4">Loading files...</p>
        ) : files.length > 0 ? (
          <div className="border border-[var(--color-border)] rounded-sm overflow-hidden mb-4">
            {files.map((f) => (
              <button key={f} onClick={() => load(f, () => selectFile(f))} disabled={loading}
                className={`w-full text-left px-4 py-2.5 font-mono text-sm border-b border-[var(--color-border)]/30 last:border-0 transition-colors
                  ${selected === f ? "bg-[var(--color-accent)]/10 text-[var(--color-accent)]" : "hover:bg-[var(--color-surface)] text-[var(--color-text)]"}
                  ${loading ? "opacity-50" : ""}`}>
                {f}
              </button>
            ))}
          </div>
        ) : !error ? (
          <p className="font-mono text-xs text-[var(--color-text-dim)] mb-4">No CSV files found in data/processed/</p>
        ) : null}

        <details className="mb-4">
          <summary className="font-mono text-xs text-[var(--color-text-dim)] cursor-pointer hover:text-[var(--color-text)]">
            Or upload a different CSV
          </summary>
          <div className="mt-2">
            <FileUpload onFile={(f) => load(f.name, () => uploadCSV(f))} loading={loading} />
          </div>
        </details>

        {error && <p className="mt-3 text-xs text-[var(--color-negative)]">{error}</p>}

        {schema && (
          <div className="mt-6">
            <div className="flex gap-6 font-mono text-xs text-[var(--color-text-dim)] mb-4">
              <span>{schema.rows.toLocaleString()} rows</span>
              <span>{schema.quarters} quarters</span>
              <span>{schema.quarter_range}</span>
              <span>{schema.features.length} features detected</span>
            </div>

            <div className="border border-[var(--color-border)] rounded-sm overflow-hidden mb-6">
              <table className="w-full text-xs font-mono">
                <thead>
                  <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
                    <th className="px-3 py-1.5 text-left text-[var(--color-text-dim)] font-medium">Column</th>
                    <th className="px-3 py-1.5 text-left text-[var(--color-text-dim)] font-medium">Type</th>
                    <th className="px-3 py-1.5 text-left text-[var(--color-text-dim)] font-medium">Sample</th>
                    <th className="px-3 py-1.5 text-left text-[var(--color-text-dim)] font-medium">Role</th>
                  </tr>
                </thead>
                <tbody>
                  {schema.columns.map((col) => (
                    <tr key={col.name} className="border-b border-[var(--color-border)]/30">
                      <td className="px-3 py-1">{col.name}</td>
                      <td className="px-3 py-1 text-[var(--color-text-dim)]">{col.dtype}</td>
                      <td className="px-3 py-1 text-[var(--color-text-dim)]">{col.sample.slice(0, 20)}</td>
                      <td className="px-3 py-1">
                        {schema.features.includes(col.name)
                          ? <span className="text-[var(--color-accent)]">feature</span>
                          : <span className="text-[var(--color-text-dim)]">meta</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button onClick={() => nav("/dashboard")}
              className="font-mono text-sm px-4 py-2 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white rounded-sm transition-colors">
              Run Models
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
