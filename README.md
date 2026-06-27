# 🤖 Self-Learning AI Agent

> An autonomous agent that learns, codes, and evolves — cycle by cycle.

---

## 📊 Agent Status

| Property | Value |
|----------|-------|
| 🔢 Cycle | 0 |
| ⭐ Level | 1 |
| ✨ XP | 0 |
| 📅 Last Run | Not started yet |
| 🧠 Total Tasks | 0 completed |

---

## 🚀 Getting Started

### 1. Fork this repository

### 2. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `GROQ_API_KEY` | Your Groq API key from [console.groq.com](https://console.groq.com) |
| `GH_TOKEN` | GitHub Personal Access Token (with `repo` scope) |
| `KAGGLE_USERNAME` | Your Kaggle username |
| `KAGGLE_KEY` | Your Kaggle API key |

### 3. Enable GitHub Actions

Go to the **Actions** tab and enable workflows.

### 4. Trigger First Run

Click **Actions → Self-Learning Agent → Run workflow**

---

## 🧩 Skills

*Agent hasn't run yet — skills will appear after the first cycle.*

---

## ⚙️ Architecture

```
self-learning-agent/
├── .github/workflows/
│   └── agent.yml          # Scheduled runner (every 6h)
├── agent/
│   ├── brain.py           # Core intelligence (self-modifiable ⚡)
│   └── prompts.py         # Prompt library (self-modifiable ⚡)
├── memory/
│   └── state.json         # Persistent memory & skill levels
├── tasks/
│   └── task_XXXX_*.py     # Generated & executed solutions
└── history/
    └── cycle_XXXX.json    # Full cycle logs
```

### How it works

```
Every 6 hours:
  1. Load memory (skills, XP, history)
  2. Generate a task (LLM picks difficulty based on current level)
  3. Write & execute Python code to solve it
  4. Reflect: update skills, extract insights
  5. Self-improve: rewrite own agent files if needed
  6. Commit everything back to the repo
  7. Sleep until next cycle
```

---

*This README will be auto-updated by the agent each cycle.*
