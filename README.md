<div align="center">

# Youmind Claude/Codex Skill

**Let Claude Code / Codex chat directly with Youmind boards from your terminal**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Skill](https://img.shields.io/badge/CLI-Skill-green.svg)](https://github.com/anthropics/claude-code)
[![GitHub](https://img.shields.io/badge/Repo-youmind--skill-black.svg)](https://github.com/p697/youmind-skill)

[Installation](#installation) • [Quick Start](#quick-start) • [How It Works](#how-it-works) • [Commands](#common-commands) • [Limitations](#limitations)

</div>

---

## Important: Local CLI Only

This skill is designed for local CLI agents (Claude Code / Codex). It relies on browser automation and persistent local auth state.

---

## The Problem

When your project knowledge is inside Youmind boards, normal agent workflows are inefficient:

- You keep switching between terminal and browser.
- Context gets lost between manual copy-paste steps.
- Metadata about which board to query is often inconsistent.
- Repetitive setup/auth friction slows daily usage.

## The Solution

This repository provides a local skill that automates the full loop:

```text
Your task -> agent runs skill -> skill asks Youmind board chat -> answer returns to terminal
```

The skill includes:

- `auth_manager.py`: persistent Youmind login setup/validation
- `board_manager.py`: local board library and Smart Add
- `ask_question.py`: stateless board chat querying
- `run.py`: environment bootstrap + unified script entry

---

## Why This Skill

Compared with ad-hoc browser/manual workflows:

- Lower friction: one command path for auth, add, and query.
- Better consistency: board metadata is normalized in local library.
- Reusable workflow: Smart Add can auto-discover board metadata.
- Safer operations: all data and browser state stay local in `data/`.

---

## Installation

```bash
# 1) Clone
cd ~/.claude/skills
git clone https://github.com/p697/youmind-skill.git

# 2) Enter the skill directory
cd youmind-skill
```

First run auto-creates `.venv`, installs dependencies, and installs Chrome for Patchright.

---

## Quick Start

### 1) Authenticate once

```bash
python scripts/run.py auth_manager.py setup
```

A browser opens. Complete Youmind login manually.

### 2) Add your board

Manual add:

```bash
python scripts/run.py board_manager.py add \
  --url "https://youmind.com/boards/..." \
  --name "My Board" \
  --description "What this board contains" \
  --topics "product,docs,research"
```

One-command Smart Add:

```bash
python scripts/run.py board_manager.py smart-add \
  --url "https://youmind.com/boards/..."
```

### 3) Ask questions

```bash
python scripts/run.py ask_question.py --question "Summarize key decisions"
```

---

## Smart Add Modes

`smart-add` supports two discovery modes:

1. Default two-pass (recommended):
- Pass 1: summary discovery
- Pass 2: structured JSON discovery
- If Pass 2 fails, it falls back to Pass 1 parsing

2. Single-pass structured mode:

```bash
python scripts/run.py board_manager.py smart-add \
  --url "https://youmind.com/boards/..." \
  --single-pass
```

Useful options:

```bash
--show-browser
--prompt "custom summary prompt"
--json-prompt "custom structured prompt"
--allow-duplicate-url
--no-activate
```

---

## How It Works

```text
scripts/
├── run.py                # Entry point, ensures .venv
├── setup_environment.py  # Installs dependencies and browser runtime
├── auth_manager.py       # Login setup/status/validate/reauth/clear
├── board_manager.py      # Board library + smart-add workflow
├── ask_question.py       # Ask board chat (stateless per query)
├── browser_utils.py      # Browser factory + interaction helpers
├── browser_session.py    # Optional session abstraction
└── cleanup_manager.py    # Local data cleanup
```

Data layout:

```text
data/
├── library.json
├── auth_info.json
└── browser_state/
    └── state.json
```

---

## Core Features

- Persistent local authentication for Youmind.
- Board library management with active board selection.
- Query by `--board-url`, `--board-id`, or active board fallback.
- Smart Add metadata discovery and normalization.
- Follow-up reminder appended to every answer.
- Cleanup workflow for browser/auth/library state.

---

## Common Commands

### Authentication

```bash
python scripts/run.py auth_manager.py status
python scripts/run.py auth_manager.py validate
python scripts/run.py auth_manager.py setup
python scripts/run.py auth_manager.py reauth
python scripts/run.py auth_manager.py clear
```

### Board Library

```bash
python scripts/run.py board_manager.py list
python scripts/run.py board_manager.py add --url URL --name NAME --description DESC --topics TOPICS
python scripts/run.py board_manager.py smart-add --url URL
python scripts/run.py board_manager.py search --query QUERY
python scripts/run.py board_manager.py activate --id BOARD_ID
python scripts/run.py board_manager.py remove --id BOARD_ID
python scripts/run.py board_manager.py stats
```

### Ask Youmind

```bash
python scripts/run.py ask_question.py --question "Your question"
python scripts/run.py ask_question.py --question "..." --board-id BOARD_ID
python scripts/run.py ask_question.py --question "..." --board-url "https://youmind.com/boards/..."
python scripts/run.py ask_question.py --question "..." --show-browser
```

### Cleanup

```bash
python scripts/run.py cleanup_manager.py
python scripts/run.py cleanup_manager.py --confirm
python scripts/run.py cleanup_manager.py --confirm --preserve-library
```

---

## Limitations

- This is browser automation, not an official Youmind API integration.
- Frontend selector changes may require updates in `scripts/config.py`.
- Query sessions are stateless (each ask opens a fresh browser session).
- Smart Add output quality depends on board chat response behavior.

---

## Troubleshooting

- If auth fails: run `python scripts/run.py auth_manager.py reauth`
- If query fails: rerun with `--show-browser` and inspect UI state
- If board lookup fails: run `python scripts/run.py board_manager.py list`
- If environment issues occur: remove `.venv` and rerun via `scripts/run.py`

More details: `references/troubleshooting.md`

---

## License

MIT (see `LICENSE`).
