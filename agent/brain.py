"""
🧠 Self-Learning Agent Brain
The core intelligence that thinks, learns, and evolves
"""

import os
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import requests

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
GITHUB_TOKEN   = os.environ.get("GH_TOKEN", "")
KAGGLE_USERNAME= os.environ.get("KAGGLE_USERNAME", "")
KAGGLE_KEY     = os.environ.get("KAGGLE_KEY", "")
REPO           = os.environ.get("GITHUB_REPOSITORY", "")
MODEL          = "llama-3.3-70b-versatile"   # Groq model
MEMORY_FILE    = Path("memory/state.json")
HISTORY_DIR    = Path("history")
TASKS_DIR      = Path("tasks")

# ── Groq LLM Call ─────────────────────────────────────────────────────────────
def call_llm(messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
    """Call Groq API and return text response."""
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY secret is not set!")
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"⚠️  LLM attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(5)
    raise RuntimeError("LLM call failed after 3 attempts")

# ── Memory System ─────────────────────────────────────────────────────────────
def load_memory() -> dict:
    """Load agent's persistent memory / state."""
    MEMORY_FILE.parent.mkdir(exist_ok=True)
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text())
    
    # Initial state for a brand-new agent
    return {
        "cycle": 0,
        "level": 1,
        "xp": 0,
        "skills": {
            "python_basics": 10,
            "algorithms": 5,
            "data_structures": 5,
            "file_io": 5,
            "api_usage": 3,
            "machine_learning": 1,
            "data_analysis": 1,
            "optimization": 1,
        },
        "completed_tasks": [],
        "failed_tasks": [],
        "insights": [],
        "self_improvements": [],
        "personality": {
            "curiosity": 0.8,
            "persistence": 0.7,
            "creativity": 0.6,
        },
        "created_at": datetime.utcnow().isoformat(),
        "last_run": None,
    }

def save_memory(state: dict):
    """Persist agent state to file."""
    MEMORY_FILE.parent.mkdir(exist_ok=True)
    state["last_run"] = datetime.utcnow().isoformat()
    MEMORY_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    print(f"💾 Memory saved — Cycle {state['cycle']}, Level {state['level']}, XP {state['xp']}")

# ── Level / XP system ─────────────────────────────────────────────────────────
XP_PER_LEVEL = 100

def add_xp(state: dict, xp: int, reason: str):
    state["xp"] += xp
    print(f"✨ +{xp} XP  ({reason})  → Total: {state['xp']}")
    while state["xp"] >= state["level"] * XP_PER_LEVEL:
        state["xp"] -= state["level"] * XP_PER_LEVEL
        state["level"] += 1
        print(f"🎉 LEVEL UP!  Agent is now Level {state['level']}")

# ── Task Generation ───────────────────────────────────────────────────────────
def generate_task(state: dict) -> dict:
    """Ask LLM to create an appropriate programming task based on current level."""
    skill_summary = json.dumps(state["skills"], indent=2)
    recent = state["completed_tasks"][-5:] if state["completed_tasks"] else []
    recent_txt = "\n".join(f"- {t['title']}" for t in recent) if recent else "None yet"
    
    system = """You are the task-generation module of a self-learning AI agent.
Your job: design ONE programming task that is:
1. Appropriate to the agent's current skill levels
2. Not a repeat of recent tasks
3. Solvable in a single Python file
4. Educational and progressively challenging
5. Includes Kaggle dataset usage IF ml/data skills are being targeted

Return ONLY valid JSON — no markdown fences, no extra text — in this exact shape:
{
  "title": "short task title",
  "description": "full task description with requirements",
  "difficulty": "beginner|intermediate|advanced",
  "target_skills": ["skill1", "skill2"],
  "expected_output": "description of what the solution should produce",
  "hints": ["hint1", "hint2"],
  "uses_kaggle": true or false,
  "kaggle_dataset": "owner/dataset-slug or null",
  "xp_reward": 10-50
}"""

    user = f"""Agent profile:
- Level: {state['level']}
- XP: {state['xp']}
- Cycle: {state['cycle']}
- Skills: {skill_summary}
- Recent completed tasks:
{recent_txt}

Generate the next programming task for this agent."""

    raw = call_llm([
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ], temperature=0.85)
    
    # Strip any accidental markdown
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    task = json.loads(raw)
    task["id"] = f"task_{state['cycle']:04d}_{int(time.time())}"
    task["created_at"] = datetime.utcnow().isoformat()
    return task

