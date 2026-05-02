from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


MODELS = ["svm", "rf", "lgbm", "xgboost", "lasso", "ridge", "lstm", "cnn_lstm", "gru", "tcn"]
ML_MODELS = {"svm", "rf", "lgbm", "xgboost", "lasso", "ridge"}
DL_MODELS = {"lstm", "cnn_lstm", "gru", "tcn"}
TASKS = ["classification", "regression"]
VARIANTS = ["onchain", "ta", "all", "boruta_onchain", "boruta_ta", "boruta_all", "univariate"]
VALID_TASKS = {
    "svm": {"classification", "regression"},
    "rf": {"classification", "regression"},
    "lgbm": {"classification", "regression"},
    "xgboost": {"classification", "regression"},
    "lasso": {"regression"},
    "ridge": {"regression"},
    "lstm": {"classification", "regression"},
    "cnn_lstm": {"classification", "regression"},
    "gru": {"classification", "regression"},
    "tcn": {"classification", "regression"},
}

VARIANT_LABELS = {
    "onchain": "链上",
    "ta": "技术面",
    "all": "融合",
    "boruta_onchain": "筛选链上",
    "boruta_ta": "筛选技术面",
    "boruta_all": "筛选融合",
    "univariate": "单变量",
}

STATUS_LABELS = {
    "complete": "完整",
    "missing_report": "缺报告",
    "missing_backtest": "缺回测",
    "missing_train": "缺预测",
}

MODEL_LABELS = {
    "svm": "SVM",
    "rf": "Random Forest",
    "lgbm": "LightGBM",
    "xgboost": "XGBoost",
    "lasso": "Lasso",
    "ridge": "Ridge",
    "lstm": "LSTM",
    "cnn_lstm": "CNN-LSTM",
    "gru": "GRU",
    "tcn": "TCN",
}

TASK_LABELS = {
    "classification": "分类任务",
    "regression": "回归任务",
}

STEP_LABELS = {
    "train": "模型训练",
    "backtest": "回测分析",
    "report": "报告生成",
}

RUN_STATUS_LABELS = {
    "running": "实时运行",
    "completed": "运行完成",
    "dry_run": "扫描中",
    "dry_run_completed": "扫描完成",
    "interrupted": "已中断",
    "failed": "运行失败",
}

SUMMARY_STATUS_LABELS = {
    "completed": "已完成",
    "skipped_existing": "已存在，跳过",
    "dry_run_existing": "扫描：已存在",
    "dry_run_missing": "扫描：缺失",
    "failed": "失败",
    "restored_old_better": "保留旧结果",
}


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def artifact_prefix(root: Path) -> str:
    config = root / "configs" / "experiment.yaml"
    if not config.exists():
        return "btc_predict"
    for line in config.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*artifact_prefix:\s*(\S+)\s*$", line)
        if match:
            return match.group(1).strip("\"'")
    return "btc_predict"


def combo_paths(root: Path, prefix: str, model: str, task: str, variant: str) -> dict[str, Path]:
    stem = f"{prefix}_{model}_{task}_{variant}"
    return {
        "preds": root / "data" / "features" / f"{stem}_preds.parquet",
        "metrics": root / "data" / "features" / f"{stem}_metrics.json",
        "backtest": root / "data" / "features" / f"{stem}_backtest_sensitivity.csv",
        "equity": root / "data" / "features" / f"{stem}_equity.parquet",
        "summary": root / "reports" / "experiments" / "summaries" / f"{prefix}_summary_{model}_{task}_{variant}.md",
    }


def combo_status(paths: dict[str, Path]) -> str:
    if not paths["preds"].exists() or not paths["metrics"].exists():
        return "missing_train"
    if not paths["backtest"].exists() or not paths["equity"].exists():
        return "missing_backtest"
    if not paths["summary"].exists():
        return "missing_report"
    return "complete"


def load_metric(path: Path, model: str, task: str) -> dict[str, float]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if task == "classification":
        return {
            key: float(data.get(f"{model}_classification_oos_{key}", "nan"))
            for key in ["accuracy", "precision", "recall", "f1"]
            if f"{model}_classification_oos_{key}" in data
        }
    return {
        key: float(data.get(f"{model}_regression_oos_{key}", "nan"))
        for key in ["rmse", "mae", "r2", "ic", "rank_ic"]
        if f"{model}_regression_oos_{key}" in data
    }


def fmt_num(value: float | str | None, digits: int = 4) -> str:
    if value is None or value == "":
        return ""
    try:
        number = float(value)
    except Exception:
        return str(value)
    if number != number:
        return ""
    return f"{number:.{digits}f}"


def human_duration(seconds: float | int | None) -> str:
    if seconds is None:
        return "--"
    try:
        seconds = max(0, int(float(seconds)))
    except Exception:
        return "--"
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def family(model: str) -> str:
    return "机器学习" if model in ML_MODELS else "深度学习"


def variant_group(variant: str) -> str:
    if variant == "univariate":
        return "单变量基线"
    if variant in {"ta", "boruta_ta"}:
        return "不含链上"
    return "包含链上"


