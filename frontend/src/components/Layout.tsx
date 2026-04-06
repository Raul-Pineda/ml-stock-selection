import type { ReactNode } from "react";

export default function Layout({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <header className="h-11 flex items-center justify-between px-4 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        <span className="font-mono text-sm font-semibold tracking-wide text-[var(--color-text)]">
          MAGIC FORMULA ML
        </span>
        {right && <div className="flex gap-2">{right}</div>}
      </header>
      <main className="p-4">{children}</main>
    </div>
  );
}
