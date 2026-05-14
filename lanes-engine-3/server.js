const express = require('express');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages';
const MODEL = 'claude-sonnet-4-20250514';

async function callClaude(system, user) {
  const res = await fetch(ANTHROPIC_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': process.env.ANTHROPIC_API_KEY,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: 4096,
      system,
      messages: [{ role: 'user', content: user }]
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error?.message || 'Anthropic API error ' + res.status);
  }
  const data = await res.json();
  return data.content.filter(b => b.type === 'text').map(b => b.text).join('');
}

function parseJSON(raw) {
  return JSON.parse(
    raw.replace(/^```json\s*/m, '').replace(/^```\s*/m, '').replace(/```\s*$/m, '').trim()
  );
}

// Stage 1: Generate questions
app.post('/api/generate', async (req, res) => {
  const { sources, scope, gaps, decisions, lenses, boldness } = req.body;

  if (!sources) return res.status(400).json({ error: 'Data sources required' });
  if (!process.env.ANTHROPIC_API_KEY) return res.status(500).json({ error: 'ANTHROPIC_API_KEY not set' });

  const boldInstr = {
    standard: 'Focus on high-feasibility questions grounded in current practice and policy.',
    bold: 'Include novel hypotheses and emerging practice models alongside grounded questions. Push past the obvious.',
    moonshot: 'Reimagine what becomes possible with full HIE data access. What new care models, surveillance systems, or interventions become possible that were never possible before?'
  }[boldness] || '';

  const ctx = [
    'Data sources: ' + sources,
    scope ? 'Population scope: ' + scope : '',
    gaps ? 'Known gaps: ' + gaps : '',
    decisions ? 'Decisions in play: ' + decisions : '',
    'Priority lenses: ' + (lenses || []).join(', '),
    'Boldness mode: ' + boldness
  ].filter(Boolean).join('\n');

  const system = `You are a public health intelligence analyst with deep expertise in epidemiology, health informatics, clinical operations, and health equity. You understand HIE data deeply: claims, FHIR encounters, registries, surveillance systems.

Generate exactly 8 high-value analytical questions for this public health dataset context. Span four tiers:
- Tier 1 (Descriptive): What is true? Baselines, distributions, outliers. These cannot be wrong — they describe.
- Tier 2 (Comparative): What is different? Cross-population, geography, time comparisons that generate hypotheses.
- Tier 3 (Actionable): What should change? Directly informs a decision by someone with budget authority.
- Bold/Novel: What becomes newly possible with this data? New models of care, surveillance, intervention timing.

Weight these priority lenses heavily: ${(lenses || []).join(', ')}.
${boldInstr}

Return ONLY a valid JSON array of exactly 8 objects. No preamble, no markdown fences, no explanation. Each object must have:
{
  "tier": "1" | "2" | "3" | "bold",
  "question": "the specific, non-obvious question",
  "rationale": "why this matters for this context (2 sentences)",
  "data_feasibility": "high/medium/low — one sentence explanation",
  "action_owner": "who specifically acts on the answer (role/function)",
  "health_metric": "one specific quantified estimate — e.g. Est. 14,000 avoidable ED visits/year at $1,850/visit = $25.9M or 8,200 QALYs lost to uncontrolled hypertension in South LA or Est. $12M annual duplicate billing fraud",
  "pathway_narrative": "how this realistically moves to action — what the path looks like, what barriers exist, who approves (2-3 sentences)",
  "so_what": "If this is true, then [specific actor with role] should [specific action] — one sentence only",
  "priority_score": integer 1-100,
  "novelty_score": integer 1-100,
  "feasibility_score": integer 1-100
}`;

  try {
    const raw = await callClaude(system, 'Context:\n' + ctx);
    const questions = parseJSON(raw);
    res.json({ questions });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Stage 2: Adversarial challenge
app.post('/api/challenge', async (req, res) => {
  const { questions } = req.body;
  if (!questions?.length) return res.status(400).json({ error: 'Questions required' });

  const system = `You are a rigorous adversarial reviewer for public health research. Challenge each question with sharp, specific critique. Identify the single most important methodological, data quality, or implementation risk that could undermine its value. Be direct and unsparing — a gentle challenge is useless.

Return ONLY a valid JSON array. No preamble, no markdown. Each object:
{
  "i": <0-based index>,
  "challenge": "the adversarial critique — 2 specific sentences identifying the core risk",
  "refinement": "how to sharpen or reframe the question to survive this challenge — 1 sentence"
}`;

  try {
    const raw = await callClaude(system, JSON.stringify(questions.map((q, i) => ({ i, question: q.question, tier: q.tier }))));
    const challenges = parseJSON(raw);
    res.json({ challenges });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`LANES engine running on port ${PORT}`));
