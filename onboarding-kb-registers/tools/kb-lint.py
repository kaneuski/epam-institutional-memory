#!/usr/bin/env python3
"""KB Register Reference Validator for the onboarding / institutional-memory ontology.

Validates cross-reference integrity and domain-specific invariants across all
register files described in kb-register-schema.md (this folder).

Generic checks (structural):
  1. All markdown links resolve to an existing entry.
  2. ID prefixes match their declared register file.
  3. No duplicate IDs within a register.
  4. Bidirectional reference coverage for Supersedes/Superseded by and Modifies pairs.
  5. Status values match the register's allowed lifecycle states.

Domain-specific checks (the reason this ontology exists):
  6. Singleton-current violation — more than one entry shares a singleton_key
     value while "current" (active for policies, current for role-assignments /
     service-ownership, always for access-tiers).
  7. Stale pointer to a superseded policy (governing_policy / modifies_policy / policy_ref).
  8. Date ordering — a superseding entry's date must be >= the entry it supersedes.
  9. Orphaned decision — a decisions.md entry with no Produces link.
  10. Incident-postmortem completeness — resolved P0/P1 incidents need a postmortem_link.
  11. Migration deadline drift — a policy's migration_deadline has passed.

Usage:
  python3 kb-lint.py [--path DIR] [--strict] [--json]

Exit codes:
  0 = clean
  1 = errors found
  2 = warnings only (with --strict, promotes to exit 1)
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

DEFAULT_REGISTERS_DIR = Path(".registers")

ENTRY_HEADING_RE = re.compile(r"^## ([A-Z]+-\d{3}):\s*(.+)$", re.MULTILINE)
LINK_RE = re.compile(r"\[([A-Z]+-\d{3})\]\(([^)]+)\)")
FIELD_ROW_RE = re.compile(r"^\|\s*([a-zA-Z_]+)\s*\|\s*(.+?)\s*\|\s*$")
REFERENCE_LINE_RE = re.compile(r"^-\s*([A-Za-z][A-Za-z /]*?):\s*(.+)$")
ID_RE = re.compile(r"\b([A-Z]+-\d{3})\b")

PREFIX_TO_FILE = {
    "POL": "policies.md",
    "DEC": "decisions.md",
    "POS": "role-assignments.md",
    "OWN": "service-ownership.md",
    "INC": "incidents.md",
    "PER": "people.md",
    "TEAM": "teams.md",
    "SYS": "services.md",
    "AT": "access-tiers.md",
    "STAGE": "onboarding-stages.md",
    "EXC": "exceptions.md",
    "OQ": "open-questions.md",
}

LIFECYCLE_STATES = {
    "policies": ["active", "superseded"],
    "decisions": ["active", "reversed"],
    "role-assignments": ["current", "former"],
    "service-ownership": ["current", "former"],
    "incidents": ["open", "investigating", "resolved"],
    "exceptions": ["active", "superseded", "revoked"],
    "open-questions": ["open", "answered", "deferred"],
}

# (register_stem, field) -> "current" status value that makes an entry the
# singleton holder for that register. None means "every entry is current"
# (used for access-tiers, which has no status field at all).
SINGLETON_RULES = {
    "policies": ("scope", "status", "active"),
    "role-assignments": ("role_title", "status", "current"),
    "service-ownership": ("service", "status", "current"),
    "access-tiers": ("tier_name", None, None),
}

# (register_stem, field) -> register_stem the field must point to, with the
# requirement that the target entry's status is "active".
STALE_POINTER_FIELDS = {
    ("access-tiers", "governing_policy"): "policies",
    ("exceptions", "modifies_policy"): "policies",
    ("onboarding-stages", "policy_ref"): "policies",
}

# (register_stem, supersedes_field) -> date field to compare for ordering.
DATE_ORDER_FIELDS = {
    "policies": ("supersedes", "effective_date"),
    "role-assignments": ("supersedes", "start_date"),
    "service-ownership": ("supersedes", "start_date"),
}


def get_prefix(entry_id: str) -> str:
    m = re.match(r"^([A-Z]+)-", entry_id)
    return m.group(1) if m else ""


def id_to_anchor(entry_id: str) -> str:
    return entry_id.lower()


def parse_register(path: Path) -> dict:
    """Parse a register file into entries with fields, links, and reference lines."""
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    headings = list(ENTRY_HEADING_RE.finditer(content))
    entries = {}

    for i, match in enumerate(headings):
        entry_id = match.group(1)
        title = match.group(2)
        start_line = content[: match.start()].count("\n") + 1
        end_line = (
            content[: headings[i + 1].start()].count("\n") + 1
            if i + 1 < len(headings)
            else len(lines) + 1
        )

        body_lines = lines[start_line - 1 : end_line - 1]
        fields = {}
        for line in body_lines:
            fm = FIELD_ROW_RE.match(line.strip())
            if fm:
                key, value = fm.group(1), fm.group(2).strip()
                if key.lower() == "field":
                    continue  # header row
                if set(value) <= {"-"}:
                    continue  # separator row
                fields[key] = value

        links = []
        for lm in LINK_RE.finditer(content, match.start(), headings[i + 1].start() if i + 1 < len(headings) else len(content)):
            target_id = lm.group(1)
            target_file = lm.group(2).split("#")[0]
            anchor = lm.group(2).split("#")[1] if "#" in lm.group(2) else None
            line_no = content[: lm.start()].count("\n") + 1
            links.append({"target_id": target_id, "target_file": target_file, "anchor": anchor, "line": line_no})

        reference_lines = []
        for line in body_lines:
            rm = REFERENCE_LINE_RE.match(line.strip())
            if rm:
                label, rest = rm.group(1).strip(), rm.group(2)
                ids = ID_RE.findall(rest)
                reference_lines.append({"label": label, "ids": ids})

        entries[entry_id] = {
            "title": title,
            "line": start_line,
            "fields": fields,
            "links": links,
            "reference_lines": reference_lines,
        }

    return {"entries": entries}


def add_error(errors, filename, line, message):
    errors.append(f"{filename}:{line} — {message}" if line else f"{filename} — {message}")


def add_warning(warnings, filename, line, message):
    warnings.append(f"{filename}:{line} — {message}" if line else f"{filename} — {message}")


def parse_date(value):
    if not value or value.lower() in ("null", "none", "n/a", ""):
        return None
    try:
        return datetime.date.fromisoformat(value.strip())
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser(description="Validate onboarding-domain KB register integrity")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--path", type=Path, default=DEFAULT_REGISTERS_DIR, help="Path to registers directory")
    args = parser.parse_args()

    registers_path = args.path

    def fail_missing(message):
        if args.json:
            print(json.dumps({"errors": 1, "warnings": 0, "details": [{"level": "error", "message": message}]}))
        else:
            print(f"ERROR: {message}")
        sys.exit(1)

    if not registers_path.exists():
        fail_missing(f"Registers directory not found: {registers_path}")

    errors = []
    warnings = []

    all_entries = {}     # id -> file stem (e.g. "policies")
    all_registers = {}   # filename -> parsed data

    register_files = sorted(registers_path.glob("*.md"))
    if not register_files:
        fail_missing(f"No register files found in {registers_path}")

    if not args.json:
        print(f"Scanning {len(register_files)} register files...")

    for reg_file in register_files:
        parsed = parse_register(reg_file)
        all_registers[reg_file.name] = parsed
        for entry_id, info in parsed["entries"].items():
            prefix = get_prefix(entry_id)
            expected_file = PREFIX_TO_FILE.get(prefix)

            # Check 2: prefix matches file
            if expected_file and expected_file != reg_file.name:
                add_error(errors, reg_file.name, info["line"], f"{entry_id} belongs in {expected_file}, not {reg_file.name}")

            # Check 3: duplicate IDs
            if entry_id in all_entries:
                add_error(errors, reg_file.name, info["line"], f"Duplicate ID {entry_id} (also in {all_entries[entry_id]}.md)")
            else:
                all_entries[entry_id] = reg_file.name.replace(".md", "")

    # Check 1: broken links + anchor sanity
    for filename, parsed in all_registers.items():
        for entry_id, info in parsed["entries"].items():
            for link in info["links"]:
                target_id = link["target_id"]
                target_file = link["target_file"]
                if target_id not in all_entries:
                    add_error(
                        errors, filename, link["line"],
                        f"Broken reference: [{target_id}]({target_file}#{link['anchor']}) — entry does not exist in any register",
                    )
                    continue
                target_stem = all_entries[target_id]
                if target_file and target_file != f"{target_stem}.md":
                    add_error(
                        errors, filename, link["line"],
                        f"Wrong file in link: [{target_id}] points to {target_file} but entry lives in {target_stem}.md",
                    )
                if link["anchor"] and link["anchor"] != id_to_anchor(target_id):
                    add_warning(warnings, filename, link["line"], f"Anchor mismatch: #{link['anchor']} should be #{id_to_anchor(target_id)}")

    # Check 4: bidirectional Supersedes/Superseded by and Modifies pairs
    BIDIRECTIONAL_LABELS = {
        "Supersedes": "Superseded by",
        "Superseded by": "Supersedes",
        "Modifies": "Modified by",
    }
    for filename, parsed in all_registers.items():
        for entry_id, info in parsed["entries"].items():
            for ref in info["reference_lines"]:
                if ref["label"] not in BIDIRECTIONAL_LABELS:
                    continue
                expected_back_label = BIDIRECTIONAL_LABELS[ref["label"]]
                for target_id in ref["ids"]:
                    if target_id not in all_entries:
                        continue
                    target_file = all_entries[target_id] + ".md"
                    target_info = all_registers.get(target_file, {}).get("entries", {}).get(target_id)
                    if not target_info:
                        continue
                    has_back_link = any(
                        r["label"] == expected_back_label and entry_id in r["ids"]
                        for r in target_info["reference_lines"]
                    )
                    if not has_back_link:
                        add_warning(
                            warnings, filename, info["line"],
                            f"One-way link: {entry_id} --{ref['label']}--> {target_id} (no '{expected_back_label}' back-link from {target_id})",
                        )

    # Check 5: status values valid for the register
    for filename, parsed in all_registers.items():
        stem = filename.replace(".md", "")
        allowed = LIFECYCLE_STATES.get(stem)
        if not allowed:
            continue
        for entry_id, info in parsed["entries"].items():
            status = info["fields"].get("status")
            if status and status not in allowed:
                add_error(errors, filename, info["line"], f"{entry_id} — invalid status '{status}'. Allowed: {', '.join(allowed)}")

    # Check 6: singleton-current violations
    for filename, parsed in all_registers.items():
        stem = filename.replace(".md", "")
        rule = SINGLETON_RULES.get(stem)
        if not rule:
            continue
        key_field, status_field, current_value = rule
        groups = {}
        for entry_id, info in parsed["entries"].items():
            key_value = info["fields"].get(key_field)
            if not key_value:
                continue
            is_current = True
            if status_field:
                is_current = info["fields"].get(status_field) == current_value
            if is_current:
                groups.setdefault(key_value, []).append(entry_id)
        for key_value, ids in groups.items():
            if len(ids) > 1:
                add_error(
                    errors, filename, None,
                    f"Singleton violation: {key_field}='{key_value}' has {len(ids)} entries marked current ({', '.join(ids)}) — only one is allowed",
                )

    # Check 7: stale pointer to superseded policy
    for filename, parsed in all_registers.items():
        stem = filename.replace(".md", "")
        for entry_id, info in parsed["entries"].items():
            # A citing entry that is itself closed out (e.g. an exception with
            # status: superseded/revoked) is a historical record, not a live
            # cross-reference — it's expected to still point at whatever policy
            # it used to modify, even after that policy is superseded.
            own_status = info["fields"].get("status")
            if stem in LIFECYCLE_STATES and own_status and own_status != LIFECYCLE_STATES[stem][0]:
                continue
            for field, target_stem in STALE_POINTER_FIELDS.items():
                if field[0] != stem:
                    continue
                field_name = field[1]
                target_id = info["fields"].get(field_name)
                if not target_id or target_id.lower() in ("null", "none"):
                    continue
                target_file = PREFIX_TO_FILE.get(get_prefix(target_id))
                target_info = all_registers.get(target_file, {}).get("entries", {}).get(target_id) if target_file else None
                if not target_info:
                    add_error(errors, filename, info["line"], f"{entry_id}.{field_name} points to {target_id}, which does not exist")
                    continue
                target_status = target_info["fields"].get("status")
                if target_status and target_status != "active":
                    add_error(
                        errors, filename, info["line"],
                        f"Stale pointer: {entry_id}.{field_name} -> {target_id} (status: {target_status}). Update to the current active policy.",
                    )

    # Check 8: date ordering on supersession
    for filename, parsed in all_registers.items():
        stem = filename.replace(".md", "")
        rule = DATE_ORDER_FIELDS.get(stem)
        if not rule:
            continue
        supersedes_field, date_field = rule
        for entry_id, info in parsed["entries"].items():
            supersedes_id = info["fields"].get(supersedes_field)
            if not supersedes_id or supersedes_id.lower() in ("null", "none"):
                continue
            this_date = parse_date(info["fields"].get(date_field))
            target_info = parsed["entries"].get(supersedes_id)
            if not target_info:
                continue  # already reported as broken/missing elsewhere if truly absent
            target_date = parse_date(target_info["fields"].get(date_field))
            if this_date and target_date and this_date < target_date:
                add_error(
                    errors, filename, info["line"],
                    f"Date ordering: {entry_id}.{date_field}={this_date} precedes {supersedes_id}.{date_field}={target_date}, which it supersedes",
                )

    # Check 9: orphaned decisions (no Produces link)
    decisions = all_registers.get("decisions.md", {}).get("entries", {})
    for entry_id, info in decisions.items():
        has_produces = any(ref["label"] == "Produces" and ref["ids"] for ref in info["reference_lines"])
        if not has_produces:
            add_warning(warnings, "decisions.md", info["line"], f"{entry_id} has no 'Produces' link — confirm this decision was applied to a register")

    # Check 10: incident postmortem completeness
    incidents = all_registers.get("incidents.md", {}).get("entries", {})
    for entry_id, info in incidents.items():
        severity = info["fields"].get("severity")
        status = info["fields"].get("status")
        postmortem_link = info["fields"].get("postmortem_link")
        if severity in ("P0", "P1") and status == "resolved":
            if not postmortem_link or postmortem_link.lower() in ("null", "none", ""):
                add_error(errors, "incidents.md", info["line"], f"{entry_id} — resolved {severity} incident has no postmortem_link")

    # Check 11: migration deadline drift
    today = datetime.date.today()
    policies = all_registers.get("policies.md", {}).get("entries", {})
    for entry_id, info in policies.items():
        deadline = parse_date(info["fields"].get("migration_deadline"))
        if deadline and deadline < today:
            add_warning(warnings, "policies.md", info["line"], f"{entry_id} — migration_deadline {deadline} has passed; verify dependents were reconciled")

    # --- Report ---
    if args.json:
        def _parse_issue(text, level):
            file_match = re.match(r"^([^:]+):\d+ — (.+)$", text) or re.match(r"^([^ ]+) — (.+)$", text)
            file_part = file_match.group(1) if file_match else None
            message = file_match.group(2) if file_match else text
            entry_match = re.search(r"\b([A-Z]+-\d{3})\b", message)
            entry = entry_match.group(1) if entry_match else None
            item = {"level": level}
            if file_part:
                item["file"] = file_part
            if entry:
                item["entry"] = entry
            item["message"] = message
            return item

        details = [_parse_issue(e, "error") for e in errors] + [_parse_issue(w, "warning") for w in warnings]
        output = {"errors": len(errors), "warnings": len(warnings), "details": details}
        print(json.dumps(output, indent=2))
        if errors:
            sys.exit(1)
        elif warnings:
            sys.exit(1 if args.strict else 2)
        sys.exit(0)

    total_entries = len(all_entries)
    total_links = sum(len(info["links"]) for p in all_registers.values() for info in p["entries"].values())
    print()
    print(f"  Registers: {len(register_files)}")
    print(f"  Entries:   {total_entries}")
    print(f"  Links:     {total_links}")
    print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
        print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings[:50]:
            print(f"  ⚠ {w}")
        if len(warnings) > 50:
            print(f"  ... and {len(warnings) - 50} more")
        print()

    if not errors and not warnings:
        print("✓ All checks passed. No issues found.")
        sys.exit(0)
    elif errors:
        print(f"✗ {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    else:
        if args.strict:
            print(f"✗ {len(warnings)} warning(s) treated as errors (--strict)")
            sys.exit(1)
        print(f"⚠ {len(warnings)} warning(s) (use --strict to fail on warnings)")
        sys.exit(2)


if __name__ == "__main__":
    main()
