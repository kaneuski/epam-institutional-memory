#!/usr/bin/env python3
"""KB Register Browser — Static HTML Generator (onboarding / institutional-memory domain)

Generates an interactive HTML browser for the 12 registers defined in
kb-register-schema.md. Produces a single self-contained HTML file with:
  - Register index (sidebar with all entity types)
  - Entry cards with metadata tables
  - Clickable cross-reference links between entities
  - Status badges with color coding
  - A timeline slider (oldest entry date -> today) that filters every
    register's entries down to what was true as of the selected date —
    this is the feature that matters most in a domain where most core
    entities get superseded rather than just accumulated.
  - A relationship graph tab — always generated, always shows the current
    snapshot (the timeline slider does not apply there; "current" is the
    only state a graph needs to show).

Usage:
  python3 kb-browser.py [--output kb-browser.html] [--path .registers]

Run from a project root that has a `.registers/` directory (or pass --path).
"""

import argparse
import datetime
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REGISTERS_DIR = Path(".registers")

ENTRY_HEADING_RE = re.compile(r"^## ([A-Z]+-\d{3}):\s+(.+)$", re.MULTILINE)
FIELD_TABLE_RE = re.compile(r"^\| (.+?) \| (.+?) \|$", re.MULTILINE)
LINK_RE = re.compile(r"\[([A-Z]+-\d{3})\]\(([^)]+)\)")
SECTION_RE = re.compile(r"^### (.+)$", re.MULTILINE)
REF_LABEL_RE = re.compile(r"^- (.+?):\s*(.+)$")

# Field names checked, in priority order, to derive each entry's validity
# window for the timeline slider.
START_FIELD_PRIORITY = ["start_date", "effective_date", "date", "raised_date", "join_date"]
END_FIELD_PRIORITY = ["end_date", "superseded_date"]

# Registers the timeline slider is allowed to filter: the Core tier (where
# supersession actually happens) plus People and Open Questions, which carry
# a meaningful "as of" date (join_date, raised_date) even though they don't
# belong to Core. Deliberately explicit rather than inferred from field
# presence — teams/services/access-tiers/onboarding-stages/exceptions are
# static facts or pointer-only records from the slider's point of view, even
# if a future register gains a date-shaped field.
TIMELINE_REGISTERS = {
    "policies.md",
    "decisions.md",
    "role-assignments.md",
    "service-ownership.md",
    "incidents.md",
    "people.md",
    "open-questions.md",
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

STATUS_COLORS = {
    "active": "#2ecc71",
    "current": "#2ecc71",
    "open": "#e67e22",
    "investigating": "#3498db",
    "resolved": "#27ae60",
    "answered": "#27ae60",
    "former": "#7f8c8d",
    "superseded": "#7f8c8d",
    "deferred": "#95a5a6",
    "reversed": "#e74c3c",
    "revoked": "#e74c3c",
}

FIELD_LABELS = {
    "status": ("Status", "Current lifecycle state of this entity"),
    "scope": ("Scope", "What this policy governs"),
    "effective_date": ("Effective", "Date this version took effect"),
    "superseded_date": ("Superseded", "Date this version was replaced"),
    "owner": ("Owner", "Person accountable for this policy"),
    "supersedes": ("Supersedes", "Prior entry this replaces"),
    "superseded_by": ("Superseded By", "Later entry that replaced this one"),
    "source_incident": ("Source Incident", "Incident that triggered this version"),
    "migration_deadline": ("Migration Deadline", "Date by which dependents must move to the new version"),
    "decision_type": ("Decision Type", "Category: policy, org-change, ownership-change, or process"),
    "date": ("Date", "When this occurred or was decided"),
    "participants": ("Participants", "Who was involved"),
    "trigger": ("Trigger", "Incident that prompted this decision"),
    "reversibility": ("Reversibility", "How costly to undo"),
    "person": ("Person", "Individual holding this role"),
    "role_title": ("Role Title", "The role/title this assignment covers"),
    "team": ("Team", "Team this role belongs to"),
    "start_date": ("Start", "Date this became true"),
    "end_date": ("End", "Date this stopped being true"),
    "service": ("Service", "Service this entry concerns"),
    "owning_team": ("Owning Team", "Team accountable for this service"),
    "tech_lead": ("Tech Lead", "Individual technical owner"),
    "severity": ("Severity", "P0, P1, or P2"),
    "postmortem_link": ("Postmortem", "Link to the written postmortem"),
    "join_date": ("Joined", "Date this person joined"),
    "location": ("Location", "Where this person is based"),
    "slack_handle": ("Slack", "Slack handle"),
    "parent_team": ("Parent Team", "Team this team reports up into"),
    "repo_link": ("Repo", "Link to the service's repository"),
    "tier_name": ("Tier", "read-only, read-write, or privileged"),
    "governing_policy": ("Governing Policy", "Policy currently defining this tier's eligibility — must be active"),
    "sequence_order": ("Sequence", "Position in the onboarding journey"),
    "day_range": ("Day Range", "Which onboarding day(s) this stage covers"),
    "handbook_version": ("Handbook Version", "Handbook version this stage was sourced from"),
    "policy_ref": ("Policy Referenced", "Policy this stage cites — must be active or the handbook content is stale"),
    "access_tier_ref": ("Access Tier Referenced", "Access tier this stage cites"),
    "modifies_policy": ("Modifies Policy", "Policy this exception overrides"),
    "trigger_condition": ("Trigger Condition", "What activates this exception"),
    "reconciliation_deadline": ("Reconciliation Deadline", "When the exception must be reconciled or revoked"),
    "raised_date": ("Raised", "Date this question was raised"),
    "priority": ("Priority", "blocking, important, or nice-to-know"),
    "source": ("Source", "Document or register entry that raised this"),
    "decision": ("Decision", "Decision that authorized this entry"),
}


def parse_frontmatter(content: str) -> dict:
    fm = {}
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            block = content[3:end].strip()
            for line in block.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    fm[key.strip()] = val.strip()
    return fm


def humanize_field(key: str) -> tuple:
    if key in FIELD_LABELS:
        return FIELD_LABELS[key]
    label = key.replace("_", " ").replace("-", " ").title()
    return (label, "")


def humanize_register_name(filename: str) -> str:
    return filename.replace(".md", "").replace("-", " ").title()


def render_markdown_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\[([A-Z]+-\d{3})\]\([^)]+\)",
        lambda m: f'<a href="#{m.group(1).lower()}" class="ref-link" data-target="{m.group(1)}">{m.group(1)}</a>',
        text
    )
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" class="ext-link">\1</a>', text)
    return text


