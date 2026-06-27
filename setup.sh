#!/usr/bin/env bash
# ============================================================
#  Self-Learning Agent — Quick Setup Script
#  Run this once after cloning to initialise the repo
# ============================================================
set -e

echo ""
echo "🤖 Self-Learning Agent — Setup"
echo "================================"
echo ""

# Check git
if ! command -v git &>/dev/null; then
  echo "❌ git not found. Please install git first."
  exit 1
fi

# Check python
if ! command -v python3 &>/dev/null; then
  echo "❌ python3 not found. Please install Python 3.9+."
  exit 1
fi

echo "✅ Prerequisites OK"
echo ""

# Create placeholder dirs
mkdir -p tasks history memory

# Ensure state.json exists
if [ ! -f memory/state.json ]; then
  cat > memory/state.json << 'EOF'
{
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
    "optimization": 1
  },
  "completed_tasks": [],
  "failed_tasks": [],
  "insights": [],
  "self_improvements": [],
  "personality": {
    "curiosity": 0.8,
    "persistence": 0.7,
    "creativity": 0.6
  },
  "created_at": null,
  "last_run": null
}
EOF
  echo "✅ Initial memory created"
fi

echo ""
echo "📋 Next steps:"
echo "  1. Push this repo to GitHub"
echo "  2. Go to Settings → Secrets → Actions and add:"
echo "       GROQ_API_KEY   — from console.groq.com"
echo "       GH_TOKEN       — GitHub PAT with 'repo' scope"
echo "       KAGGLE_USERNAME — your Kaggle username"
echo "       KAGGLE_KEY     — your Kaggle API key"
echo "  3. Enable GitHub Actions in the Actions tab"
echo "  4. Trigger the first run manually"
echo ""
echo "🚀 Done! The agent will run every 6 hours automatically."
