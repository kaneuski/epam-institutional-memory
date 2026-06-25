"""
Validate that the three KB custom skills are reachable in the cloud and show
the SKILL.md frontmatter (name + description) that the agent loads into context.

What "available" means here:
  - The skill_id stored in each .skill_*_id dotfile resolves to a real skill
    in the workspace (GET /v1/skills/{id} returns HTTP 200).
  - The skill's latest version is reachable (GET /v1/skills/{id}/versions/{v}).
  - The version carries a non-empty name and description — the two fields the
    agent receives as Level-1 metadata (always loaded, ~100 tokens per skill).

Usage:
    python inspect_skills.py
"""

import os
import sys
from pathlib import Path

from anthropic import Anthropic, NotFoundError

SKILL_DOTFILES = [
    (".skill_kb_browser_id",   "kb-browser"),
    (".skill_kb_snapshot_id",  "kb-snapshot"),
    (".skill_kb_updater_id",   "kb-updater"),
]


def check_skill(client: Anthropic, skill_name: str, skill_id: str) -> bool:
    print(f"\n── {skill_name}  ({skill_id})")

    try:
        skill = client.beta.skills.retrieve(skill_id)
    except NotFoundError:
        print("  ✗  NOT FOUND — skill_id is invalid or was deleted")
        return False

    latest = skill.latest_version
    if not latest:
        print("  ✗  Skill exists but has no versions")
        return False

    try:
        version = client.beta.skills.versions.retrieve(latest, skill_id=skill_id)
    except NotFoundError:
        print(f"  ✗  Version {latest} not found")
        return False

    ok = bool(version.name and version.description)
    status = "✓" if ok else "✗"

    print(f"  {status}  source:     {skill.source}")
    print(f"  {status}  version:    {version.version}")
    print(f"  {status}  directory:  {version.directory}")
    print(f"  {status}  created:    {skill.created_at}")
    print()
    print("  SKILL.md frontmatter (what the agent sees in context):")
    print(f"    name:        {version.name!r}")
    print(f"    description: {version.description!r}")

    if not version.name:
        print("  ✗  name is empty — SKILL.md frontmatter may be malformed")
    if not version.description:
        print("  ✗  description is empty — agent won't know when to trigger this skill")

    return ok


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    missing = [f for f, _ in SKILL_DOTFILES if not Path(f).exists()]
    if missing:
        raise SystemExit(
            f"Missing dotfiles: {missing}\nRun upload_skills.py first."
        )

    client = Anthropic()

    print("Inspecting KB skills in workspace...\n")
    results = []
    for dotfile, name in SKILL_DOTFILES:
        skill_id = Path(dotfile).read_text().strip()
        ok = check_skill(client, name, skill_id)
        results.append((name, ok))

    print("\n" + "─" * 60)
    all_ok = all(ok for _, ok in results)
    for name, ok in results:
        mark = "✓" if ok else "✗"
        print(f"  {mark}  {name}")
    print()

    if all_ok:
        print("All skills are available and correctly parsed.")
        print("The agent will auto-load each skill's description on startup")
        print("(~100 tokens per skill) and read the full SKILL.md on demand.")
    else:
        print("Some skills failed validation. Re-run upload_skills.py to fix.")
        sys.exit(1)


if __name__ == "__main__":
    main()
