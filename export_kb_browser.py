"""
Generate the KB browser HTML in the cloud and download it locally.

The agent generates the HTML during a session. When the FUSE mount at
/mnt/memory/ rejects writes over 100 KiB, the agent falls back to /tmp/ and
the file is automatically captured as a session output. After the session,
files.list(scope_id=session_id) finds it and files.download() pulls it down.

Usage:
    python export_kb_browser.py
"""

import os
import subprocess
from pathlib import Path

from anthropic import Anthropic  # type: ignore[import]

GENERATE_MESSAGE = """\
Work from the directory that contains .registers/:

  KB_ROOT=$(find /mnt/memory -name ".registers" -maxdepth 3 -type d | head -1 | xargs dirname)
  cd "$KB_ROOT"

Run the kb-browser skill to validate cross-references and generate the HTML
browser. The skill writes the file to /tmp/ — make sure it is captured as a
session output.

When done, print the filename on a line by itself prefixed with GENERATED:
"""

BETAS = ["managed-agents-2026-04-01"]


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

    print("Step 1: generating KB browser HTML in the cloud...\n" + "=" * 60)

    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="generate kb-browser HTML",
        resources=[
            {
                "type": "memory_store",
                "memory_store_id": memory_store_id,
                "access": "read_write",
                "instructions": (
                    "Persistent KB workspace at /mnt/memory/. "
                    "Contains KB tooling (tools/, scaffold-registers.py, "
                    "kb-register-schema.md) and live registers at .registers/."
                ),
            }
        ],
        betas=BETAS,
    )

    session_id = session.id
    print(f"Session: {session_id}\n")

    with client.beta.sessions.events.stream(session_id) as stream:
        client.beta.sessions.events.send(
            session_id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": GENERATE_MESSAGE}],
                }
            ],
        )
        for event in stream:
            if event.type == "session.status_idle":
                break
            for block in getattr(event, "content", None) or []:
                if getattr(block, "type", None) == "text":
                    text = getattr(block, "text", "")
                    if text.strip():
                        print(text, flush=True)

    print("\nStep 2: listing session output files...\n" + "=" * 60)

    files = client.beta.files.list(
        scope_id=session_id,
        betas=BETAS,
    )

    html_files = [f for f in files.data if f.filename.endswith(".html")]
    if not html_files:
        print("No HTML files found in session outputs.")
        print(f"Check: https://platform.claude.com/sessions/{session_id}")
        return

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    for f in html_files:
        out_path = output_dir / f.filename
        print(f"Downloading {f.filename} ({f.id})...")
        content = client.beta.files.download(f.id)
        content.write_to_file(str(out_path))
        print(f"Saved to {out_path.resolve()}")

        result = subprocess.run(["open", str(out_path)], capture_output=True)
        if result.returncode == 0:
            print("Opened in browser.")
        else:
            print(f"Open manually: {out_path.resolve()}")


if __name__ == "__main__":
    main()
