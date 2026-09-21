# agent-skills

A collection of portable [Agent Skills](https://agentskills.io) (`SKILL.md`
format) that work across AI coding agents — Claude Code, OpenAI Codex CLI,
and any other tool supporting the open skills standard.


## Skills

| Skill | Description |
| --- | --- |
| [android-reverse-tethering](plugins/android-reverse-tethering/skills/android-reverse-tethering/SKILL.md) | Share the PC's internet with an Android phone over USB (reverse tethering via gnirehtet). Setup, start/stop, verification, and troubleshooting. |
| [samsung-messages-adb](plugins/samsung-messages-adb/skills/samsung-messages-adb/SKILL.md) | Read and search text messages on a Samsung Galaxy over adb — SMS, MMS, and RCS (Chat+). Covers the three separate message stores and the timestamp-unit gotchas that make messages "invisible" to naive queries. |
| [watchtell](https://github.com/pchuri/watchtell/blob/main/skills/watchtell/SKILL.md) | Hand off long-lived watching to a local daemon — "tell me when this CI goes red", "notify me when this repo publishes a release". Compiles the request into a deterministic bash checker once, then polls LLM-free and alerts only on state transitions. Lives in [its own repo](https://github.com/pchuri/watchtell) alongside the CLI it drives. |
| [samsung-call-transcribe](plugins/samsung-call-transcribe/skills/samsung-call-transcribe/SKILL.md) | Pull Samsung Galaxy call recordings over adb and transcribe with local Whisper (ggml-large-v3-turbo) via ffmpeg and whisper-cli. Outputs both plain text and timestamped SRT subtitles. |
| [kakaotalk-mac](plugins/kakaotalk-mac/skills/kakaotalk-mac/SKILL.md) | macOS KakaoTalk local SQLite DB query (messages, chatrooms, photos) and confirmed sending via `kakaocli`. |
| [smartthings](plugins/smartthings/skills/smartthings/SKILL.md) | Query and control Samsung SmartThings devices (lights, plugs, AC, appliances, sensors) via the official CLI or REST API with persistent OAuth sessions. |

## Install

### Claude Code

```
/plugin marketplace add pchuri/agent-skills
/plugin install android-reverse-tethering@pchuri-skills
/plugin install samsung-messages-adb@pchuri-skills
/plugin install samsung-call-transcribe@pchuri-skills
/plugin install kakaotalk-mac@pchuri-skills
/plugin install smartthings@pchuri-skills
/plugin install watchtell@pchuri-skills
```

Each plugin is installable independently — pick the ones you need.

`watchtell` is sourced from its own repo rather than vendored here, so its
`SKILL.md` stays in lockstep with the CLI command surface it documents. It
also needs that CLI on your `PATH`:

```sh
npm install -g watchtell
```

If you already ran `watchtell skill install`, the skill is symlinked into
`~/.claude/skills` — skip the plugin, or you will have it registered twice.

### OpenAI Codex CLI

Copy a skill into Codex's user-level skills directory:

```sh
git clone https://github.com/pchuri/agent-skills.git /tmp/agent-skills \
  && mkdir -p ~/.agents/skills \
  && cp -r /tmp/agent-skills/plugins/*/skills/* ~/.agents/skills/
```

Then use them implicitly (just describe the task) or explicitly with
`$android-reverse-tethering` / `$samsung-messages-adb` / `$watchtell`.

The copy above skips `watchtell`, which is not vendored here — install that
one from its own CLI instead:

```sh
npm install -g watchtell && watchtell skill install --codex
```

Note this lands in `~/.codex/skills/watchtell` rather than the
`~/.agents/skills/` used above. Codex reads both.

### Other tools / manual

Any agent that supports the Agent Skills standard can use these skills —
copy a skill directory from `plugins/<plugin>/skills/` into your tool's
skills location. There is no `plugins/watchtell/`; that skill lives
upstream, so take it from a `watchtell` checkout (`skills/watchtell/`) or
let `watchtell skill install` place it for you.

## Usage examples

> "Set up reverse tethering so my Android phone uses this computer's internet over USB."

The agent checks `adb`, installs `gnirehtet` if needed, starts the relay,
verifies the connection from the relay log, and tells you when the phone is
online — including the one-time VPN approval popup on first use.

> "Turn reverse tethering off."

The agent stops the relay **and** brings down the VPN on the phone (skipping
the second step is the classic mistake that leaves the phone without
internet).

> "Find the text message with the academy's payment info on my phone."

The agent searches all three Samsung message stores (SMS, MMS parts, RCS) —
not just `content://sms`, where long business messages never appear because
they are delivered as MMS with the body stored in `content://mms/part`.

> "Let me know when the GitHub Actions run on main starts failing."

The agent hands the watch off to the watchtell daemon: the request is
compiled into a bash checker once, the daemon keeps polling it after your
session ends, and you get notified on the ok→failing transition — not on
every poll.

> "Turn off the bed light and set the living room AC to 24°C."

The agent queries device IDs by label using the SmartThings REST API, checks
their current status, and dispatches capability commands (`switch: off`,
`thermostatCoolingSetpoint: 24.0`).

## License

MIT
