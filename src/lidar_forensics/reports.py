from __future__ import annotations

import csv
import html
import io
import json
import os
from typing import Any

from lidar_forensics.models import AnalysisResult, IncidentCategory


DISCLAIMER = (
    "This tool determines whether sensor messages remain present and characterizes "
    "the failure signature. Geometric recovery depends on the surviving measurements "
    "and trajectory information."
)


def structured_brief_input(result: AnalysisResult) -> dict[str, Any]:
    return {
        "recording_label": "local_recording",
        "duration_s": result.duration_s,
        "summary": result.summary.model_dump(),
        "stream_metrics": [metric.model_dump() for metric in result.stream_metrics],
        "findings": [
            {
                "finding_id": incident.finding_id,
                "finding_role": incident.finding_role.value,
                "category": incident.category.value,
                "confidence": incident.confidence.value,
                "start": incident.start,
                "end": incident.end,
                "duration": incident.duration,
                "streams_stopped": incident.streams_stopped,
                "streams_continued": incident.streams_continued,
                "timestamp_disagreement": incident.timestamp_disagreement,
                "confirmed_facts": incident.confirmed_facts,
                "interpretation": incident.interpretation,
                "hypotheses": incident.hypotheses,
                "missing_evidence": incident.missing_evidence,
                "recommended_tests": incident.recommended_tests,
            }
            for incident in result.findings
        ],
        "required_claim_policy": {
            "root_cause_proven": False,
            "must_separate_observation_and_hypothesis": True,
            "disclaimer": DISCLAIMER,
        },
    }


def markdown_brief(result: AnalysisResult) -> str:
    actionable = [item for item in result.findings if item.category != IncidentCategory.NORMAL]
    confirmed = [fact for item in result.findings for fact in item.confirmed_facts]
    interpretations = list(dict.fromkeys(item.interpretation for item in result.findings))
    hypotheses = list(dict.fromkeys(value for item in result.findings for value in item.hypotheses))
    missing = list(dict.fromkeys(value for item in result.findings for value in item.missing_evidence))
    tests = list(dict.fromkeys(value for item in result.findings for value in item.recommended_tests))

    def bullets(values: list[str], fallback: str) -> str:
        return "\n".join(f"- {value}" for value in values) if values else f"- {fallback}"

    primary_count = result.summary.primary_incident_count
    related_count = result.summary.related_finding_count
    primary_label = "primary incident" if primary_count == 1 else "primary incidents"
    related_label = "related finding" if related_count == 1 else "related findings"

    return f"""# LiDAR Forensics diagnostic finding brief

**Recording:** {result.recording_id}  
**Diagnostic status:** {result.summary.diagnostic_status}  
**Duration:** {result.duration_s:.3f} s  
**Detected findings:** {len(actionable)} ({primary_count} {primary_label}, {related_count} {related_label})  
**Recording continuity:** {result.summary.recording_continuity_percent:.2f}%  
**LiDAR relative availability:** {result.summary.lidar_relative_availability_percent:.2f}%

## Confirmed observations

{bullets(confirmed, "No configured anomaly threshold was exceeded.")}

## Interpretation

{bullets(interpretations, "No failure interpretation is required for this baseline.")}

## Hypotheses

{bullets(hypotheses, "No failure hypothesis is asserted.")}

These hypotheses are not a proven root cause.

## Missing evidence

{bullets(missing, "No additional evidence is required for the current classification.")}

## Recommended next tests

{bullets(tests, "Retain the recording as a comparison baseline.")}

## Scope statement

{DISCLAIMER}
"""


def ai_or_template_brief(result: AnalysisResult) -> tuple[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return markdown_brief(result), "deterministic-template"
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            instructions=(
                "Write a concise engineering diagnostic finding brief in Markdown. "
                "Use only supplied measurements. Separate confirmed observations, "
                "interpretation, hypotheses, missing evidence, and recommended next tests. "
                "Never claim a proven root cause or guaranteed geometric recovery."
            ),
            input=json.dumps(structured_brief_input(result)),
        )
        return response.output_text, "openai"
    except (ImportError, Exception) as exc:
        brief = markdown_brief(result)
        brief += f"\n\n> AI generation was unavailable; deterministic fallback used ({type(exc).__name__}).\n"
        return brief, "deterministic-fallback"


