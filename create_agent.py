"""
Provision everything this track needs in one shot:
  1. Three custom KB skills (kb-updater, kb-snapshot, kb-browser)
  2. A Managed Agent with the full agent toolset + those skills
  3. A cloud Environment (the container the agent runs in)
  4. A Memory Store that survives across sessions
  5. Direct API seeding of KB tooling + 12 register files into the store

The memory store "Institutional Memory" mounts at:
  /mnt/memory/Institutional Memory/

After this script completes the agent's memory store contains:
  /kb-register-schema.md
  /tools/scaffold-registers.py
  /tools/kb-lint.py
  /tools/kb-browser.py
  /.registers/  (12 empty register files)

Agents see these under /mnt/memory/Institutional Memory/<path>.

Re-running is idempotent: existing dotfiles are reused, seeding is skipped
if .bootstrap_done exists.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python create_agent.py
"""

import os
import subprocess
import tempfile
from pathlib import Path

from anthropic import Anthropic, APIStatusError

# ── constants ─────────────────────────────────────────────────────────────────

MEMORY_STORE_NAME = "Institutional Memory"
# FUSE mount path in session containers: /mnt/memory/<store-name>/
MEMORY_MOUNT_PATH = f"/mnt/memory/{MEMORY_STORE_NAME}"

SKILLS_DIR = Path("onboarding-kb-registers/skills")
KB_DIR     = Path("onboarding-kb-registers")

SKILL_CONFIGS = [
    {
        "name": "kb-browser",
        "display_title": "EPAM KB Register Browser",
        "id_file": ".skill_kb_browser_id",
    },
    {
        "name": "kb-snapshot",
        "display_title": "EPAM KB Register Snapshot",
        "id_file": ".skill_kb_snapshot_id",
    },
    {
        "name": "kb-updater",
        "display_title": "EPAM KB Register Updater",
        "id_file": ".skill_kb_updater_id",
    },
]

# Store-relative paths for KB tool files (seeded via API, not via agent session)
KB_TOOL_FILES = {
    "/kb-register-schema.md":       KB_DIR / "kb-register-schema.md",
    "/tools/scaffold-registers.py": KB_DIR / "tools" / "scaffold-registers.py",
    "/tools/kb-lint.py":            KB_DIR / "tools" / "kb-lint.py",
    "/tools/kb-browser.py":         KB_DIR / "tools" / "kb-browser.py",
}

SYSTEM_PROMPT = """\
You are the Institutional Memory Agent for a fast-growing company.

Your job: be the smartest possible answer to questions about how this company
works — its policies, its people, its customers, its product. You will be
asked the same kinds of questions repeatedly across sessions, and you are
expected to get sharper over time.

# Knowledge base

Your institutional memory lives in structured registers at `/mnt/memory/Institutional Memory/.registers/`.
These registers survive across sessions and hold the single source of truth for
policies, role assignments, service ownership, and more.

**Reading the KB** — use the `kb-snapshot` skill to get a digest of current truth
across all registers at the start of any session where you need context.

**Writing to the KB** — use the `kb-updater` skill whenever you receive a source
document (policy, org announcement, handbook revision, incident postmortem). The
skill handles classification, the supersede algorithm for singleton registers
(so stale entries are retired correctly), cross-reference propagation, and linting.
Never write directly to `.registers/` with file tools — all writes go through
`kb-updater`.

# How to answer

- Derive answers from the registers, not from raw document text in the conversation.
- When new information contradicts what the registers say, run `kb-updater` first,
  then answer from the updated state. Lead with what changed.
- Be concise.
"""


def upload_skill(client: Anthropic, cfg: dict) -> str:
    """Upload a KB skill from SKILLS_DIR, or reuse its ID if already uploaded."""
    id_path = Path(cfg["id_file"])
    if id_path.exists():
        skill_id = id_path.read_text().strip()
        print(f"  {cfg['name']}: reusing {skill_id}")
        return skill_id

    skill_name = cfg["name"]
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    with open(skill_md, "rb") as f:
        skill = client.beta.skills.create(
            files=[(f"{skill_name}/SKILL.md", f)],
            display_title=cfg["display_title"],
        )
    id_path.write_text(skill.id)
    print(f"  {cfg['name']}: created {skill.id}  (version {skill.latest_version})")
    return skill.id


