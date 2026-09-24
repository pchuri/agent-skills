---
name: muse-usage
description: Check Meta Muse Code CLI token/subscription usage and rate limit status via interactive TUI. Use when the user asks to check muse usage, limits, or quota.
---

# Meta Muse Code Usage Checker

This skill automates inspecting token and subscription usage limits for the Meta Muse Code CLI (`muse`).

## Background

The `muse` CLI provides a `/usage` slash command that displays current session token counts, subagent status, and subscription tier usage (rolling period & weekly limits). However, because `muse` runs as an interactive full-screen terminal (TUI) without a headless `/usage` flag, a pseudo-terminal (PTY) runner is used to launch the session, send `/usage`, and parse the output box.

## Requirements

- `muse` CLI installed and available on `PATH` (typically installed at `~/.local/bin/muse`).
- Python 3 with standard library modules (`pty`, `termios`, `fcntl`, `select`).

## Execution

Run the bundled script relative to the skill directory or using Python:

```bash
python3 "<path-to-skill>/scripts/check_usage.py"
```

If installed in `~/.agents/skills/muse-usage`:

```bash
python3 ~/.agents/skills/muse-usage/scripts/check_usage.py
```

### Sample Output

```text
┌───────────────────────────────────────────────────────┐
│  Session usage                                        │
│                                                       │
│    Input      0                                       │
│    Cached     0                                       │
│    Output     0                                       │
│    Total      0                                       │
│                                                       │
│    Turns         0                                    │
│    Subagents  none                                    │
│                                                       │
│  Subscription · Muse Code Power Usage                 │
│    Current        2% used · Resets at 2:41 AM         │
│    Weekly         40% used · Resets Sep 28 at 9:00 AM │
│    as of 10:08 PM                                     │
└───────────────────────────────────────────────────────┘
```

## Reporting Guidelines

When reporting usage to the user:
1. Render the parsed usage box directly in markdown code blocks.
2. Clearly summarize:
   - **Subscription Plan** (e.g., Muse Code Power Usage)
   - **Current Rolling Window Usage** (% used and reset timestamp)
   - **Weekly Usage** (% used and reset timestamp)
3. If requested, project whether the remaining weekly quota is sufficient based on elapsed time and current consumption rate.