def extract_validity(fields: dict):
    """Return (valid_from, valid_to) ISO date strings, or (None, None) if untimed."""
    valid_from = None
    for f in START_FIELD_PRIORITY:
        v = fields.get(f, "").strip()
        if v and v.lower() not in ("null", "none", "") and DATE_RE.match(v):
            valid_from = v
            break
    valid_to = None
    for f in END_FIELD_PRIORITY:
        v = fields.get(f, "").strip()
        if v and v.lower() not in ("null", "none", "") and DATE_RE.match(v):
            valid_to = v
            break
    return valid_from, valid_to


def parse_entry_body(content: str, start: int, next_start: int) -> dict:
    body = content[start:next_start]

    fields = {}
    for match in FIELD_TABLE_RE.finditer(body):
        key = match.group(1).strip().strip("*").strip()
        val = match.group(2).strip()
        if key != "Field" and key != "---" and set(key) != {"-"}:
            fields[key] = val

    refs = []
    in_refs = False
    current_ref_label = ""
    for line in body.split("\n"):
        if line.strip() == "### References":
            in_refs = True
            continue
        if in_refs:
            if line.startswith("## ") or line.startswith("### "):
                break
            ref_match = REF_LABEL_RE.match(line.strip())
            if ref_match:
                current_ref_label = ref_match.group(1)
                link_text = ref_match.group(2)
                link_ids = LINK_RE.findall(link_text)
                if link_ids:
                    refs.append({"label": current_ref_label, "links": [{"id": lid, "href": lhref} for lid, lhref in link_ids]})

    seen_ids = set()
    all_links = []
    for match in LINK_RE.finditer(body):
        lid = match.group(1)
        if lid not in seen_ids:
            seen_ids.add(lid)
            all_links.append({"id": lid, "href": match.group(2)})
    all_links.sort(key=lambda x: x["id"])

    sections = {}
    for match in SECTION_RE.finditer(body):
        sections[match.group(1)] = True

    prose_lines = []
    in_table = False
    in_refs_section = False
    for line in body.split("\n"):
        if line.strip() == "### References":
            in_refs_section = True
            continue
        if in_refs_section:
            if line.startswith("## ") or (line.startswith("### ") and line.strip() != "### References"):
                in_refs_section = False
            else:
                continue
        if line.startswith("|"):
            in_table = True
            continue
        if in_table and not line.startswith("|"):
            in_table = False
        if not line.startswith("##") and not in_table and line.strip() and set(line.strip()) != {"-"}:
            prose_lines.append(line)

    valid_from, valid_to = extract_validity(fields)

    return {
        "fields": fields,
        "refs": refs,
        "all_links": all_links,
        "sections": list(sections.keys()),
        "prose": "\n".join(prose_lines[:10]),
        "valid_from": valid_from,
        "valid_to": valid_to,
    }


def parse_register(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)
    first_entry = ENTRY_HEADING_RE.search(content)
    schema_content = content[:first_entry.start()] if first_entry else content
    schema_html = render_register_md_to_html(schema_content)

    entries = []
    headings = list(ENTRY_HEADING_RE.finditer(content))

    for i, match in enumerate(headings):
        entry_id = match.group(1)
        title = match.group(2)
        start = match.end()
        next_start = headings[i + 1].start() if i + 1 < len(headings) else len(content)
        body = parse_entry_body(content, start, next_start)

        entries.append({
            "id": entry_id,
            "title": title,
            "fields": body["fields"],
            "refs": body["refs"],
            "all_links": body["all_links"],
            "prose": body["prose"],
            "valid_from": body["valid_from"],
            "valid_to": body["valid_to"],
        })

    return {"filename": path.name, "frontmatter": fm, "entries": entries, "schema_html": schema_html}


def render_md_table(rows: list) -> str:
    parts = ['<table class="rm-table">']
    header_emitted = False
    for row in rows:
        cells = [c.strip() for c in row.strip('|').split('|')]
        if all(re.match(r'^[-:| ]+$', c) for c in cells):
            header_emitted = True
            continue
        tag = 'th' if not header_emitted else 'td'
        parts.append('<tr>' + ''.join(
            f'<{tag} class="rm-td">{render_markdown_inline(c)}</{tag}>' for c in cells
        ) + '</tr>')
        if not header_emitted:
            header_emitted = True
    parts.append('</table>')
    return '\n'.join(parts)


