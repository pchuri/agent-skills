# agent-skills

A collection of portable [Agent Skills](https://agentskills.io) (`SKILL.md`
format) that work across AI coding agents — Claude Code, OpenAI Codex CLI,
and any other tool supporting the open skills standard.

이식 가능한 Agent Skills(`SKILL.md` 표준) 모음입니다. Claude Code, OpenAI
Codex CLI 등 오픈 스킬 표준을 지원하는 모든 AI 코딩 에이전트에서 동작합니다.

## Skills

| Skill | Description |
| --- | --- |
| [android-reverse-tethering](plugins/android-reverse-tethering/skills/android-reverse-tethering/SKILL.md) | Share the PC's internet with an Android phone over USB (reverse tethering via gnirehtet). Setup, start/stop, verification, and troubleshooting. |
| [samsung-messages-adb](plugins/samsung-messages-adb/skills/samsung-messages-adb/SKILL.md) | Read and search text messages on a Samsung Galaxy over adb — SMS, MMS, and RCS (Chat+). Covers the three separate message stores and the timestamp-unit gotchas that make messages "invisible" to naive queries. |

## Install

### Claude Code

```
/plugin marketplace add pchuri/agent-skills
/plugin install android-reverse-tethering@pchuri-skills
/plugin install samsung-messages-adb@pchuri-skills
```

Each plugin is installable independently — pick the ones you need.

### OpenAI Codex CLI

Copy a skill into Codex's user-level skills directory:

```sh
git clone https://github.com/pchuri/agent-skills.git /tmp/agent-skills \
  && mkdir -p ~/.agents/skills \
  && cp -r /tmp/agent-skills/plugins/*/skills/* ~/.agents/skills/
```

Then use them implicitly (just describe the task) or explicitly with
`$android-reverse-tethering` / `$samsung-messages-adb`.

### Other tools / manual

Any agent that supports the Agent Skills standard can use these skills —
copy a skill directory from `plugins/<plugin>/skills/` into your tool's
skills location.

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

## License

MIT
