"""
ContentEngine AI — Multi-Format Content Pipeline
Built by Ata Okuzcuoglu as a working proof-of-concept for Workerbase.

Takes a raw insight (news, trend, competitor move, customer quote) and produces
publish-ready content across 4 channels in under 60 seconds.
"""

import streamlit as st
import anthropic
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import io

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="ContentEngine AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=DM+Sans:wght@400;500;700&display=swap');

    .stApp { font-family: 'DM Sans', sans-serif; }

    .hero-header {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.05);
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #fff;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: rgba(255,255,255,0.6);
        margin-top: 0.5rem;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(99,102,241,0.2);
        color: #818cf8;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 1rem;
        border: 1px solid rgba(99,102,241,0.3);
    }

    .content-card {
        background: #fafafa;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .card-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #6366f1;
        margin-bottom: 0.75rem;
        font-weight: 700;
    }

    .stat-box {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .stat-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
    }
    .stat-label { font-size: 0.75rem; color: #64748b; margin-top: 2px; }

    .analysis-card {
        background: linear-gradient(135deg, #fefce8 0%, #fef9c3 100%);
        border: 1px solid #fde047;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .analysis-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 700;
        color: #854d0e;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
    }

    /* Platform Mockups */
    .linkedin-mockup {
        background: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        overflow: hidden;
        margin: 1rem 0;
        font-family: -apple-system, system-ui, sans-serif;
    }
    .linkedin-header {
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .linkedin-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0a66c2, #004182);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 700;
        font-size: 18px;
    }
    .linkedin-meta { font-size: 0.85rem; }
    .linkedin-name { font-weight: 600; color: #000; }
    .linkedin-title { color: #666; font-size: 0.75rem; }
    .linkedin-body { padding: 0 16px 16px; font-size: 0.9rem; line-height: 1.6; color: #333; white-space: pre-wrap; }
    .linkedin-actions {
        padding: 8px 16px;
        border-top: 1px solid #e0e0e0;
        display: flex;
        justify-content: space-around;
        color: #666;
        font-size: 0.8rem;
    }

    .reddit-mockup {
        background: #fff;
        border: 1px solid #ccc;
        border-radius: 4px;
        overflow: hidden;
        margin: 1rem 0;
        font-family: -apple-system, system-ui, sans-serif;
    }
    .reddit-sidebar {
        background: #f8f9fa;
        padding: 8px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        float: left;
        min-width: 40px;
    }
    .reddit-vote { color: #878a8c; font-size: 0.75rem; font-weight: 700; }
    .reddit-vote-count { color: #1a1a1b; font-weight: 700; }
    .reddit-content { padding: 8px 12px; }
    .reddit-sub { font-size: 0.75rem; color: #787c7e; margin-bottom: 4px; }
    .reddit-sub strong { color: #1c1c1c; }
    .reddit-title-text { font-size: 1.1rem; font-weight: 600; color: #1a1a1b; margin-bottom: 8px; }
    .reddit-body { font-size: 0.9rem; line-height: 1.5; color: #1a1a1b; white-space: pre-wrap; }
    .reddit-footer { padding: 4px 12px 8px; font-size: 0.75rem; color: #878a8c; display: flex; gap: 12px; }

    .email-mockup {
        background: #fff;
        border: 1px solid #dadce0;
        border-radius: 8px;
        overflow: hidden;
        margin: 1rem 0;
        font-family: -apple-system, system-ui, sans-serif;
        max-width: 600px;
    }
    .email-toolbar {
        background: #f2f2f2;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.8rem;
        color: #5f6368;
        border-bottom: 1px solid #dadce0;
    }
    .email-subject { padding: 12px 16px; font-size: 1rem; font-weight: 600; color: #202124; border-bottom: 1px solid #f0f0f0; }
    .email-meta { padding: 8px 16px; font-size: 0.8rem; color: #5f6368; }
    .email-body-content { padding: 16px; font-size: 0.9rem; line-height: 1.7; color: #202124; white-space: pre-wrap; }

    .blog-mockup {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        margin: 1rem 0;
        font-family: 'Georgia', serif;
    }
    .blog-header-bar {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        padding: 24px;
    }
    .blog-category { font-family: 'DM Sans', sans-serif; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 2px; color: #818cf8; margin-bottom: 8px; }
    .blog-headline { font-size: 1.4rem; font-weight: 700; color: #fff; line-height: 1.3; }
    .blog-byline { font-family: 'DM Sans', sans-serif; font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-top: 12px; }
    .blog-body-content { padding: 24px; font-size: 0.95rem; line-height: 1.8; color: #374151; white-space: pre-wrap; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Prompt Templates ─────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert B2B content strategist specializing in manufacturing technology, 
Industry 4.0, and connected worker platforms. You write for technical decision-makers 
(plant managers, VP Operations, CTO) who are pragmatic, time-constrained, and skeptical of hype.

Your tone: authoritative but not academic. Direct. Data-aware. You understand factory floors, 
not just boardrooms. You never use generic marketing fluff.

Company context: You're creating content for a manufacturing SaaS company that provides 
a connected worker platform used in 60+ factories (customers include Bosch, Porsche, BASF, 
thyssenkrupp). The platform connects people, machines, and processes in real-time to boost 
productivity 20%+. They're entering the US market and doing category creation.

CRITICAL RULES:
- Never use buzzwords without substance
- Every claim should be backed by a specific example or data point
- Write like someone who has actually visited a factory floor
- Be contrarian when appropriate — challenge conventional wisdom
- Manufacturing audience hates fluff — be concrete"""

FORMAT_PROMPTS = {
    "linkedin": """Create a LinkedIn post based on this insight. Requirements:
- Hook in the first line (pattern interrupt — question, bold claim, or surprising stat)
- 150-250 words max
- Use line breaks for readability (LinkedIn format)
- End with a question or call-to-action that invites discussion
- Include 3-5 relevant hashtags at the end
- Tone: thought leadership, not salesy. Like a plant manager sharing what they learned.
- NO emojis in the body text. Professional tone.

Raw insight: {insight}

Industry context: {context}

Return ONLY the post text, nothing else.""",

    "blog": """Create a blog post draft based on this insight. Requirements:
- Compelling headline (specific, not generic)
- 400-600 word draft
- Opening paragraph that hooks with a specific problem or scenario
- 2-3 subheadings that break up the content
- Include at least one specific example or data point
- End with a clear takeaway or next step
- SEO-friendly but not keyword-stuffed
- Write for VP Operations / Plant Managers who scan, don't read

Raw insight: {insight}

Industry context: {context}

Return the full blog post with headline.""",

    "reddit": """Create a Reddit post for r/manufacturing or r/industry40 based on this insight. Requirements:
- Title that feels native to Reddit (not promotional)
- 100-200 word body that shares a genuine observation or question
- Conversational, peer-to-peer tone
- Ask for input from the community
- NO company mentions — this is thought leadership, not promotion
- Feel like a manufacturing engineer sharing something interesting
- Include a TL;DR at the end

Raw insight: {insight}

Industry context: {context}

Return the title on the first line, then a blank line, then the body.""",

    "email": """Create a nurture email sequence hook (1 email) based on this insight. Requirements:
- Subject line (A/B test: give 2 options)
- Preview text (40-90 chars)
- 100-150 word body
- One clear CTA (not hard sell — think "See how Factory X solved this")
- Tone: helpful peer, not vendor
- For manufacturing operations leaders

Raw insight: {insight}

Industry context: {context}

Format:
Subject A: ...
Subject B: ...
Preview: ...

[body]

CTA: ...""",
}

ANALYSIS_PROMPT = """Analyze this raw insight for content potential. Return a JSON object with:
{{
    "core_angle": "The main content angle in one sentence",
    "audience_pain": "What pain point does this address for manufacturing leaders?",
    "contrarian_take": "What's the non-obvious perspective here?",
    "content_hooks": ["hook1", "hook2", "hook3"],
    "trending_relevance": "Why does this matter RIGHT NOW?",
    "suggested_channels": ["ranked list of best channels for this content"]
}}

Raw insight: {insight}
Industry context: {context}

Return ONLY valid JSON, no markdown formatting, no backticks."""


# ── Helpers ──────────────────────────────────────────────────

def fetch_url_content(url):
    """Fetch and extract main text content from a URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ContentEngine/1.0"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        # Try article tag first, then main, then body
        content = soup.find("article") or soup.find("main") or soup.find("body")
        if not content:
            return None, "Could not extract content from the page."

        text = content.get_text(separator="\n", strip=True)

        # Clean up: remove excessive blank lines, limit length
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        clean_text = "\n".join(lines)

        # Truncate to ~3000 chars to keep prompt manageable
        if len(clean_text) > 3000:
            clean_text = clean_text[:3000] + "\n\n[...truncated]"

        # Get title
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""

        if title_text:
            clean_text = f"Title: {title_text}\n\n{clean_text}"

        return clean_text, None
    except requests.exceptions.Timeout:
        return None, "Request timed out. Try a different URL."
    except requests.exceptions.RequestException as e:
        return None, f"Failed to fetch URL: {str(e)[:100]}"
    except Exception as e:
        return None, f"Error extracting content: {str(e)[:100]}"


def extract_file_content(uploaded_file):
    """Extract text from uploaded files (PDF, TXT, DOCX, CSV, MD)."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".txt") or name.endswith(".md"):
            return uploaded_file.read().decode("utf-8", errors="ignore"), None

        elif name.endswith(".csv"):
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            # Truncate large CSVs
            lines = content.split("\n")
            if len(lines) > 100:
                content = "\n".join(lines[:100]) + f"\n\n[...truncated, {len(lines)} total rows]"
            return content, None

        elif name.endswith(".pdf"):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                pages = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        pages.append(f"[Page {i+1}]\n{text}")
                full_text = "\n\n".join(pages)
                if len(full_text) > 4000:
                    full_text = full_text[:4000] + "\n\n[...truncated]"
                if not full_text.strip():
                    return None, "PDF appears to be image-based (no extractable text)."
                return full_text, None
            except ImportError:
                return None, "PyPDF2 not available. Install with: pip install PyPDF2"

        elif name.endswith(".docx"):
            try:
                import docx
                doc = docx.Document(io.BytesIO(uploaded_file.read()))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                full_text = "\n\n".join(paragraphs)
                if len(full_text) > 4000:
                    full_text = full_text[:4000] + "\n\n[...truncated]"
                return full_text, None
            except ImportError:
                return None, "python-docx not available. Install with: pip install python-docx"

        else:
            return None, f"Unsupported file type: {name.split('.')[-1]}"

    except Exception as e:
        return None, f"Error reading file: {str(e)[:100]}"


# ── Tone & Audience Configs ──────────────────────────────────

TONE_OPTIONS = {
    "🎯 Thought Leadership": "Authoritative, insight-driven. You're the expert sharing what you've learned. No selling.",
    "⚡ Provocative / Contrarian": "Challenge conventional wisdom. Be bold. Make people disagree in the comments.",
    "📊 Data-Driven / Analytical": "Lead with numbers, benchmarks, and evidence. Minimal opinion, maximum proof.",
    "🤝 Conversational / Peer": "Talk like a colleague over coffee. Casual but smart. First person.",
    "📚 Educational / How-To": "Teach something specific. Step-by-step. Practical and actionable.",
}

AUDIENCE_OPTIONS = {
    "👔 C-Suite / VP": "Time-constrained executives. Lead with business impact, ROI, risk. Skip technical details.",
    "🔧 Ops / Engineering": "Hands-on practitioners. They want specifics, not buzzwords. Technical credibility matters.",
    "📈 Marketing / Growth": "Growth-oriented marketers. Speak their language: CAC, LTV, conversion, attribution.",
    "🏭 Industry / Domain Expert": "Deep domain knowledge. Don't explain basics. Peer-to-peer expert conversation.",
    "🌍 General / Mixed": "Broad audience. Balance accessibility with depth. Define jargon when used.",
}

VOICE_EXTRACT_PROMPT = """Analyze these writing samples and extract a Brand Voice Profile. 
Study the patterns carefully across ALL samples and return a JSON object:

{{
    "voice_summary": "One-paragraph description of this brand's writing voice",
    "sentence_style": "Short/Medium/Long. How long are typical sentences? Any signature structures?",
    "hook_pattern": "How do they typically open posts/paragraphs? Question? Bold claim? Data? Story?",
    "vocabulary_level": "Technical jargon level: Low/Medium/High. Key recurring terms or phrases.",
    "signature_phrases": ["List of 3-5 recurring phrases, transitions, or verbal tics"],
    "tone_markers": "Confident/Humble/Provocative/Neutral? First person or third? Formal or casual?",
    "structural_pattern": "How do they structure content? Short paragraphs? Lists? Stories then data?",
    "cta_style": "How do they end? Question? Challenge? Invitation? Summary?",
    "what_they_avoid": "What do they clearly NOT do? (e.g., never use emojis, never use jargon, etc.)",
    "mimicry_instructions": "Specific, actionable instructions for an AI to write in this voice. Be very precise."
}}

Writing samples:
{samples}

Return ONLY valid JSON, no markdown formatting, no backticks."""

SCORING_PROMPT = """Score this content on 5 dimensions. Return a JSON object:

{{
    "hook_strength": {{"score": 1-10, "reason": "Why this score"}},
    "readability": {{"score": 1-10, "reason": "Why this score"}},
    "specificity": {{"score": 1-10, "reason": "Does it use concrete examples/data vs vague claims?"}},
    "channel_fit": {{"score": 1-10, "reason": "How well does it match the channel's native style?"}},
    "cta_clarity": {{"score": 1-10, "reason": "Is the call-to-action clear and compelling?"}},
    "overall": 1-10,
    "one_line_improvement": "Single most impactful edit to improve this content"
}}

Channel: {channel}
Content:
{content}

Return ONLY valid JSON, no markdown formatting, no backticks."""

REPURPOSE_PROMPT = """You are a content repurposing expert. Take this long-form content and break it into 
multiple standalone pieces, each optimized for its target format.

Source content:
{content}

Company/industry context:
{context}

Create exactly these pieces and return as a JSON object:
{{
    "title_summary": "One-line summary of the source content",
    "pieces": [
        {{
            "format": "linkedin_post_1",
            "label": "LinkedIn: [angle/hook description]",
            "content": "The full LinkedIn post text, 150-250 words, hook-first, with hashtags"
        }},
        {{
            "format": "linkedin_post_2",
            "label": "LinkedIn: [different angle]",
            "content": "A DIFFERENT LinkedIn post from a different angle of the same source"
        }},
        {{
            "format": "linkedin_post_3",
            "label": "LinkedIn: [third angle]",
            "content": "A THIRD LinkedIn post, maybe a hot take or contrarian view from the content"
        }},
        {{
            "format": "twitter_thread",
            "label": "X/Twitter: Thread (8-10 tweets)",
            "content": "1/ Opening tweet that hooks\\n\\n2/ Context...\\n\\n3/ ...each tweet separated by double newline, numbered"
        }},
        {{
            "format": "blog_short",
            "label": "Blog: Short-form (300 words)",
            "content": "A concise blog post with headline, 2 sections, clear takeaway"
        }},
        {{
            "format": "email_nurture",
            "label": "Email: Nurture sequence hook",
            "content": "Subject A: ...\\nSubject B: ...\\nPreview: ...\\n\\n[body 100-150 words]\\n\\nCTA: ..."
        }},
        {{
            "format": "reddit_post",
            "label": "Reddit: Discussion starter",
            "content": "Title on first line\\n\\nBody with peer tone, question at end, TL;DR"
        }},
        {{
            "format": "carousel_outline",
            "label": "Carousel: LinkedIn/Instagram (8 slides)",
            "content": "Slide 1 (Hook): ...\\nSlide 2: ...\\nSlide 3: ...\\n...\\nSlide 8 (CTA): ..."
        }},
        {{
            "format": "newsletter_blurb",
            "label": "Newsletter: Quick blurb (75 words)",
            "content": "Short, punchy summary for a newsletter section. Link teaser."
        }},
        {{
            "format": "quote_cards",
            "label": "Quote Cards: 3 shareable quotes",
            "content": "Quote 1: \\"....\\"\\n\\nQuote 2: \\"....\\"\\n\\nQuote 3: \\"....\\""
        }}
    ]
}}

CRITICAL: Each piece must be a DIFFERENT angle or format — not just the same text reformatted. 
Extract different insights, stats, or arguments from the source for each piece.
Return ONLY valid JSON, no markdown formatting, no backticks."""


def repurpose_content(client, content, context):
    """Break long-form content into 10 platform-specific pieces."""
    prompt = REPURPOSE_PROMPT.format(content=content[:5000], context=context)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip()), None
    except json.JSONDecodeError:
        return None, "Failed to parse repurposed content."
    except Exception as e:
        return None, f"Error: {str(e)[:150]}"
    # Priority: st.secrets > user input
    api_key = ""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass
    if not api_key:
        api_key = st.session_state.get("api_key", "")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def has_api_key():
    """Check if API key is available from any source."""
    try:
        if st.secrets.get("ANTHROPIC_API_KEY", ""):
            return True
    except Exception:
        pass
    return bool(st.session_state.get("api_key", ""))

def generate_content(client, format_type, insight, context, tone_desc="", audience_desc="", voice_profile=None):
    prompt = FORMAT_PROMPTS[format_type].format(insight=insight, context=context)

    # Inject tone and audience into prompt
    modifiers = ""
    if tone_desc:
        modifiers += f"\n\nTONE INSTRUCTION: {tone_desc}"
    if audience_desc:
        modifiers += f"\nAUDIENCE: {audience_desc}"

    # Inject brand voice profile
    if voice_profile:
        voice_instructions = voice_profile.get("mimicry_instructions", "")
        voice_summary = voice_profile.get("voice_summary", "")
        sig_phrases = ", ".join(voice_profile.get("signature_phrases", []))
        avoid = voice_profile.get("what_they_avoid", "")

        modifiers += f"""

BRAND VOICE (CRITICAL — match this voice exactly):
{voice_summary}

Mimicry instructions: {voice_instructions}
Hook pattern: {voice_profile.get('hook_pattern', '')}
Sentence style: {voice_profile.get('sentence_style', '')}
Structural pattern: {voice_profile.get('structural_pattern', '')}
Signature phrases to use naturally: {sig_phrases}
CTA style: {voice_profile.get('cta_style', '')}
Things to AVOID: {avoid}"""

    if modifiers:
        prompt = prompt + modifiers

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"


def extract_brand_voice(client, samples_text):
    """Extract brand voice profile from writing samples."""
    prompt = VOICE_EXTRACT_PROMPT.format(samples=samples_text)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip()), None
    except json.JSONDecodeError:
        return None, "Failed to parse voice profile. Try with different samples."
    except Exception as e:
        return None, f"Error: {str(e)[:100]}"


def score_content(client, content, channel):
    """Score generated content on quality dimensions."""
    prompt = SCORING_PROMPT.format(content=content, channel=channel)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip())
    except:
        return None


def render_linkedin_mockup(content):
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""
<div class="linkedin-mockup">
    <div class="linkedin-header">
        <div class="linkedin-avatar">CE</div>
        <div class="linkedin-meta">
            <div class="linkedin-name">ContentEngine AI</div>
            <div class="linkedin-title">Generated via Pipeline · Just now · 🌐</div>
        </div>
    </div>
    <div class="linkedin-body">{safe}</div>
    <div class="linkedin-actions">
        <span>👍 Like</span><span>💬 Comment</span><span>🔄 Repost</span><span>📤 Send</span>
    </div>
</div>"""


def render_reddit_mockup(content):
    lines = content.strip().split("\n")
    title = lines[0] if lines else "Untitled"
    body = "\n".join(lines[2:]) if len(lines) > 2 else ""
    safe_t = title.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    safe_b = body.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f"""
<div class="reddit-mockup">
    <div style="display:flex;">
        <div class="reddit-sidebar">
            <span class="reddit-vote">▲</span>
            <span class="reddit-vote-count">247</span>
            <span class="reddit-vote">▼</span>
        </div>
        <div class="reddit-content">
            <div class="reddit-sub"><strong>r/marketing</strong> · Posted by u/contentengine · 2h</div>
            <div class="reddit-title-text">{safe_t}</div>
            <div class="reddit-body">{safe_b}</div>
        </div>
    </div>
    <div class="reddit-footer">
        <span>💬 42 Comments</span><span>📤 Share</span><span>⭐ Save</span>
    </div>
</div>"""


def render_email_mockup(content):
    safe = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    subject = "Your weekly insight"
    for line in content.split("\n"):
        if line.startswith("Subject A:"):
            subject = line.replace("Subject A:","").strip()
            break
    safe_s = subject.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f"""
<div class="email-mockup">
    <div class="email-toolbar">
        <span>📥 Inbox</span> → <span style="color:#202124;font-weight:600;">ContentEngine</span>
    </div>
    <div class="email-subject">{safe_s}</div>
    <div class="email-meta">From: content@company.com · To: [First Name] · Now</div>
    <div class="email-body-content">{safe}</div>
</div>"""


def render_blog_mockup(content):
    import re
    lines = content.strip().split("\n")
    headline = lines[0].lstrip("# ").strip() if lines else "Untitled"
    body_lines = lines[1:]

    # Simple markdown → HTML conversion
    html_parts = []
    for line in body_lines:
        line = line.strip()
        if not line:
            html_parts.append("<br>")
            continue
        # Headings
        if line.startswith("## "):
            text = line.lstrip("# ").strip()
            text = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            html_parts.append(f'<h3 style="font-family: DM Sans, sans-serif; font-size:1.1rem; font-weight:700; color:#1a1a2e; margin:20px 0 8px;">{text}</h3>')
            continue
        # Bold
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        # Italic
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
        # Escape remaining HTML (but preserve our tags)
        safe_line = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        # Restore our tags
        safe_line = safe_line.replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
        safe_line = safe_line.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
        html_parts.append(f'<p style="margin:0 0 8px;">{safe_line}</p>')

    body_html = "\n".join(html_parts)
    safe_h = headline.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    # Word count for read time
    word_count = len(content.split())
    read_min = max(1, word_count // 200)

    return f"""
<div class="blog-mockup">
    <div class="blog-header-bar">
        <div class="blog-category">Insights</div>
        <div class="blog-headline">{safe_h}</div>
        <div class="blog-byline">ContentEngine AI · {read_min} min read</div>
    </div>
    <div class="blog-body-content" style="white-space:normal;">{body_html}</div>
</div>"""


MOCKUP_RENDERERS = {
    "linkedin": render_linkedin_mockup,
    "blog": render_blog_mockup,
    "reddit": render_reddit_mockup,
    "email": render_email_mockup,
}


def analyze_insight(client, insight, context):
    prompt = ANALYSIS_PROMPT.format(insight=insight, context=context)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip())
    except:
        return None


# ── Demo Insights ────────────────────────────────────────────

DEMO_INSIGHTS = {
    "🤖 GenAI Hits the Factory Floor": {
        "insight": "Google Cloud and manufacturing companies recently demonstrated Generative AI use cases for factory floors — converting static PDF manuals into dynamic step-by-step work instructions, and using historical process data to predict machine setup times. Companies like MAN Truck & Bus, GKN, and Knorr-Bremse participated. The key finding: workers don't need AI expertise — they need AI that fits into existing workflows.",
        "context": "Connected Worker platforms are the natural delivery layer for factory AI. The skills gap in manufacturing is widening — 2.1M unfilled jobs projected by 2030 in the US alone. Training new workers faster is existential for many factories. AI-generated work instructions could cut onboarding time by 40-60%."
    },
    "📉 Skills Crisis — 2.1M Jobs Unfilled by 2030": {
        "insight": "A Deloitte study shows 2.1 million manufacturing jobs will go unfilled by 2030 due to the skills gap. Meanwhile, average factory worker tenure has dropped below 3 years. The old model of 6-month apprenticeships doesn't work when your workforce turns over every 2-3 years. Some factories are now onboarding workers in days instead of months using digital guidance systems.",
        "context": "Connected Worker platforms address this directly by embedding knowledge into the workflow. Instead of training workers to memorize procedures, the system guides them in real-time. Factories using this approach report 30-50% faster onboarding and 25% fewer quality defects from new workers."
    },
    "🔧 Lean is Broken — Toyota's Model Can't Keep Up": {
        "insight": "Toyota's lean production system was revolutionary 40 years ago. But lean was designed for stable, high-volume production. Today's reality: batch sizes are shrinking, product variants are exploding, and customer demand shifts weekly. A German auto supplier went from 12 product variants to 200+ in five years. Their lean system couldn't keep up.",
        "context": "This is the core argument for Dynamic Process Execution: manufacturing needs to shift from pre-planned, rigid workflows to adaptive, real-time orchestration. Lean was like a railway schedule — efficient but inflexible. DPE is like ride-sharing — it responds to demand in real time."
    },
    "🇺🇸 US Reshoring Wave — $200B Problem": {
        "insight": "The CHIPS Act, IRA, and supply chain security concerns are driving a massive reshoring wave in US manufacturing. Over $200B in new factory investments announced since 2022. But here's the problem nobody's talking about: these new factories need workers, and the US manufacturing workforce is older and smaller than ever. You can build a $20B chip fab, but who's going to run it?",
        "context": "This is directly relevant to US market entry. New factories being built need connected worker solutions from day one — they can't rely on institutional knowledge that doesn't exist yet. Greenfield factories are the perfect entry point: no legacy systems, no change management resistance, and an urgent need for digital-first worker enablement."
    }
}

# ── Pre-generated Workerbase content ─────────────────────────

PREGENERATED = {
    "linkedin": """Your factory has 200 years of accumulated knowledge.

Your average worker has been there 2.7 years.

That's the gap nobody's talking about in the "reshoring" conversation.

Washington announced $200B+ in new factory investments since 2022. The CHIPS Act. The IRA. Supply chain security. Great.

But buildings don't make products. People do.

And the US manufacturing workforce is older and smaller than it's been in decades. The workers who knew every machine sound, every quality trick, every shortcut — they're retiring.

The new workers? They're capable. But they don't have 20 years of tribal knowledge in their heads.

This is why the real infrastructure investment isn't in concrete and steel. It's in the systems that capture knowledge and deliver it to the right person, at the right moment, on the factory floor.

The factories that win the reshoring wave won't be the ones with the most automation. They'll be the ones that figured out how to make a day-one worker perform like a year-five veteran.

That's not a training problem. That's an architecture problem.

How is your factory handling knowledge transfer to new workers?

#Manufacturing #Reshoring #Industry40 #ConnectedWorker #ManufacturingTech""",

    "blog": """# The $200 Billion Blind Spot: Why New Factories Need Digital Workers Before Day One

**The reshoring math has a people problem.**

Since 2022, over $200 billion in new US factory investments have been announced. The CHIPS Act and Inflation Reduction Act are fueling the largest manufacturing construction boom in a generation. Politicians love the photo ops. Investors love the projections.

But walk into any of these construction sites and ask the operations team one question: *Where are you going to find the workers?*

The silence is deafening.

## The Knowledge Gap Is the Real Infrastructure Problem

The US manufacturing workforce has been shrinking for decades. The average factory worker's tenure has dropped below three years. The experienced operators who could troubleshoot a production line by listening to the machines — they're retiring faster than we can replace them.

Deloitte projects 2.1 million manufacturing jobs will go unfilled by 2030. That number was calculated *before* the reshoring wave added hundreds of new facilities to the demand side.

Here's what makes this different from previous labor shortages: these new facilities are greenfield builds. There is no institutional knowledge. No veteran worker to shadow. No "ask Bob, he's been here 30 years."

## Why Digital-First Beats Train-First

The old manufacturing playbook says: hire workers, train them for months, pair them with veterans, and hope the knowledge transfers through osmosis. That model assumed stability — low turnover, long careers, gradual complexity increases.

None of those assumptions hold anymore.

The factories that will actually succeed in the reshoring wave are designing their operations around a different principle: embed the knowledge into the workflow, not into the worker's memory.

This means real-time digital guidance that walks a day-one operator through complex procedures. It means AI-powered work instructions that adapt to the specific machine, product variant, and worker skill level. It means capturing every process improvement digitally so it's available to every worker instantly — not locked in someone's head.

## The Greenfield Advantage

Ironically, new factories have an advantage here. No legacy systems to replace. No "we've always done it this way" resistance. They can build digital-first from the ground up.

The smart ones are doing exactly that. They're making connected worker platforms part of the factory design — not an afterthought bolted on after the first quality crisis.

**The takeaway:** The reshoring wave will be won or lost not by who builds the biggest factory, but by who figures out how to make new workers productive fastest. The infrastructure that matters most isn't concrete — it's digital.""",

    "reddit": """Has anyone else noticed the massive disconnect in the reshoring conversation?

I've been following the US manufacturing reshoring wave pretty closely — $200B+ in new factory investments, CHIPS Act money flowing, everyone's excited.

But I keep running into the same problem when I talk to ops people at these new facilities: where are the workers coming from?

I visited a greenfield facility last month. Beautiful building, latest equipment, impressive automation. Asked the plant manager about staffing. He basically said they're planning to hire people with zero manufacturing experience and train them on the job. For complex assembly processes.

The old model was: hire someone, pair them with a 20-year veteran for 6 months, and let the knowledge transfer through osmosis. But these new plants don't HAVE veterans. There's no institutional knowledge to transfer.

Some places are starting to use digital guidance systems that walk new workers through procedures step-by-step on tablets/wearables. Basically embedding the expertise into the system instead of relying on worker memory. Seems promising but I'm curious about real-world results.

Anyone working at a greenfield facility dealing with this? How are you handling onboarding when there's no "tribal knowledge" to lean on?

TL;DR: Reshoring wave is building tons of new factories but nobody's talking about where the skilled workers will come from. Old apprenticeship model doesn't work at greenfield sites. Digital guidance systems seem like the answer but want to hear real experiences.""",

    "email": """Subject A: The reshoring problem nobody's solving (yet)
Subject B: Your new factory needs workers. Where will they come from?
Preview: 2.1M unfilled jobs by 2030. New approach inside.

Hi [First Name],

Quick question: if you're building or expanding a factory in the US right now, where are you finding experienced workers?

The reshoring numbers are impressive — $200B+ in new investments. But every ops leader I talk to says the same thing: the buildings are going up faster than the workforce is materializing.

Deloitte's 2.1M unfilled jobs projection was calculated before the current construction boom. The gap is only widening.

The factories figuring this out aren't waiting for the labor market to fix itself. They're redesigning onboarding around digital systems that make a week-one worker perform like a month-six worker.

One automotive supplier cut new worker onboarding from 12 weeks to 3 using real-time digital guidance on the shop floor. Quality defects from new workers dropped 25%.

CTA: See how leading manufacturers are solving the skills gap → [link]"""
}

# ── Multi-Industry Showcase Demos ─────────────────────────────

SHOWCASE_DEMOS = {
    "🍎 Tech — Why Apple's AI Strategy Is Failing": {
        "description": "Apple Intelligence launched with hype but delivers hallucinated notifications, basic summaries, and no real Siri upgrade. Meanwhile, Google and OpenAI ship weekly. What went wrong?",
        "linkedin": """Apple spent $100 billion on R&D last year.

Their AI summarized a news headline so badly it became international news.

Meanwhile, Google shipped Gemini into every product in 6 months. OpenAI went from GPT-4 to real-time voice to video generation in 18 months. Meta open-sourced Llama and built an AI ecosystem overnight.

Apple launched "Apple Intelligence" and gave us... notification summaries that hallucinate.

Here's what went wrong:

Apple's entire business model is built on control. Closed ecosystem. Curated experience. Privacy as religion. These are genuine strengths for hardware and OS design.

But they're fatal weaknesses for AI.

AI development requires rapid iteration. Ship fast, break things, learn from millions of users, ship again. Google and OpenAI deploy model updates weekly. Apple ships annually.

AI development requires data. Lots of it. Apple's privacy stance — which customers love — means they can't train on user data the way competitors do. Noble? Yes. Competitive? No.

AI development requires openness. The biggest breakthroughs are coming from open research, open models, open collaboration. Apple's secrecy culture is fundamentally incompatible with how the AI ecosystem evolves.

The result: Apple is 2-3 years behind on the technology that will define the next decade of computing.

This isn't a temporary setback. It's a structural mismatch between Apple's DNA and what AI demands.

The question isn't whether Apple will catch up. It's whether the closed-ecosystem model survives the AI era at all.

What's your take — can Apple adapt, or is this a fundamental disadvantage?

#Apple #AI #BigTech #ArtificialIntelligence #TechStrategy""",

        "blog": """# Apple's $100 Billion AI Problem: Why Control Culture Can't Win the AI Race

**The company that perfected closed ecosystems is losing to open ones.**

Apple Intelligence was supposed to be the moment Apple proved it could compete in AI. Instead, it became a case study in why the world's most valuable company might be structurally incapable of winning the AI race.

The hallucinated notification summaries were embarrassing. The basic text tools were underwhelming. The "upgraded" Siri remained largely unchanged. And developers who expected an AI platform got a limited set of APIs that felt years behind Google and OpenAI.

## The Structural Mismatch

Apple's DNA is control. Closed hardware. Curated App Store. Vertically integrated experiences. This philosophy built the most profitable technology company in history.

But AI doesn't reward control. It rewards speed, data, and openness — three things Apple's culture actively resists.

Google deploys model improvements weekly. OpenAI pushes updates to millions of users and iterates in real-time. Meta open-sourced Llama and created an entire ecosystem of developers improving its models for free.

Apple ships major updates annually. In AI, that's a geological timescale.

## The Data Paradox

Apple's privacy commitment is genuine and customers love it. But it creates a fundamental training data disadvantage. Google processes billions of search queries, Gmail messages, and YouTube interactions daily. Apple deliberately doesn't access equivalent user data.

## The Open vs. Closed Dilemma

The most significant AI breakthroughs of the past two years have come from open research and open models. The community that advances AI fastest is inherently collaborative and transparent.

Apple's secrecy culture — the locked-down campuses, the compartmentalized teams, the surprise-driven product launches — is the opposite of how AI innovation happens.

## What This Means

Apple isn't going away. They have $160B in cash, a loyal ecosystem of 2B+ devices, and the best hardware engineering on the planet. But the AI gap is widening, not closing.

The real question is whether Apple's closed-ecosystem advantage in hardware and OS can survive in a world where the core intelligence layer is being built in the open, by competitors who move 10x faster.

**The takeaway:** Apple's AI problem isn't talent or money. It's culture. And culture is the hardest thing to change.""",

        "reddit": """Is anyone else underwhelmed by Apple Intelligence, or am I missing something?

Genuine question. I've been an Apple user for 15 years and I was excited about Apple Intelligence. But after using it for months, I'm struggling to see what it actually does well.

The notification summaries hallucinate regularly. I got a summary that said a friend "expressed negative feelings about my relationship" — it was a restaurant recommendation. The writing tools are basic rewriting that any LLM can do. Siri is still Siri.

Meanwhile I watch friends using Gemini on their Pixels doing genuinely useful stuff — real-time translation in calls, AI-organized photos that actually work, document understanding that feels magical.

I think Apple's privacy-first approach is admirable, but I'm starting to wonder if it's a structural disadvantage for AI. You can't build great AI without data, and Apple deliberately limits what data they can use.

The other thing that bugs me: Apple ships AI updates annually. Google and OpenAI ship weekly. In a field moving this fast, annual updates mean you're always 6-12 months behind.

Anyone found genuine daily-use value from Apple Intelligence? Or are we all just waiting for the "real" update?

TL;DR: Apple Intelligence feels 2-3 years behind Google/OpenAI. Privacy-first approach may be structurally incompatible with competitive AI development. Wondering if other Apple users feel the same or if I'm missing key features.""",

        "email": """Subject A: Apple's AI is 2 years behind. Here's why it matters.
Subject B: The $100B blind spot in Apple's strategy
Preview: Control culture vs. AI speed. Something has to give.

Hi [First Name],

Quick question: when was the last time Apple Intelligence actually helped you do something useful?

If you're struggling to answer, you're not alone.

While Google ships Gemini updates weekly and OpenAI pushes boundaries monthly, Apple is stuck in annual release cycles. In AI, that's an eternity.

The root cause isn't talent or money — Apple has plenty of both. It's structural: their closed-ecosystem, privacy-first, secrecy-driven culture is fundamentally mismatched with how AI innovation works.

AI rewards speed, data, and openness. Apple's DNA is control, privacy, and secrecy.

We broke down the 5 structural reasons Apple is losing the AI race — and what it means for the broader tech ecosystem.

CTA: Read the full analysis → [link]"""
    },

    "🏥 Healthcare — GLP-1 Drugs Are Disrupting Everything": {
        "description": "Ozempic and GLP-1 drugs aren't just treating obesity. They're reshaping airline seat economics, food industry revenue, alcohol consumption, and even addiction research. The second-order effects are massive.",
        "linkedin": """The most disruptive technology of 2024-2026 isn't AI.

It's a diabetes drug.

GLP-1 medications (Ozempic, Wegovy, Mounjaro) are reshaping industries that have nothing to do with healthcare:

Airlines are recalculating fuel costs. If passengers weigh less on average, fuel consumption drops. One airline estimated potential savings of $80M/year.

Snack companies are panicking. Walmart reported that customers on GLP-1 drugs buy measurably less food. Not different food — less food, period.

Alcohol consumption is dropping among GLP-1 users. Not because the drugs target alcohol — but because they seem to reduce compulsive behavior broadly. Researchers are now studying them for gambling and smoking addiction.

Bariatric surgery volumes are declining 15-20% at major hospital systems. A $2.5B surgical market is being disrupted by a weekly injection.

Knee replacement demand may drop. Less weight = less joint degradation. Orthopedic device companies are quietly revising long-term forecasts.

Life insurance companies are rethinking actuarial tables. If 30% of obese adults normalize their weight, mortality projections change significantly.

We're watching a single class of medication reshape the economic assumptions of at least 6 major industries simultaneously.

This is what real disruption looks like. Not a new app. A molecule.

What second-order effects of GLP-1 drugs are you watching?

#Healthcare #GLP1 #Disruption #Pharma #Innovation #SecondOrderEffects""",

        "blog": """# The GLP-1 Disruption: How a Diabetes Drug Is Reshaping Airlines, Food, Insurance, and Addiction

**The most consequential technology shift of the decade isn't happening in Silicon Valley.**

When Novo Nordisk launched semaglutide for weight management, the obvious disruption was in healthcare: fewer obesity-related diseases, declining bariatric surgery volumes, a shift from surgical to pharmaceutical weight management.

But the second-order effects are what make GLP-1 drugs arguably the most disruptive technology of the mid-2020s — and most of them have nothing to do with healthcare at all.

## Airlines: The Fuel Equation Is Changing

Passenger weight directly affects fuel consumption. Airlines have used average passenger weight assumptions in fuel calculations for decades. If GLP-1 adoption continues at current rates, average passenger weight could decrease meaningfully over the next 5-10 years.

One major carrier estimated potential annual fuel savings of $80M if average passenger weight dropped by just a few kilograms. Across the global airline industry, the implications run into billions.

## Food & Beverage: The Consumption Cliff

Walmart reported measurable decreases in food purchases among customers using GLP-1 medications. Not a shift in what they buy — a reduction in how much they buy overall.

For snack food companies built on high-frequency consumption, this is existential. If 15-20% of your core consumer base reduces consumption by 20-30%, the revenue impact is severe. Several major food companies have acknowledged GLP-1 drugs as a risk factor in investor presentations.

## The Addiction Wildcard

Perhaps the most unexpected finding: GLP-1 drugs appear to reduce compulsive behaviors beyond eating. Users report decreased alcohol consumption, reduced urge to gamble, and lower nicotine cravings.

Researchers believe this is because GLP-1 receptors exist throughout the brain's reward system, not just in appetite centers. Clinical trials are now underway for alcohol use disorder and smoking cessation.

If these trials succeed, the addressable market for GLP-1 drugs expands from obesity into addiction — a complete redefinition of what these molecules can do.

## Insurance and Longevity

Life insurance actuarial tables are built on population-level obesity and mortality data. If GLP-1 drugs meaningfully reduce obesity rates — and early data suggests they can — the entire foundation of life insurance pricing needs to be recalculated.

This affects pension funds, health insurance premiums, disability projections, and long-term care planning. The financial modeling implications alone are staggering.

**The takeaway:** GLP-1 drugs are the rare innovation that disrupts not one industry but many simultaneously. The companies and industries that recognize these second-order effects early will adapt. Those that don't will be caught off guard by a molecule they never saw as competition.""",

        "reddit": """The second-order effects of GLP-1 drugs are wild and nobody's connecting the dots

Everyone talks about Ozempic for weight loss. But the downstream economic effects are something else entirely.

A few things I've been tracking:

Airlines are recalculating fuel costs based on projected decreases in average passenger weight. One carrier estimated $80M/year in potential savings.

Walmart publicly stated that GLP-1 users are buying measurably less food. Not healthier food — just less total volume. Snack companies are listing this as a risk factor in earnings calls.

Bariatric surgery volumes are dropping 15-20% at major hospital systems. A multi-billion dollar surgical specialty is being disrupted by a weekly injection.

The weirdest one: GLP-1 users are reporting reduced alcohol consumption, gambling urges, and nicotine cravings. Turns out GLP-1 receptors are all over the brain's reward system, not just appetite centers. Clinical trials for addiction treatment are already underway.

And insurance companies are starting to rethink actuarial tables. If obesity rates drop significantly, mortality projections for entire populations change.

We might be watching a single drug class reshape the economic assumptions of 6+ industries simultaneously. Has anyone seen analysis on the orthopedic device impact? Less obesity should mean fewer knee replacements long-term.

TL;DR: GLP-1 drugs are disrupting airlines (fuel costs), food industry (less consumption), bariatric surgery (declining volumes), insurance (new actuarial models), and potentially addiction treatment. The second-order effects are more disruptive than the primary use case.""",

        "email": """Subject A: A diabetes drug is disrupting 6 industries at once
Subject B: The second-order effects nobody's modeling yet
Preview: Airlines, food, insurance, addiction — all from one molecule.

Hi [First Name],

What if the most disruptive technology of 2026 isn't AI — but a diabetes drug?

GLP-1 medications are creating second-order effects across industries that have nothing to do with healthcare. Airlines are recalculating fuel costs. Walmart reports measurably lower food purchases from GLP-1 users. Bariatric surgery volumes are dropping 15-20%.

The wildcard: these drugs appear to reduce compulsive behavior broadly — alcohol, gambling, nicotine. Clinical trials for addiction treatment are underway.

We mapped the cross-industry impact of GLP-1 adoption across 6 sectors — with the data points and projections most analysts are missing.

CTA: See the GLP-1 cross-industry impact map → [link]"""
    },

    "🏭 Manufacturing — The $200B Reshoring Blind Spot": {
        "description": "$200B+ in new US factory investments, but nobody's talking about where the skilled workers will come from. The reshoring wave has a people problem.",
        "linkedin": PREGENERATED["linkedin"],
        "blog": PREGENERATED["blog"],
        "reddit": PREGENERATED["reddit"],
        "email": PREGENERATED["email"],
    }
}


# ── Sidebar ──────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    # Check if API key is in secrets (server-side)
    _secrets_key = ""
    try:
        _secrets_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass

    if _secrets_key:
        st.success("✅ API connected", icon="🔑")
    else:
        api_key = st.text_input(
            "Claude API Key",
            type="password",
            help="Your Anthropic API key. Session only — never stored.",
            key="api_key"
        )

    st.divider()

    st.markdown("### 🏭 Context Injection")
    default_ctx = "Tell the AI about your company, product, or industry. This background gets woven into every piece of content it generates."
    context = st.text_area("What does your company do?", value=default_ctx, height=120)

    st.divider()

    st.markdown("### 📊 Output Channels")
    gen_linkedin = st.checkbox("LinkedIn Post", value=True)
    gen_blog = st.checkbox("Blog Draft", value=True)
    gen_reddit = st.checkbox("Reddit Thread", value=True)
    gen_email = st.checkbox("Email Sequence", value=True)

    st.divider()

    st.markdown("### 🎙️ Brand Voice")
    voice_enabled = st.checkbox("Enable Brand Voice Cloning", value=False,
        help="Upload writing samples to clone a specific brand voice across all outputs.")

    if voice_enabled:
        voice_input_method = st.radio("Voice samples via:", ["Paste text", "Upload file"], horizontal=True, key="voice_method")

        if voice_input_method == "Paste text":
            voice_samples = st.text_area(
                "Paste 3-5 writing samples (posts, emails, blog excerpts)",
                placeholder="Paste the CEO's LinkedIn posts, company blog excerpts, or any writing samples that represent the target voice...",
                height=150,
                key="voice_samples_text"
            )
        else:
            voice_file = st.file_uploader("Upload samples", type=["txt", "md", "pdf", "docx"], key="voice_file")
            voice_samples = ""
            if voice_file:
                file_content, err = extract_file_content(voice_file)
                if file_content:
                    voice_samples = file_content
                    st.success(f"Extracted {len(file_content.split())} words")
                elif err:
                    st.error(err)

        if voice_samples and st.button("🧬 Extract Voice DNA", key="extract_voice"):
            client = get_client()
            if client:
                with st.spinner("🧬 Analyzing writing patterns..."):
                    profile, err = extract_brand_voice(client, voice_samples)
                if profile:
                    st.session_state["voice_profile"] = profile
                    st.success("Brand voice profile extracted!")
                    with st.expander("View Voice Profile"):
                        st.markdown(f"**Summary:** {profile.get('voice_summary', 'N/A')}")
                        st.markdown(f"**Hook Pattern:** {profile.get('hook_pattern', 'N/A')}")
                        st.markdown(f"**Sentence Style:** {profile.get('sentence_style', 'N/A')}")
                        st.markdown(f"**Tone:** {profile.get('tone_markers', 'N/A')}")
                        phrases = profile.get('signature_phrases', [])
                        if phrases:
                            st.markdown(f"**Signature Phrases:** {', '.join(phrases)}")
                        st.markdown(f"**Avoids:** {profile.get('what_they_avoid', 'N/A')}")
                elif err:
                    st.error(err)
            else:
                st.warning("API key required. Add it in the sidebar or configure Streamlit Secrets.")

        if "voice_profile" in st.session_state:
            st.markdown(f"✅ **Voice loaded:** {st.session_state['voice_profile'].get('tone_markers', 'Custom')[:40]}")
            if st.button("🗑️ Clear Voice Profile", key="clear_voice"):
                del st.session_state["voice_profile"]
                st.rerun()

    st.divider()

    st.markdown("### 📈 Quality Scoring")
    enable_scoring = st.checkbox("Score generated content", value=False,
        help="After generation, each output gets a quality score (hook, readability, specificity, channel fit, CTA).")

    st.divider()

    st.markdown(
        "<div style='font-size:0.75rem; color:#94a3b8; font-family: JetBrains Mono, monospace;'>"
        "Built by Ata Okuzcuoglu<br>"
        "MSc Management & Technology @ TUM"
        "</div>",
        unsafe_allow_html=True
    )


# ── Main Content ─────────────────────────────────────────────

st.markdown("""
<div class="hero-header">
    <div class="hero-title">⚡ ContentEngine AI</div>
    <div class="hero-subtitle">
        Paste an insight, drop a URL, or upload a doc — get publish-ready content for LinkedIn, your blog, Reddit, and email. All at once.
    </div>
    <div class="hero-badge">Brand Voice Cloning · Repurpose Mode · Quality Scoring · Multi-Source Input</div>
</div>
""", unsafe_allow_html=True)

# Welcome intro
st.markdown("""
<div style="background: linear-gradient(135deg, #f0f4ff, #e8f0fe); border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; border: 1px solid #c3d4f7;">
    <div style="font-family: 'DM Sans', sans-serif; font-size: 0.95rem; color: #1e3a5f; line-height: 1.6;">
        <strong>How to use:</strong><br>
        <strong>1.</strong> <strong>Live Pipeline</strong> → paste text, a URL, or upload a file → get 4 channel-ready outputs<br>
        <strong>2.</strong> <strong>Repurpose</strong> → drop a long blog post or article → get 10 different content pieces<br>
        <strong>3.</strong> <strong>Industry Showcase</strong> → see pre-generated examples across Tech, Healthcare, Manufacturing
    </div>
</div>
""", unsafe_allow_html=True)

tab_pipeline, tab_repurpose, tab_showcase, tab_architecture = st.tabs([
    "🔧 Live Pipeline",
    "🔄 Repurpose",
    "📦 Industry Showcase",
    "🏗️ Architecture"
])


# ─── TAB 1: Live Pipeline ────────────────────────────────────
with tab_pipeline:
    st.markdown("### 📥 What's your raw material?")
    st.caption("Paste anything — a headline, a competitor's blog post, a customer quote, a trend you spotted. The pipeline turns it into content.")

    input_mode = st.radio(
        "Input method:",
        ["✍️ Write / Paste", "🔗 URL", "📄 Upload File"],
        horizontal=True,
    )

    if input_mode == "🔗 URL":
        url_input = st.text_input(
            "Article / post URL",
            placeholder="https://techcrunch.com/2026/... — any article, blog post, or news page",
        )
        if url_input:
            with st.spinner("🔗 Fetching article content..."):
                fetched_text, error = fetch_url_content(url_input)
            if error:
                st.error(error)
                insight_text = ""
            else:
                st.success(f"Extracted {len(fetched_text.split())} words from URL")
                insight_text = st.text_area(
                    "Extracted content (edit if needed):",
                    value=fetched_text,
                    height=200,
                )
        else:
            insight_text = ""

    elif input_mode == "📄 Upload File":
        uploaded = st.file_uploader(
            "Upload a document",
            type=["pdf", "txt", "md", "csv", "docx"],
            help="Supports PDF, TXT, Markdown, CSV, DOCX. Content is extracted and used as the raw insight."
        )
        if uploaded:
            with st.spinner(f"📄 Extracting content from {uploaded.name}..."):
                file_text, error = extract_file_content(uploaded)
            if error:
                st.error(error)
                insight_text = ""
            else:
                st.success(f"Extracted {len(file_text.split())} words from {uploaded.name}")
                insight_text = st.text_area(
                    "Extracted content (edit if needed):",
                    value=file_text,
                    height=200,
                )
        else:
            insight_text = ""

    else:  # Write / Paste
        insight_text = st.text_area(
            "Raw insight",
            placeholder="Paste a news headline, competitor move, customer quote, Reddit thread, press release, or any raw signal...",
            height=140,
        )

    # ── Tone & Audience Controls ──────────────────────────────
    st.markdown("---")
    st.markdown("### 🎨 How should it sound?")
    col_tone, col_audience = st.columns(2)

    with col_tone:
        selected_tone = st.selectbox(
            "Tone",
            list(TONE_OPTIONS.keys()),
            index=0,
            help="Controls the voice and style of all generated content."
        )
        tone_desc = TONE_OPTIONS[selected_tone]

    with col_audience:
        selected_audience = st.selectbox(
            "Target Audience",
            list(AUDIENCE_OPTIONS.keys()),
            index=4,  # Default: General / Mixed
            help="Adjusts complexity, jargon, and framing for the target reader."
        )
        audience_desc = AUDIENCE_OPTIONS[selected_audience]

    st.caption(f"**Tone:** {tone_desc}  \n**Audience:** {audience_desc}")

    st.markdown("---")

    channels = []
    if gen_linkedin: channels.append("linkedin")
    if gen_blog: channels.append("blog")
    if gen_reddit: channels.append("reddit")
    if gen_email: channels.append("email")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run = st.button("⚡ Run Pipeline", type="primary", use_container_width=True)
    with col_info:
        runs_left = 10 - len(st.session_state.get("run_timestamps", []))
        st.caption(f"{len(channels)} channels · ~{len(channels) * 8 + 5}s · {max(0, runs_left)} runs left today")

    # Rate limiting: 10 runs per session per day
    DAILY_LIMIT = 10
    if "run_timestamps" not in st.session_state:
        st.session_state["run_timestamps"] = []

    # Clean old timestamps (older than 24h)
    now = time.time()
    st.session_state["run_timestamps"] = [
        t for t in st.session_state["run_timestamps"] if now - t < 86400
    ]

    if run:
        if len(st.session_state["run_timestamps"]) >= DAILY_LIMIT:
            st.error(f"Daily limit reached ({DAILY_LIMIT} runs per session). Come back tomorrow or use your own API key.")
        elif not insight_text.strip():
            st.warning("Please enter a raw insight to process.")
        elif not has_api_key():
            st.warning("Please enter your Claude API key in the sidebar.")
        else:
            client = get_client()
            if client:
                st.session_state["run_timestamps"].append(time.time())
                start_time = time.time()

                # Step 1: Analysis
                with st.status("🔍 Analyzing insight...", expanded=True) as status:
                    st.write("Extracting core angle, pain points, and content hooks...")
                    analysis = analyze_insight(client, insight_text, context)

                    if analysis:
                        status.update(label="✅ Analysis complete", state="complete")
                        st.markdown(f"""
<div class="analysis-card">
    <div class="analysis-title">📊 Content Analysis</div>
    <p><strong>Core Angle:</strong> {analysis.get('core_angle', 'N/A')}</p>
    <p><strong>Audience Pain:</strong> {analysis.get('audience_pain', 'N/A')}</p>
    <p><strong>Contrarian Take:</strong> {analysis.get('contrarian_take', 'N/A')}</p>
    <p><strong>Why Now:</strong> {analysis.get('trending_relevance', 'N/A')}</p>
</div>""", unsafe_allow_html=True)
                        hooks = analysis.get('content_hooks', [])
                        if hooks:
                            st.markdown("**Content Hooks:**")
                            for h in hooks:
                                st.markdown(f"- {h}")
                    else:
                        status.update(label="⚠️ Analysis skipped — generating directly", state="complete")

                # Step 2: Generate
                st.markdown("---")
                st.markdown("### 📤 Generated Content")

                channel_labels = {
                    "linkedin": "💼 LinkedIn Post",
                    "blog": "📝 Blog Draft",
                    "reddit": "🟠 Reddit Thread",
                    "email": "📧 Email Sequence"
                }

                results = {}
                progress = st.progress(0)
                for i, ch in enumerate(channels):
                    with st.spinner(f"Generating {channel_labels[ch]}..."):
                        voice_profile = st.session_state.get("voice_profile", None) if voice_enabled else None
                        results[ch] = generate_content(client, ch, insight_text, context, tone_desc, audience_desc, voice_profile)
                    progress.progress((i + 1) / len(channels))

                elapsed = time.time() - start_time

                # Stats
                st.markdown("---")
                cols = st.columns(4)
                total_words = sum(len(v.split()) for v in results.values())
                wps = total_words / elapsed if elapsed > 0 else 0
                stats = [
                    (str(len(channels)), "Channels"),
                    (str(total_words), "Words Generated"),
                    (f"{elapsed:.1f}s", "Pipeline Time"),
                    (f"{wps:.0f}", "Words/sec")
                ]
                for col, (num, label) in zip(cols, stats):
                    with col:
                        st.markdown(f'<div class="stat-box"><div class="stat-number">{num}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

                st.markdown("---")

                # Output cards
                for ch in channels:
                    st.markdown(f'<div class="content-card"><div class="card-label">{channel_labels[ch]}</div></div>', unsafe_allow_html=True)
                    st.text_area(
                        f"{ch} output",
                        value=results[ch],
                        height=300,
                        key=f"out_{ch}",
                        label_visibility="collapsed"
                    )
                    col_dl, col_score = st.columns([1, 3])
                    with col_dl:
                        st.download_button(
                            f"📋 Download {ch}",
                            results[ch],
                            file_name=f"contentengine_{ch}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain",
                            key=f"dl_{ch}"
                        )

                # Quality scoring (optional)
                if enable_scoring:
                    st.markdown("---")
                    st.markdown("### 📈 Content Quality Scores")
                    score_progress = st.progress(0)
                    all_scores = {}
                    for i, ch in enumerate(channels):
                        with st.spinner(f"Scoring {channel_labels[ch]}..."):
                            all_scores[ch] = score_content(client, results[ch], ch)
                        score_progress.progress((i + 1) / len(channels))

                    for ch in channels:
                        scores = all_scores.get(ch)
                        if scores:
                            overall = scores.get("overall", "?")
                            # Color based on score
                            color = "#22c55e" if overall >= 7 else "#f59e0b" if overall >= 5 else "#ef4444"

                            st.markdown(f"""
<div class="content-card" style="border-left: 4px solid {color};">
    <div class="card-label">{channel_labels[ch]} — Score: {overall}/10</div>
    <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:8px;">
        <span>🪝 Hook: <strong>{scores.get('hook_strength',{}).get('score','?')}</strong></span>
        <span>📖 Read: <strong>{scores.get('readability',{}).get('score','?')}</strong></span>
        <span>🎯 Specific: <strong>{scores.get('specificity',{}).get('score','?')}</strong></span>
        <span>📱 Fit: <strong>{scores.get('channel_fit',{}).get('score','?')}</strong></span>
        <span>👆 CTA: <strong>{scores.get('cta_clarity',{}).get('score','?')}</strong></span>
    </div>
    <div style="font-size:0.9rem; color:#6366f1;"><strong>Top improvement:</strong> {scores.get('one_line_improvement','N/A')}</div>
</div>""", unsafe_allow_html=True)


# ─── TAB 2: Repurpose ────────────────────────────────────────
with tab_repurpose:
    st.markdown("""
    ### 🔄 Repurpose: One Piece → 10 Outputs

    Drop in a long blog post, article, or document. The pipeline breaks it into
    **10 platform-specific pieces** — each from a different angle, not just reformatted.
    """)

    rep_input_mode = st.radio(
        "Source content:",
        ["✍️ Paste text", "🔗 URL", "📄 Upload File"],
        horizontal=True,
        key="rep_input_mode"
    )

    rep_text = ""
    if rep_input_mode == "🔗 URL":
        rep_url = st.text_input("Article URL:", placeholder="https://...", key="rep_url")
        if rep_url:
            with st.spinner("🔗 Fetching..."):
                fetched, err = fetch_url_content(rep_url)
            if err:
                st.error(err)
            elif fetched:
                st.success(f"Extracted {len(fetched.split())} words")
                rep_text = st.text_area("Source content (edit if needed):", value=fetched, height=250, key="rep_fetched")

    elif rep_input_mode == "📄 Upload File":
        rep_file = st.file_uploader("Upload source content:", type=["pdf", "txt", "md", "csv", "docx"], key="rep_file")
        if rep_file:
            with st.spinner(f"📄 Extracting from {rep_file.name}..."):
                file_text, err = extract_file_content(rep_file)
            if err:
                st.error(err)
            elif file_text:
                st.success(f"Extracted {len(file_text.split())} words")
                rep_text = st.text_area("Source content (edit if needed):", value=file_text, height=250, key="rep_file_text")
    else:
        rep_text = st.text_area(
            "Paste your long-form content:",
            placeholder="Paste a full blog post, article, whitepaper section, newsletter, or any long-form content you want to break into pieces...",
            height=250,
            key="rep_paste"
        )

    if st.button("🔄 Repurpose into 10 Pieces", type="primary", use_container_width=True, key="rep_run"):
        if not rep_text.strip():
            st.warning("Please add some source content first.")
        elif not has_api_key():
            st.warning("API key required.")
        elif len(st.session_state.get("run_timestamps", [])) >= 10:
            st.error("Daily limit reached. Come back tomorrow.")
        else:
            client = get_client()
            if client:
                st.session_state["run_timestamps"] = st.session_state.get("run_timestamps", [])
                st.session_state["run_timestamps"].append(time.time())

                with st.status("🔄 Breaking content into 10 pieces...", expanded=True) as status:
                    st.write("Analyzing source content...")
                    st.write("Extracting different angles and insights...")
                    st.write("Generating platform-specific pieces...")
                    result, err = repurpose_content(client, rep_text, context)

                    if err:
                        status.update(label="❌ Error", state="error")
                        st.error(err)
                    elif result:
                        status.update(label=f"✅ Generated {len(result.get('pieces', []))} pieces", state="complete")

                st.markdown("---")

                if result:
                    st.markdown(f"**Source:** {result.get('title_summary', 'Content repurposed')}")
                    st.markdown(f"**Pieces generated:** {len(result.get('pieces', []))}")
                    st.markdown("---")

                    # Format icons
                    format_icons = {
                        "linkedin": "💼", "twitter": "🐦", "blog": "📝",
                        "email": "📧", "reddit": "🟠", "carousel": "🎠",
                        "newsletter": "📰", "quote": "💬",
                    }

                    for i, piece in enumerate(result.get("pieces", []), 1):
                        label = piece.get("label", f"Piece {i}")
                        fmt = piece.get("format", "")
                        content = piece.get("content", "")

                        # Get icon
                        icon = "📄"
                        for key, ic in format_icons.items():
                            if key in fmt.lower():
                                icon = ic
                                break

                        st.markdown(f'<div class="content-card"><div class="card-label">{icon} {label}</div></div>', unsafe_allow_html=True)

                        # Use appropriate mockup for known formats
                        if "linkedin" in fmt.lower():
                            st.markdown(render_linkedin_mockup(content), unsafe_allow_html=True)
                        elif "reddit" in fmt.lower():
                            st.markdown(render_reddit_mockup(content), unsafe_allow_html=True)
                        elif "email" in fmt.lower():
                            st.markdown(render_email_mockup(content), unsafe_allow_html=True)
                        elif "blog" in fmt.lower():
                            st.markdown(render_blog_mockup(content), unsafe_allow_html=True)
                        else:
                            # Generic card for other formats
                            safe_content = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                            st.markdown(f"""
<div style="background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:1.25rem; margin:0.5rem 0; font-size:0.9rem; line-height:1.7; white-space:pre-wrap; color:#374151;">
{safe_content}
</div>""", unsafe_allow_html=True)

                        with st.expander("📋 Copy raw text"):
                            st.text_area(f"piece_{i}", value=content, height=150, key=f"rep_piece_{i}", label_visibility="collapsed")
                            st.download_button(f"Download", content, file_name=f"repurposed_{fmt}.txt", key=f"dl_rep_{i}")

                    # Download all
                    st.markdown("---")
                    all_content = "\n\n" + "="*60 + "\n\n"
                    all_content = all_content.join([
                        f"[{p.get('label', f'Piece {i}')}]\n\n{p.get('content', '')}"
                        for i, p in enumerate(result.get("pieces", []), 1)
                    ])
                    st.download_button(
                        "📦 Download All 10 Pieces",
                        all_content,
                        file_name=f"repurposed_all_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        type="primary",
                        use_container_width=True,
                        key="dl_rep_all"
                    )


# ─── TAB 3: Industry Showcase ─────────────────────────────────
with tab_showcase:
    st.markdown("""
    ### 📦 See It in Action

    Pick an industry. See how one raw insight turns into a LinkedIn post, blog article,
    Reddit thread, and email — each written for its platform. Ready to publish.
    """)

    selected_demo = st.selectbox(
        "Pick an industry:",
        list(SHOWCASE_DEMOS.keys()),
        key="showcase_selector"
    )

    demo_data = SHOWCASE_DEMOS[selected_demo]

    st.markdown(f"**The insight:** {demo_data['description']}")
    st.markdown("---")

    showcase_channels = [
        ("💼 LINKEDIN POST", "linkedin"),
        ("📝 BLOG DRAFT", "blog"),
        ("🟠 REDDIT THREAD", "reddit"),
        ("📧 EMAIL SEQUENCE", "email"),
    ]

    for label, key in showcase_channels:
        st.markdown(f'<div class="card-label">{label}</div>', unsafe_allow_html=True)
        renderer = MOCKUP_RENDERERS.get(key)
        if renderer:
            st.markdown(renderer(demo_data[key]), unsafe_allow_html=True)
        with st.expander("📋 View raw text / copy"):
            st.text_area(f"sc_{key}_{selected_demo[:4]}", value=demo_data[key], height=250, key=f"sc_{key}_{hash(selected_demo) % 10000}", label_visibility="collapsed")
            st.download_button(f"Copy {key}", demo_data[key], file_name=f"showcase_{key}.txt", key=f"dl_sc_{key}_{hash(selected_demo) % 10000}")
        st.markdown("---")

    st.info("💡 **Same insight, 4 platforms, different voice each time.** Switch industries above to compare. Then try it yourself in the Live Pipeline tab.")


# ─── TAB 4: Architecture ─────────────────────────────────────
with tab_architecture:
    st.markdown("""
    ### 🏗️ How ContentEngine Works

    A **structured pipeline** with domain-specific prompt engineering,
    brand voice cloning, and multi-source content extraction.
    """)

    st.markdown("---")

    st.markdown("#### Pipeline Flow")
    st.code("""
    ┌─────────────────┐
    │     INPUTS       │
    │                  │
    │  ✍️ Text/Paste    │     ┌──────────────┐     ┌─────────────────────┐
    │  🔗 URL Import   │────→│   ANALYSIS   │────→│  PARALLEL GENERATE  │
    │  📄 PDF Upload   │     │  (AI layer)  │     │  + Tone & Audience  │
    │  📎 DOCX/CSV     │     └──────────────┘     │                     │
    │  📦 Demo         │           │               │  ├─ LinkedIn Post    │
    └─────────────────┘      Extracts:            │  ├─ Blog Draft       │
                              · Core angle         │  ├─ Reddit Thread    │
              ┌───────┐       · Pain point         │  └─ Email Sequence   │
              │ TONE  │       · Contrarian take     └─────────────────────┘
              │ CTRL  │       · Content hooks                │
              └───┬───┘       · Channel ranking        ┌─────┴─────┐
              ┌───┴────┐                               │  4 OUTPUTS │
              │AUDIENCE │                              │  < 60 sec  │
              │  CTRL   │                              └───────────┘
              └────────┘
    """, language=None)

    st.markdown("---")

    st.markdown("#### Prompt-and-Pray vs. Pipeline")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **❌ Prompt-and-Pray**
        - Open ChatGPT
        - "Write me a LinkedIn post"
        - Get generic output
        - Manually rewrite for other channels
        - No brand voice consistency
        - No quality feedback loop
        """)
    with col2:
        st.markdown("""
        **✅ ContentEngine Pipeline**
        - Multi-source input (text, URL, PDF, DOCX)
        - Brand Voice Cloning from samples
        - Tone + Audience controls per run
        - Format-specific prompt per channel
        - Auto quality scoring (5 dimensions)
        - One insight → consistent narrative × 4
        """)

    st.markdown("---")

    st.markdown("#### Technical Stack")
    st.markdown("""
    | Layer | Detail |
    |---|---|
    | **Model** | Claude Sonnet 4 (`claude-sonnet-4-20250514`) |
    | **Prompt Architecture** | 5-layer: System + Format + Context + Voice + Tone/Audience |
    | **Brand Voice** | Extract voice DNA from writing samples → inject into all generations |
    | **Quality Scoring** | 5-dimension scoring (hook, readability, specificity, channel fit, CTA) |
    | **Input Sources** | Text, URL (BeautifulSoup), PDF (PyPDF2), DOCX (python-docx), CSV |
    | **Anti-fluff System** | Rules at system prompt level — no buzzwords without data |
    | **Extensibility** | New channel = new format prompt + 15 minutes of work |
    | **Deployment** | Streamlit Cloud — zero-config, shareable link |
    """)

    st.markdown("---")

    st.markdown("#### Scaling Roadmap")
    st.markdown("""
    **v3 — Monitoring Layer** → RSS feeds from industry news, competitor blog monitors,
    Reddit/HN keyword alerts → auto-surface insights for human review

    **v4 — Workflow Integration** → HubSpot API (email sequences), Buffer (social scheduling),
    Slack notifications (content ready for review), content calendar auto-population

    **v5 — Performance Loop** → Track insight → content → engagement, feed performance data
    back into prompt optimization, A/B test system prompts based on channel metrics
    """)

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#94a3b8; font-size:0.85rem; padding:1rem;'>"
        "Built by <strong>Ata Okuzcuoglu</strong> · MSc Management & Technology @ TUM · "
        "<a href='https://linkedin.com/in/atakzcgl' style='color:#6366f1;'>LinkedIn</a>"
        "</div>",
        unsafe_allow_html=True
    )
