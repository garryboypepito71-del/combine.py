import json
import re
from datetime import datetime
from pathlib import Path

DEFAULT_STATE = {
    "records": [],
    "labor_records": [],
    "payroll_expenses": [],
    "budget": 0.0,
    "remaining_money": 0.0,
    "view": "home",
}


def get_data_file_path(base_dir=None):
    base_path = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parent
    return base_path / "aily_data.json"


def load_state(data_file=None):
    path = Path(data_file) if data_file is not None else get_data_file_path()

    if not path.exists():
        return dict(DEFAULT_STATE)

    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_STATE)

    if not isinstance(loaded, dict):
        return dict(DEFAULT_STATE)

    state = dict(DEFAULT_STATE)
    for key, default_value in DEFAULT_STATE.items():
        if key not in loaded:
            continue
        value = loaded[key]

        if key in {"records", "labor_records", "payroll_expenses"}:
            state[key] = value if isinstance(value, list) else []
        elif key in {"budget", "remaining_money"}:
            try:
                state[key] = float(value)
            except (TypeError, ValueError):
                state[key] = default_value
        else:
            state[key] = value

    return state


def save_state(state, data_file=None):
    path = Path(data_file) if data_file is not None else get_data_file_path()
    payload = {
        "records": state.get("records", []),
        "labor_records": state.get("labor_records", []),
        "payroll_expenses": state.get("payroll_expenses", []),
        "budget": float(state.get("budget", 0.0)),
        "remaining_money": float(state.get("remaining_money", 0.0)),
        "view": state.get("view", "home"),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def get_receipt_root(base_dir=None):
    base_path = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parent
    return base_path / "receipts"


def get_receipt_folder(report_type, base_dir=None):
    root = get_receipt_root(base_dir)
    folder_name = "construction" if report_type == "construction" else "payroll"
    folder = root / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_report_html(report_type, html, title=None, base_dir=None):
    folder = get_receipt_folder(report_type, base_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", title or "receipt").strip("_") or "receipt"
    safe_type = re.sub(r"[^A-Za-z0-9._-]+", "_", report_type).strip("_") or "report"
    file_name = f"{safe_type}_{safe_title}_{timestamp}.html"
    path = folder / file_name
    path.write_text(html, encoding="utf-8")
    return path


def list_saved_reports(report_type, base_dir=None):
    folder = get_receipt_folder(report_type, base_dir)
    files = sorted(folder.glob("*.html"), key=lambda item: item.stat().st_mtime, reverse=True)
    return files


def delete_report_file(report_path, base_dir=None):
    path = Path(report_path)
    if not path.exists():
        return False
    path.unlink(missing_ok=True)
    return True
