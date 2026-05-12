import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import Anthropic from '@anthropic-ai/sdk';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

const client = new Anthropic();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Step 1: Analyze the situation and generate clarifying questions
app.post('/api/analyze', async (req, res) => {
  const { input } = req.body;

  if (!input || input.trim().length < 10) {
    return res.status(400).json({ error: 'Please describe your situation in more detail.' });
  }

  try {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1500,
      system: `You are a relationship counselor who deeply understands both male and female perspectives. You specialize in helping men understand their partners better and navigate relationship dynamics with empathy and emotional intelligence.

Your job is to:
1. Quickly understand the situation a man is describing
2. Generate 1-3 MULTIPLE CHOICE clarifying questions that will help you give better advice
3. Each question should have 3-4 answer options

Rules:
- Questions should uncover emotional context, not just facts
- Options should be non-judgmental and cover the real range of possibilities
- Keep questions concise and relatable to a guy who may not naturally think in emotional terms
- Questions should feel easy to answer, not like therapy

Respond ONLY with valid JSON in this exact format:
{
  "situationSummary": "2-3 sentence empathetic summary of what's happening from a neutral lens",
  "questions": [
    {
      "id": "q1",
      "question": "Question text here",
      "options": [
        { "id": "a", "text": "Option A text" },
        { "id": "b", "text": "Option B text" },
        { "id": "c", "text": "Option C text" }
      ]
    }
  ]
}

Generate 1-3 questions maximum. Only ask what you truly need to give better advice.`,
      messages: [
        {
          role: 'user',
          content: `Here's my situation: ${input}`
        }
      ]
    });

    const text = response.content[0].text;
    const cleaned = text.replace(/```json|```/g, '').trim();
    const parsed = JSON.parse(cleaned);
    res.json(parsed);
  } catch (err) {
    console.error('Analyze error:', err);
    res.status(500).json({ error: 'Failed to analyze situation. Please try again.' });
  }
});

// Step 2: Generate full advice based on input + question answers
app.post('/api/advise', async (req, res) => {
  const { input, answers } = req.body;

  if (!input) {
    return res.status(400).json({ error: 'Missing situation input.' });
  }

  const answersText = answers && answers.length > 0
    ? answers.map(a => `Q: ${a.question}\nA: ${a.answer}`).join('\n\n')
    : 'No additional context provided.';

  try {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 2000,
      system: `You are a relationship counselor who deeply understands both male and female perspectives in romantic relationships. You help men — who often underestimate the emotional complexity of their partners — understand what's really happening and what to actually do about it.

Your advice is:
- Warm but direct
- Never preachy or condescending
- Written in plain language a regular guy can absorb
- Grounded in what women actually feel, not what men assume they feel
- Realistic — not asking men to be perfect, just better

Your response must be structured as valid JSON only, with no markdown or preamble:

{
  "headline": "A short, punchy 5-10 word title capturing the core insight",
  "herPerspective": {
    "title": "What she's likely feeling",
    "content": "2-3 sentences explaining what's going on emotionally for her. Be specific, empathetic, and honest. Name the actual feeling."
  },
  "hisPerspective": {
    "title": "Where you're coming from",
    "content": "2-3 sentences validating his perspective without excusing blind spots. Show him you get it."
  },
  "whatReallyHappened": "1-2 sentences cutting through to the real dynamic at play — the thing neither person may have said out loud",
  "actionSteps": [
    {
      "step": "Step title (4-6 words)",
      "detail": "1-2 sentences of concrete, specific guidance"
    }
  ],
  "thingsToAvoid": [
    "One specific thing to NOT say or do"
  ],
  "closingThought": "A single closing sentence that reframes the situation with compassion and a forward-looking perspective"
}

Keep actionSteps to 3-4 items. Keep thingsToAvoid to 2-3 items.`,
      messages: [
        {
          role: 'user',
          content: `Situation: ${input}\n\nAdditional context from my answers:\n${answersText}`
        }
      ]
    });

    const text = response.content[0].text;
    const cleaned = text.replace(/```json|```/g, '').trim();
    const parsed = JSON.parse(cleaned);
    res.json(parsed);
  } catch (err) {
    console.error('Advise error:', err);
    res.status(500).json({ error: 'Failed to generate advice. Please try again.' });
  }
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Better Boyfriend Advisor running on port ${PORT}`);
});