# ── Solution Execution ────────────────────────────────────────────────────────
def solve_task(task: dict, state: dict) -> dict:
    """Ask LLM to write code, execute it, capture result."""
    skill_summary = json.dumps(state["skills"], indent=2)

    system = """You are the coding module of a self-learning AI agent.
Write a complete, runnable Python script that solves the given task.

Rules:
- Self-contained in one file (install packages with subprocess/pip if needed)
- Include error handling
- Print progress and final results clearly
- If using Kaggle: use environment variables KAGGLE_USERNAME and KAGGLE_KEY
- The script must ACTUALLY run and produce output
- Add a comment block at the top summarising what you learned

Return ONLY the raw Python code — no markdown, no triple backticks."""

    user = f"""Task: {task['title']}

Description:
{task['description']}

Expected output: {task['expected_output']}

Hints: {json.dumps(task['hints'])}

Agent skills: {skill_summary}

Uses Kaggle: {task.get('uses_kaggle', False)}
Kaggle dataset: {task.get('kaggle_dataset', 'N/A')}

Write the Python solution:"""

    code = call_llm([
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ], temperature=0.3, max_tokens=4096)

    # Strip accidental fences
    code = re.sub(r"^```python\n?|^```\n?|```$", "", code, flags=re.MULTILINE).strip()

    # Save code to tasks/
    TASKS_DIR.mkdir(exist_ok=True)
    code_path = TASKS_DIR / f"{task['id']}.py"
    code_path.write_text(code, encoding="utf-8")
    print(f"📝 Solution written → {code_path}")

    # Execute with timeout
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    try:
        result = subprocess.run(
            [sys.executable, str(code_path)],
            capture_output=True, text=True, timeout=300, env=env
        )
        success = result.returncode == 0
        output = (result.stdout or "") + (result.stderr or "")
        output = output[:8000]   # cap log size
    except subprocess.TimeoutExpired:
        success = False
        output = "❌ Execution timed out after 5 minutes"
    except Exception as e:
        success = False
        output = f"❌ Execution error: {e}"

    print("─" * 60)
    print(output[:2000])
    print("─" * 60)

    return {
        "success": success,
        "output": output,
        "code_path": str(code_path),
        "code": code,
    }

# ── Reflection & Self-Improvement ─────────────────────────────────────────────
def reflect_and_improve(task: dict, execution: dict, state: dict) -> dict:
    """
    After each task: reflect, update skills, and optionally rewrite
    parts of the agent's own source code to become smarter.
    """
    system = """You are the meta-learning and self-improvement module of an AI agent.
After each task execution, you:
1. Analyse what worked and what didn't
2. Update skill levels (0-100) based on demonstrated ability
3. Extract insights and lessons learned
4. Suggest concrete self-improvements to the agent's code/config
5. Optionally rewrite agent files to make them smarter

Return ONLY valid JSON — no markdown — in this exact shape:
{
  "reflection": "2-3 sentence analysis of this cycle",
  "skill_updates": {"skill_name": new_value_0_to_100, ...},
  "new_skills": {"new_skill": initial_value, ...},
  "insights": ["insight1", "insight2"],
  "self_improvement": {
    "description": "what to improve in the agent itself",
    "target_file": "agent/brain.py or agent/prompts.py or null",
    "patch_description": "describe the change (agent will apply it next cycle)"
  },
  "personality_update": {"curiosity": 0.0-1.0, "persistence": 0.0-1.0, "creativity": 0.0-1.0}
}"""

    user = f"""Task attempted: {task['title']}
Difficulty: {task['difficulty']}
Target skills: {task['target_skills']}
Success: {execution['success']}

Output (truncated):
{execution['output'][:3000]}

Current skills: {json.dumps(state['skills'], indent=2)}
Current personality: {json.dumps(state['personality'], indent=2)}
Total cycles completed: {state['cycle']}

Reflect and suggest improvements:"""

    raw = call_llm([
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ], temperature=0.6)
    
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    return json.loads(raw)

