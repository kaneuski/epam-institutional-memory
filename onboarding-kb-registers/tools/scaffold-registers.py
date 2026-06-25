#!/usr/bin/env python3
"""
scaffold-registers.py

Scaffolds all 12 KB register files for the onboarding / institutional-memory
ontology (see kb-register-schema.md in this folder).

Usage:
    python3 scaffold-registers.py [--path DIR] [--dry-run]

Default target directory: ./.registers

The leading dot is deliberate: this directory holds generated, continuously-mutated state (register
entries written by kb-updater), not source code. Treat it like a data/cache directory, not a package.
"""

import argparse
import datetime
import json
import os

DEFAULT_REGISTERS_DIR = ".registers"

TODAY = datetime.date.today().isoformat()

REGISTERS = [
    # --- Core ---
    {
        "filename": "policies.md",
        "type": "policy",
        "tier": "core",
        "lifecycle": "evolving",
        "id_prefix": "POL",
        "singleton_key": "scope",
        "source_doc_types": ["policy-doc"],
        "title": "Policies",
        "description": "Versioned governance documents. At most one status:active entry per scope.",
    },
    {
        "filename": "decisions.md",
        "type": "decision",
        "tier": "core",
        "lifecycle": "evolving",
        "id_prefix": "DEC",
        "singleton_key": None,
        "source_doc_types": ["policy-doc", "team-directory-update"],
        "title": "Decisions",
        "description": "Explicit decisions, their rationale, and the registers they changed.",
    },
    {
        "filename": "role-assignments.md",
        "type": "role-assignment",
        "tier": "core",
        "lifecycle": "evolving",
        "id_prefix": "POS",
        "singleton_key": "role_title",
        "source_doc_types": ["team-directory", "team-directory-update"],
        "title": "Role Assignments",
        "description": "Who holds what role, with supersession history. At most one status:current entry per role_title.",
    },
    {
        "filename": "service-ownership.md",
        "type": "service-ownership",
        "tier": "core",
        "lifecycle": "evolving",
        "id_prefix": "OWN",
        "singleton_key": "service",
        "source_doc_types": ["onboarding-handbook", "team-directory-update"],
        "title": "Service Ownership",
        "description": "Which team/lead owns which service, with supersession history. At most one status:current entry per service.",
    },
    {
        "filename": "incidents.md",
        "type": "incident",
        "tier": "core",
        "lifecycle": "tracked-until-closed",
        "id_prefix": "INC",
        "singleton_key": None,
        "source_doc_types": ["policy-doc"],
        "title": "Incidents",
        "description": "Trigger events behind policy and process changes.",
    },
    # --- Domain ---
    {
        "filename": "people.md",
        "type": "person",
        "tier": "domain",
        "lifecycle": "static",
        "id_prefix": "PER",
        "singleton_key": None,
        "source_doc_types": ["team-directory", "team-directory-update"],
        "title": "People",
        "description": "Identity facts about individuals. Current title is derived from role-assignments.md, not stored here.",
    },
    {
        "filename": "teams.md",
        "type": "team",
        "tier": "domain",
        "lifecycle": "static",
        "id_prefix": "TEAM",
        "singleton_key": None,
        "source_doc_types": ["team-directory"],
        "title": "Teams",
        "description": "Team identity and mission.",
    },
    {
        "filename": "services.md",
        "type": "service",
        "tier": "domain",
        "lifecycle": "static",
        "id_prefix": "SYS",
        "singleton_key": None,
        "source_doc_types": ["onboarding-handbook"],
        "title": "Services",
        "description": "Service identity and purpose. Ownership lives in service-ownership.md, not here.",
    },
    {
        "filename": "access-tiers.md",
        "type": "access-tier",
        "tier": "domain",
        "lifecycle": "evolving",
        "id_prefix": "AT",
        "singleton_key": "tier_name",
        "source_doc_types": ["policy-doc", "onboarding-handbook"],
        "title": "Access Tiers",
        "description": "The access-level taxonomy, with eligibility criteria pointing at the currently governing policy.",
    },
    # --- Traceability ---
    {
        "filename": "onboarding-stages.md",
        "type": "onboarding-stage",
        "tier": "traceability",
        "lifecycle": "static",
        "id_prefix": "STAGE",
        "singleton_key": None,
        "source_doc_types": ["onboarding-handbook"],
        "title": "Onboarding Stages",
        "description": "Sequential new-hire journey stages from the onboarding handbook.",
    },
    {
        "filename": "exceptions.md",
        "type": "exception",
        "tier": "traceability",
        "lifecycle": "tracked-until-closed",
        "id_prefix": "EXC",
        "singleton_key": None,
        "source_doc_types": ["policy-doc"],
        "title": "Exceptions",
        "description": "Conditional carve-outs that override a standard policy.",
    },
    {
        "filename": "open-questions.md",
        "type": "open-question",
        "tier": "traceability",
        "lifecycle": "tracked-until-closed",
        "id_prefix": "OQ",
        "singleton_key": None,
        "source_doc_types": ["any"],
        "title": "Open Questions",
        "description": "Unresolved ambiguities surfaced while ingesting source documents.",
    },
]


def format_list(items):
    if not items:
        return "[]"
    formatted = ", ".join(f'"{item}"' for item in items)
    return f"[{formatted}]"


def render_file(reg):
    singleton_key = reg["singleton_key"]
    singleton_value = f'"{singleton_key}"' if singleton_key else "null"
    source_doc_types = format_list(reg["source_doc_types"])

    return (
        f"---\n"
        f"type: {reg['type']}\n"
        f"tier: {reg['tier']}\n"
        f"lifecycle: {reg['lifecycle']}\n"
        f"id_prefix: {reg['id_prefix']}\n"
        f"singleton_key: {singleton_value}\n"
        f"source_doc_types: {source_doc_types}\n"
        f"last_updated: {TODAY}\n"
        f"---\n"
        f"\n"
        f"# {reg['title']}\n"
        f"\n"
        f"{reg['description']}\n"
        f"\n"
        f"---\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold all 12 KB register files for the onboarding / institutional-memory ontology."
    )
    parser.add_argument(
        "--path",
        default=DEFAULT_REGISTERS_DIR,
        help=f"Target registers directory (default: {DEFAULT_REGISTERS_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without writing any files.",
    )
    args = parser.parse_args()

    registers_path = args.path

    if not args.dry_run:
        os.makedirs(registers_path, exist_ok=True)

    created = 0
    skipped = 0

    for reg in REGISTERS:
        file_path = os.path.join(registers_path, reg["filename"])

        if os.path.exists(file_path):
            skipped += 1
            if args.dry_run:
                print(f"  SKIP  {file_path} (already exists)")
            continue

        content = render_file(reg)

        if args.dry_run:
            print(f"  CREATE  {file_path}")
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            created += 1

    if args.dry_run:
        would_create = len(REGISTERS) - skipped
        print(
            f"\nDry run complete. Would create {would_create} register(s). "
            f"Would skip {skipped} (already exist)."
        )
    else:
        print(f"Created {created} register(s). Skipped {skipped} (already exist).")


if __name__ == "__main__":
    main()
