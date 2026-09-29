#!/usr/bin/env bash
set -e

echo "Creating AI Prospector Web directory structure..."

mkdir -p ai-prospector-web/templates
cd ai-prospector-web

# 1. requirements.txt
cat << 'EOF' > requirements.txt
flask>=3.0.0
gunicorn>=21.2.0
EOF

# 2. Procfile
cat << 'EOF' > Procfile
web: gunicorn app:app
EOF

# 3. render.yaml
cat << 'EOF' > render.yaml
services:
  - type: web
      name: ai-prospector-cute
          runtime: python
              buildCommand: pip install -r requirements.txt
                  startCommand: gunicorn app:app
                      plan: free
                      EOF

                      # 4. .gitignore
                      cat << 'EOF' > .gitignore
                      *.pyc
                      __pycache__/
                      instance/
                      .pytest_cache/
                      .coverage
                      htmlcov/
                      dist/
                      build/
                      *.egg-info/
                      .env
                      venv/
                      ENV/
                      prospector.db
                      EOF

                      # 5. README.md
                      cat << 'EOF' > README.md
                      # AI Prospector 🧸

                      A cute, offline-first prospecting intelligence and compliance-enforcing CRM.

                      ## Features
                      - **Deterministic AI Need Engine:** Identifies automation opportunities (AI Chatbots, Smart Booking, Review Boosters, etc.) without requiring external API keys.
                      - **SQLite Database Triggers:** Enforces opt-outs and suppression defense-in-depth directly at the DB level.
                      - **Pastel Web Interface:** Soft, friendly management console for leads and outreach.
                      - **Free Cloud Ready:** Pre-configured for zero-cost hosting on Render or PythonAnywhere.

                      ## Local Setup
                      ```bash
                      pip install -r requirements.txt
                      python app.py
                      