def render_register_md_to_html(content: str) -> str:
    lines = content.split('\n')
    out: list = []
    i = 0

    if lines and lines[0].strip() == '---':
        fm_lines: list = []
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            fm_lines.append(lines[i])
            i += 1
        i += 1
        if fm_lines:
            out.append('<div class="rm-fm">')
            for fl in fm_lines:
                if ':' in fl:
                    k, v = fl.split(':', 1)
                    out.append(
                        f'<div class="rm-fm-row">'
                        f'<span class="rm-fm-key">{html.escape(k.strip().replace("_", " "))}</span>'
                        f'<span class="rm-fm-val">{html.escape(v.strip())}</span>'
                        f'</div>'
                    )
            out.append('</div>')

    table_rows: list = []
    list_items: list = []

    def flush_table():
        if table_rows:
            out.append(render_md_table(list(table_rows)))
            table_rows.clear()

    def flush_list():
        if list_items:
            out.append('<ul class="rm-ul">' + ''.join(
                f'<li>{render_markdown_inline(li)}</li>' for li in list_items
            ) + '</ul>')
            list_items.clear()

    while i < len(lines):
        line = lines[i]
        if line.startswith('|'):
            flush_list()
            table_rows.append(line)
            i += 1
            continue
        flush_table()
        m_li = re.match(r'^[-*]\s+(.+)$', line)
        if m_li:
            list_items.append(m_li.group(1))
            i += 1
            continue
        flush_list()
        if re.match(r'^---+$', line.strip()):
            out.append('<hr class="rm-hr">')
            i += 1
            continue
        m_h = re.match(r'^(#{1,3})\s+(.+)$', line)
        if m_h:
            lvl = len(m_h.group(1))
            out.append(f'<h{lvl} class="rm-h{lvl}">{render_markdown_inline(m_h.group(2))}</h{lvl}>')
            i += 1
            continue
        if not line.strip():
            out.append('<div class="rm-sp"></div>')
            i += 1
            continue
        out.append(f'<p class="rm-p">{render_markdown_inline(line)}</p>')
        i += 1

    flush_table()
    flush_list()
    return '\n'.join(out)


def build_mermaid(registers: list) -> str:
    """Current-snapshot relationship graph — not affected by the timeline slider."""

    def sanitize(entry_id: str) -> str:
        return re.sub(r"[^A-Za-z0-9]", "", entry_id)

    all_ids = set()
    for reg in registers:
        for entry in reg["entries"]:
            all_ids.add(entry["id"])

    lines = ["graph LR"]

    for reg in registers:
        for entry in reg["entries"]:
            node_var = sanitize(entry["id"])
            lines.append(f'  {node_var}["{entry["id"]}: {entry["title"]}"]')

    seen_edges: set = set()
    for reg in registers:
        for entry in reg["entries"]:
            src_var = sanitize(entry["id"])
            for link in entry["all_links"]:
                tgt_id = link["id"]
                if tgt_id == entry["id"] or tgt_id not in all_ids:
                    continue
                tgt_var = sanitize(tgt_id)
                edge = (src_var, tgt_var)
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    lines.append(f"  {src_var} --> {tgt_var}")

    return "\n".join(lines)


def _normalize_svg_size(svg: str) -> str:
    """Mermaid emits width="100%" with no explicit height, which shrinks the
    diagram to fit whatever container it's dropped into — fine for a small
    graph, unreadable for one with 50+ nodes. Pin width/height to the SVG's
    own viewBox so it renders at native size; the graph panel's zoom controls
    and scroll area handle navigating a diagram that's now larger than the
    viewport.
    """
    vb_match = re.search(r'viewBox="[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)"', svg)
    if not vb_match:
        return svg
    vb_w = int(round(float(vb_match.group(1))))
    vb_h = int(round(float(vb_match.group(2))))
    svg = re.sub(r'\swidth="[^"]*"', '', svg, count=1)
    svg = re.sub(r'\sheight="[^"]*"', '', svg, count=1)
    svg = re.sub(r'max-width:\s*[\d.]+px;?\s*', '', svg)
    svg = svg.replace('<svg ', f'<svg width="{vb_w}" height="{vb_h}" ', 1)
    return svg


def _render_mermaid_to_svg(mermaid_content: str) -> str:
    mmdc = None
    for candidate in ["mmdc", "npx @mermaid-js/mermaid-cli"]:
        try:
            result = subprocess.run(
                candidate.split() + ["--version"],
                capture_output=True, timeout=10,
            )
            if result.returncode == 0:
                mmdc = candidate.split()
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    if mmdc is None:
        escaped = html.escape(mermaid_content)
        return f'<pre style="font-size:12px;padding:1rem;">{escaped}</pre>'

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "diagram.mmd")
        output_file = os.path.join(tmpdir, "diagram.svg")
        with open(input_file, "w") as f:
            f.write(mermaid_content)
        try:
            result = subprocess.run(
                mmdc + ["-i", input_file, "-o", output_file,
                        "-t", "neutral", "-b", "transparent"],
                capture_output=True, timeout=30,
            )
            if result.returncode == 0 and os.path.exists(output_file):
                with open(output_file) as f:
                    svg = f.read()
                svg = re.sub(r"<\?xml[^>]*\?>", "", svg).strip()
                svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg).strip()
                return _normalize_svg_size(svg)
        except subprocess.TimeoutExpired:
            pass

    escaped = html.escape(mermaid_content)
    return f'<pre style="font-size:12px;padding:1rem;">{escaped}</pre>'


