# ⚡ ContentEngine AI

**AI-powered content pipeline. One insight → four channels → under 60 seconds.**

Drop in a raw signal — news, URL, PDF, customer quote — and get publish-ready LinkedIn posts, blog drafts, Reddit threads, and email sequences. With Brand Voice Cloning, SEO analysis, AI visuals, and quality scoring built in.

**[Live Demo](https://contentengine-ai.streamlit.app)** · **[Case Study](https://www.notion.so/326feccf871081f7a3cde0e1033be38b)** · Built by [Ata Okuzcuoglu](https://linkedin.com/in/atakzcgl)

---

## Features

### 🔧 Live Pipeline
Paste text, import a URL, or upload a PDF/DOCX → get 4 channel-native outputs with tone and audience controls.

### 🔄 Repurpose Mode
Drop a long blog post or article → get 10 different content pieces: 3 LinkedIn posts, X thread, short blog, email, Reddit thread, carousel outline, newsletter blurb, quote cards.

### 🧬 Brand Voice Cloning
Upload 3-5 writing samples → AI extracts voice DNA (hook patterns, sentence style, signature phrases, tone markers). Every output matches that voice.

### 📊 SEO Readiness Analysis
Every blog output gets instant SEO scoring — pure Python, zero API cost:
- Flesch-Kincaid readability + grade level
- Word count optimization check
- Keyword extraction (frequency-based)
- Heading structure analysis (H1/H2/H3)
- Auto-generated meta description (155 chars)
- Composite SEO score (0-100)

Replaces what Surfer SEO charges $89/month for.

### 🖼️ AI Visuals
Auto-generated images via Pollinations.ai (free, no API key):
- Blog header images (1200×630)
- LinkedIn post visuals
- Quote card backgrounds
- Carousel slide backgrounds
- All downloadable as PNG

### 📈 Content Quality Scoring
5-dimension scoring per output: hook strength, readability, specificity, channel fit, CTA clarity. With improvement suggestions.

### 📦 Export All
- Markdown Bundle (.md)
- Content Calendar (weekday assignments + previews)
- Plain Text (copy-paste ready)

---

## Industry Showcase

Pre-generated demos across 3 industries — no API key needed:

| Demo | Topic |
|---|---|
| 🍎 Tech | Apple's AI strategy is failing — control culture vs AI speed |
| 🏥 Healthcare | GLP-1 drugs disrupting 6+ industries beyond obesity |
| 🏭 Manufacturing | $200B reshoring wave with no workers to fill it |

Each demo shows platform-native mockups: LinkedIn cards, Reddit threads, email inboxes, blog layouts.

---

## Architecture

```
INPUTS (Text, URL, PDF, DOCX, CSV)
        │
   ┌────┴────┐
   │ EXTRACT  │──→ ANALYSIS ──→ PARALLEL GENERATE
   │ CONTENT  │    (angles,     (4 channels +
   └─────────┘     hooks,        voice + tone)
                    pain)              │
   ┌─────────┐                   ┌────┴────┐
   │ BRAND   │──────────────────→│ OUTPUTS │
   │ VOICE   │                   │ + SEO   │
   └─────────┘                   │ + SCORE │
   ┌─────────┐                   │ + IMAGE │
   │ TONE +  │──────────────────→│         │
   │AUDIENCE │                   └─────────┘
   └─────────┘
```

**5-Layer Prompt Architecture:** System Prompt → Analysis → Format Prompts → Context Injection → Voice Profile

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

For public deployment: add `ANTHROPIC_API_KEY` to Streamlit Secrets.

---

## Tech Stack

| Component | Detail |
|---|---|
| Model | Claude Sonnet 4 |
| Framework | Streamlit |
| SEO Analysis | Pure Python (Flesch-Kincaid, keyword extraction) |
| URL Extraction | BeautifulSoup |
| PDF Processing | PyPDF2 |
| DOCX Processing | python-docx |
| AI Visuals | Pollinations.ai (free) |
| Deployment | Streamlit Cloud |

---

*Part of the [MarTech × AI Portfolio](https://www.notion.so/30ffeccf87108174a30cd60449aebaf3)*
