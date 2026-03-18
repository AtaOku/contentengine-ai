# ⚡ ContentEngine AI

**Full-stack AI content operations system. From "what should I write?" to "published across 4 channels" — in one tool.**

**[Live Demo](https://contentengine-ai.streamlit.app)** · **[Case Study](https://www.notion.so/326feccf871081f7a3cde0e1033be38b)** · **[Full Portfolio](https://www.notion.so/30ffeccf87108174a30cd60449aebaf3)**

Built by [Ata Okuzcuoglu](https://linkedin.com/in/ataokuzcuoglu)

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   INPUTS     │     │   ANALYSIS   │     │   BATCH GENERATE    │
│              │     │  (1 API call) │     │   (1 API call)      │
│ Text/URL/    │────→│              │────→│                     │
│ PDF/DOCX/CSV │     │ Core angle   │     │  Analysis feeds     │
└─────────────┘     │ Pain point   │     │  all 4 channels:    │
                     │ Hooks        │     │  LinkedIn + Blog    │
┌──────────────┐     │ Why now      │     │  + Reddit + Email   │
│ KNOWLEDGE    │     └──────────────┘     └─────────────────────┘
│ BASE         │            │                      │
│ Company      │            ▼                 ┌────┴────┐
│ Industry     │    Consistent narrative ←───│ OPTIMIZE │
│ Audience     │     across all channels      │ SEO+Score│
│ Competitors  │                              └─────────┘
│ Voice DNA    │
└──────────────┘     Total: 2 API calls (was 5)
```

**Key decisions:** Analysis feeds generation (not thrown away). Batch mode = 1 API call for 4 channels (~60% cost reduction). Structured Knowledge Base (6 fields, not freeform). Fallback: batch fails → individual generation with analysis.

## Features

| Tab | What It Does |
|---|---|
| 🔧 **Pipeline** | Input → 4 channel content via batch generation |
| 🔄 **Repurpose** | 1 article → 10 platform-specific pieces |
| 🔍 **Trend Radar** | Industry → 8 trending topics with hooks |
| 📊 **Data → Content** | CSV/data → story angles → Pipeline |
| 📦 **Showcase** | 3 demos with carousel + distribution (no API) |
| 🏗️ **How It Works** | Architecture + feature map |

**Plus:** Brand Voice Cloning · SEO with target keyword tracking ($0) · Carousel Builder · Content Chain · Multi-Language (EN/DE/TR/ES/FR) · Quality Scoring · Content History · Cost estimation

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
streamlit run app.py
```