def generate_html(registers: list, output_path: Path):
    today = datetime.date.today().isoformat()

    all_entries = {}
    timeline_dates = set()
    for reg in registers:
        timeline_eligible = reg["filename"] in TIMELINE_REGISTERS
        for entry in reg["entries"]:
            valid_from = entry["valid_from"] if timeline_eligible else None
            valid_to = entry["valid_to"] if timeline_eligible else None
            all_entries[entry["id"]] = {
                "register": reg["filename"],
                "title": entry["title"],
                "status": entry["fields"].get("status", ""),
                "valid_from": valid_from,
                "valid_to": valid_to,
            }
            if valid_from:
                timeline_dates.add(valid_from)
    timeline_dates.add(today)
    timeline_dates = sorted(timeline_dates)

    entries_json = json.dumps(all_entries, indent=2)
    timeline_json = json.dumps(timeline_dates)

    registers_meta = {}
    for reg in registers:
        registers_meta[reg["filename"]] = {
            "display_name": humanize_register_name(reg["filename"]),
            "frontmatter": reg["frontmatter"],
            "entry_count": len(reg["entries"]),
            "schema_html": reg["schema_html"],
            "timeline_eligible": reg["filename"] in TIMELINE_REGISTERS,
        }
    registers_json = json.dumps(registers_meta)

    TIER_ORDER = ["core", "domain", "traceability"]
    TIER_LABELS = {"core": "Core", "domain": "Domain", "traceability": "Traceability"}

    tier_groups: dict = {}
    for reg in registers:
        tier = reg["frontmatter"].get("tier", "other").strip('"').strip("'") or "other"
        tier_groups.setdefault(tier, []).append(reg)

    tier_sequence = TIER_ORDER + sorted(t for t in tier_groups if t not in TIER_ORDER)

    register_nav = ""
    for tier in tier_sequence:
        regs = tier_groups.get(tier)
        if not regs:
            continue
        regs = sorted(regs, key=lambda r: r["filename"])
        tier_label = TIER_LABELS.get(tier, tier.title())
        tier_total = sum(len(r["entries"]) for r in regs)
        register_nav += f'<div class="tier-group">\n'
        register_nav += (
            f'<div class="tier-header" data-tier="{tier}">'
            f'<span class="tier-toggle">&#9662;</span>'
            f'<span class="tier-name">{html.escape(tier_label)}</span>'
            f'<span class="tier-count">{tier_total}</span></div>\n'
        )
        register_nav += '<div class="tier-children">\n'
        for reg in regs:
            count = len(reg["entries"])
            display_name = humanize_register_name(reg["filename"])
            empty_style = ' style="opacity:0.45"' if count == 0 else ''
            register_nav += f'<div class="reg-item" data-file="{reg["filename"]}"{empty_style}>'
            register_nav += f'<span class="reg-name">{display_name}</span>'
            register_nav += f'<span class="reg-count">{count}</span></div>\n'
        register_nav += '</div>\n</div>\n'

    entry_cards = ""
    for reg in registers:
        timeline_eligible = reg["filename"] in TIMELINE_REGISTERS
        for entry in reg["entries"]:
            eid = entry["id"]
            status = entry["fields"].get("status", "")
            status_color = STATUS_COLORS.get(status, "#666")

            fields_html = ""
            for k, v in entry["fields"].items():
                if k == "status":
                    continue
                label, tooltip = humanize_field(k)
                rendered_v = render_markdown_inline(v)
                tooltip_attr = f' title="{html.escape(tooltip)}"' if tooltip else ''
                fields_html += f'<div class="field-cell field-key"{tooltip_attr}>{html.escape(label)}</div><div class="field-cell">{rendered_v}</div>'

            refs_html = ""
            if entry["refs"]:
                for ref_group in entry["refs"]:
                    ref_label = ref_group["label"]
                    ref_links = " ".join(
                        f'<a href="#{link["id"].lower()}" class="ref-link" data-target="{link["id"]}">{link["id"]}</a>'
                        for link in ref_group["links"]
                    )
                    refs_html += f'<div class="ref-group"><span class="ref-label">{html.escape(ref_label)}:</span> {ref_links}</div>'
            elif entry["all_links"]:
                refs_html = '<div class="ref-group"><span class="ref-label">References:</span> '
                refs_html += " ".join(
                    f'<a href="#{link["id"].lower()}" class="ref-link" data-target="{link["id"]}">{link["id"]}</a>'
                    for link in entry["all_links"]
                )
                refs_html += '</div>'

            prose_rendered = render_markdown_inline(entry["prose"][:500])
            prose_html = prose_rendered.replace("\n", "<br>\n")

            valid_from_attr = (entry["valid_from"] or "") if timeline_eligible else ""
            valid_to_attr = (entry["valid_to"] or "") if timeline_eligible else ""

            entry_cards += f'''
<div class="entry-card" id="{eid.lower()}" data-id="{eid}" data-register="{reg['filename']}" data-status="{status}" data-valid-from="{valid_from_attr}" data-valid-to="{valid_to_attr}">
  <div class="entry-header">
    <span class="entry-id">{eid}</span>
    <span class="entry-title">{html.escape(entry["title"])}</span>
    {f'<span class="status-badge" style="background:{status_color}">{status.title()}</span>' if status else ''}
  </div>
  <div class="entry-meta">
    <span class="register-badge">{humanize_register_name(reg["filename"])}</span>
    {f'<span class="validity-badge">valid {valid_from_attr} → {valid_to_attr or "present"}</span>' if valid_from_attr else ''}
  </div>
  <div class="fields-grid">{fields_html}</div>
  <div class="entry-prose">{prose_html}</div>
  <div class="entry-refs">{refs_html}</div>
</div>
'''

    mermaid_content = build_mermaid(registers)
    graph_svg = _render_mermaid_to_svg(mermaid_content)
    graph_panel = f'''<div id="graph-panel" style="display:none; flex-direction:column; background:#fff; flex:1; min-height:0;">
  <div class="graph-toolbar">
    <button class="graph-zoom-btn" id="graph-zoom-out" title="Zoom out">&#8722;</button>
    <span class="graph-zoom-level" id="graph-zoom-level">100%</span>
    <button class="graph-zoom-btn" id="graph-zoom-in" title="Zoom in">+</button>
    <button class="graph-zoom-btn" id="graph-zoom-reset" title="Reset zoom">Reset</button>
  </div>
  <div id="graph-scroll" style="flex:1; min-height:0; overflow:auto; padding:1rem;">
    <div id="graph-zoom-wrap" style="transform-origin: 0 0; display:inline-block;">
{graph_svg}
    </div>
  </div>
</div>'''

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Onboarding KB Register Browser</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; height: 100vh; background: #f8f9fa; color: #2c3e50; }}

