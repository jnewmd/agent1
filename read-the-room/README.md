# Read the Room — Relationship Advisor

An agentic relationship advisor for men who want to show up better in love.

## How it works

**Step 1 — Input**: Describe your situation in plain language. A fight, a gift gone wrong, something she said, a fear you have.

**Step 2 — Clarification**: The AI analyzes your situation and asks up to 3 targeted multiple-choice questions to better understand the dynamics at play.

**Step 3 — Advice**: Full output including:
- Her perspective (what she's actually feeling)
- Your perspective (validated without excuse-making)
- What's really going on (the unspoken dynamic)
- Concrete action steps
- Things to avoid
- A closing reframe

## Tech stack

- Node.js + Express (ESM)
- Anthropic Claude claude-sonnet-4-20250514
- Pure HTML/CSS/JS frontend (no build step)
- Deployable on Railway in one click

## Local development

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

npm install
npm run dev
```

Open http://localhost:3000

## Deploy to Railway

1. Push this repo to GitHub
2. Create a new project on railway.app
3. Connect your GitHub repo
4. Add environment variable: `ANTHROPIC_API_KEY=your_key_here`
5. Railway auto-detects Node.js and deploys

The `railway.toml` config handles the rest.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `PORT` | No | Port to run on (Railway sets this automatically) |
