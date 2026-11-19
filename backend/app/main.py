import io
import re
import multiprocessing as mp

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .llm import generate_code, suggest_questions

app = FastAPI(title="AI Excel Copilot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

BLOCKED = re.compile(
    r"\b(import|__\w+__|open|exec|eval|compile|os|sys|subprocess|socket|shutil|input|globals|locals|getattr|setattr|to_csv|to_excel|read_csv|read_excel)\b"
)
SAFE_BUILTINS = {
    k: __builtins__[k] if isinstance(__builtins__, dict) else getattr(__builtins__, k)
    for k in "len range min max sum abs round sorted list dict set tuple str int float bool enumerate zip map filter any all".split()
}


def _worker(code, df, q):
    try:
        scope = {"df": df.copy(), "pd": pd, "np": np}
        exec(code, {"__builtins__": SAFE_BUILTINS}, scope)
        if "result" not in scope:
            raise ValueError("Code did not set a `result` variable.")
        q.put(("ok", scope["result"]))
    except Exception as e:  # noqa: BLE001
        q.put(("err", f"{type(e).__name__}: {e}"))


def run_code(code: str, df: pd.DataFrame):
    """Run generated code in a separate process with a timeout. NOT a full sandbox."""
    if BLOCKED.search(code):
        raise ValueError("Generated code used a blocked operation.")
    q = mp.Queue()
    p = mp.Process(target=_worker, args=(code, df, q))
    p.start()
    p.join(config.EXEC_TIMEOUT_SEC)
    if p.is_alive():
        p.terminate()
        raise TimeoutError("Code took too long to run.")
    if q.empty():
        raise RuntimeError("Code crashed before returning a result.")
    status, val = q.get()
    if status == "err":
        raise RuntimeError(val)
    return val


def to_frame(r) -> pd.DataFrame:
    if isinstance(r, pd.DataFrame):
        return r.reset_index(drop=True)
    if isinstance(r, pd.Series):
        return r.reset_index()
    return pd.DataFrame({"Result": [r]})


def clean(v):
    if v is None or (isinstance(v, float) and np.isnan(v)) or v is pd.NaT:
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if np.isnan(v) else float(v)
    if isinstance(v, (pd.Timestamp,)):
        return v.isoformat()
    return v if isinstance(v, (int, float, str, bool)) else str(v)


def read_dataframe(raw, filename):
    name = (filename or "").lower()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(raw), nrows=config.MAX_ROWS)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(raw), nrows=config.MAX_ROWS)
    raise ValueError("Upload a .xlsx, .xls or .csv file.")


def dataframe_suggestions(df):
    sample_values = {
        column: [str(value) for value in df[column].dropna().head(3).tolist()]
        for column in df.select_dtypes(exclude="number").columns
    }
    return suggest_questions(
        list(df.columns),
        [str(dtype) for dtype in df.dtypes],
        sample_values,
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/suggestions")
async def suggestions(file: UploadFile = File(...)):
    try:
        raw = await file.read()
        if len(raw) > config.MAX_FILE_MB * 1024 * 1024:
            raise ValueError(f"File is larger than {config.MAX_FILE_MB} MB.")
        df = read_dataframe(raw, file.filename)
        if df.empty:
            raise ValueError("The file has no rows.")
        return {"suggestions": dataframe_suggestions(df), "error": None}
    except Exception as e:  # noqa: BLE001
        return {"suggestions": [], "error": str(e)}


@app.post("/api/ask")
async def ask(file: UploadFile = File(...), question: str = Form(...)):
    out = {
        "python_code": "", "columns": [], "rows": [], "row_count": 0,
        "suggestions": [], "error": None,
    }
    try:
        raw = await file.read()
        if len(raw) > config.MAX_FILE_MB * 1024 * 1024:
            raise ValueError(f"File is larger than {config.MAX_FILE_MB} MB.")
        df = read_dataframe(raw, file.filename)
        if df.empty:
            raise ValueError("The file has no rows.")
        out["suggestions"] = dataframe_suggestions(df)
        code = generate_code(list(df.columns), [str(t) for t in df.dtypes], question)
        out["python_code"] = code
        res = to_frame(run_code(code, df)).head(config.MAX_ROWS)
        out["columns"] = [str(c) for c in res.columns]
        out["rows"] = [[clean(v) for v in row] for row in res.itertuples(index=False)]
        out["row_count"] = len(res)
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)
    return out