# ── Apply Self-Improvements ───────────────────────────────────────────────────
def apply_self_improvement(improvement: dict, state: dict):
    """
    The agent rewrites its own files when the LLM decides something needs fixing.
    """
    target = improvement.get("target_file")
    if not target:
        return
    
    target_path = Path(target)
    if not target_path.exists():
        print(f"⚠️  Self-improvement target not found: {target}")
        return

    description = improvement.get("patch_description", "")
    current_code = target_path.read_text(encoding="utf-8")

    system = """You are the self-modification module of an AI agent.
You will receive the current source of an agent file and a description of what to improve.
Return the COMPLETE improved file — no markdown, no truncation, no omissions.
Only Python code."""

    user = f"""File: {target}

Improvement needed:
{description}

Current code:
{current_code}

Return the complete improved file:"""

    print(f"🔧 Applying self-improvement to {target}...")
    new_code = call_llm([
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ], temperature=0.2, max_tokens=8192)

    new_code = re.sub(r"^```python\n?|^```\n?|```$", "", new_code, flags=re.MULTILINE).strip()
    
    # Backup original
    backup = target_path.with_suffix(f".py.bak_{int(time.time())}")
    backup.write_text(current_code, encoding="utf-8")
    
    # Write improved version
    target_path.write_text(new_code, encoding="utf-8")
    print(f"✅ Self-improvement applied! Backup: {backup.name}")
    
    state["self_improvements"].append({
        "cycle": state["cycle"],
        "file": target,
        "description": description,
        "timestamp": datetime.utcnow().isoformat(),
    })

# ── History Logging ───────────────────────────────────────────────────────────
def log_history(task: dict, execution: dict, reflection: dict, state: dict):
    """Write a detailed log for this cycle."""
    HISTORY_DIR.mkdir(exist_ok=True)
    log = {
        "cycle": state["cycle"],
        "timestamp": datetime.utcnow().isoformat(),
        "task": task,
        "execution": {
            "success": execution["success"],
            "output_preview": execution["output"][:1500],
            "code_path": execution["code_path"],
        },
        "reflection": reflection,
        "state_after": {
            "level": state["level"],
            "xp": state["xp"],
            "skills": state["skills"],
        },
    }
    log_path = HISTORY_DIR / f"cycle_{state['cycle']:04d}.json"
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False))
    print(f"📚 History logged → {log_path}")

# ── README Update ─────────────────────────────────────────────────────────────
def update_readme(state: dict, task: dict, execution: dict):
    """Rewrite README with latest agent stats."""
    skills_md = "\n".join(
        f"| {k} | {'█' * (v // 10)}{'░' * (10 - v // 10)} | {v}/100 |"
        for k, v in sorted(state["skills"].items(), key=lambda x: -x[1])
    )
    
    recent_tasks = state["completed_tasks"][-10:]
    tasks_md = "\n".join(
        f"| {t['cycle']} | {t['title']} | {'✅' if t['success'] else '❌'} | +{t.get('xp',0)} XP |"
        for t in reversed(recent_tasks)
    ) or "| — | No tasks yet | — | — |"

    improvements_md = "\n".join(
        f"- **Cycle {i['cycle']}**: {i['description'][:80]}"
        for i in state["self_improvements"][-5:]
    ) or "_No self-improvements yet_"

    insights_md = "\n".join(
        f"- {ins}" for ins in state["insights"][-8:]
    ) or "_No insights yet_"

    readme = f"""# 🤖 Self-Learning AI Agent

> An autonomous agent that learns, codes, and evolves — cycle by cycle.

---

## 📊 Agent Status

| Property | Value |
|----------|-------|
| 🔢 Cycle | {state['cycle']} |
| ⭐ Level | {state['level']} |
| ✨ XP | {state['xp']} |
| 📅 Last Run | {state.get('last_run', 'Never')[:19].replace('T', ' ')} UTC |
| 🧠 Total Tasks | {len(state['completed_tasks'])} completed, {len(state['failed_tasks'])} failed |

---

## 🎯 Latest Task

**{task['title']}**

> {task['description'][:200]}...

- Difficulty: `{task['difficulty']}`
- Result: {'✅ Success' if execution['success'] else '❌ Failed'}

---

## 🧩 Skills

| Skill | Progress | Level |
|-------|----------|-------|
{skills_md}

---

## 📜 Recent Task History

| Cycle | Task | Result | XP |
|-------|------|--------|----|
{tasks_md}

---

## 💡 Insights Learned

{insights_md}

---

## 🔧 Self-Improvements Applied

{improvements_md}

---

## ⚙️ Architecture

```
self-learning-agent/
├── .github/workflows/
│   └── agent.yml          # Scheduled runner (every 6h)
├── agent/
│   ├── brain.py           # Core intelligence (self-modifiable)
│   └── prompts.py         # Prompt library (self-modifiable)
├── memory/
│   └── state.json         # Persistent memory & skill levels
├── tasks/
│   └── task_XXXX_*.py     # Generated & executed solutions
└── history/
    └── cycle_XXXX.json    # Full cycle logs
```

---

*This README is auto-generated by the agent each cycle.*
"""
    Path("README.md").write_text(readme, encoding="utf-8")
    print("📄 README updated")

