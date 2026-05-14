# LANES / DPH Intelligence Engine

Agentic question generation for LA County public health HIE data. Takes a dataset description, generates tiered analytical questions, stress-tests them adversarially, and prioritizes by health impact and actionability.

## Stack

- Node.js + Express (server)
- Vanilla HTML/CSS/JS (frontend, no build step)
- Anthropic Claude API (two-stage agentic pipeline)

## Local development

```bash
npm install
ANTHROPIC_API_KEY=your_key_here node server.js
```

Open http://localhost:3000

## Deploy to Railway

1. Push this folder to a GitHub repo
2. Go to railway.app → New Project → Deploy from GitHub repo
3. Select the repo
4. In the Railway dashboard, go to Variables and add:
   - `ANTHROPIC_API_KEY` = your Anthropic API key
5. Railway auto-detects Node.js and deploys. Your public URL appears in the dashboard.

That's it. No build step, no Docker needed.

## How it works

**Stage 1 — Generate** (`POST /api/generate`)  
Takes dataset context, priority lenses, and boldness mode. Returns 8 questions across four tiers: descriptive, comparative, actionable, and bold/novel. Each question includes rationale, health/cost impact estimate, action owner, data feasibility, pathway narrative, and a "so what" sentence.

**Stage 2 — Challenge** (`POST /api/challenge`)  
Sends every question to an adversarial agent that identifies the single most important methodological or data quality risk and suggests a refinement.

**Frontend**  
Scores are displayed with animated bars. Questions can be sorted by priority, novelty, or feasibility. Results export as plain text or JSON.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `PORT` | No | Port to listen on (Railway sets this automatically) |