def build_matrix(root: Path, prefix: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for model in MODELS:
        for task in TASKS:
            if task not in VALID_TASKS[model]:
                continue
            for variant in VARIANTS:
                paths = combo_paths(root, prefix, model, task, variant)
                rows.append(
                    {
                        "model": model,
                        "task": task,
                        "variant": variant,
                        "family": family(model),
                        "variant_group": variant_group(variant),
                        "status": combo_status(paths),
                        "metrics": load_metric(paths["metrics"], model, task),
                    }
                )
    return rows


def latest_state(root: Path) -> dict[str, object]:
    path = root / "reports" / "supplement_runs" / "latest_run_state.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def latest_summary(root: Path) -> tuple[Path | None, list[dict[str, str]]]:
    summaries = sorted(
        (root / "reports" / "supplement_runs").glob("*/full_matrix_summary.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not summaries:
        return None, []
    path = summaries[0]
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return path, list(csv.DictReader(f))


def all_summaries(root: Path) -> list[tuple[Path, list[dict[str, str]]]]:
    paths = sorted(
        (root / "reports" / "supplement_runs").glob("*/full_matrix_summary.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    result = []
    for path in paths[:20]:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                result.append((path, list(csv.DictReader(f))))
        except Exception:
            continue
    return result


def recent_logs(root: Path, limit: int = 20) -> list[Path]:
    return sorted(
        (root / "reports" / "supplement_runs").glob("*/logs/*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]


def read_tail(path: Path, max_lines: int = 18) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:])
    except Exception:
        return ""


def top_tables(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    cls = [row for row in rows if row["task"] == "classification" and "f1" in row["metrics"]]
    reg = [row for row in rows if row["task"] == "regression" and ("ic" in row["metrics"] or "rmse" in row["metrics"])]
    cls_top = sorted(cls, key=lambda row: row["metrics"].get("f1", -999), reverse=True)
    reg_top = sorted(reg, key=lambda row: (row["metrics"].get("ic", -999), -row["metrics"].get("rmse", 999)), reverse=True)
    return cls_top, reg_top


def status_cards(rows: list[dict[str, object]]) -> str:
    total = len(rows)
    counts = Counter(row["status"] for row in rows)
    done = counts["complete"]
    cards = [
        ("完整产物", f"{done}/{total}", "可直接进入论文结果表"),
        ("缺预测", str(counts["missing_train"]), "需要 train"),
        ("缺回测", str(counts["missing_backtest"]), "需要 backtest"),
        ("缺报告", str(counts["missing_report"]), "需要 report"),
    ]
    return "".join(
        f"<article class='metric-card'><span>{html.escape(title)}</span><b>{html.escape(value)}</b><small>{html.escape(sub)}</small></article>"
        for title, value, sub in cards
    )


def latest_events_html(rows: list[dict[str, object]]) -> str:
    open_rows = [row for row in rows if row.get("status") != "complete"]
    if not open_rows:
        return "<p class='muted'>暂无待补事项。</p>"
    order = {"missing_train": 0, "missing_backtest": 1, "missing_report": 2}
    open_rows = sorted(open_rows, key=lambda row: (order.get(str(row.get("status")), 9), str(row.get("model")), str(row.get("task")), str(row.get("variant"))))[:10]
    return "".join(
        f"<li class='{html.escape(row.get('status',''))}'><b>{html.escape(row.get('model',''))}</b>"
        f"<span>{html.escape(TASK_LABELS.get(row.get('task',''), row.get('task','')))} / {html.escape(VARIANT_LABELS.get(row.get('variant',''), row.get('variant','')))}</span>"
        f"<em>{html.escape(SUMMARY_STATUS_LABELS.get(row.get('status',''), row.get('status','')))}</em></li>"
        for row in open_rows
    )


def matrix_table(rows: list[dict[str, object]], task: str, model_set: set[str], title: str, view_id: str) -> str:
    row_map = {(row["model"], row["variant"]): row for row in rows if row["task"] == task and row["model"] in model_set}
    models = [model for model in MODELS if model in model_set and task in VALID_TASKS[model]]
    header = "".join(f"<th>{html.escape(VARIANT_LABELS[v])}</th>" for v in VARIANTS)
    body = []
    for model in models:
        cells = []
        for variant in VARIANTS:
            row = row_map.get((model, variant))
            if not row:
                cells.append("<td class='na'>N/A</td>")
                continue
            status = str(row["status"])
            metrics = row["metrics"]
            metric_line = ""
            if task == "classification" and "f1" in metrics:
                metric_line = f"F1 {fmt_num(metrics.get('f1'))}"
            elif task == "regression":
                metric_line = f"IC {fmt_num(metrics.get('ic'))}" if "ic" in metrics else f"RMSE {fmt_num(metrics.get('rmse'))}"
            cells.append(
                f"<td class='cell {status}' title='{html.escape(model + ' / ' + task + ' / ' + variant)}'>"
                f"<b>{html.escape(STATUS_LABELS[status])}</b><span>{html.escape(metric_line)}</span></td>"
            )
        body.append(f"<tr><th>{html.escape(model)}</th>{''.join(cells)}</tr>")
    return f"<section class='matrix-panel' data-matrix='{view_id}'><h3>{html.escape(title)}</h3><table class='matrix'><thead><tr><th>模型</th>{header}</tr></thead><tbody>{''.join(body)}</tbody></table></section>"


def top_table(rows: list[dict[str, object]], task: str, title: str) -> str:
    if task == "classification":
        headers = ["#", "模型类别", "模型", "数据集", "链上信息", "Accuracy", "Precision", "Recall", "F1"]
        lines = []
        for i, row in enumerate(rows, 1):
            m = row["metrics"]
            values = [i, row["family"], row["model"], row["variant"], row["variant_group"], fmt_num(m.get("accuracy")), fmt_num(m.get("precision")), fmt_num(m.get("recall")), fmt_num(m.get("f1"))]
            lines.append("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in values) + "</tr>")
    else:
        headers = ["#", "模型类别", "模型", "数据集", "链上信息", "RMSE", "MAE", "IC", "RankIC"]
        lines = []
        for i, row in enumerate(rows, 1):
            m = row["metrics"]
            values = [i, row["family"], row["model"], row["variant"], row["variant_group"], fmt_num(m.get("rmse")), fmt_num(m.get("mae")), fmt_num(m.get("ic")), fmt_num(m.get("rank_ic"))]
            lines.append("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in values) + "</tr>")
    return (
        f"<article class='rank-card'>"
        f"<div class='rank-head'><h3>{html.escape(title)}</h3><span>{len(rows)} 条结果</span></div>"
        f"<div class='rank-scroll'><table class='top-table'><thead><tr>{''.join(f'<th>{html.escape(h)}</th>' for h in headers)}</tr></thead>"
        f"<tbody>{''.join(lines)}</tbody></table></div></article>"
    )


def logs_view(logs: list[Path]) -> str:
    if not logs:
        return "<p class='muted'>暂无日志。</p>"
    items = []
    panels = []
    for idx, path in enumerate(logs):
        active = "active" if idx == 0 else ""
        escaped_name = html.escape(path.name)
        items.append(f"<button class='log-item {active}' data-log='{idx}'>{escaped_name}<small>{datetime.fromtimestamp(path.stat().st_mtime).strftime('%H:%M:%S')}</small></button>")
        tail = read_tail(path)
        error_class = "has-error" if ("Traceback" in tail or "Error" in tail or "ModuleNotFound" in tail) else ""
        panels.append(f"<pre class='log-panel {active} {error_class}' data-log-panel='{idx}'>{html.escape(tail)}</pre>")
    return f"<div class='logs-layout'><aside>{''.join(items)}</aside><main>{''.join(panels)}</main></div>"


def runs_view(summaries: list[tuple[Path, list[dict[str, str]]]]) -> str:
    if not summaries:
        return "<p class='muted'>暂无历史批次。</p>"
    lines = []
    for path, rows in summaries:
        counts = Counter(row.get("status", "") for row in rows)
        run_id = path.parent.name
        values = [
            run_id,
            str(len(rows)),
            str(counts.get("completed", 0)),
            str(counts.get("failed", 0)),
            str(counts.get("skipped_existing", 0)),
            str(path),
        ]
        lines.append("<tr>" + "".join(f"<td>{html.escape(v)}</td>" for v in values) + "</tr>")
    headers = ["运行批次", "总记录", "completed", "failed", "skipped", "summary path"]
    return f"<table class='top-table'><thead><tr>{''.join(f'<th>{h}</th>' for h in headers)}</tr></thead><tbody>{''.join(lines)}</tbody></table>"


def live_batch_path(state: dict[str, object], fallback: str) -> str:
    run_root = state.get("run_root") if isinstance(state, dict) else None
    return str(run_root) if run_root else fallback


def live_batch_counts(state: dict[str, object], fallback: str) -> str:
    if not isinstance(state, dict) or not state:
        return fallback
    processed = state.get("processed", "--")
    total = state.get("total", "--")
    status = RUN_STATUS_LABELS.get(str(state.get("status", "")), str(state.get("status", "")) or "--")
    counts = state.get("counts", {})
    if isinstance(counts, dict) and counts:
        completed = counts.get("completed", 0)
        skipped = counts.get("skipped_existing", 0)
        failed = counts.get("failed", 0)
        missing = counts.get("dry_run_missing", 0)
        parts = [
            f"本次脚本进度 {processed}/{total}",
            f"新完成 {completed}",
            f"已有结果跳过 {skipped}",
            f"失败 {failed}",
        ]
        if missing:
            parts.append(f"扫描缺失 {missing}")
        return f"{status} ｜ " + " ｜ ".join(parts)
    return f"{status} ｜ 本次脚本进度 {processed}/{total}"


def state_seed(state: dict[str, object]) -> str:
    return json.dumps(state, ensure_ascii=False).replace("</", "<\\/")


def js_seed(name: str, value: object) -> str:
    return f"const {name} = {json.dumps(value, ensure_ascii=False)};"


def dashboard_data(root: Path) -> dict[str, object]:
    prefix = artifact_prefix(root)
    rows = build_matrix(root, prefix)
    state = latest_state(root)
    latest_path, latest_rows = latest_summary(root)
    summaries = all_summaries(root)
    logs = recent_logs(root)
    cls_top, reg_top = top_tables(rows)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    latest_count = Counter(row.get("status", "") for row in latest_rows)
    latest_count_text = " · ".join(
        f"{SUMMARY_STATUS_LABELS.get(k, k)}: {v}" for k, v in latest_count.items()
    )
    latest_path_text = str(latest_path) if latest_path else "暂无"
    current_batch_path_text = live_batch_path(state, latest_path_text)
    current_batch_count_text = live_batch_counts(state, latest_count_text or "暂无摘要")
    matrix_html = (
        "<div class='matrix-tabs'>"
        "<button class='active' data-matrix-target='ml-cls'>机器学习-分类</button>"
        "<button data-matrix-target='ml-reg'>机器学习-回归</button>"
        "<button data-matrix-target='dl-cls'>深度学习-分类</button>"
        "<button data-matrix-target='dl-reg'>深度学习-回归</button>"
        "</div>"
        + matrix_table(rows, "classification", ML_MODELS, "机器学习分类任务进度矩阵", "ml-cls").replace("matrix-panel", "matrix-panel active", 1)
        + matrix_table(rows, "regression", ML_MODELS, "机器学习回归任务进度矩阵", "ml-reg")
        + matrix_table(rows, "classification", DL_MODELS, "深度学习分类任务进度矩阵", "dl-cls")
        + matrix_table(rows, "regression", DL_MODELS, "深度学习回归任务进度矩阵", "dl-reg")
    )
    top_rank_html = (
        top_table(cls_top, "classification", "分类任务 Top Rank（按 F1）")
        + top_table(reg_top, "regression", "回归任务 Top Rank（按 IC，RMSE 辅助）")
    )
    return {
        "built_at": now,
        "prefix": prefix,
        "state": state,
        "status_cards_html": status_cards(rows),
        "latest_path_text": current_batch_path_text,
        "latest_count_text": current_batch_count_text,
        "latest_events_html": latest_events_html(rows),
        "matrix_html": matrix_html,
        "top_rank_html": top_rank_html,
        "logs_html": logs_view(logs),
        "runs_html": runs_view(summaries),
    }


def render(root: Path, refresh_seconds: int) -> str:
    data = dashboard_data(root)
    now = str(data["built_at"])
    state = data["state"]
    css = """
    :root{--bg:#06090d;--panel:rgba(12,20,28,.78);--panel2:rgba(7,13,18,.9);--line:rgba(106,232,255,.18);--text:#effcff;--muted:#8ca8b0;--cyan:#5ef7ff;--green:#43ff9a;--amber:#ffd166;--red:#ff5267;--blue:#60a5fa}
    html{font-size:16px;-webkit-text-size-adjust:100%;text-size-adjust:100%}
    *{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 14% 0%,rgba(67,255,154,.16),transparent 28%),radial-gradient(circle at 94% 18%,rgba(94,247,255,.15),transparent 32%),linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px),#06090d;background-size:auto,auto,24px 24px,24px 24px;color:var(--text);font-family:'Microsoft YaHei UI','Microsoft YaHei','Segoe UI',sans-serif;font-size:15px;overflow:hidden}
    body:before{content:"";position:fixed;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(255,255,255,.024) 0,rgba(255,255,255,.024) 1px,transparent 1px,transparent 5px);opacity:.36}
    *{scrollbar-width:none} *::-webkit-scrollbar{width:0;height:0}
    .topbar{height:76px;display:grid;grid-template-columns:300px 1fr 220px;gap:18px;align-items:center;padding:12px 20px;border-bottom:1px solid var(--line);background:rgba(4,8,12,.94);backdrop-filter:blur(18px);position:fixed;inset:0 0 auto 0;z-index:10}
    .brand h1{margin:0;font-size:22px;letter-spacing:.06em}.brand span{display:none}
    .top-meta{justify-self:center;color:#eaffff;font-size:28px;font-weight:900;letter-spacing:.16em;white-space:nowrap;text-shadow:0 0 24px rgba(94,247,255,.28)}
    .top-health{justify-self:end;border:1px solid var(--line);border-radius:999px;padding:9px 13px;background:rgba(13,25,33,.72);font-family:Consolas,monospace;color:var(--muted);white-space:nowrap}.top-health b{color:var(--green)}
    .shell{display:grid;grid-template-columns:220px 1fr;height:calc(100vh - 76px);margin-top:76px}
    .sidebar{border-right:1px solid var(--line);padding:20px 12px;background:rgba(5,10,15,.72);backdrop-filter:blur(16px);display:flex;flex-direction:column}.nav button{width:100%;display:flex;align-items:center;gap:10px;margin:8px 0;padding:14px 16px;border:1px solid transparent;border-radius:15px;background:transparent;color:var(--muted);text-align:left;cursor:pointer;font-size:16px;font-weight:700}.nav button.active,.nav button:hover{border-color:var(--line);background:rgba(94,247,255,.08);color:var(--text);box-shadow:inset 0 0 24px rgba(94,247,255,.035)}.legend{margin-top:auto;margin-bottom:18px;padding:14px 10px;color:var(--muted);font-size:15px;border:1px solid rgba(106,232,255,.08);border-radius:16px;background:rgba(0,0,0,.12)}.legend span{display:flex;align-items:center;gap:10px;margin:13px 0;letter-spacing:.02em}.dot{display:inline-block;width:12px;height:12px;border-radius:50%;box-shadow:0 0 16px currentColor;flex:0 0 auto}.dot.complete{background:var(--green);color:var(--green)}.dot.missing_train{background:var(--red);color:var(--red)}.dot.missing_backtest{background:var(--amber);color:var(--amber)}.dot.missing_report{background:var(--blue);color:var(--blue)}
    .content{height:100%;overflow:hidden;padding:20px 22px}.view{display:none;height:100%;overflow:hidden;animation:fade .18s ease}.view.active{display:flex;flex-direction:column;gap:14px}@keyframes fade{from{opacity:.5;transform:translateY(4px)}to{opacity:1;transform:none}}
    .grid4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.metric-card,.panel,.table-card,.matrix-panel,.cockpit{border:1px solid var(--line);background:var(--panel);border-radius:18px;box-shadow:0 22px 60px rgba(0,0,0,.28),inset 0 1px rgba(255,255,255,.06);backdrop-filter:blur(18px)}.metric-card{padding:18px;min-width:0;clip-path:polygon(0 0,calc(100% - 16px) 0,100% 16px,100% 100%,16px 100%,0 calc(100% - 16px))}.metric-card span{color:var(--muted);font-size:14px}.metric-card b{display:block;margin:8px 0;font-size:30px;font-family:Consolas,monospace}.metric-card small{color:var(--muted);font-size:13px}
    .cockpit{display:grid;grid-template-columns:220px minmax(420px,1fr) 430px;gap:22px;align-items:center;margin-bottom:14px;padding:20px 24px;min-height:230px;background:linear-gradient(135deg,rgba(94,247,255,.1),rgba(12,20,28,.86) 36%,rgba(67,255,154,.075));position:relative;overflow:hidden}
    .cockpit:before{content:"";position:absolute;inset:-40%;background:linear-gradient(100deg,transparent 42%,rgba(94,247,255,.07),transparent 58%);animation:sweep 5s linear infinite;pointer-events:none}@keyframes sweep{from{transform:translateX(-20%)}to{transform:translateX(20%)}}
    .ring{width:148px;height:148px;border-radius:50%;display:grid;place-items:center;justify-self:center;background:conic-gradient(var(--green) 0deg,var(--cyan) 0deg,rgba(255,255,255,.08) 0deg);box-shadow:0 0 36px rgba(94,247,255,.18),inset 0 0 28px rgba(0,0,0,.45);position:relative}.ring:after{content:"";position:absolute;inset:16px;border-radius:50%;background:#071015;border:1px solid var(--line)}.ring b{position:relative;z-index:1;font-family:Consolas,monospace;font-size:30px;transform:translateY(-6px)}.ring span{position:absolute;z-index:1;transform:translateY(26px);font-size:12px;color:var(--muted)}.cockpit-head{display:grid;grid-template-columns:auto auto 1fr;align-items:center;gap:10px;margin-bottom:10px}.cockpit h2{margin:0;font-size:24px;color:var(--text);font-weight:900;letter-spacing:.02em}.run-badge{justify-self:end;border:1px solid rgba(106,232,255,.2);border-radius:999px;padding:6px 10px;background:rgba(0,0,0,.16);font-family:Consolas,monospace;color:#c9fff5;font-size:13px}.cockpit code{display:block;font-size:15px;color:#ccfff6;min-height:0}.cockpit code:empty{display:none}.hint-tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.hint-tags span{border:1px solid rgba(106,232,255,.14);border-radius:999px;padding:5px 9px;background:rgba(94,247,255,.045);color:var(--muted);font-size:12px}
    .status-pill{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:999px;padding:6px 10px;margin-left:8px;color:var(--muted);font-size:12px}.status-pill:before{content:"";width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 14px var(--green)}.status-pill.stale:before{background:var(--amber);box-shadow:0 0 14px var(--amber)}
    .task-grid{display:grid;grid-template-columns:repeat(4,minmax(110px,1fr));gap:10px;margin:14px 0}.task-chip{border:1px solid var(--line);border-radius:13px;padding:10px 12px;background:rgba(0,0,0,.15)}.task-chip small{display:block;color:var(--muted);font-size:12px}.task-chip b{display:block;margin-top:4px;font-size:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .progress-stack{display:grid;gap:12px;margin-top:16px}.progress-row label{display:flex;justify-content:space-between;margin-bottom:6px;color:var(--muted);font-size:13px;font-family:Consolas,monospace}.bigbar{height:14px;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:rgba(255,255,255,.07)}.bigbar div{height:100%;width:0;background:linear-gradient(90deg,var(--green),var(--cyan),#d8ff78);transition:width .45s ease}
    .run-facts{display:grid;gap:10px;position:relative;z-index:1}.run-facts div{border:1px solid var(--line);border-radius:13px;padding:10px 12px;background:rgba(0,0,0,.16)}.run-facts small{display:block;color:var(--muted);font-size:12px}.run-facts b{display:block;margin-top:3px;font-family:Consolas,monospace;font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .batch-box{display:grid;grid-template-columns:minmax(0,1fr) 620px;gap:18px;align-items:center;border:1px solid var(--line);border-radius:18px;padding:16px 18px;background:linear-gradient(145deg,rgba(7,16,21,.88),rgba(12,28,25,.72));position:relative;z-index:1;min-width:0}.batch-main{min-width:0}.batch-box h2{margin:0 0 10px;font-size:20px;letter-spacing:.06em}.batch-path{font-family:Consolas,monospace;font-size:17px;font-weight:800;color:#d8fbff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border:1px solid rgba(106,232,255,.13);border-radius:13px;padding:11px 12px;background:rgba(0,0,0,.16)}.batch-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.batch-stat{border:1px solid rgba(106,232,255,.14);border-radius:13px;padding:11px 12px;background:rgba(0,0,0,.17)}.batch-stat small{display:block;color:var(--muted);font-size:12px}.batch-stat b{display:block;margin-top:5px;font-family:Consolas,monospace;font-size:22px}.batch-stat.fail b{color:var(--red)}.batch-stat.skip b{color:var(--amber)}.batch-stat.done b{color:var(--green)}
    .panel,.table-card,.matrix-panel{padding:16px;margin-top:0}.panel h2,.table-card h3,.matrix-panel h3{margin:0 0 12px;font-size:18px;letter-spacing:.04em}.muted{color:var(--muted)}.pathline{font-family:Consolas,monospace;font-size:14px;color:#bad4dc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.batch-counts{font-size:16px;font-weight:700}
    .events-panel{flex:1;min-height:0;overflow:auto}.events{list-style:none;padding:0;margin:0;display:grid;gap:8px}.events li{display:grid;grid-template-columns:120px 1fr 150px;gap:10px;align-items:center;border:1px solid var(--line);border-radius:12px;padding:9px 11px;background:rgba(0,0,0,.18)}.events em{font-style:normal;text-align:right;color:var(--muted)}.events li.failed em{color:var(--red)}.events li.completed em,.events li.skipped_existing em{color:var(--green)}.events li.dry_run_missing em{color:var(--amber)}
    .matrix-tabs{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:12px}.matrix-tabs button{border:1px solid var(--line);background:rgba(94,247,255,.05);color:var(--muted);border-radius:999px;padding:8px 12px;cursor:pointer}.matrix-tabs button.active{color:var(--text);background:rgba(94,247,255,.15)}
    .matrix-panel{display:none}.matrix-panel.active{display:block}table{width:100%;border-collapse:separate;border-spacing:0}th,td{padding:10px 11px;border-bottom:1px solid var(--line);text-align:center;white-space:nowrap}th{color:#dff8ff}.matrix td{min-width:112px}.cell b{display:block;font-size:13px}.cell span{display:block;margin-top:4px;color:rgba(255,255,255,.8);font-family:Consolas,monospace}.complete{background:linear-gradient(155deg,rgba(67,255,154,.28),rgba(67,255,154,.06))}.missing_train{background:linear-gradient(155deg,rgba(255,82,103,.32),rgba(255,82,103,.06))}.missing_backtest{background:linear-gradient(155deg,rgba(255,209,102,.32),rgba(255,209,102,.06))}.missing_report{background:linear-gradient(155deg,rgba(96,165,250,.32),rgba(96,165,250,.06))}.na{color:#52636b;background:rgba(255,255,255,.025)}
    .top-results{height:100%;min-height:0;display:grid;grid-template-rows:1fr 1fr;gap:14px}.rank-card{min-width:0;min-height:0;border:1px solid var(--line);background:linear-gradient(135deg,rgba(94,247,255,.055),rgba(8,16,22,.86) 32%,rgba(67,255,154,.035));border-radius:18px;box-shadow:0 22px 60px rgba(0,0,0,.28),inset 0 1px rgba(255,255,255,.06);backdrop-filter:blur(18px);padding:16px;display:flex;flex-direction:column;position:relative;overflow:hidden}.rank-card:before{content:"";position:absolute;inset:0 0 auto;height:2px;background:linear-gradient(90deg,transparent,var(--cyan),var(--green),transparent);opacity:.75}.rank-card:after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(90deg,rgba(94,247,255,.04) 1px,transparent 1px);background-size:32px 100%;opacity:.35}.rank-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;position:relative;z-index:1}.rank-head h3{margin:0;font-size:24px;letter-spacing:.07em;text-shadow:0 0 20px rgba(94,247,255,.22)}.rank-head h3:before{content:"TOP RANK";display:inline-block;margin-right:12px;border:1px solid rgba(94,247,255,.24);border-radius:999px;padding:5px 10px;color:var(--cyan);background:rgba(94,247,255,.065);font-family:Consolas,monospace;font-size:13px;font-weight:900;letter-spacing:.14em;vertical-align:middle}.rank-head span{border:1px solid rgba(106,232,255,.14);border-radius:999px;padding:6px 10px;color:var(--muted);font-size:13px;background:rgba(0,0,0,.16)}.rank-scroll{position:relative;z-index:1;min-height:0;flex:1;overflow:auto}.top-table td,.top-table th{text-align:left}.top-table thead th{position:sticky;top:0;z-index:1;background:rgba(8,16,22,.96);backdrop-filter:blur(12px)}.top-table td:nth-child(n+6),.top-table th:nth-child(n+6){text-align:right;font-family:Consolas,monospace}.top-table tr:hover{background:rgba(94,247,255,.055)}
    .logs-layout{display:grid;grid-template-columns:360px 1fr;gap:14px;height:calc(100vh - 170px)}.logs-layout aside,.logs-layout main{min-height:0;overflow:auto}.log-item{width:100%;display:block;text-align:left;border:1px solid var(--line);background:rgba(9,18,25,.72);color:var(--text);border-radius:12px;padding:10px;margin-bottom:8px;cursor:pointer}.log-item small{display:block;color:var(--muted)}.log-item.active{border-color:var(--cyan);box-shadow:0 0 22px rgba(94,247,255,.1)}.log-panel{display:none;margin:0;height:100%;white-space:pre-wrap;overflow:auto;border:1px solid var(--line);border-radius:14px;background:#06090d;color:#b9d4db;padding:14px;line-height:1.45}.log-panel.active{display:block}.log-panel.has-error{border-color:rgba(255,82,103,.45);box-shadow:inset 0 0 22px rgba(255,82,103,.08)}
    @media(max-width:1500px){.topbar{grid-template-columns:240px 1fr 190px}.top-health{font-size:12px}.top-meta{font-size:22px}.grid4{grid-template-columns:repeat(2,minmax(0,1fr))}.cockpit{grid-template-columns:150px 1fr}.run-facts{grid-column:1 / -1;grid-template-columns:repeat(4,1fr)}.batch-box{grid-template-columns:1fr}.batch-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
    @media(max-width:1100px){.topbar{grid-template-columns:1fr;height:auto;position:relative}.shell{margin-top:0;height:auto;grid-template-columns:1fr}.sidebar{position:sticky;top:0;z-index:9}.nav{display:flex;overflow:auto}.nav button{min-width:130px}.grid4{grid-template-columns:1fr 1fr}.logs-layout{grid-template-columns:1fr;height:auto}.content{height:auto;overflow:visible}.cockpit{grid-template-columns:1fr}.ring{margin:auto}.run-facts{grid-template-columns:1fr 1fr}body{overflow:auto}}
    """
    js = """
    <script>
    __MODEL_LABELS__
    __TASK_LABELS__
    __VARIANT_LABELS__
    __STEP_LABELS__
    __RUN_STATUS_LABELS__
    const pageBuiltAt = "__PAGE_BUILT_AT__";
    const seedState = JSON.parse(document.getElementById("state-seed").textContent || "{}");
    const seedData = JSON.parse(document.getElementById("data-seed").textContent || "{}");
    let currentDataBuiltAt = seedData.built_at || pageBuiltAt;
    function fmtDuration(seconds){ if(seconds===null||seconds===undefined||Number.isNaN(Number(seconds))) return "--"; seconds=Math.max(0,Math.floor(Number(seconds))); const h=Math.floor(seconds/3600),m=Math.floor((seconds%3600)/60),s=seconds%60; if(h>0)return `${h}h ${String(m).padStart(2,"0")}m`; if(m>0)return `${m}m ${String(s).padStart(2,"0")}s`; return `${s}s`; }
    function parseLocalTime(text){ if(!text)return null; const d=new Date(String(text).replace(" ","T")); return Number.isNaN(d.getTime())?null:d; }
    function setText(id,value){ const el=document.getElementById(id); if(el) el.textContent=value; }
    function stepLabel(raw){ if(!raw)return "--"; const first=String(raw).split(";")[0]; return STEP_LABELS[first] || STEP_LABELS[raw] || raw; }
    function currentText(current,stepElapsed){ if(!current||(!current.model&&!current.task&&!current.variant&&!current.steps&&!current.active_step))return ""; const model=MODEL_LABELS[current.model]||current.model||"--"; const task=TASK_LABELS[current.task]||current.task||"--"; const variant=VARIANT_LABELS[current.variant]||current.variant||"--"; const step=stepLabel(current.active_step||current.steps); let text=`${model} · ${task} · ${variant} · ${step}`; if(stepElapsed!==undefined&&stepElapsed!==null){ text += ` · 本阶段已运行 ${fmtDuration(stepElapsed)}`; } return text; }
    function countsText(counts){ if(!counts)return "waiting"; return Object.entries(counts).map(([k,v])=>`${k}: ${v}`).join(" · "); }
    function normalizedStatus(state){
      const status=String(state.status||"");
      if(status==="completed" && state.counts && Object.prototype.hasOwnProperty.call(state.counts,"dry_run_missing")) return "dry_run_completed";
      return status;
    }
    function applyState(state){
      const processed=Number(state.processed||0),total=Number(state.total||0),pct=total>0?processed/total*100:0;
      const now=new Date(), started=parseLocalTime(state.started_at), updated=parseLocalTime(state.updated_at);
      const age=updated?Math.max(0,(now-updated)/1000):null;
      const runStatus=normalizedStatus(state);
      const terminal=["completed","dry_run_completed","interrupted","failed"].includes(runStatus);
      const isStale=!terminal && age!==null && age>20;
      const liveElapsed=started?Math.max(0,(now-started)/1000):state.elapsed_seconds;
      const statusLabel=RUN_STATUS_LABELS[runStatus] || runStatus.toUpperCase() || "--";
      const remainingCombos=Math.max(0,total-processed);
      const stepStarted=parseLocalTime(state.current?.step_started_at);
      const stepElapsed=(!terminal && stepStarted)?Math.max(0,(now-stepStarted)/1000):state.current?.step_elapsed_seconds;
      setText("run-id",state.run_id||"--");
      setText("live-processed",`${processed}/${total}`);
      setText("live-counts",countsText(state.counts));
      setText("top-health",terminal?statusLabel:(isStale?`状态滞后 ${fmtDuration(age)}`:"实时同步"));
      setText("cockpit-pct",`${pct.toFixed(1)}%`);
      setText("cockpit-run",state.run_id||"--");
      setText("task-model",MODEL_LABELS[state.current?.model]||state.current?.model||"--");
      setText("task-task",TASK_LABELS[state.current?.task]||state.current?.task||"--");
      setText("task-variant",VARIANT_LABELS[state.current?.variant]||state.current?.variant||"--");
      setText("task-step",stepLabel(state.current?.active_step||state.current?.steps));
      setText("cockpit-finish",terminal ? "已结束" : fmtDuration(stepElapsed));
      setText("cockpit-eta",total>0?`${remainingCombos} 个组合`:"--");
      setText("cockpit-elapsed",fmtDuration(liveElapsed));
      setText("cockpit-updated",state.updated_at?`${state.updated_at}${isStale?" · 已滞后":""}`:"--");
      setText("batch-path",state.run_root||"--");
      setText("batch-progress",total>0?`${processed}/${total}`:"--");
      setText("batch-completed",state.counts?.completed||0);
      setText("batch-skipped",state.counts?.skipped_existing||0);
      setText("batch-failed",state.counts?.failed||0);
      const freshness=document.getElementById("freshness-pill"); if(freshness){ freshness.textContent=terminal?statusLabel:(isStale?`状态滞后 ${fmtDuration(age)}`:"实时同步"); freshness.classList.toggle("stale",isStale||runStatus==="interrupted"); }
      const totalBar=document.getElementById("cockpit-total-progress"); if(totalBar)totalBar.style.width=`${pct.toFixed(2)}%`;
      const ring=document.getElementById("cockpit-ring"); if(ring)ring.style.background=`conic-gradient(var(--green) 0deg, var(--cyan) ${pct*3.6}deg, rgba(255,255,255,.08) ${pct*3.6}deg)`;
    }
    async function refreshState(){ try{ const r=await fetch(`latest_run_state.json?ts=${Date.now()}`,{cache:"no-store"}); if(!r.ok)return; applyState(await r.json()); }catch(e){ setText("cockpit-current","live polling unavailable: open via http://127.0.0.1:8765/dashboard.html"); } }
    function activateView(id){ document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active",v.dataset.view===id)); document.querySelectorAll(".nav button").forEach(b=>b.classList.toggle("active",b.dataset.target===id)); }
    function activateMatrix(id){ document.querySelectorAll(".matrix-panel").forEach(v=>v.classList.toggle("active",v.dataset.matrix===id)); document.querySelectorAll(".matrix-tabs button").forEach(b=>b.classList.toggle("active",b.dataset.matrixTarget===id)); }
    function activateLog(id){ document.querySelectorAll(".log-item").forEach(v=>v.classList.toggle("active",v.dataset.log===id)); document.querySelectorAll(".log-panel").forEach(v=>v.classList.toggle("active",v.dataset.logPanel===id)); }
    function remember(){ const view=document.querySelector(".view.active")?.dataset.view||"overview"; const matrix=document.querySelector(".matrix-panel.active")?.dataset.matrix||"ml-cls"; sessionStorage.setItem("btcDashView",view); sessionStorage.setItem("btcDashMatrix",matrix); }
    function restore(){ activateView(sessionStorage.getItem("btcDashView")||"overview"); activateMatrix(sessionStorage.getItem("btcDashMatrix")||"ml-cls"); }
    function bindControls(){
      document.querySelectorAll(".nav button").forEach(b=>{ if(b.dataset.bound)return; b.dataset.bound="1"; b.addEventListener("click",()=>{activateView(b.dataset.target); remember();}); });
      document.querySelectorAll(".matrix-tabs button").forEach(b=>{ if(b.dataset.bound)return; b.dataset.bound="1"; b.addEventListener("click",()=>{activateMatrix(b.dataset.matrixTarget); remember();}); });
      document.querySelectorAll(".log-item").forEach(b=>{ if(b.dataset.bound)return; b.dataset.bound="1"; b.addEventListener("click",()=>activateLog(b.dataset.log)); });
    }
    function setHTML(id,value){ const el=document.getElementById(id); if(el && value!==undefined && el.innerHTML!==value) el.innerHTML=value; }
    function applyDashboardData(data){
      if(!data)return;
      currentDataBuiltAt = data.built_at || currentDataBuiltAt;
      setHTML("status-cards",data.status_cards_html);
      const path=document.getElementById("latest-path"); if(path){ path.textContent=data.latest_path_text||"暂无"; path.title=data.latest_path_text||"暂无"; }
      setText("latest-counts",data.latest_count_text||"暂无摘要");
      setHTML("latest-events",data.latest_events_html);
      setHTML("matrix-root",data.matrix_html);
      setHTML("top-rank-root",data.top_rank_html);
      setHTML("logs-root",data.logs_html);
      setHTML("runs-root",data.runs_html);
      bindControls();
      restore();
      applyState(data.state || seedState);
    }
    async function refreshDashboardData(){ try{ const r=await fetch(`dashboard_data.json?ts=${Date.now()}`,{cache:"no-store"}); if(!r.ok)return; const data=await r.json(); if(data.built_at && data.built_at!==currentDataBuiltAt){ remember(); applyDashboardData(data); } }catch(e){} }
    bindControls(); restore(); applyDashboardData(seedData); refreshState(); refreshDashboardData(); setInterval(refreshState,1000); setInterval(refreshDashboardData,3000);
    </script>
    """
    js = js.replace("__MODEL_LABELS__", js_seed("MODEL_LABELS", MODEL_LABELS))
    js = js.replace("__TASK_LABELS__", js_seed("TASK_LABELS", TASK_LABELS))
    js = js.replace("__VARIANT_LABELS__", js_seed("VARIANT_LABELS", VARIANT_LABELS))
    js = js.replace("__STEP_LABELS__", js_seed("STEP_LABELS", STEP_LABELS))
    js = js.replace("__RUN_STATUS_LABELS__", js_seed("RUN_STATUS_LABELS", RUN_STATUS_LABELS))
    js = js.replace("__PAGE_BUILT_AT__", now)
    data_seed = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="dashboard-built-at" content="{html.escape(now)}">
  <title>实验进度仪表盘</title>
  <style>{css}</style>
</head>
<body>
  <script type="application/json" id="state-seed">{state_seed(state)}</script>
  <script type="application/json" id="data-seed">{data_seed}</script>
  <header class="topbar">
    <section class="brand"><h1>BTC Predict HUD</h1><span></span></section>
    <section class="top-meta">本地实验监控台</section>
    <section class="top-health"><b id="top-health">LIVE</b></section>
  </header>
  <div class="shell">
    <aside class="sidebar">
      <nav class="nav">
        <button class="active" data-target="overview">Overview</button>
        <button data-target="matrix">Matrix</button>
        <button data-target="top">Top Results</button>
        <button data-target="logs">Logs</button>
        <button data-target="runs">Runs</button>
      </nav>
      <div class="legend">
        <span><i class="dot complete"></i>完整</span>
        <span><i class="dot missing_train"></i>缺预测</span>
        <span><i class="dot missing_backtest"></i>缺回测</span>
        <span><i class="dot missing_report"></i>缺报告</span>
      </div>
    </aside>
    <main class="content">
      <section class="view active" data-view="overview">
        <article class="cockpit">
          <div class="ring" id="cockpit-ring"><b id="cockpit-pct">--</b><span>本次脚本进度</span></div>
          <div>
            <div class="cockpit-head">
              <h2>实时运行状态</h2>
              <span class="status-pill" id="freshness-pill">实时同步</span>
              <span class="run-badge">批次 <span id="cockpit-run">--</span></span>
            </div>
            <div class="task-grid">
              <div class="task-chip"><small>模型</small><b id="task-model">--</b></div>
              <div class="task-chip"><small>任务</small><b id="task-task">--</b></div>
              <div class="task-chip"><small>数据集</small><b id="task-variant">--</b></div>
              <div class="task-chip"><small>阶段</small><b id="task-step">--</b></div>
            </div>
            <div class="hint-tags"><span>环形：本次脚本进度</span><span>批次概览：产物与失败记录</span></div>
            <div class="progress-stack">
              <div class="progress-row">
                <label><span>本次运行进度</span><span id="live-processed">--</span></label>
                <div class="bigbar"><div id="cockpit-total-progress"></div></div>
              </div>
            </div>
          </div>
          <div class="run-facts">
            <div><small>已运行</small><b id="cockpit-elapsed">--</b></div>
            <div><small>剩余组合</small><b id="cockpit-eta">--</b></div>
            <div><small>本阶段耗时</small><b id="cockpit-finish">--</b></div>
            <div><small>最后更新</small><b id="cockpit-updated">--</b></div>
          </div>
        </article>
        <div class="grid4" id="status-cards">{data["status_cards_html"]}</div>
        <article class="batch-box">
          <div class="batch-main">
            <h2>当前批次概览</h2>
            <div class="batch-path" id="batch-path" title="{html.escape(str(data["latest_path_text"]))}">{html.escape(str(data["latest_path_text"]))}</div>
          </div>
          <div class="batch-grid">
            <div class="batch-stat"><small>本次进度</small><b id="batch-progress">--</b></div>
            <div class="batch-stat done"><small>新完成</small><b id="batch-completed">0</b></div>
            <div class="batch-stat skip"><small>已有跳过</small><b id="batch-skipped">0</b></div>
            <div class="batch-stat fail"><small>失败记录</small><b id="batch-failed">0</b></div>
          </div>
          <p id="latest-path" style="display:none">{html.escape(str(data["latest_path_text"]))}</p>
          <p id="latest-counts" style="display:none">{html.escape(str(data["latest_count_text"]))}</p>
        </article>
        <article class="panel events-panel"><h2>当前待补事项</h2><ul class="events" id="latest-events">{data["latest_events_html"]}</ul></article>
      </section>
      <section class="view" data-view="matrix" id="matrix-root">{data["matrix_html"]}</section>
      <section class="view" data-view="top">
        <div class="top-results" id="top-rank-root">{data["top_rank_html"]}</div>
      </section>
      <section class="view" data-view="logs" id="logs-root">{data["logs_html"]}</section>
      <section class="view" data-view="runs"><article class="panel"><h2>历史批次</h2><div id="runs-root">{data["runs_html"]}</div></article></section>
    </main>
  </div>
  {js}
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the experiment dashboard HTML.")
    parser.add_argument("--output", default="reports/supplement_runs/dashboard.html")
    parser.add_argument("--data-output", default="reports/supplement_runs/dashboard_data.json")
    parser.add_argument("--refresh-seconds", type=int, default=5)
    args = parser.parse_args()
    root = project_root()
    out = root / args.output
    data_out = root / args.data_output
    out.parent.mkdir(parents=True, exist_ok=True)
    data_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(root, args.refresh_seconds), encoding="utf-8")
    data_out.write_text(json.dumps(dashboard_data(root), ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