def findings_csv(result: AnalysisResult) -> str:
    output = io.StringIO()
    fields = [
        "finding_id",
        "finding_role",
        "start",
        "end",
        "duration",
        "classification",
        "confidence",
        "streams_stopped",
        "streams_continued",
        "timestamp_disagreement",
        "interpretation",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for incident in result.findings:
        writer.writerow(
            {
                "finding_id": incident.finding_id,
                "finding_role": incident.finding_role.value,
                "start": f"{incident.start:.6f}",
                "end": f"{incident.end:.6f}",
                "duration": f"{incident.duration:.6f}",
                "classification": incident.category.value,
                "confidence": incident.confidence.value,
                "streams_stopped": ";".join(incident.streams_stopped),
                "streams_continued": ";".join(incident.streams_continued),
                "timestamp_disagreement": incident.timestamp_disagreement,
                "interpretation": incident.interpretation,
            }
        )
    return output.getvalue()


def findings_json(result: AnalysisResult) -> str:
    return result.model_dump_json(indent=2)


def standalone_html(result: AnalysisResult) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(item.finding_id)}</td>"
        f"<td><span class='role {html.escape(item.finding_role.value.lower().replace('_', '-'))}'>{html.escape(item.finding_role.value.replace('_', ' ').title())}</span></td>"
        f"<td><span class='tag {html.escape(item.category.value.lower())}'>{html.escape(item.category.value)}</span></td>"
        f"<td>{item.start:.3f}</td><td>{item.duration:.3f}</td>"
        f"<td>{html.escape(item.confidence.value)}</td>"
        f"<td>{html.escape(item.interpretation)}</td></tr>"
        for item in result.findings
    )
    details = "".join(
        f"<section><h2>{html.escape(item.finding_id)} · {html.escape(item.category.value)}</h2>"
        f"<p><strong>Role:</strong> {html.escape(item.finding_role.value.replace('_', ' ').title())}</p>"
        f"<h3>Confirmed observations</h3><ul>{''.join(f'<li>{html.escape(value)}</li>' for value in item.confirmed_facts)}</ul>"
        f"<h3>Missing evidence</h3><ul>{''.join(f'<li>{html.escape(value)}</li>' for value in item.missing_evidence)}</ul>"
        f"<h3>Recommended next tests</h3><ul>{''.join(f'<li>{html.escape(value)}</li>' for value in item.recommended_tests)}</ul></section>"
        for item in result.findings
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>LiDAR Forensics · {html.escape(result.recording_id)}</title>
<style>
body{{font:14px Arial,sans-serif;color:#182027;background:#f5f7f8;margin:0}}main{{max-width:1100px;margin:auto;padding:36px}}
h1{{font-size:28px;margin:0 0 6px}}.meta{{color:#59666f}}.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#cbd2d6;margin:26px 0}}
.summary div{{background:white;padding:18px}}.summary strong{{display:block;font-size:22px;margin-top:8px}}table{{width:100%;border-collapse:collapse;background:white}}
th,td{{text-align:left;padding:10px;border-bottom:1px solid #d9dfe2}}th{{background:#e8edef;font-size:12px;text-transform:uppercase}}section{{border-top:2px solid #2d5966;padding:18px 0}}
.tag,.role{{font:11px monospace;border:1px solid #7a878d;padding:3px 6px}}.role.related-finding{{border-style:dashed}}.scope{{background:#fff4cf;border-left:4px solid #d39d17;padding:14px;margin-top:24px}}@media print{{body{{background:white}}main{{padding:0}}}}
</style></head><body><main>
<h1>LiDAR Forensics</h1><p class="meta">Standalone finding report · {html.escape(result.recording_id)}</p>
<div class="summary"><div>Status<strong>{html.escape(result.summary.diagnostic_status)}</strong></div><div>Duration<strong>{result.duration_s:.3f} s</strong></div><div>Detected findings<strong>{result.summary.detected_findings_count}</strong></div><div>Recording continuity<strong>{result.summary.recording_continuity_percent:.2f}%</strong></div><div>LiDAR relative availability<strong>{result.summary.lidar_relative_availability_percent:.2f}%</strong></div><div>Observed streams<strong>{result.summary.observed_streams}</strong></div></div>
<table><thead><tr><th>ID</th><th>Role</th><th>Classification</th><th>Start</th><th>Duration</th><th>Confidence</th><th>Interpretation</th></tr></thead><tbody>{rows}</tbody></table>
{details}<p class="scope"><strong>Scope:</strong> {html.escape(DISCLAIMER)}</p>
</main></body></html>"""
