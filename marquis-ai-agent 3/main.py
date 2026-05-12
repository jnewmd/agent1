import os
import json
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()
templates = Jinja2Templates(directory="templates")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

LOOKUP_SYSTEM = """You are a business intelligence researcher. Given a company name, use web search to find accurate, current information about the company.

Return ONLY valid JSON, no markdown, no preamble:
{
  "name": string (official company name),
  "sector": string (e.g. "Post-Acute Care", "Health Insurance", "Hospital System", "Pharma", "Health IT"),
  "subsector": string (more specific),
  "hq": string (city, state),
  "founded": string (year or "Unknown"),
  "employees": string (e.g. "4,000+"),
  "revenue": string (e.g. "$500M-$1B" or "Unknown"),
  "description": string (2-3 sentences, factual, specific),
  "ai_signals": [string] (3-5 specific operational characteristics that indicate AI opportunity),
  "known_vendors": [string] (any known EHR, billing, or tech vendors),
  "confidence": number (0-100, confidence in this profile)
}"""

LOOKUP_TOOLS = [{"type": "web_search_20250305", "name": "web_search"}]

ANALYSIS_SYSTEM = """You are a senior healthcare AI strategy consultant advising C-suite leaders and boards. You have deep expertise across post-acute care, senior living, health systems, payers, pharma, and health IT.

Your analysis is grounded in operational reality, regulatory context, and published evidence. You cite real studies, CMS data, and industry benchmarks.

Output ONLY valid JSON, no markdown, no preamble:
{
  "headline": string (one punchy sentence with a dollar figure or % impact),
  "executive_summary": string (3-4 sentences, board-ready),
  "readiness_score": number (0-100),
  "total_value_low": number (conservative 3-year NPV in USD millions),
  "total_value_high": number (optimistic 3-year NPV in USD millions),
  "opportunities": [
    {
      "title": string,
      "priority": "high" | "medium" | "low",
      "category": string,
      "description": string (2-3 sentences specific to this company),
      "roi_annual_low": number (USD thousands, conservative),
      "roi_annual_high": number (USD thousands, optimistic),
      "payback_months": number,
      "confidence": number (0-100),
      "confidence_rationale": string,
      "complexity": "low" | "medium" | "high",
      "timeframe": string,
      "risk_factors": [string],
      "adversary_objections": [
        {
          "objection": string,
          "response": string
        }
      ],
      "evidence": [
        {
          "citation": string,
          "finding": string
        }
      ]
    }
  ],
  "top_adversary_argument": string,
  "top_adversary_response": string,
  "recommended_entry_point": string,
  "watch_outs": [string]
}

Return 5-7 opportunities. Use real dollar figures grounded in industry benchmarks. Cite real sources."""

ANALYSIS_TOOLS = [{"type": "web_search_20250305", "name": "web_search"}]


class LookupRequest(BaseModel):
    company: str


class AnalysisRequest(BaseModel):
    company_profile: dict
    depth: str = "strategic"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/lookup")
async def lookup_company(req: LookupRequest):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    async def stream():
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1500,
                    "stream": True,
                    "system": LOOKUP_SYSTEM,
                    "tools": LOOKUP_TOOLS,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Look up this company and return a structured JSON profile: {req.company}"
                        }
                    ],
                },
            ) as response:
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        for line in chunk.split("\n"):
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    return
                                try:
                                    event = json.loads(data)
                                    if event.get("type") == "content_block_delta":
                                        text = event.get("delta", {}).get("text", "")
                                        if text:
                                            yield text
                                except json.JSONDecodeError:
                                    pass

    return StreamingResponse(stream(), media_type="text/plain")


@app.post("/analyze")
async def analyze(req: AnalysisRequest):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    depth_prompts = {
        "strategic": "Frame for board and C-suite: competitive advantage, ROI narrative, strategic risk. Lead with business impact.",
        "operational": "Focus on workflow changes, staff roles affected, daily process improvements, time savings, error reduction.",
        "technical": "Focus on build vs. buy, EHR/billing integration complexity, data readiness, vendor evaluation criteria.",
    }
    depth_prompt = depth_prompts.get(req.depth, depth_prompts["strategic"])
    profile = req.company_profile
    company_name = profile.get("name", "this company")

    user_prompt = f"""Analyze AI transformation opportunities for {company_name}.

Company profile:
{json.dumps(profile, indent=2)}

Analysis depth: {depth_prompt}

Use web search to find:
1. Recent AI initiatives or tech investments by this company
2. Peer benchmarks (similar companies that have deployed AI)
3. Published studies on AI ROI in {profile.get('sector', 'healthcare')}
4. Regulatory or compliance context for their sector

Produce the full opportunity analysis with ROI estimates, confidence scores, risk factors, adversary objections, and evidence citations."""

    async def stream():
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 4000,
                    "stream": True,
                    "system": ANALYSIS_SYSTEM,
                    "tools": ANALYSIS_TOOLS,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            ) as response:
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        for line in chunk.split("\n"):
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    return
                                try:
                                    event = json.loads(data)
                                    if event.get("type") == "content_block_delta":
                                        text = event.get("delta", {}).get("text", "")
                                        if text:
                                            yield text
                                except json.JSONDecodeError:
                                    pass

    return StreamingResponse(stream(), media_type="text/plain")


@app.get("/health")
async def health():
    return {"status": "ok"}