def _create_memory(client: Anthropic, store_id: str, path: str, content: str) -> None:
    """Create a memory entry, skipping silently if the path already exists."""
    try:
        client.beta.memory_stores.memories.create(store_id, path=path, content=content)
        print(f"  created  {path}")
    except APIStatusError as e:
        if e.status_code == 409:
            print(f"  exists   {path}")
        else:
            raise


def seed_memory_store(client: Anthropic, memory_store_id: str) -> None:
    """Seed KB tooling and scaffold registers directly into the memory store via the API.

    Files land at store-relative paths (e.g. /kb-register-schema.md).  The FUSE
    mount makes them visible inside sessions at MEMORY_MOUNT_PATH/<path>.
    """
    print("\nSeeding KB workspace into memory store...")

    for store_path, local_path in KB_TOOL_FILES.items():
        _create_memory(client, memory_store_id, store_path, local_path.read_text())

    # Run scaffold-registers.py locally into a temp dir, then upload each file.
    scaffold_script = KB_DIR / "tools" / "scaffold-registers.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        registers_dir = Path(tmpdir) / ".registers"
        subprocess.run(
            ["python3", str(scaffold_script), "--path", str(registers_dir)],
            check=True,
            capture_output=True,
        )
        for reg_file in sorted(registers_dir.iterdir()):
            _create_memory(
                client,
                memory_store_id,
                f"/.registers/{reg_file.name}",
                reg_file.read_text(),
            )

    Path(".bootstrap_done").write_text("1")
    print("Seed complete.")


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    client = Anthropic()

    # 1. KB skills
    print("Uploading KB skills...")
    skill_ids = [upload_skill(client, cfg) for cfg in SKILL_CONFIGS]

    # 2. Agent — created with skills attached from the start
    agent_id_path = Path(".agent_id")
    if agent_id_path.exists():
        agent_id = agent_id_path.read_text().strip()
        print(f"\nAgent:                reusing {agent_id}")
    else:
        print("\nCreating agent...")
        agent = client.beta.agents.create(
            name="EPAM Institutional Memory Agent",
            model="claude-sonnet-4-6",
            system=SYSTEM_PROMPT,
            tools=[{"type": "agent_toolset_20260401"}],
            skills=[
                {"type": "custom", "skill_id": sid, "version": "latest"}
                for sid in skill_ids
            ],
            metadata={
                "hackathon": "partner-basecamp-2026",
                "track": "memory-agent",
                "partner": "EPAM Systems, Inc.",
            },
        )
        agent_id = agent.id
        agent_id_path.write_text(agent_id)
        print(f"Agent created:        {agent_id}  (version {agent.version}, {len(skill_ids)} skills)")

    # 3. Environment
    env_id_path = Path(".environment_id")
    if env_id_path.exists():
        environment_id = env_id_path.read_text().strip()
        print(f"Environment:          reusing {environment_id}")
    else:
        environment = client.beta.environments.create(
            name="memory-agent-env",
            config={
                "type": "cloud",
                "networking": {"type": "unrestricted"},
            },
        )
        environment_id = environment.id
        env_id_path.write_text(environment_id)
        print(f"Environment created:  {environment_id}")

    # 4. Memory store
    store_id_path = Path(".memory_store_id")
    if store_id_path.exists():
        memory_store_id = store_id_path.read_text().strip()
        print(f"Memory store:         reusing {memory_store_id}")
    else:
        memory_store = client.beta.memory_stores.create(
            name=MEMORY_STORE_NAME,
            description=(
                "Persistent KB workspace for the Institutional Memory Agent. "
                "Contains KB tooling (tools/, scaffold-registers.py, kb-register-schema.md), "
                "live registers (.registers/), snapshots, and memory.md summary. "
                "Newer register entries supersede older ones on the same singleton key."
            ),
        )
        memory_store_id = memory_store.id
        store_id_path.write_text(memory_store_id)
        print(f"Memory store created: {memory_store_id}")

    # 5. Seed KB tooling + .registers/ directly into the memory store via the API
    if Path(".bootstrap_done").exists():
        print("\nSeed already done — skipping.")
    else:
        seed_memory_store(client, memory_store_id=memory_store_id)

    print("\nSetup complete.")
    print(f"  Memory store Console:  https://platform.claude.com/memory-stores/{memory_store_id}")
    print(f"  Inspect memory:        python inspect_memory.py")
    print(f"  Verify skills:         python inspect_skills.py")
    print(f"\nNext:  python run_session_1.py")


if __name__ == "__main__":
    main()
