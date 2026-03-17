# ⚡ ContentEngine AI

**Multi-format AI content pipeline for B2B manufacturing marketing.**

One raw insight → four publish-ready outputs → under 60 seconds.

Built by [Ata Okuzcuoglu](https://linkedin.com/in/atakzcgl) as a working proof-of-concept for Workerbase.

## What This Does

ContentEngine takes a raw signal (news article, competitor move, customer quote, trend observation) and produces channel-native content across four formats simultaneously:

- **LinkedIn Post** — thought leadership with hooks and hashtags
- **Blog Draft** — SEO-structured with subheadings and data points
- **Reddit Thread** — peer-to-peer tone, zero promotion
- **Email Sequence** — A/B subject lines, clear CTA

## Why This Isn't "Using ChatGPT"

| Prompt-and-Pray | ContentEngine Pipeline |
|---|---|
| Generic prompt → generic output | Structured analysis → format-specific generation |
| Manual rewrite per channel | One input → 4 channel-native outputs |
| No domain knowledge | Manufacturing-specific system prompt |
| Inconsistent messaging | Consistent narrative across all channels |
| No quality guardrails | Anti-fluff rules enforced at system level |

## Architecture

```
RAW INSIGHT → ANALYSIS (extract angle, pain, hooks) → PARALLEL GENERATE → 4 OUTPUTS
```

- **System Prompt:** Manufacturing domain expertise, anti-fluff rules, factory-floor perspective
- **Format Prompts:** Channel-specific prompt engineering (LinkedIn ≠ Reddit ≠ Email)
- **Context Injection:** Company-specific background injected into every generation
- **Model:** Claude Sonnet 4

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Add your Claude API key in the sidebar. Select a demo insight or paste your own.

## Scaling Roadmap

- **v2:** Monitoring layer (RSS, competitor blogs, Reddit alerts)
- **v3:** Workflow integration (HubSpot, Buffer, Slack)
- **v4:** Performance feedback loop (engagement → prompt optimization)

## Tech Stack

- Python / Streamlit
- Anthropic Claude API
- Prompt chaining architecture

---

*Built as part of a MarTech × AI portfolio demonstrating the intersection of marketing domain expertise and AI engineering.*
