import { useState } from "react";
import { Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import type { Schema } from "./types";

export default function App() {
  const [schema, setSchema] = useState<Schema | null>(null);
  return (
    <Routes>
      <Route path="/" element={<Upload onSchema={setSchema} />} />
      <Route path="/dashboard" element={<Dashboard schema={schema} />} />
    </Routes>
  );
}
