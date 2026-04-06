import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface Props {
  onFile: (file: File) => void;
  loading?: boolean;
}

export default function FileUpload({ onFile, loading }: Props) {
  const onDrop = useCallback((files: File[]) => { if (files[0]) onFile(files[0]); }, [onFile]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { "text/csv": [".csv"] }, multiple: false });

  return (
    <div
      {...getRootProps()}
      className={`border border-dashed rounded-sm p-12 text-center cursor-pointer transition-colors
        ${isDragActive ? "border-[var(--color-accent)] bg-[var(--color-accent)]/5" : "border-[var(--color-border)] hover:border-[var(--color-text-dim)]"}
        ${loading ? "opacity-50 pointer-events-none" : ""}`}
    >
      <input {...getInputProps()} />
      <p className="font-mono text-sm text-[var(--color-text-dim)]">
        {loading ? "Uploading..." : isDragActive ? "Drop CSV here" : "Drop CSV or click to browse"}
      </p>
    </div>
  );
}
