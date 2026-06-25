"""
Session 1 — ingest round 1 baseline documents into the KB registers.

Assumes create_agent.py has already bootstrapped /mnt/memory/ with KB tooling
and an empty .registers/ directory.

The agent uses the kb-updater skill to classify each document and write
structured entries into /mnt/memory/.registers/.

Usage:
    python run_session_1.py
"""

import os
from pathlib import Path

from anthropic import Anthropic

DOCS_DIR      = Path("synthetic-data/round1")
SESSION_TITLE = "Session 1 — KB ingestion: round 1 baseline"

INGEST_PREAMBLE = (
    "Below are the company's baseline onboarding documents (round 1). "
    "Please ingest each one into the KB registers at /mnt/memory/.registers/ "
    "using the kb-updater skill. Work from /mnt/memory/ as your base directory."
)


def load_docs(docs_dir: Path) -> str:
    blocks = []
    for path in sorted(docs_dir.glob("*.md")):
        print(f"  including {path.name}")
        blocks.append(f"=====  DOCUMENT: {path.name}  =====\n{path.read_text()}")
    return "\n\n".join(blocks)


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    for required in (".agent_id", ".environment_id", ".memory_store_id"):
        if not Path(required).exists():
            raise SystemExit(f"Missing {required} — run create_agent.py first.")

    agent_id        = Path(".agent_id").read_text().strip()
    environment_id  = Path(".environment_id").read_text().strip()
    memory_store_id = Path(".memory_store_id").read_text().strip()

    client = Anthropic()

    print(f"Loading docs from {DOCS_DIR}/...")
    context = load_docs(DOCS_DIR)

    print(f"\nStarting session with memory store {memory_store_id}...")
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title=SESSION_TITLE,
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "Persistent KB workspace at /mnt/memory/. Contains KB tooling "
                    "(tools/, scaffold-registers.py, kb-register-schema.md) and live "
                    "registers at .registers/. Tools are under tools/. Always check this at session start."
                ),
            }
        ],
    )

    user_message = f"{INGEST_PREAMBLE}\n\n{context}"

    print("\nAgent working...\n")
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": user_message}],
                }
            ],
        )
        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if getattr(block, "type", None) == "text":
                        print(block.text, end="", flush=True)
            elif event.type == "agent.tool_use":
                name   = getattr(event, "name", "?")
                inp    = getattr(event, "input", {}) or {}
                target = inp.get("path") or inp.get("file_path") or inp.get("command") or ""
                if "/mnt/memory" in str(target):
                    print(f"\n  [memory: {name}  {target}]", flush=True)
                else:
                    print(f"\n  [{name}]", flush=True)
            elif event.type == "session.status_idle":
                print("\n\n[agent finished]")
                break

    print(f"Inspect registers:  python inspect_memory.py")
    print(f"Next:               python run_session_2.py")


if __name__ == "__main__":
    main()
