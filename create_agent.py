"""
Provision everything this track needs in one shot:
  1. Three custom KB skills (kb-updater, kb-snapshot, kb-browser)
  2. A Managed Agent with the full agent toolset + those skills
  3. A cloud Environment (the container the agent runs in)
  4. A Memory Store that survives across sessions
  5. A bootstrap session that writes KB tooling into /mnt/memory/ and scaffolds
     the 12 register files at /mnt/memory/.registers/

After this script completes the agent's memory store contains:
  /mnt/memory/scaffold-registers.py
  /mnt/memory/kb-register-schema.md
  /mnt/memory/tools/kb-lint.py
  /mnt/memory/tools/kb-browser.py
  /mnt/memory/.registers/  (12 empty register files)

run_session_*.py scripts can then assume the workspace is ready and focus
purely on ingestion and Q&A.

Re-running is idempotent: existing dotfiles are reused, the bootstrap session
is skipped if .bootstrap_done exists.

Usage:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python create_agent.py
"""

import os
from pathlib import Path

from anthropic import Anthropic

# ── KB skill definitions ───────────────────────────────────────────────────────

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

# Files to write into /mnt/memory/ during the bootstrap session
KB_TOOL_FILES = {
    "/mnt/memory/kb-register-schema.md":      KB_DIR / "kb-register-schema.md",
    "/mnt/memory/tools/scaffold-registers.py": KB_DIR / "tools" / "scaffold-registers.py",
    "/mnt/memory/tools/kb-lint.py":            KB_DIR / "tools" / "kb-lint.py",
    "/mnt/memory/tools/kb-browser.py":         KB_DIR / "tools" / "kb-browser.py",
}

SYSTEM_PROMPT = """\
You are the Institutional Memory Agent for a fast-growing company.

Your job: be the smartest possible answer to questions about how this company
works — its policies, its people, its customers, its product. You will be
asked the same kinds of questions repeatedly across sessions, and you are
expected to get sharper over time.

# Knowledge base

Your institutional memory lives in structured registers at `/mnt/memory/.registers/`.
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


def build_bootstrap_message() -> str:
    """
    Build the user message for the one-time workspace bootstrap session.

    Embeds every KB tool file so the agent can write them to /mnt/memory/
    and then scaffolds the 12 register files. The bootstrap session runs once;
    subsequent sessions find everything already in place.
    """
    parts = [
        "=== KB WORKSPACE BOOTSTRAP ===\n",
        (
            "Write each file below to the exact path shown using your write tool. "
            "Create parent directories as needed (e.g. mkdir -p /mnt/memory/tools). "
            "Then scaffold the registers. Confirm each step with a brief status line.\n"
        ),
    ]

    for dest_path, src_path in KB_TOOL_FILES.items():
        content = src_path.read_text()
        parts.append(f"-----  FILE: {dest_path}  -----\n{content}\n-----  END  -----\n")

    parts.append(
        "After writing all files, run:\n"
        "  cd /mnt/memory && python3 tools/scaffold-registers.py --path .registers\n\n"
        "When done, reply with a single line: BOOTSTRAP COMPLETE"
    )

    return "\n".join(parts)


def run_bootstrap_session(
    client: Anthropic,
    agent_id: str,
    environment_id: str,
    memory_store_id: str,
) -> None:
    """Run a one-time session that writes KB tooling and scaffolds .registers/."""
    print("\nBootstrapping KB workspace in memory store...")
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="Bootstrap — write KB tooling + scaffold registers",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "Write the KB tool files and scaffold the register directory "
                    "exactly as instructed. This runs once during setup."
                ),
            }
        ],
    )

    bootstrap_message = build_bootstrap_message()

    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": bootstrap_message}],
                }
            ],
        )
        for event in stream:
            if event.type == "agent.tool_use":
                name   = getattr(event, "name", "?")
                inp    = getattr(event, "input", {}) or {}
                target = inp.get("path") or inp.get("file_path") or inp.get("command") or ""
                print(f"  [{name}]  {str(target)[:80]}", flush=True)
            elif event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        print(f"  agent: {block.text}", flush=True)
            elif event.type == "session.status_idle":
                break

    Path(".bootstrap_done").write_text("1")
    print("Bootstrap complete.")


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    client = Anthropic()

    # 1. KB skills
    print("Uploading KB skills...")
    skill_ids = [upload_skill(client, cfg) for cfg in SKILL_CONFIGS]

    # 2. Agent — created with skills attached from the start
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
    Path(".agent_id").write_text(agent.id)
    print(f"Agent created:        {agent.id}  (version {agent.version}, {len(skill_ids)} skills)")

    # 3. Environment
    environment = client.beta.environments.create(
        name="memory-agent-env",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
        },
    )
    Path(".environment_id").write_text(environment.id)
    print(f"Environment created:  {environment.id}")

    # 4. Memory store
    memory_store = client.beta.memory_stores.create(
        name="Institutional Memory",
        description=(
            "Persistent KB workspace for the Institutional Memory Agent. "
            "Contains KB tooling (tools/, scaffold-registers.py, kb-register-schema.md), "
            "live registers (.registers/), snapshots, and memory.md summary. "
            "Newer register entries supersede older ones on the same singleton key."
        ),
    )
    Path(".memory_store_id").write_text(memory_store.id)
    print(f"Memory store created: {memory_store.id}")

    # 5. Bootstrap — write KB tooling + scaffold .registers/ into the memory store
    if Path(".bootstrap_done").exists():
        print("\nBootstrap already done — skipping.")
    else:
        run_bootstrap_session(
            client,
            agent_id=agent.id,
            environment_id=environment.id,
            memory_store_id=memory_store.id,
        )

    print("\nSetup complete.")
    print(f"  Memory store Console:  https://platform.claude.com/memory-stores/{memory_store.id}")
    print(f"  Inspect memory:        python inspect_memory.py")
    print(f"  Verify skills:         python inspect_skills.py")
    print(f"\nNext:  python run_session_1.py")


if __name__ == "__main__":
    main()
