# ⚡ ContentEngine AI

**AI content pipeline. One insight → four channels → under 60 seconds.**

Drop in text, a URL, or a file. Get publish-ready LinkedIn posts, blog drafts, Reddit threads, and email sequences — with Brand Voice Cloning, SEO analysis, AI visuals, and quality scoring. Free to use.

**[Live Demo](https://contentengine-ai.streamlit.app)** · **[Case Study](https://www.notion.so/326feccf871081f7a3cde0e1033be38b)** · Built by [Ata Okuzcuoglu](https://linkedin.com/in/atakzcgl)

---

## Features

### 🔧 Live Pipeline
Paste text, import a URL, or upload a PDF/DOCX → get 4 channel-native outputs with tone and audience controls.

### 🔄 Repurpose Mode
Drop a long blog post or article → get 10 different content pieces: 3 LinkedIn posts, X thread, short blog, email, Reddit thread, carousel outline, newsletter blurb, 3 quote cards.

### 🧬 Brand Voice Cloning
Upload 3-5 writing samples → AI extracts voice DNA (hook patterns, sentence style, signature phrases, tone markers) → every output matches that voice.

### 📊 SEO Readiness (replaces $89/mo Surfer SEO)
Every blog output gets instant analysis — zero API cost, pure Python:
- SEO Score (0-100)
- Flesch-Kincaid readability + grade level
- Word count optimization check
- Keyword extraction
- Heading structure analysis
- Auto-generated meta description (155 chars)

### 🖼️ AI Visuals (free via Pollinations.ai)
Blog headers, LinkedIn visuals, quote card backgrounds, carousel slides — auto-generated and downloadable as PNG.

### 📈 Quality Scoring
5-dimension scoring per output: hook strength, readability, specificity, channel fit, CTA clarity.

### 📦 Export All
Markdown bundle, content calendar, or plain text — download everything in one click.

### 📄 Multi-Source Input
Text, URL (auto-extract), PDF, DOCX, CSV, Markdown — drop anything in.

---

## Architecture

```
INPUTS (Text, URL, PDF, DOCX)
    │
    ▼
ANALYSIS → PARALLEL GENERATE → 4 OUTPUTS
    │         + Voice Profile       │
    │         + Tone/Audience       │
    │                               ▼
    │                          SEO ANALYSIS
    │                          AI VISUALS
    │                          QUALITY SCORE
    │                               │
    ▼                               ▼
EXPORT (Markdown · Calendar · TXT · PNG)
```

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Tech Stack

| Component | Detail |
|---|---|
| Model | Claude Sonnet 4 |
| SEO Analysis | Pure Python (Flesch-Kincaid, keyword extraction) |
| AI Visuals | Pollinations.ai (free, no API key) |
| URL Extraction | BeautifulSoup |
| PDF/DOCX | PyPDF2, python-docx |
| Framework | Streamlit |
| Deployment | Streamlit Cloud |

---

*Part of the [MarTech × AI Portfolio](https://www.notion.so/30ffeccf87108174a30cd60449aebaf3)*
