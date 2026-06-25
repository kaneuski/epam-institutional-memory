"""
Push local changes for kb-browser to the cloud:
  1. Publish a new skill version from onboarding-kb-registers/skills/kb-browser/SKILL.md
  2. Update /tools/kb-browser.py in the memory store

Usage:
    python upload_updates.py
"""

import os
from pathlib import Path

from anthropic import Anthropic

SKILL_ID_FILE   = ".skill_kb_browser_id"
SKILL_MD        = Path("onboarding-kb-registers/skills/kb-browser/SKILL.md")
KB_BROWSER_PY   = Path("onboarding-kb-registers/tools/kb-browser.py")
MEMORY_PATH     = "/tools/kb-browser.py"


BETAS = ["managed-agents-2026-04-01"]


def update_skill(client: Anthropic, skill_id: str) -> None:
    with open(SKILL_MD, "rb") as f:
        result = client.beta.skills.versions.create(
            skill_id,
            files=[("kb-browser/SKILL.md", f)],
            betas=BETAS,
        )
    print(f"Skill new version: {result.version}  (skill {skill_id})")


def update_memory(client: Anthropic, memory_store_id: str) -> None:
    memories = client.beta.memory_stores.memories.list(
        memory_store_id,
        path_prefix=MEMORY_PATH,
        betas=BETAS,
    )
    match = next((m for m in memories if m.path == MEMORY_PATH), None)
    content = KB_BROWSER_PY.read_text()

    if match is None:
        client.beta.memory_stores.memories.create(
            memory_store_id,
            path=MEMORY_PATH,
            content=content,
            betas=BETAS,
        )
        print(f"Memory created:    {MEMORY_PATH}")
    else:
        client.beta.memory_stores.memories.update(
            match.id,
            memory_store_id=memory_store_id,
            content=content,
            betas=BETAS,
        )
        print(f"Memory updated:    {MEMORY_PATH}  (id {match.id})")


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (SKILL_ID_FILE, ".memory_store_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required} — run create_agent.py first.")

    skill_id        = Path(SKILL_ID_FILE).read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    client = Anthropic()

    print(f"Uploading kb-browser updates...")
    update_skill(client, skill_id)
    update_memory(client, memory_store_id)
    print("Done.")


if __name__ == "__main__":
    main()
