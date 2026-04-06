async function api(url: string, init?: RequestInit) {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const listFiles = () => api("/api/files") as Promise<{ files: string[] }>;
export const selectFile = (name: string) => api(`/api/select/${name}`, { method: "POST" });
export const fetchComparison = () => api("/api/results/comparison");
export const fetchPerQuarter = () => api("/api/results/per-quarter");
export const fetchFeatures = () => api("/api/results/features");

export async function uploadCSV(file: File) {
  const form = new FormData();
  form.append("file", file);
  return api("/api/upload", { method: "POST", body: form });
}

export function trainModels(onEvent: (data: Record<string, unknown>) => void) {
  const es = new EventSource("/api/train");
  es.onmessage = (e) => {
    const data = JSON.parse(e.data);
    onEvent(data);
    if (data.event === "complete") es.close();
  };
  es.onerror = () => es.close();
  return () => es.close();
}

export const downloadXlsx = () => window.open("/api/export/xlsx", "_blank");
