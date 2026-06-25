"""
List every file in the agent's memory store and show the first 20 lines of each.

Runs a short session that executes a single bash pipeline and streams the raw
tool output — the agent is not asked to interpret or summarise anything.

Usage:
    python inspect_memory.py
"""

import os
from pathlib import Path

from anthropic import Anthropic

# One pipeline: list every file (including hidden dirs like .registers/),
# then head each one.  The agent is told to run this exact command and nothing
# else, so it cannot silently summarise the output.
DISCOVER_COMMAND = r"""
echo "=== /mnt/ ===" && ls -la /mnt/ 2>&1
echo "=== /mnt/memory/ ===" && ls -la "/mnt/memory/" 2>&1
"""

BASH_COMMAND = r"""find /mnt/memory -mindepth 1 -type f | sort | while IFS= read -r f; do
  printf '\n======  %s  ======\n' "$f"
  head -20 "$f"
done"""

INSPECT_MESSAGE = (
    f"Run each bash command below in sequence. Reply with the raw stdout only — "
    f"no commentary, no formatting, no markdown.\n\n"
    f"Command 1 (discover mount layout):\n```\n{DISCOVER_COMMAND}\n```\n\n"
    f"Command 2 (dump all files):\n```\n{BASH_COMMAND}\n```"
)


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

    print(f"Memory store: {memory_store_id}")
    print("=" * 60)

    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="inspect /mnt/memory/",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": "Read-only inspection of /mnt/memory/.",
            }
        ],
    )

    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": INSPECT_MESSAGE}],
                }
            ],
        )
        for event in stream:
            if event.type == "session.status_idle":
                break
            # Capture every text block from every event type — tool results,
            # agent messages, etc. — so nothing the agent sees is filtered out.
            for block in getattr(event, "content", None) or []:
                btype = getattr(block, "type", None)
                if btype == "text":
                    text = getattr(block, "text", "")
                    if text.strip():
                        print(text)
                elif btype == "tool_result":
                    # Tool result blocks carry bash stdout directly
                    for inner in getattr(block, "content", None) or []:
                        if getattr(inner, "type", None) == "text":
                            print(getattr(inner, "text", ""))


if __name__ == "__main__":
    main()
