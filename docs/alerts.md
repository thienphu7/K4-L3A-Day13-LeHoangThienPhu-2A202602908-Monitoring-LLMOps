# Symptom-based alerts and runbooks

All alerts use the 60-minute dashboard window and are evaluated from user-visible symptoms. Slack notifications go to `#llmops-alerts`.

## High error rate

- Name: `high_error_rate`
- Severity: critical
- Condition: `error_rate_pct > 2` for 5 minutes
- SLO: burns the 0.5% error budget for `fast_successful_requests`.
- User impact: requests fail or return an error instead of an answer.
- First checks:
  1. Compare `request_failed` with `request_received` and group by `error_type`.
  2. Check `tool_success` and retrieval timeout/failure events.
  3. Pick one failed request and follow its `correlation_id` into Langfuse.
- Temporary mitigation: disable the failing incident/tool path, reduce load, or roll back the latest prompt/model configuration.
- Owner: `api-oncall`
- Channel: Slack `#llmops-alerts`
- Runbook: inspect logs -> follow correlation ID -> compare child span status -> mitigate -> verify error rate for 15 minutes.

## High latency P95

- Name: `high_latency_p95`
- Severity: warning
- Condition: `latency_p95_ms > 3000` for 10 minutes
- SLO: violates the 3,000 ms good-event threshold.
- User impact: tail users experience slow answers or timeouts.
- First checks:
  1. Compare latency P50/P95/P99 and TTFT P95.
  2. Compare `retriever` and `generation` child durations in a slow trace.
  3. Check whether `rag_slow`, upstream failures, or output-token growth is active.
- Temporary mitigation: disable the slow practice incident, reduce retrieval scope, or cap generation output.
- Owner: `api-oncall`
- Channel: Slack `#llmops-alerts`
- Runbook: inspect latency panel -> select a slow correlation ID -> identify the longest child -> mitigate -> confirm P95 recovery.

## Low retrieval success

- Name: `low_retrieval_success`
- Severity: warning
- Condition: `retrieval_success_rate_pct < 90` for 10 minutes
- SLO: retrieval success guardrail is at least 90%.
- User impact: answers may lack relevant context or fall back to generic responses.
- First checks:
  1. Review `tool_success` and `error_type` breakdown.
  2. Check `retriever` span status and duration for affected traces.
  3. Validate vector-store availability and query/document matching.
- Temporary mitigation: route to the fallback corpus, disable the failing retrieval incident, or retry with bounded backoff.
- Owner: `retrieval-oncall`
- Channel: Slack `#llmops-alerts`
- Runbook: inspect retrieval-success panel -> select a failed request -> follow its trace -> restore/retry retrieval -> verify rate above 90%.
