import os
import json
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()
templates = Jinja2Templates(directory="templates")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

MARQUIS_CONTEXT = """
Marquis Companies is a senior living and post-acute care operator founded in 1989, based in Milwaukie, Oregon.
Operations: 22+ campuses (skilled nursing, assisted living, independent living) across Oregon, California, Nevada.
Workforce: 4,000+ employees.
Services: post-hospital rehab, long-term care, memory care, in-home care (Marquis at Home).
Sister company: Consonus Healthcare (rehab therapy, pharmacy, consulting — 11 states).
Health plans: AgeRight Advantage (Medicare Advantage plan), AgeRight Clinical Services (NP-delivered primary care).
Housing: LifeTime Design universal design for aging in place.
Philosophy: person-centered care, championing each resident's aging journey.
Key revenue drivers: Medicare/Medicaid skilled nursing reimbursement, MA plan premiums, rehab therapy revenue through Consonus, home health episodic payments.
Pain points common to this segment: nurse staffing shortages, high documentation burden (MDS, care plans, progress notes), referral leakage from hospitals, avoidable readmissions, medication errors in post-acute, family communication overhead, CMS star rating pressure.
"""

UNIT_LABELS = {
    "all": "all business units",
    "snf": "skilled nursing facilities",
    "assisted": "assisted and independent living",
    "consonus": "Consonus Healthcare",
    "ageright": "AgeRight MA plan and NP services",
    "home": "Marquis at Home (home health)",
}

DEPTH_PROMPTS = {
    "strategic": "Focus on executive-level strategic framing: competitive advantage, ROI narrative, board-level risk/reward. Avoid technical implementation detail.",
    "operational": "Focus on workflow-level specifics: which staff roles are affected, what daily processes change, where manual work is eliminated. Be concrete about time savings and error reduction.",
    "technical": "Focus on build vs. buy decisions, integration complexity with EHR/billing systems, data readiness requirements, and vendor evaluation criteria.",
}

SYSTEM_PROMPT = """You are a senior healthcare AI strategy consultant with deep expertise in post-acute care, senior living, and health plan operations. You produce structured, rigorous AI transformation opportunity reports for healthcare executives.

Your analysis is grounded in operational reality — you understand MDS documentation, CMS star ratings, Medicare Advantage risk adjustment, rehab therapy RVUs, skilled nursing reimbursement, and home health episodic payments.

Output format (strict JSON, no markdown, no preamble):
{
  "summary": {
    "total_opportunities": number,
    "high_priority": number,
    "est_fte_impact": string,
    "headline": string
  },
  "opportunities": [
    {
      "title": string,
      "priority": "high" | "medium" | "low",
      "category": string,
      "description": string,
      "impact": string,
      "complexity": "low" | "medium" | "high",
      "timeframe": string
    }
  ],
  "watch_out": string
}

Return 6-8 opportunities. Be specific to Marquis's actual business model, not generic healthcare AI talking points."""


class AnalysisRequest(BaseModel):
    unit: str = "all"
    depth: str = "strategic"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze")
async def analyze(req: AnalysisRequest):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    unit_label = UNIT_LABELS.get(req.unit, "all business units")
    depth_prompt = DEPTH_PROMPTS.get(req.depth, DEPTH_PROMPTS["strategic"])

    user_prompt = f"""Analyze AI transformation opportunities for Marquis Companies, focused on: {unit_label}.

Context about Marquis:
{MARQUIS_CONTEXT}

Analysis depth: {depth_prompt}

Identify the highest-value AI opportunities specific to their integrated model (SNF + AL + home health + MA plan + Consonus rehab/pharmacy). Their integrated structure creates unique cross-entity data opportunities most competitors lack."""

    async def stream_response():
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
                    "max_tokens": 2000,
                    "stream": True,
                    "system": SYSTEM_PROMPT,
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

    return StreamingResponse(stream_response(), media_type="text/plain")


@app.get("/health")
async def health():
    return {"status": "ok"}
