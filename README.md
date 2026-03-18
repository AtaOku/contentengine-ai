# ⚡ ContentEngine AI

**Full-stack AI content operations system. From "what should I write?" to "published across 4 channels" — in one tool.**

**[Live Demo](https://contentengine-ai.streamlit.app)** · **[Case Study](https://www.notion.so/326feccf871081f7a3cde0e1033be38b)** · **[Full Portfolio](https://www.notion.so/30ffeccf87108174a30cd60449aebaf3)**

Built by [Ata Okuzcuoglu](https://linkedin.com/in/ataokuzcuoglu)

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   INPUTS     │     │   ANALYSIS   │     │   BATCH GENERATE    │
│ Text/URL/    │────→│  (1 API call) │────→│   (1 API call)      │
│ PDF/DOCX/CSV │     │ Core angle   │     │  4 channels as JSON │
└─────────────┘     │ Pain point   │     │  LinkedIn + Blog    │
                     │ Hooks        │     │  + Reddit + Email   │
┌──────────────┐     └──────────────┘     └─────────────────────┘
│ KNOWLEDGE    │            │                      │
│ BASE         │            ▼                 ┌────┴────┐
│ Company      │    Consistent narrative ←───│ OPTIMIZE │
│ Audience     │     across all channels      │ SEO+Score│
│ Voice DNA    │                              └─────────┘
└──────────────┘     Total: 2 API calls (was 5)
```

## Modular Package Structure

```
contentengine/
├── app.py                      ← Streamlit UI (3,068 lines)
├── config/
│   ├── prompts.py              ← 8 prompt templates (382 lines)
│   ├── settings.py             ← Tone/audience presets, model config (131 lines)
│   └── demos.py                ← Pre-generated showcase content (396 lines)
├── engine/
│   ├── pipeline.py             ← generate_content, generate_batch, analyze_insight
│   ├── seo.py                  ← seo_analyze, target keyword tracking, render panel
│   ├── carousel.py             ← generate_carousel, render_carousel_slide
│   ├── chain.py                ← generate_content_chain (distribution strategy)
│   ├── trends.py               ← scan_trends (Trend Radar)
│   ├── data_to_content.py      ← CSV → story angles
│   ├── repurpose.py            ← 1 article → 10 pieces
│   └── voice.py                ← Brand voice extraction + quality scoring
├── ui/
│   ├── mockups.py              ← LinkedIn/Reddit/Email/Blog mockup renderers
│   ├── styles.py               ← Custom CSS
│   └── components.py           ← Image helpers
└── utils/
    ├── extractors.py           ← URL fetch, PDF, DOCX extraction
    └── export.py               ← Markdown bundle, content calendar
```

## Features

| Tab | What It Does |
|---|---|
| 🔧 **Pipeline** | Input → 4 channels via analysis-fed batch generation (2 API calls) |
| 🔄 **Repurpose** | 1 article → 10 platform-specific pieces |
| 🔍 **Trend Radar** | Industry → 8 trending topics with hooks |
| 📊 **Data → Content** | CSV/data → story angles → Pipeline |
| 📦 **Showcase** | 3 demos with carousel + distribution (no API) |
| 🏗️ **How It Works** | Architecture + feature map |

**Built-in:** Brand Voice Cloning · Target Keyword SEO ($0) · Carousel Builder · Content Chain · Multi-Language (EN/DE/TR/ES/FR) · Quality Scoring · Content History · Cost estimation · Dynamic onboarding

## Key Architectural Decisions

1. **Analysis feeds generation** — structured analysis injected into every format prompt (not thrown away)
2. **Batch generation** — 4 channels in 1 API call as JSON (~60% cost reduction)
3. **Structured Knowledge Base** — 6 fields vs. freeform text for richer context
4. **Anti-meta-commentary** — AI never says "I notice..." — always produces content
5. **Fallback design** — batch fails → individual generation with analysis injection

## Tech Stack

| Component | Detail |
|---|---|
| Model | Claude Sonnet 4 (batch JSON) |
| Pipeline | Analysis → Batch Generate (2 API calls) |
| SEO | Flesch-Kincaid + keyword density + target keyword ($0) |
| Visuals | Pollinations.ai (free) |
| Input | BeautifulSoup, PyPDF2, python-docx |
| Framework | Streamlit |

## Quick Start

```bash
pip install -r requirements.txt
# Add ANTHROPIC_API_KEY to .streamlit/secrets.toml
streamlit run app.py
```
