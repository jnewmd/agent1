# Marquis Companies — AI Opportunity Analyzer

FastAPI app that generates structured AI transformation opportunity reports for Marquis Companies using Claude as the analysis engine.

## Local development

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
uvicorn main:app --reload
# open http://localhost:8000
```

## Deploy to Railway

1. Push this folder to a GitHub repo
2. Go to railway.app → New Project → Deploy from GitHub repo
3. Select the repo
4. Add environment variable: `ANTHROPIC_API_KEY` = your key
5. Railway auto-detects the Procfile and deploys

That's it. Railway gives you a public URL.

## Project structure

```
marquis-ai-agent/
├── main.py              # FastAPI app + Claude API call
├── templates/
│   └── index.html       # Full UI (controls, report, follow-ups)
├── requirements.txt
├── Procfile             # Railway process definition
└── README.md
```

## Customizing

- Edit `MARQUIS_CONTEXT` in `main.py` to update org facts
- Edit `SYSTEM_PROMPT` to change report format or tone
- Add more business units to `UNIT_LABELS`
- Swap `claude-sonnet-4-20250514` for a different model as needed
