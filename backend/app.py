"""FastAPI app — upload CSV, run models, serve results."""

import asyncio
import json
from io import StringIO

import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.pipeline import MODELS, ROOT, build_excel, run_pipeline, validate_csv

DATA_DIR = ROOT / "src" / "data" / "processed"

app = FastAPI(title="Magic Formula ML")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

state = {"df": None, "comparison": None, "per_quarter": None, "features": None}


def _load_df(df):
    schema = validate_csv(df)
    state.update(df=df, schema=schema, comparison=None, per_quarter=None, features=None)
    return schema


def _df_records(key):
    df = state[key]
    if df is None:
        return JSONResponse({"error": "No results yet"}, 400)
    # use pandas to_json to safely handle numpy types, then parse back for JSONResponse
    return JSONResponse(json.loads(df.to_json(orient="records")))


@app.get("/api/files")
async def list_files():
    return {"files": sorted(f.name for f in DATA_DIR.glob("*.csv"))}


@app.post("/api/select/{filename}")
async def select_file(filename: str):
    path = DATA_DIR / filename
    if not path.exists() or path.suffix != ".csv":
        return JSONResponse({"error": "File not found"}, 404)
    return _load_df(pd.read_csv(path))


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    return _load_df(pd.read_csv(StringIO(content.decode("utf-8"))))


@app.get("/api/train")
async def train():
    if state["df"] is None:
        return JSONResponse({"error": "No data uploaded"}, 400)

    events: list[dict] = []

    def on_progress(model, layer, fold, total, auc):
        events.append({"event": "progress", "model": model, "layer": layer,
                        "fold": fold, "total": total, "auc": round(auc or 0, 4)})

    async def stream():
        roster = [{"model": m, "layer": fs} for m, fs, _, _ in MODELS]
        yield f"data: {json.dumps({'event': 'roster', 'models': roster})}\n\n"

        loop = asyncio.get_running_loop()
        task = loop.run_in_executor(None, lambda: run_pipeline(state["df"], on_progress))

        sent = 0
        while not task.done():
            await asyncio.sleep(0.3)
            while sent < len(events):
                yield f"data: {json.dumps(events[sent])}\n\n"
                sent += 1

        comp_df, pq_df, fi = await task
        state.update(comparison=comp_df, per_quarter=pq_df, features=fi)

        while sent < len(events):
            yield f"data: {json.dumps(events[sent])}\n\n"
            sent += 1
        yield f"data: {json.dumps({'event': 'complete'})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/results/comparison")
async def results_comparison():
    return _df_records("comparison")


@app.get("/api/results/per-quarter")
async def results_per_quarter():
    return _df_records("per_quarter")


@app.get("/api/results/features")
async def results_features():
    if state["features"] is None:
        return JSONResponse({"error": "No results yet"}, 400)
    return state["features"]


@app.get("/api/export/xlsx")
async def export_xlsx():
    if state["comparison"] is None:
        return JSONResponse({"error": "No results yet"}, 400)
    buf = build_excel(state["comparison"], state["per_quarter"], state["features"] or {})
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=model_comparison.xlsx"})