# ── Main Cycle ────────────────────────────────────────────────────────────────
def run_cycle():
    print("\n" + "═" * 60)
    print("🤖 SELF-LEARNING AGENT — Starting New Cycle")
    print("═" * 60 + "\n")

    # 1. Load memory
    state = load_memory()
    state["cycle"] += 1
    print(f"📖 Cycle #{state['cycle']} | Level {state['level']} | XP {state['xp']}\n")

    # 2. Generate task
    print("🎯 Generating task...")
    task = generate_task(state)
    print(f"📌 Task: {task['title']} [{task['difficulty']}]")
    print(f"   {task['description'][:120]}...\n")

    # 3. Solve task
    print("💻 Solving task...")
    execution = solve_task(task, state)
    status = "✅ SUCCESS" if execution["success"] else "❌ FAILED"
    print(f"\n{status}\n")

    # 4. Award XP
    xp = task.get("xp_reward", 20) if execution["success"] else task.get("xp_reward", 5) // 2
    add_xp(state, xp, task["title"])

    # 5. Record task
    task_record = {
        "cycle": state["cycle"],
        "id": task["id"],
        "title": task["title"],
        "difficulty": task["difficulty"],
        "success": execution["success"],
        "xp": xp,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if execution["success"]:
        state["completed_tasks"].append(task_record)
    else:
        state["failed_tasks"].append(task_record)

    # 6. Reflect & learn
    print("🔍 Reflecting on this cycle...")
    reflection = reflect_and_improve(task, execution, state)

    # Update skills
    for skill, val in reflection.get("skill_updates", {}).items():
        if skill in state["skills"]:
            old = state["skills"][skill]
            state["skills"][skill] = max(0, min(100, int(val)))
            print(f"   📈 {skill}: {old} → {state['skills'][skill]}")

    # Add new skills discovered
    for skill, val in reflection.get("new_skills", {}).items():
        if skill not in state["skills"]:
            state["skills"][skill] = max(0, min(100, int(val)))
            print(f"   🆕 New skill: {skill} = {state['skills'][skill]}")

    # Save insights
    for insight in reflection.get("insights", []):
        if insight and insight not in state["insights"]:
            state["insights"].append(insight)
    state["insights"] = state["insights"][-50:]   # cap at 50

    # Update personality
    if "personality_update" in reflection:
        for trait, val in reflection["personality_update"].items():
            if trait in state["personality"]:
                state["personality"][trait] = round(float(val), 2)

    print(f"\n💭 Reflection: {reflection.get('reflection', '')[:150]}")

    # 7. Self-improvement
    improvement = reflection.get("self_improvement", {})
    if improvement.get("target_file"):
        apply_self_improvement(improvement, state)

    # 8. Log history
    log_history(task, execution, reflection, state)

    # 9. Update README
    update_readme(state, task, execution)

    # 10. Save memory
    save_memory(state)

    print("\n" + "═" * 60)
    print(f"✅ Cycle #{state['cycle']} complete!")
    print(f"   Level {state['level']} | XP {state['xp']} | Tasks done: {len(state['completed_tasks'])}")
    print("═" * 60 + "\n")

# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_cycle()
  