.sidebar {{ width: 280px; background: #fff; border-right: 1px solid #e0e0e0; overflow-y: auto; padding: 16px; flex-shrink: 0; }}
.sidebar h2 {{ font-size: 14px; text-transform: uppercase; color: #7f8c8d; margin-bottom: 12px; letter-spacing: 0.5px; }}
.reg-item {{ display: flex; align-items: center; padding: 8px 12px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; font-size: 13px; }}
.reg-item:hover {{ background: #f0f0f0; }}
.reg-item.active {{ background: #eef; }}
.reg-name {{ flex: 1; }}
.reg-count {{ background: #eee; border-radius: 10px; padding: 2px 8px; font-size: 11px; color: #666; }}

.tier-group {{ margin-top: 8px; }}
.tier-header {{ display: flex; align-items: center; gap: 6px; padding: 6px 8px; cursor: pointer; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; color: #95a5a6; user-select: none; }}
.tier-header:hover {{ background: #f5f5f5; color: #7f8c8d; }}
.tier-toggle {{ font-size: 10px; width: 10px; display: inline-block; transition: transform 0.15s; }}
.tier-header.collapsed .tier-toggle {{ transform: rotate(-90deg); }}
.tier-count {{ margin-left: auto; background: #f0f0f0; border-radius: 10px; padding: 1px 7px; font-size: 10px; color: #999; font-weight: 500; text-transform: none; letter-spacing: 0; }}
.tier-children {{ padding-left: 12px; border-left: 1px solid #f0f0f0; margin-left: 10px; }}
.tier-children.collapsed {{ display: none; }}

.main {{ flex: 1; display: flex; flex-direction: column; overflow: hidden; }}

/* Timeline slider */
.timeline-bar {{ padding: 14px 24px; background: #fff; border-bottom: 1px solid #e0e0e0; display: flex; gap: 16px; align-items: center; }}
.timeline-label {{ font-size: 12px; color: #7f8c8d; white-space: nowrap; }}
.timeline-date {{ font-size: 14px; font-weight: 600; color: #2c3e50; min-width: 110px; }}
.timeline-bar input[type="range"] {{ flex: 1; }}
.timeline-now-btn {{ padding: 6px 12px; font-size: 12px; border: 1px solid #bdc3c7; border-radius: 6px; background: #fff; cursor: pointer; }}
.timeline-now-btn:hover {{ background: #eaf0fb; border-color: #3498db; color: #2980b9; }}
.timeline-note {{ font-size: 11px; color: #95a5a6; }}

.content {{ flex: 1; overflow-y: auto; padding: 24px; }}
.entry-card {{ background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 16px; border: 1px solid #e8e8e8; transition: box-shadow 0.2s; }}
.entry-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
.entry-card.highlighted {{ border-color: #3498db; box-shadow: 0 0 0 3px rgba(52,152,219,0.15); }}
.entry-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }}
.entry-id {{ font-weight: 700; font-size: 15px; font-family: "SF Mono", Menlo, monospace; color: #2c3e50; }}
.entry-title {{ font-size: 15px; color: #34495e; flex: 1; }}
.status-badge {{ padding: 3px 10px; border-radius: 12px; font-size: 11px; color: #fff; font-weight: 500; }}
.entry-meta {{ display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }}
.register-badge {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #f0f0f0; color: #666; }}
.validity-badge {{ padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #fff7e6; color: #b8860b; font-family: "SF Mono", Menlo, monospace; }}
.fields-grid {{ display: grid; grid-template-columns: auto 1fr auto 1fr; gap: 0; margin-bottom: 10px; font-size: 13px; }}
.field-cell {{ padding: 6px 10px; border-bottom: 1px solid #f5f5f5; }}
.field-key {{ font-weight: 500; color: #7f8c8d; white-space: nowrap; }}
.entry-prose {{ font-size: 13px; color: #555; margin-bottom: 10px; line-height: 1.5; }}
.entry-refs {{ display: block; margin-top: 20px; }}
.ref-link {{ display: inline-block; padding: 3px 8px; background: #eef6ff; border-radius: 4px; font-size: 12px; font-family: "SF Mono", Menlo, monospace; color: #2980b9; text-decoration: none; cursor: pointer; }}
.ref-link:hover {{ background: #d4eaff; }}
.ext-link {{ color: #2980b9; text-decoration: none; }}
.ext-link:hover {{ text-decoration: underline; }}
.ref-group {{ margin-bottom: 8px; display: block; }}
.ref-group .ref-link {{ margin-top: 4px; }}
.ref-label {{ font-size: 12px; color: #7f8c8d; font-weight: 500; margin-right: 6px; }}
.field-key {{ cursor: help; position: relative; }}
.field-key[title] {{ border-bottom: 1px dotted #bbb; }}
.field-key[title]:hover {{ color: #2c3e50; border-bottom-color: #2c3e50; }}
.entry-prose code {{ background: #f0f0f0; padding: 1px 4px; border-radius: 3px; font-size: 12px; }}
.entry-prose strong {{ font-weight: 600; color: #2c3e50; }}

.stats {{ padding: 8px 24px; background: #fff; border-top: 1px solid #e0e0e0; font-size: 12px; color: #7f8c8d; display: flex; gap: 20px; }}

.empty-state {{ display: flex; align-items: center; justify-content: center; height: 100%; color: #95a5a6; font-size: 14px; text-align: center; }}

.graph-toolbar {{ display: flex; align-items: center; gap: 8px; padding: 8px 14px; border-bottom: 1px solid #e0e0e0; background: #fafafa; flex-shrink: 0; }}
.graph-zoom-btn {{ width: 28px; height: 28px; border: 1px solid #bdc3c7; border-radius: 6px; background: #fff; cursor: pointer; font-size: 15px; line-height: 1; display: flex; align-items: center; justify-content: center; color: #2c3e50; }}
.graph-zoom-btn:hover {{ background: #eaf0fb; border-color: #3498db; color: #2980b9; }}
.graph-zoom-btn#graph-zoom-reset {{ width: auto; padding: 0 10px; font-size: 12px; }}
.graph-zoom-level {{ font-size: 12px; color: #7f8c8d; min-width: 42px; text-align: center; }}
#graph-zoom-wrap {{ transition: transform 0.1s ease-out; }}

.reg-header {{ display:none; padding: 10px 24px; background: #f4f6f8; border-bottom: 1px solid #e0e0e0; align-items: center; gap: 12px; }}
.reg-header.visible {{ display: flex; }}
.reg-header-name {{ font-size: 15px; font-weight: 600; color: #2c3e50; flex: 1; }}
.reg-header-meta {{ font-size: 12px; color: #7f8c8d; }}
.reg-file-btn {{ padding: 5px 12px; font-size: 12px; border: 1px solid #bdc3c7; border-radius: 5px; background: #fff; color: #2c3e50; cursor: pointer; text-decoration: none; }}
.reg-file-btn:hover {{ background: #eaf0fb; border-color: #3498db; color: #2980b9; }}

.modal-overlay {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:1000; align-items:center; justify-content:center; }}
.modal-overlay.open {{ display:flex; }}
.modal-box {{ background:#fff; border-radius:10px; width:min(860px,92vw); max-height:88vh; display:flex; flex-direction:column; box-shadow:0 8px 40px rgba(0,0,0,0.22); }}
.modal-header {{ padding:14px 20px; border-bottom:1px solid #e0e0e0; display:flex; align-items:center; gap:10px; }}
.modal-title {{ font-size:15px; font-weight:600; flex:1; color:#2c3e50; }}
.modal-close {{ background:none; border:none; font-size:20px; cursor:pointer; color:#7f8c8d; line-height:1; padding:0 4px; }}
.modal-close:hover {{ color:#2c3e50; }}
.modal-body {{ overflow-y:auto; padding:24px 28px; flex:1; font-size:14px; line-height:1.6; color:#2c3e50; }}
.rm-fm {{ background:#f8f9fa; border:1px solid #e0e0e0; border-radius:8px; margin-bottom:20px; overflow:hidden; }}
.rm-fm-row {{ display:grid; grid-template-columns:140px 1fr; border-bottom:1px solid #eee; padding:8px 14px; align-items:baseline; }}
.rm-fm-row:last-child {{ border-bottom:none; }}
.rm-fm-key {{ font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; color:#7f8c8d; padding-right:12px; white-space:nowrap; }}
.rm-fm-val {{ font-size:13px; color:#2c3e50; word-break:break-word; }}
.rm-h1 {{ font-size:20px; font-weight:700; margin:16px 0 8px; color:#2c3e50; }}
.rm-h2 {{ font-size:16px; font-weight:700; margin:14px 0 6px; color:#2c3e50; border-bottom:1px solid #eee; padding-bottom:4px; }}
.rm-h3 {{ font-size:14px; font-weight:600; margin:12px 0 4px; color:#34495e; }}
.rm-p {{ margin:4px 0; }}
.rm-hr {{ border:none; border-top:1px solid #e0e0e0; margin:12px 0; }}
.rm-sp {{ height:4px; }}
.rm-table {{ border-collapse:collapse; width:100%; margin:8px 0; font-size:13px; }}
.rm-td {{ border:1px solid #ddd; padding:6px 10px; text-align:left; }}
th.rm-td {{ background:#f0f0f0; font-weight:600; }}
.rm-ul {{ margin:4px 0 4px 20px; }}
.rm-ul li {{ margin:2px 0; }}
</style>
</head>
<body>

<div class="sidebar">
  <h2>Registers</h2>
  <div class="reg-item" data-file="graph" id="graph-nav-item"><span class="reg-name">Current Snapshot</span></div>
  {register_nav}
</div>

<div class="main">
  <div class="timeline-bar" id="timeline-bar">
    <span class="timeline-label">As of</span>
    <span class="timeline-date" id="timeline-date-label"></span>
    <input type="range" id="timeline-slider" min="0" max="{len(timeline_dates) - 1}" step="1" value="{len(timeline_dates) - 1}">
    <button class="timeline-now-btn" id="timeline-now-btn">Now</button>
    <span class="timeline-note" id="timeline-note">Reconstructs every register as it looked on the selected date — superseded/former entries reappear as you go back.</span>
  </div>
  <div class="reg-header" id="reg-header">
    <span class="reg-header-name" id="reg-header-name"></span>
    <span class="reg-header-meta" id="reg-header-meta"></span>
    <button class="reg-file-btn" id="reg-file-btn">View metadata</button>
  </div>
  <div class="content" id="content">
    <div class="empty-state" id="empty-state" style="display:none;">Select a register from the sidebar to browse its entries.</div>
    {entry_cards}
  </div>
  {graph_panel}
  <div class="stats">
    <span id="stats-count">Showing all entries</span>
    <span>Registers: {len(registers)}</span>
    <span>Total entries: {sum(len(r["entries"]) for r in registers)}</span>
  </div>
</div>

<div class="modal-overlay" id="modal-overlay">
  <div class="modal-box">
    <div class="modal-header">
      <span class="modal-title" id="modal-title"></span>
      <button class="modal-close" id="modal-close">&#x2715;</button>
    </div>
    <div class="modal-body" id="modal-body"></div>
  </div>
</div>

<script>
const allEntries = {entries_json};
const allRegisters = {registers_json};
const timelineDates = {timeline_json};
const TODAY = "{today}";

let currentRegister = null;
let currentDate = TODAY;

function isValidAtDate(card, dateStr) {{
  const vf = card.dataset.validFrom;
  const vt = card.dataset.validTo;
  if (!vf) return true; // no time data on this entry -> always shown
  if (dateStr < vf) return false;
  if (vt && dateStr >= vt) return false;
  return true;
}}

function applyFilters() {{
  document.querySelectorAll('.entry-card').forEach(c => {{
    const registerMatch = (c.dataset.register === currentRegister);
    const timelineMatch = isValidAtDate(c, currentDate);
    c.style.display = (registerMatch && timelineMatch) ? '' : 'none';
  }});
  updateStats();
}}

function isTimelineEligible(register) {{
  return !!(register && allRegisters[register] && allRegisters[register].timeline_eligible);
}}

function setTimelineBarEnabled(eligible) {{
  var tb = document.getElementById('timeline-bar');
  tb.style.display = eligible ? 'flex' : 'none';
}}

function applyState(state, push) {{
  if (push) history.pushState(state, '', state.view === 'entry' ? '#' + state.id.toLowerCase() : state.view === 'graph' ? '#graph' : '#');

  if (state.view === 'entry') {{
    showEntry(state.id);
  }} else if (state.view === 'graph') {{
    showGraph();
  }} else if (state.view === 'list' && state.register) {{
    showList(state.register);
  }} else {{
    showWelcome();
  }}
}}

function showWelcome() {{
  currentRegister = null;
  var gp = document.getElementById('graph-panel');
  if (gp) gp.style.display = 'none';
  document.getElementById('content').style.display = '';
  document.querySelectorAll('.entry-card').forEach(c => {{ c.style.display = 'none'; c.classList.remove('highlighted'); }});
  var empty = document.getElementById('empty-state');
  if (empty) empty.style.display = 'flex';
  setTimelineBarEnabled(false);
  document.querySelectorAll('.reg-item').forEach(i => i.classList.remove('active'));
  updateRegHeader(null);
  updateStats();
}}

function showList(register) {{
  currentRegister = register;
  var gp = document.getElementById('graph-panel');
  if (gp) gp.style.display = 'none';
  document.getElementById('content').style.display = '';
  var empty = document.getElementById('empty-state');
  if (empty) empty.style.display = 'none';
  setTimelineBarEnabled(isTimelineEligible(register));
  document.querySelectorAll('.entry-card').forEach(c => c.classList.remove('highlighted'));
  document.querySelectorAll('.reg-item').forEach(i => {{
    i.classList.toggle('active', i.dataset.file === register);
  }});
  updateRegHeader(register);
  applyFilters();
}}

function updateRegHeader(register) {{
  var hdr = document.getElementById('reg-header');
  var nameEl = document.getElementById('reg-header-name');
  var metaEl = document.getElementById('reg-header-meta');
  if (!hdr) return;
  var reg = register ? allRegisters[register] : null;
  if (!reg) {{ hdr.classList.remove('visible'); return; }}
  hdr.classList.add('visible');
  nameEl.textContent = reg.display_name;
  var fm = reg.frontmatter;
  var meta = [];
  if (fm.type) meta.push('type: ' + fm.type);
  if (fm.id_prefix) meta.push('prefix: ' + fm.id_prefix);
  if (fm.lifecycle) meta.push(fm.lifecycle);
  if (fm.singleton_key && fm.singleton_key !== 'null') meta.push('singleton key: ' + fm.singleton_key);
  meta.push(reg.entry_count + ' ' + (reg.entry_count === 1 ? 'entry' : 'entries'));
  metaEl.textContent = meta.join(' · ');
}}

function showEntry(entryId) {{
  const anchor = entryId.toLowerCase();
  const card = document.getElementById(anchor);
  if (!card) return;
  const register = card.dataset.register;
  currentRegister = register;
  document.querySelectorAll('.reg-item').forEach(i => {{
    i.classList.toggle('active', i.dataset.file === register);
  }});
  var gp = document.getElementById('graph-panel');
  if (gp) gp.style.display = 'none';
  document.getElementById('content').style.display = '';
  var empty = document.getElementById('empty-state');
  if (empty) empty.style.display = 'none';
  setTimelineBarEnabled(isTimelineEligible(register));
  applyFilters();
  card.classList.add('highlighted');
  card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
}}

document.querySelectorAll('.reg-item').forEach(item => {{
  item.addEventListener('click', () => {{
    if (item.dataset.file === 'graph') {{
      applyState({{ view: 'graph' }}, true);
    }} else {{
      applyState({{ view: 'list', register: item.dataset.file }}, true);
    }}
  }});
}});

document.querySelectorAll('.tier-header').forEach(header => {{
  header.addEventListener('click', () => {{
    header.classList.toggle('collapsed');
    const children = header.nextElementSibling;
    if (children) children.classList.toggle('collapsed');
  }});
}});

document.addEventListener('click', (e) => {{
  const link = e.target.closest('.ref-link');
  if (link) {{
    e.preventDefault();
    applyState({{ view: 'entry', id: link.dataset.target }}, true);
  }}
}});

window.addEventListener('popstate', (e) => {{
  const state = e.state || {{ view: 'welcome' }};
  applyState(state, false);
}});

(function() {{
  const hash = location.hash.slice(1);
  if (hash.toLowerCase() === 'graph') {{
    applyState({{ view: 'graph' }}, false);
  }} else if (hash && allEntries[hash.toUpperCase()]) {{
    applyState({{ view: 'entry', id: hash.toUpperCase() }}, false);
  }} else {{
    applyState({{ view: 'welcome' }}, false);
  }}
}})();

function updateStats() {{
  if (!currentRegister) {{
    document.getElementById('stats-count').textContent = 'No register selected';
    return;
  }}
  const visible = document.querySelectorAll('.entry-card:not([style*="display: none"])').length;
  const total = document.querySelectorAll('.entry-card').length;
  const dateNote = currentDate === TODAY ? '' : ` as of ${{currentDate}}`;
  document.getElementById('stats-count').textContent = `Showing ${{visible}} of ${{total}} entries${{dateNote}}`;
}}

function showGraph() {{
  var gp = document.getElementById('graph-panel');
  var ep = document.getElementById('content');
  if (!gp) return;
  gp.style.display = 'flex';
  ep.style.display = 'none';
  setTimelineBarEnabled(false);
  document.querySelectorAll('.reg-item').forEach(i => i.classList.remove('active'));
  var nav = document.getElementById('graph-nav-item');
  if (nav) nav.classList.add('active');
  wireGraphNodes();
}}

document.getElementById('reg-file-btn').addEventListener('click', function() {{
  var activeItem = document.querySelector('.reg-item.active');
  if (!activeItem) return;
  var register = activeItem.dataset.file;
  if (!register || register === 'graph') return;
  var reg = allRegisters[register];
  if (!reg) return;
  document.getElementById('modal-title').textContent = reg.display_name + ' — metadata';
  document.getElementById('modal-body').innerHTML = reg.schema_html;
  document.getElementById('modal-overlay').classList.add('open');
}});

document.getElementById('modal-close').addEventListener('click', function() {{
  document.getElementById('modal-overlay').classList.remove('open');
}});

document.getElementById('modal-overlay').addEventListener('click', function(e) {{
  if (e.target === this) this.classList.remove('open');
}});

document.addEventListener('keydown', function(e) {{
  if (e.key === 'Escape') document.getElementById('modal-overlay').classList.remove('open');
}});

function wireGraphNodes() {{
  var gp = document.getElementById('graph-panel');
  if (!gp || gp._nodesWired) return;
  gp._nodesWired = true;
  var sanMap = {{}};
  Object.keys(allEntries).forEach(function(id) {{
    sanMap[id.replace(/[^A-Za-z0-9]/g, '')] = id;
  }});
  gp.querySelectorAll('g.node').forEach(function(node) {{
    var m = node.id.match(/flowchart-(.+)-\\d+$/);
    if (!m) return;
    var entryId = sanMap[m[1]];
    if (!entryId) return;
    node.style.cursor = 'pointer';
    node.setAttribute('title', entryId);
    node.addEventListener('mouseenter', function() {{ node.style.opacity = '0.75'; }});
    node.addEventListener('mouseleave', function() {{ node.style.opacity = ''; }});
    node.addEventListener('click', function() {{
      applyState({{ view: 'entry', id: entryId }}, true);
    }});
  }});
}}

// Graph zoom controls
(function() {{
  var zoomLevel = 1;
  var wrap = document.getElementById('graph-zoom-wrap');
  var levelLabel = document.getElementById('graph-zoom-level');

  function applyZoom() {{
    if (wrap) wrap.style.transform = 'scale(' + zoomLevel + ')';
    if (levelLabel) levelLabel.textContent = Math.round(zoomLevel * 100) + '%';
  }}

  var zoomInBtn = document.getElementById('graph-zoom-in');
  var zoomOutBtn = document.getElementById('graph-zoom-out');
  var zoomResetBtn = document.getElementById('graph-zoom-reset');

  if (zoomInBtn) zoomInBtn.addEventListener('click', function() {{
    zoomLevel = Math.min(3, Math.round((zoomLevel + 0.2) * 100) / 100);
    applyZoom();
  }});
  if (zoomOutBtn) zoomOutBtn.addEventListener('click', function() {{
    zoomLevel = Math.max(0.2, Math.round((zoomLevel - 0.2) * 100) / 100);
    applyZoom();
  }});
  if (zoomResetBtn) zoomResetBtn.addEventListener('click', function() {{
    zoomLevel = 1;
    applyZoom();
  }});
}})();

// Timeline slider wiring
const timelineSlider = document.getElementById('timeline-slider');
const timelineDateLabel = document.getElementById('timeline-date-label');

function setTimelineIndex(idx) {{
  idx = Math.max(0, Math.min(timelineDates.length - 1, idx));
  currentDate = timelineDates[idx];
  timelineSlider.value = idx;
  timelineDateLabel.textContent = currentDate + (currentDate === TODAY ? ' (today)' : '');
  applyFilters();
}}

timelineSlider.addEventListener('input', function() {{
  setTimelineIndex(parseInt(this.value, 10));
}});

document.getElementById('timeline-now-btn').addEventListener('click', function() {{
  setTimelineIndex(timelineDates.length - 1);
}});

setTimelineIndex(timelineDates.length - 1);
</script>

</body>
</html>'''

    output_path.write_text(html_content, encoding="utf-8")
    print(f"✓ Onboarding KB browser generated: {output_path}")
    print(f"  Registers: {len(registers)}")
    print(f"  Entries:   {sum(len(r['entries']) for r in registers)}")
    print(f"  Timeline:  {timeline_dates[0]} -> {timeline_dates[-1]} ({len(timeline_dates)} steps)")
    print(f"  Open in browser: file://{output_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Generate HTML browser for the onboarding KB registers")
    parser.add_argument("--output", "-o", type=Path, default=Path("kb-browser.html"), help="Output HTML file")
    parser.add_argument("--path", type=Path, default=REGISTERS_DIR, help="Path to registers directory")
    args = parser.parse_args()

    if not args.path.exists():
        print(f"ERROR: Registers directory not found: {args.path}")
        print("Run scaffold-registers.py first, or pass --path to point at an existing .registers/ directory.")
        sys.exit(1)

    register_files = sorted(args.path.glob("*.md"))

    if not register_files:
        print(f"No register files found in {args.path}")
        sys.exit(1)

    registers = []
    for rf in register_files:
        try:
            parsed = parse_register(rf)
            registers.append(parsed)
        except Exception as e:
            print(f"  Warning: could not parse {rf.name}: {e}", file=sys.stderr)

    generate_html(registers, args.output)


if __name__ == "__main__":
    main()
