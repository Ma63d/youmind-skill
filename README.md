<div align="center">

# Youmind Claude/Codex Skill

Use CLI agents to chat directly with [Youmind](https://youmind.com/) boards through browser automation.

</div>

---

## What This Is

This repository provides a local skill that:
- Authenticates once with Youmind (`auth_manager.py`)
- Stores board links and metadata (`board_manager.py`)
- Sends questions to board chat and returns answers (`ask_question.py`)
- Manages environment and cleanup (`run.py`, `cleanup_manager.py`)

It follows the same architecture pattern as the original NotebookLM skill, but targets Youmind boards.

## Quick Start

```bash
# 1) Authenticate
python scripts/run.py auth_manager.py setup

# 2) Add a board
python scripts/run.py board_manager.py add \
  --url "https://youmind.com/boards/..." \
  --name "My Board" \
  --description "What this board contains" \
  --topics "product,docs"

# Or Smart Add (auto metadata)
python scripts/run.py board_manager.py smart-add \
  --url "https://youmind.com/boards/..."

# Use one-pass mode if needed
python scripts/run.py board_manager.py smart-add \
  --url "https://youmind.com/boards/..." \
  --single-pass

# 3) Ask a question
python scripts/run.py ask_question.py --question "Summarize key decisions"
```

## Script Commands

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
python scripts/run.py board_manager.py smart-add --url URL --single-pass
python scripts/run.py board_manager.py search --query "keyword"
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

## Architecture

```text
scripts/
├── run.py               # Universal runner (ensures .venv)
├── setup_environment.py # Creates/updates .venv and dependencies
├── auth_manager.py      # Youmind login state management
├── board_manager.py     # Local board library CRUD
├── ask_question.py      # Stateless board chat query
├── browser_utils.py     # Browser factory + stealth helpers
├── browser_session.py   # Optional stateful session abstraction
└── cleanup_manager.py   # Data cleanup tool
```

## Data Directory

```text
data/
├── library.json
├── auth_info.json
└── browser_state/
    └── state.json
```

Do not commit `data/`.

## Notes

- Browser automation relies on UI selectors and may need updates when Youmind UI changes.
- Use `--show-browser` when debugging selector or auth issues.
- Each question is stateless; ask explicit follow-up questions for missing details.
