"""Render a dependency-free six-panel HTML dashboard from structured logs."""

from __future__ import annotations

import html
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
OUTPUT_PATH = ROOT / "data" / "dashboard.html"


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def load_records() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    records = []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if timestamp >= cutoff:
            records.append(record)
    return records


def metric_rows(records: list[dict]) -> list[tuple[str, str, str, str]]:
    responses = [r for r in records if r.get("event") == "response_sent"]
    requests = [r for r in records if r.get("event") == "request_received"]
    failures = [r for r in records if r.get("event") == "request_failed"]
    latencies = [float(r["latency_ms"]) for r in responses if r.get("latency_ms") is not None]
    ttft = [float(r["ttft_ms"]) for r in responses if r.get("ttft_ms") is not None]
    costs = [float(r["cost_usd"]) for r in responses if r.get("cost_usd") is not None]
    tokens_in = sum(int(r.get("tokens_in", 0)) for r in responses)
    tokens_out = sum(int(r.get("tokens_out", 0)) for r in responses)
    quality = [float(r["quality_score"]) for r in responses if r.get("quality_score") is not None]
    retrieval_values = [r.get("tool_success") for r in responses if r.get("tool_success") is not None]
    retrieval_success = (
        100 * sum(value is True for value in retrieval_values) / len(retrieval_values)
        if retrieval_values
        else 0.0
    )
    error_rate = 100 * len(failures) / len(requests) if requests else 0.0
    return [
        ("Latency", f"P50 {percentile(latencies, .50):.0f} / P95 {percentile(latencies, .95):.0f} / P99 {percentile(latencies, .99):.0f}; TTFT P95 {percentile(ttft, .95):.0f}", "ms", "SLO P95 <= 3000 ms; TTFT shown"),
        ("Traffic", f"{len(requests)} requests", "requests / 60 min", "Traffic baseline >= 1 request/min"),
        ("Errors", f"{error_rate:.2f}% errors; retrieval {retrieval_success:.1f}%", "%", "Error rate <= 2%; retrieval >= 90%"),
        ("Cost", f"${sum(costs):.4f}", "USD / 60 min", "Window total <= $2.50"),
        ("Tokens", f"Input {tokens_in:,} / Output {tokens_out:,}", "tokens", "Window total <= 50,000"),
        ("Quality", f"{sum(quality) / len(quality) if quality else 0.0:.2f}", "score 0-1", "Mean >= 0.75"),
    ]


def render(records: list[dict]) -> str:
    cards = []
    for title, value, unit, threshold in metric_rows(records):
        cards.append(
            "<section class='panel'>"
            f"<h2>{html.escape(title)}</h2>"
            f"<div class='value'>{html.escape(value)}</div>"
            f"<div class='unit'>{html.escape(unit)}</div>"
            f"<div class='threshold'>{html.escape(threshold)}</div>"
            "</section>"
        )
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>K4-L3A Monitoring Dashboard</title>
<style>
body{font:16px system-ui,sans-serif;background:#101827;color:#e5e7eb;margin:32px}
h1{margin-bottom:4px}.subtitle{color:#9ca3af;margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(220px,1fr));gap:16px}
.panel{background:#1f2937;border:1px solid #374151;border-radius:12px;padding:20px;min-height:130px}
h2{font-size:18px;margin:0 0 20px}.value{font-size:26px;font-weight:700}
.unit,.threshold{color:#9ca3af;margin-top:8px}.threshold{border-top:1px solid #374151;padding-top:10px;font-size:13px}
</style></head><body>
<h1>K4-L3A Day 13 Monitoring &amp; LLMOps</h1>
<div class="subtitle">Time range: last 60 minutes · Source: data/logs.jsonl · Refresh: 30 seconds</div>
<main class="grid">""" + "".join(cards) + "</main></body></html>"


def main() -> None:
    records = load_records()
    OUTPUT_PATH.write_text(render(records), encoding="utf-8")
    print(f"Rendered 6 panels from {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
