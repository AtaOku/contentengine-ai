# ⚡ ContentEngine AI

**AI-powered content pipeline. One insight → four channels → under 60 seconds.**

Not "use ChatGPT sometimes." A structured pipeline with Brand Voice Cloning, quality scoring, and format-specific prompt engineering.

Built by [Ata Okuzcuoglu](https://linkedin.com/in/atakzcgl) · [Live Demo](https://contentengine-ai.streamlit.app) · [Case Study](https://www.notion.so/326feccf871081f7a3cde0e1033be38b)

---

## What It Does

Drop in a raw signal — news article, competitor move, customer quote, PDF whitepaper, any URL — and get publish-ready content across four channels simultaneously:

- **LinkedIn Post** — hook-first, thought leadership, hashtag strategy
- **Blog Draft** — SEO-structured, subheadings, data-backed claims
- **Reddit Thread** — peer-to-peer tone, zero promotion, community-native
- **Email Sequence** — A/B subject lines, preview text, single CTA

Each format has its own prompt engineering. The system prompt enforces domain expertise and anti-fluff rules. Messaging stays consistent across all four outputs.

---

## Key Features

### 🧬 Brand Voice Cloning
Upload 3-5 writing samples (CEO's LinkedIn posts, company blog, team emails) → AI extracts a Brand Voice Profile: hook patterns, sentence style, signature phrases, tone markers, structural preferences. Every output matches that voice.

### 📈 Content Quality Scoring
Each output gets scored on 5 dimensions: hook strength, readability, specificity, channel fit, CTA clarity. Overall score (1-10) with color coding and a single top improvement suggestion per piece.

### 📄 Multi-Source Input
- **Text / Paste** — raw text, headlines, quotes
- **URL Import** — auto-extracts article content (BeautifulSoup)
- **PDF Upload** — whitepapers, press releases, reports (PyPDF2)
- **DOCX Upload** — briefs, meeting notes (python-docx)
- **CSV / TXT / Markdown** — data exports, research notes

### 🎨 Tone & Audience Controls
- **5 Tone Presets:** Thought Leadership · Provocative · Data-Driven · Conversational · Educational
- **5 Audience Presets:** C-Suite · Ops/Engineering · Marketing · Domain Expert · General

---

## Architecture

```
INPUTS (Text, URL, PDF, DOCX, CSV)
        │
        ▼
   ┌─────────┐     ┌──────────────┐     ┌─────────────────────┐
   │ EXTRACT  │────→│   ANALYSIS   │────→│  PARALLEL GENERATE  │
   │ CONTENT  │     │  Core angle  │     │  + Voice + Tone     │
   └─────────┘     │  Pain point  │     │                     │
                    │  Hooks       │     │  ├─ LinkedIn Post    │
   ┌─────────┐     │  Why now?    │     │  ├─ Blog Draft       │
   │ BRAND   │     └──────────────┘     │  ├─ Reddit Thread    │
   │ VOICE   │───────────────────────→  │  └─ Email Sequence   │
   └─────────┘                          └─────────────────────┘
   ┌─────────┐                                    │
   │ TONE +  │──────────────────────────────────→ │
   │AUDIENCE │                              ┌─────┴─────┐
   └─────────┘                              │  SCORING   │
                                            │  5-dim     │
                                            └───────────┘
```

**5-Layer Prompt Architecture:** System Prompt (domain) → Analysis (JSON extraction) → Format Prompts (channel) → Context Injection (company) → Voice Profile (brand DNA)

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Add your Claude API key in the sidebar. Choose an input method and run.

---

## Why This Isn't a ChatGPT Wrapper

| ChatGPT Wrapper | ContentEngine |
|---|---|
| Single prompt → generic output | 5-layer prompt architecture |
| Manual rewrite per channel | 4 channel-native outputs simultaneously |
| No brand consistency | Brand Voice Cloning from samples |
| No quality feedback | 5-dimension quality scoring |
| Text input only | URL, PDF, DOCX, CSV auto-extraction |
| Same tone every time | Tone + Audience controls per run |

---

*Part of the [MarTech × AI Portfolio](https://www.notion.so/30ffeccf87108174a30cd60449aebaf3) — demonstrating the intersection of marketing domain expertise and AI engineering.*
