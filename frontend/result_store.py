import json
import uuid
from pathlib import Path

RUNS_DIR = Path(__file__).resolve().parent / "data" / "runs"


def save_run(pipeline_result: dict) -> str:
    """Persist full pipeline output to disk; return run id (cookie-safe)."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    path = RUNS_DIR / f"{run_id}.json"
    path.write_text(json.dumps(pipeline_result, ensure_ascii=False), encoding="utf-8")
    return run_id


def load_run(run_id: str) -> dict | None:
    if not run_id:
        return None
    path = RUNS_DIR / f"{run_id}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
