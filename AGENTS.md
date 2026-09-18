# agent-skills — Agent Guidelines

## Repository Overview

This is a **public open-source repository** containing portable [Agent Skills](https://agentskills.io) (`SKILL.md` format) and Claude Code plugin definitions that work across AI coding agents (Claude Code, OpenAI Codex CLI, etc.).

## Language & Documentation Rules

- **English Only**: Because this repository is public, all documentation, `SKILL.md` files, plugin manifests (`plugin.json`, `marketplace.json`), commit messages, and pull request descriptions **must be written in English**.
  - Domain-specific terms in other languages (such as Korean search keywords, app UI labels, or service-specific identifiers) are permitted only when necessary as technical examples (e.g., KakaoTalk, Samsung 채팅+).
- **Style**: Clear, concise, and technical instructions suitable for AI agents and human contributors.

## Privacy & Cleanliness Guardrails

- **No Local Paths**: Never hardcode user-specific local file paths (e.g., `/Users/<username>/...`). Always use generic environment variables or `$HOME` expansions (e.g., `${WHISPER_MODEL_PATH:-$HOME/models/...}`).
- **No Personal Data**: Never commit personal context, private notes, credentials, API keys, phone numbers, or account identifiers.
- **Temporary Files**: Skills that process user data (such as call recordings or database extracts) must operate in temporary locations (`/tmp`) and must never commit media files or raw transcripts to git.

## Git & Contribution Workflow

- **Branching & PRs**: Avoid pushing directly to `main`. Create a feature or fix branch (e.g., `feat/...`, `docs/...`, `fix/...`) and submit a GitHub Pull Request via `gh pr create`.
- **Commit Messages**: Follow Conventional Commits in English (e.g., `docs: translate skill to English`, `feat: add new skill`).
- **Commits**: Ensure author email and name match the repository config (`pchuri <pchuri@gmail.com>`).
