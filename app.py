"""
ContentEngine AI — Multi-Format Content Pipeline
Built by Ata Okuzcuoglu — Full-stack AI content operations system.

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

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Prompt Templates ─────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert content strategist who creates high-impact, channel-native content.
You adapt to ANY industry, company, or topic based on the context provided.

Your strengths:
- You write for busy decision-makers who are skeptical of hype
- You understand the difference between LinkedIn tone, blog structure, Reddit peer-talk, and email nurture
- You extract the most interesting angle from any raw material — even if the source is messy or off-topic

CRITICAL RULES:
- NEVER comment on the input. NEVER say "I notice the content is about..." or "This appears to be..."
- ALWAYS produce the requested content format. No exceptions. No meta-commentary.
- If the input is in a different language, still produce content in English (unless instructed otherwise)
- If the input seems unrelated to the company context, find the best angle and create compelling content anyway
- Never use buzzwords without substance
- Every claim should be backed by a specific example or data point
- Be contrarian when appropriate — challenge conventional wisdom
- Your output is ONLY the content itself. No explanations, no preamble, no "Here's your post:" """

FORMAT_PROMPTS = {
    "linkedin": """Create a LinkedIn post based on this insight. Requirements:
- Hook in the first line (pattern interrupt — question, bold claim, or surprising stat)
- 150-250 words max
- Use line breaks for readability (LinkedIn format)
- End with a question or call-to-action that invites discussion
- Include 3-5 relevant hashtags at the end
- Tone: thought leadership, not salesy
- NO emojis in the body text. Professional tone.
- NEVER comment on the input quality. Just create great content.

Tone guidance: {tone}
Audience: {audience}

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
- NEVER comment on the input. NEVER say "I notice..." — just write the blog post.

Tone guidance: {tone}
Audience: {audience}

Raw insight: {insight}

Industry context: {context}

Return ONLY the full blog post with headline. No preamble.""",

    "reddit": """Create a Reddit post based on this insight. Requirements:
- Title that feels native to Reddit (not promotional)
- 100-200 word body that shares a genuine observation or question
- Conversational, peer-to-peer tone
- Ask for input from the community
- NO company mentions — this is thought leadership, not promotion
- Feel like an industry insider sharing something interesting
- Include a TL;DR at the end
- NEVER explain yourself. Just write the Reddit post.

Tone guidance: {tone}
Audience: {audience}

Raw insight: {insight}

Industry context: {context}

Return the title on the first line, then a blank line, then the body. Nothing else.""",

    "email": """Create a nurture email (1 email) based on this insight. Requirements:
- Subject line (A/B test: give 2 options)
- Preview text (40-90 chars)
- 100-150 word body
- One clear CTA (not hard sell)
- Tone: helpful peer, not vendor
- NEVER comment on the input. NEVER say "I notice the content is about..." — just write the email.

Tone guidance: {tone}
Audience: {audience}

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
    "audience_pain": "What pain point does this address for the target audience?",
    "contrarian_take": "What's the non-obvious perspective here?",
    "content_hooks": ["hook1", "hook2", "hook3"],
    "trending_relevance": "Why does this matter RIGHT NOW?",
    "suggested_channels": ["ranked list of best channels for this content"]
}}

CRITICAL: Even if the input is in another language or seems unusual, ALWAYS extract the best content angle. Never refuse.

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


# ── SEO Readiness Analysis (Pure Python — zero cost) ─────────

import re
import math
from collections import Counter

def calculate_flesch_kincaid(text):
    """Calculate Flesch-Kincaid readability grade level."""
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    words = text.split()
    if not sentences or not words:
        return 0, 0

    syllable_count = 0
    for word in words:
        word = word.lower().strip(".,!?;:'\"()-")
        if not word:
            continue
        # Simple syllable counter
        count = 0
        vowels = "aeiouy"
        if word[0] in vowels:
            count += 1
        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count = 1
        syllable_count += count

    num_sentences = len(sentences)
    num_words = len(words)

    # Flesch Reading Ease
    ease = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllable_count / num_words)
    # Flesch-Kincaid Grade Level
    grade = 0.39 * (num_words / num_sentences) + 11.8 * (syllable_count / num_words) - 15.59

    return round(max(0, min(100, ease)), 1), round(max(0, grade), 1)


def extract_keywords(text, top_n=10):
    """Extract top keywords by frequency (excluding stop words)."""
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "shall", "it", "its", "this",
        "that", "these", "those", "i", "you", "he", "she", "we", "they", "them",
        "their", "my", "your", "his", "her", "our", "not", "no", "if", "when",
        "what", "which", "who", "how", "where", "why", "all", "each", "every",
        "both", "few", "more", "most", "other", "some", "such", "than", "too",
        "very", "just", "about", "also", "into", "over", "after", "before",
        "between", "through", "during", "without", "again", "further", "then",
        "once", "here", "there", "so", "as", "up", "out", "off", "down", "only",
        "own", "same", "don", "now", "s", "t", "re", "ve", "ll", "d", "m",
    }
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in stop_words]
    counter = Counter(filtered)
    return counter.most_common(top_n)


def analyze_heading_structure(text):
    """Analyze heading hierarchy in blog content."""
    lines = text.strip().split("\n")
    headings = []
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            headings.append(("H1", line.lstrip("# ")))
        elif line.startswith("## "):
            headings.append(("H2", line.lstrip("## ")))
        elif line.startswith("### "):
            headings.append(("H3", line.lstrip("### ")))

    issues = []
    h1_count = sum(1 for h in headings if h[0] == "H1")
    h2_count = sum(1 for h in headings if h[0] == "H2")

    if h1_count == 0:
        issues.append("Missing H1 headline")
    elif h1_count > 1:
        issues.append(f"Multiple H1s ({h1_count}) — use only one")
    if h2_count == 0:
        issues.append("No H2 subheadings — add 2-3 for scannability")
    elif h2_count < 2:
        issues.append("Only 1 H2 — add more for better structure")

    return headings, issues


def generate_meta_description(text, max_len=155):
    """Generate a meta description from content."""
    # Get first meaningful paragraph (skip headline)
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("**"):
            continue
        if len(line) > 50:
            # Truncate to max_len at word boundary
            if len(line) <= max_len:
                return line
            truncated = line[:max_len]
            last_space = truncated.rfind(" ")
            if last_space > 100:
                return truncated[:last_space] + "..."
            return truncated + "..."
    return text[:max_len].strip() + "..."


def seo_analyze(text, target_keyword=""):
    """Complete SEO readiness analysis for blog content."""
    words = text.split()
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    avg_sentence_len = round(word_count / max(1, len(sentences)), 1)

    reading_ease, grade_level = calculate_flesch_kincaid(text)
    keywords = extract_keywords(text)
    headings, heading_issues = analyze_heading_structure(text)
    meta_desc = generate_meta_description(text)

    # Word count assessment
    if word_count < 300:
        wc_status = "⚠️ Too short"
        wc_note = "Under 300 words — aim for 600-1500 for SEO"
    elif word_count < 600:
        wc_status = "🟡 Acceptable"
        wc_note = "Could be longer for competitive keywords"
    elif word_count <= 1500:
        wc_status = "✅ Optimal"
        wc_note = "Sweet spot for most blog content"
    else:
        wc_status = "✅ Long-form"
        wc_note = "Great for in-depth topics, ensure it stays focused"

    # Readability assessment
    if reading_ease >= 60:
        read_status = "✅ Easy to read"
    elif reading_ease >= 40:
        read_status = "🟡 Moderate"
    else:
        read_status = "⚠️ Complex"

    # Sentence length
    if avg_sentence_len <= 20:
        sent_status = "✅ Good"
    elif avg_sentence_len <= 25:
        sent_status = "🟡 Slightly long"
    else:
        sent_status = "⚠️ Too long — break up sentences"

    # Overall SEO score (0-100)
    score = 50  # base
    if 600 <= word_count <= 1500:
        score += 15
    elif 300 <= word_count < 600:
        score += 8
    if reading_ease >= 50:
        score += 15
    elif reading_ease >= 35:
        score += 8
    if len(headings) >= 3:
        score += 10
    elif len(headings) >= 2:
        score += 5
    if not heading_issues:
        score += 10
    else:
        score += max(0, 10 - len(heading_issues) * 3)

    # Target keyword analysis
    kw_data = None
    if target_keyword and target_keyword.strip():
        kw = target_keyword.strip().lower()
        text_lower = text.lower()
        kw_count = text_lower.count(kw)
        kw_density = round((kw_count / max(1, word_count)) * 100, 2)

        # Check keyword placement
        kw_in_title = any(kw in h[1].lower() for h in headings if h[0] == "H1")
        kw_in_headings = any(kw in h[1].lower() for h in headings)
        kw_in_meta = kw in meta_desc.lower()
        kw_in_first_100 = kw in " ".join(words[:100]).lower()

        # Density assessment
        if 0.5 <= kw_density <= 2.5:
            density_status = "✅ Optimal"
        elif kw_density < 0.5:
            density_status = "⚠️ Low — use keyword more"
        else:
            density_status = "⚠️ High — risk of keyword stuffing"

        # Keyword score contribution
        kw_score = 0
        if kw_count > 0: kw_score += 3
        if kw_in_title: kw_score += 5
        if kw_in_headings: kw_score += 3
        if kw_in_meta: kw_score += 2
        if kw_in_first_100: kw_score += 2
        if 0.5 <= kw_density <= 2.5: kw_score += 5
        score += kw_score

        kw_data = {
            "keyword": target_keyword.strip(),
            "count": kw_count,
            "density": kw_density,
            "density_status": density_status,
            "in_title": kw_in_title,
            "in_headings": kw_in_headings,
            "in_meta": kw_in_meta,
            "in_first_100": kw_in_first_100,
            "placement_checks": sum([kw_in_title, kw_in_headings, kw_in_meta, kw_in_first_100]),
        }

    score = min(100, max(0, score))

    return {
        "score": score,
        "word_count": word_count,
        "wc_status": wc_status,
        "wc_note": wc_note,
        "reading_ease": reading_ease,
        "grade_level": grade_level,
        "read_status": read_status,
        "avg_sentence_len": avg_sentence_len,
        "sent_status": sent_status,
        "keywords": keywords,
        "headings": headings,
        "heading_issues": heading_issues,
        "meta_description": meta_desc,
        "sentence_count": len(sentences),
        "target_keyword": kw_data,
    }


def render_seo_panel(seo_data):
    """Render SEO analysis as HTML panel."""
    score = seo_data["score"]
    color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"

    keywords_html = ", ".join([f"<strong>{kw}</strong> ({c})" for kw, c in seo_data["keywords"][:8]])
    headings_html = " → ".join([f"{h[0]}" for h in seo_data["headings"]]) if seo_data["headings"] else "<em>None found</em>"
    issues_html = " · ".join(seo_data["heading_issues"]) if seo_data["heading_issues"] else "✅ Good structure"

    # Target keyword section
    kw_section = ""
    kw = seo_data.get("target_keyword")
    if kw:
        checks = []
        checks.append(f"{'✅' if kw['in_title'] else '❌'} In title")
        checks.append(f"{'✅' if kw['in_headings'] else '❌'} In headings")
        checks.append(f"{'✅' if kw['in_first_100'] else '❌'} In first 100 words")
        checks.append(f"{'✅' if kw['in_meta'] else '❌'} In meta description")
        checks_html = " · ".join(checks)
        kw_section = f"""
    <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:10px; margin:8px 0;">
        <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#2563eb; font-weight:700; margin-bottom:6px;">🎯 Target Keyword: "{kw['keyword']}"</div>
        <div style="font-size:0.85rem; margin-bottom:4px;">Count: <strong>{kw['count']}</strong> · Density: <strong>{kw['density']}%</strong> {kw['density_status']} · Placement: <strong>{kw['placement_checks']}/4</strong></div>
        <div style="font-size:0.8rem; color:#374151;">{checks_html}</div>
    </div>"""

    return f"""
<div style="background:linear-gradient(135deg,#f8fafc,#f0f4ff); border:1px solid #c3d4f7; border-left:4px solid {color}; border-radius:12px; padding:1.25rem; margin:0.75rem 0;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; color:#4f46e5; font-weight:700;">📊 SEO Readiness Report</span>
        <span style="background:{color}; color:#fff; padding:4px 12px; border-radius:20px; font-family:'JetBrains Mono',monospace; font-size:0.85rem; font-weight:700;">{score}/100</span>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:12px; font-size:0.85rem;">
        <div><strong>Words:</strong> {seo_data['word_count']} {seo_data['wc_status']}</div>
        <div><strong>Readability:</strong> {seo_data['reading_ease']} {seo_data['read_status']}</div>
        <div><strong>Avg sentence:</strong> {seo_data['avg_sentence_len']} words {seo_data['sent_status']}</div>
    </div>{kw_section}
    <div style="font-size:0.85rem; margin-bottom:8px;">
        <strong>Top keywords:</strong> {keywords_html}
    </div>
    <div style="font-size:0.85rem; margin-bottom:8px;">
        <strong>Heading structure:</strong> {headings_html} — {issues_html}
    </div>
    <div style="background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-top:8px;">
        <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#6366f1; font-weight:700; margin-bottom:4px;">Auto-generated Meta Description</div>
        <div style="font-size:0.85rem; color:#374151; line-height:1.5;">{seo_data['meta_description']}</div>
        <div style="font-size:0.7rem; color:#9ca3af; margin-top:4px;">{len(seo_data['meta_description'])} / 155 chars</div>
    </div>
</div>"""


# ── Trend Radar ──────────────────────────────────────────────

TREND_RADAR_PROMPT = """You are a content strategist scanning for trending topics and content opportunities.

Industry/niche: {industry}
Company context: {context}

Identify 8 trending topics, news stories, or emerging conversations that a content team should write about THIS WEEK. For each, return:

{{
    "trends": [
        {{
            "title": "Short punchy title",
            "summary": "2-3 sentence explanation of the trend",
            "why_now": "Why this matters right now (timeliness)",
            "content_angles": ["angle 1", "angle 2", "angle 3"],
            "best_channels": ["linkedin", "blog", "reddit", "email"],
            "urgency": "high/medium/low",
            "sample_hook": "A ready-to-use opening line for a LinkedIn post about this"
        }}
    ]
}}

Focus on:
- Conversations already happening on LinkedIn, Reddit, and industry publications
- Competitor moves or industry shifts
- Data releases, research findings, regulatory changes
- Contrarian takes on popular narratives

Return ONLY valid JSON, no markdown formatting, no backticks."""


def scan_trends(client, industry, context):
    """Scan for trending content opportunities."""
    prompt = TREND_RADAR_PROMPT.format(industry=industry, context=context)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip()), None
    except json.JSONDecodeError:
        return None, "Failed to parse trends."
    except Exception as e:
        return None, f"Error: {str(e)[:150]}"


# ── Data-to-Content ──────────────────────────────────────────

DATA_TO_CONTENT_PROMPT = """You are a data analyst who turns raw data into compelling content insights.

Analyze this data and extract 3-5 key insights that would make great content pieces.
For each insight, explain what story the data tells and suggest a content angle.

Data:
{data}

Context about the company/industry:
{context}

Return a JSON object:
{{
    "data_summary": "Brief description of the dataset",
    "insights": [
        {{
            "insight": "The key finding in one sentence",
            "data_evidence": "The specific numbers/trends that support this",
            "story_angle": "How to frame this as a compelling narrative",
            "headline_suggestion": "A blog/LinkedIn headline for this insight",
            "target_audience": "Who cares most about this finding"
        }}
    ],
    "overall_narrative": "The overarching story this data tells"
}}

Return ONLY valid JSON, no markdown formatting, no backticks."""


def analyze_data_for_content(client, data_text, context):
    """Extract content insights from raw data."""
    prompt = DATA_TO_CONTENT_PROMPT.format(data=data_text[:4000], context=context)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip()), None
    except json.JSONDecodeError:
        return None, "Failed to parse data insights."
    except Exception as e:
        return None, f"Error: {str(e)[:150]}"


# ── Content Chain ────────────────────────────────────────────

CONTENT_CHAIN_PROMPT = """You have generated these content pieces from the same insight. 
Create a cross-linking and distribution strategy.

Content pieces:
{pieces}

Return a JSON object:
{{
    "distribution_order": ["Which piece to publish first, second, etc. with reasoning"],
    "cross_references": [
        {{
            "from": "channel name",
            "to": "channel name",
            "how": "Specific instruction on how to reference (e.g., 'In the LinkedIn post, add: Read the full analysis on our blog [link]')"
        }}
    ],
    "content_ecosystem": "How these pieces work together as a system — the narrative arc across channels",
    "timing_suggestion": "Recommended publishing schedule (e.g., Blog Monday AM, LinkedIn Monday PM, Email Tuesday)"
}}

Return ONLY valid JSON, no markdown formatting, no backticks."""


def generate_content_chain(client, results, channel_labels):
    """Generate cross-linking strategy for content pieces."""
    pieces_text = "\n\n".join([
        f"[{channel_labels.get(ch, ch)}]:\n{content[:500]}..."
        for ch, content in results.items()
    ])
    prompt = CONTENT_CHAIN_PROMPT.format(pieces=pieces_text)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip()), None
    except Exception:
        return None, "Failed to generate content chain."


# ── Carousel Builder ─────────────────────────────────────────

CAROUSEL_PROMPT = """Create a LinkedIn/Instagram carousel from this content. 
Design exactly 8 slides.

Source content:
{content}

Return a JSON object:
{{
    "slides": [
        {{
            "slide_number": 1,
            "type": "hook",
            "headline": "Bold hook text (max 8 words)",
            "body": "Supporting text (max 20 words)",
            "visual_prompt": "Image description for AI generation"
        }},
        {{
            "slide_number": 2,
            "type": "content",
            "headline": "Key point (max 8 words)",
            "body": "Explanation (max 30 words)",
            "visual_prompt": "Image description"
        }}
    ]
}}

Slide types: hook (slide 1), content (slides 2-6), stat (for data points), cta (last slide).
Make headlines punchy. Body text scannable. Each slide should work standalone but build a narrative.
Return ONLY valid JSON, no markdown formatting, no backticks."""


def generate_carousel(client, content):
    """Generate carousel slide content."""
    prompt = CAROUSEL_PROMPT.format(content=content[:3000])
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip()), None
    except json.JSONDecodeError:
        return None, "Failed to parse carousel."
    except Exception as e:
        return None, f"Error: {str(e)[:150]}"


def render_carousel_slide(slide, seed=1):
    """Render a single carousel slide as visual HTML with AI background."""
    headline = slide.get("headline", "")
    body = slide.get("body", "")
    slide_num = slide.get("slide_number", 1)
    slide_type = slide.get("type", "content")

    # Color schemes per slide type
    schemes = {
        "hook": ("linear-gradient(135deg, #1a1a2e, #16213e)", "#818cf8", "#fff"),
        "content": ("linear-gradient(135deg, #0f172a, #1e293b)", "#60a5fa", "#e2e8f0"),
        "stat": ("linear-gradient(135deg, #064e3b, #065f46)", "#34d399", "#fff"),
        "cta": ("linear-gradient(135deg, #4c1d95, #5b21b6)", "#c4b5fd", "#fff"),
    }
    bg, accent, text_color = schemes.get(slide_type, schemes["content"])

    safe_h = headline.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    safe_b = body.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    return f"""
<div style="width:100%; aspect-ratio:1/1; max-width:400px; background:{bg}; border-radius:16px; padding:2rem; display:flex; flex-direction:column; justify-content:center; position:relative; overflow:hidden; margin:0.5rem auto;">
    <div style="position:absolute; top:12px; right:16px; font-size:0.7rem; color:rgba(255,255,255,0.3); font-family:'JetBrains Mono',monospace;">{slide_num}/8</div>
    <div style="font-size:1.5rem; font-weight:800; color:{text_color}; line-height:1.2; margin-bottom:0.75rem; font-family:'DM Sans',sans-serif;">{safe_h}</div>
    <div style="font-size:0.95rem; color:rgba(255,255,255,0.7); line-height:1.5; font-family:'DM Sans',sans-serif;">{safe_b}</div>
    <div style="position:absolute; bottom:16px; left:2rem; right:2rem; height:3px; background:rgba(255,255,255,0.1); border-radius:2px;">
        <div style="width:{slide_num * 12.5}%; height:100%; background:{accent}; border-radius:2px;"></div>
    </div>
</div>"""


# ── Image Generation (Free — Pollinations.ai) ────────────────

def generate_image_url(prompt, width=1200, height=630, seed=None):
    """Generate a free AI image URL via Pollinations.ai. Falls back to placeholder."""
    import urllib.parse
    clean_prompt = prompt.strip()[:150]
    encoded = urllib.parse.quote(clean_prompt)
    # Use flux model, shorter prompts for reliability
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&model=flux&safe=true"
    if seed:
        url += f"&seed={seed}"
    return url


def get_blog_header_prompt(blog_content):
    lines = blog_content.strip().split("\n")
    headline = lines[0].lstrip("# ").strip()[:50] if lines else "Business"
    return f"minimalist blog header, abstract, blue gradient, {headline}"


def get_quote_card_prompt(quote_text):
    return "dark gradient background, navy gold, minimal, abstract"


def show_image_with_download(img_url, caption, key_suffix, filename="generated_image.png"):
    """Show AI image. Fails silently — never breaks the page."""
    try:
        st.image(img_url, caption=caption, use_container_width=True)
    except Exception:
        pass


def build_markdown_bundle(results, insight_text="", channel_labels=None):
    """Build a complete Markdown document with all generated content."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not channel_labels:
        channel_labels = {
            "linkedin": "LinkedIn Post", "blog": "Blog Draft",
            "reddit": "Reddit Thread", "email": "Email Sequence"
        }

    md = f"""# ContentEngine AI — Export Bundle
**Generated:** {now}
**Source insight:** {insight_text[:200]}{'...' if len(insight_text) > 200 else ''}

---

"""
    for ch, content in results.items():
        label = channel_labels.get(ch, ch)
        md += f"## {label}\n\n{content}\n\n---\n\n"

    return md


def build_content_calendar(results, channel_labels=None):
    """Build a simple content calendar as a Markdown table."""
    if not channel_labels:
        channel_labels = {
            "linkedin": "LinkedIn Post", "blog": "Blog Draft",
            "reddit": "Reddit Thread", "email": "Email Sequence"
        }

    now = datetime.now()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Assign each piece to a day
    channels = list(results.keys())
    cal = "# Content Calendar\n\n"
    cal += "| Day | Channel | Content Preview | Status |\n"
    cal += "|---|---|---|---|\n"

    for i, ch in enumerate(channels):
        day = days[i % len(days)]
        label = channel_labels.get(ch, ch)
        # First 80 chars as preview
        preview = results[ch][:80].replace("\n", " ").replace("|", "/") + "..."
        cal += f"| {day} | {label} | {preview} | 📝 Draft |\n"

    cal += "\n---\n\n"

    # Full content below
    cal += "## Full Content\n\n"
    for ch, content in results.items():
        label = channel_labels.get(ch, ch)
        cal += f"### {label}\n\n{content}\n\n---\n\n"

    return cal


def build_repurpose_bundle(result):
    """Build a Markdown bundle from repurpose output."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# ContentEngine AI — Repurpose Bundle
**Generated:** {now}
**Source:** {result.get('title_summary', 'Content repurposed')}
**Pieces:** {len(result.get('pieces', []))}

---

"""
    for i, piece in enumerate(result.get("pieces", []), 1):
        label = piece.get("label", f"Piece {i}")
        content = piece.get("content", "")
        md += f"## {i}. {label}\n\n{content}\n\n---\n\n"

    return md


def get_client():
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

def generate_content(client, format_type, insight, context, tone_desc="", audience_desc="", voice_profile=None, language="English", analysis=None):
    """Generate content for a single channel. Fallback if batch fails."""
    # Inject analysis into insight if available
    enriched_insight = insight
    if analysis:
        enriched_insight = f"""CONTENT ANALYSIS (use this to guide your writing):
Core angle: {analysis.get('core_angle', '')}
Audience pain: {analysis.get('audience_pain', '')}
Contrarian take: {analysis.get('contrarian_take', '')}
Hooks: {', '.join(analysis.get('content_hooks', []))}
Why now: {analysis.get('trending_relevance', '')}

RAW INSIGHT:
{insight}"""

    prompt = FORMAT_PROMPTS[format_type].format(
        insight=enriched_insight, 
        context=context,
        tone=tone_desc or "Professional thought leadership",
        audience=audience_desc or "Business decision-makers"
    )

    modifiers = ""
    if language and language != "English":
        modifiers += f"\n\nCRITICAL: Write the ENTIRE output in {language}. All text, headlines, hashtags, CTAs — everything in {language}."

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
Signature phrases to use naturally: {sig_phrases}
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
        return f"Error: {str(e)[:200]}"


BATCH_PROMPT = """Generate content for ALL 4 channels from this single insight.
Use the analysis below to ensure consistent messaging across all outputs.

CONTENT ANALYSIS:
Core angle: {core_angle}
Audience pain: {audience_pain}
Contrarian take: {contrarian_take}
Hooks: {hooks}
Why now: {trending}

RAW INSIGHT:
{insight}

COMPANY/INDUSTRY CONTEXT:
{context}

TONE: {tone}
AUDIENCE: {audience}
{language_instruction}
{voice_instruction}

Generate ALL 4 pieces. Return a JSON object with exactly these keys:
{{
    "linkedin": "Full LinkedIn post (150-250 words, hook first, line breaks, 3-5 hashtags, no emojis)",
    "blog": "Full blog post (400-600 words, headline with ##, subheadings, specific examples, SEO-friendly)",
    "reddit": "Title on first line, blank line, then body (100-200 words, peer tone, no promotion, TL;DR)",
    "email": "Subject A: ...\\nSubject B: ...\\nPreview: ...\\n---\\n[body 100-150 words]\\nCTA: ..."
}}

CRITICAL RULES:
- Use the analysis to maintain consistent narrative across all 4 pieces
- Each piece MUST be channel-native (LinkedIn ≠ Reddit ≠ Blog ≠ Email)
- NEVER comment on the input. Just produce the content.
- Return ONLY valid JSON. No markdown backticks. No preamble."""


def generate_batch(client, insight, context, analysis, tone_desc="", audience_desc="", voice_profile=None, language="English"):
    """Generate all 4 channels in a single API call. ~60% cheaper than 4 separate calls."""
    lang_instruction = ""
    if language and language != "English":
        lang_instruction = f"CRITICAL: Write ALL content in {language}."

    voice_instruction = ""
    if voice_profile:
        voice_instruction = f"""BRAND VOICE (match exactly):
{voice_profile.get('voice_summary', '')}
Hook pattern: {voice_profile.get('hook_pattern', '')}
Sentence style: {voice_profile.get('sentence_style', '')}
Signature phrases: {', '.join(voice_profile.get('signature_phrases', []))}
Avoid: {voice_profile.get('what_they_avoid', '')}"""

    prompt = BATCH_PROMPT.format(
        core_angle=analysis.get('core_angle', 'N/A') if analysis else 'N/A',
        audience_pain=analysis.get('audience_pain', 'N/A') if analysis else 'N/A',
        contrarian_take=analysis.get('contrarian_take', 'N/A') if analysis else 'N/A',
        hooks=', '.join(analysis.get('content_hooks', [])) if analysis else 'N/A',
        trending=analysis.get('trending_relevance', 'N/A') if analysis else 'N/A',
        insight=insight[:3000],
        context=context[:500],
        tone=tone_desc or "Professional thought leadership",
        audience=audience_desc or "Business decision-makers",
        language_instruction=lang_instruction,
        voice_instruction=voice_instruction,
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip()), None
    except json.JSONDecodeError:
        return None, "batch_parse_error"
    except Exception as e:
        return None, f"Error: {str(e)[:200]}"


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
    except Exception:
        return None


def render_linkedin_mockup(content):
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""
<div style="background:#fff; border:1px solid #e0e0e0; border-radius:8px; overflow:hidden; margin:1rem 0; font-family:-apple-system,system-ui,sans-serif;">
    <div style="padding:12px 16px; display:flex; align-items:center; gap:10px;">
        <div style="width:48px; height:48px; border-radius:50%; background:linear-gradient(135deg,#0a66c2,#004182); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:18px; flex-shrink:0;">CE</div>
        <div>
            <div style="font-weight:600; color:#000; font-size:0.9rem;">ContentEngine AI</div>
            <div style="color:#666; font-size:0.75rem;">Generated via Pipeline · Just now</div>
        </div>
    </div>
    <div style="padding:0 16px 16px; font-size:0.9rem; line-height:1.6; color:#333; white-space:pre-wrap;">{safe}</div>
    <div style="padding:8px 16px; border-top:1px solid #e0e0e0; display:flex; justify-content:space-around; color:#666; font-size:0.8rem;">
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
<div style="background:#fff; border:1px solid #ccc; border-radius:4px; overflow:hidden; margin:1rem 0; font-family:-apple-system,system-ui,sans-serif;">
    <div style="display:flex;">
        <div style="background:#f8f9fa; padding:8px; display:flex; flex-direction:column; align-items:center; gap:4px; min-width:40px;">
            <span style="color:#878a8c; font-size:0.75rem;">▲</span>
            <span style="color:#1a1a1b; font-weight:700; font-size:0.85rem;">247</span>
            <span style="color:#878a8c; font-size:0.75rem;">▼</span>
        </div>
        <div style="padding:8px 12px; flex:1;">
            <div style="font-size:0.75rem; color:#787c7e; margin-bottom:4px;"><strong style="color:#1c1c1c;">r/marketing</strong> · Posted by u/contentengine · 2h</div>
            <div style="font-size:1.1rem; font-weight:600; color:#1a1a1b; margin-bottom:8px;">{safe_t}</div>
            <div style="font-size:0.9rem; line-height:1.5; color:#1a1a1b; white-space:pre-wrap;">{safe_b}</div>
        </div>
    </div>
    <div style="padding:4px 12px 8px; font-size:0.75rem; color:#878a8c; display:flex; gap:12px;">
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
<div style="background:#fff; border:1px solid #dadce0; border-radius:8px; overflow:hidden; margin:1rem 0; font-family:-apple-system,system-ui,sans-serif; max-width:600px;">
    <div style="background:#f2f2f2; padding:8px 16px; font-size:0.8rem; color:#5f6368; border-bottom:1px solid #dadce0;">
        📥 Inbox → <span style="color:#202124; font-weight:600;">ContentEngine</span>
    </div>
    <div style="padding:12px 16px; font-size:1rem; font-weight:600; color:#202124; border-bottom:1px solid #f0f0f0;">{safe_s}</div>
    <div style="padding:8px 16px; font-size:0.8rem; color:#5f6368;">From: content@company.com · To: [First Name] · Now</div>
    <div style="padding:16px; font-size:0.9rem; line-height:1.7; color:#202124; white-space:pre-wrap;">{safe}</div>
</div>"""


def render_blog_mockup(content):
    import re
    lines = content.strip().split("\n")
    headline = lines[0].lstrip("# ").strip() if lines else "Untitled"
    body_lines = lines[1:]

    html_parts = []
    for line in body_lines:
        line = line.strip()
        if not line:
            html_parts.append("<br>")
            continue
        if line.startswith("## "):
            text = line.lstrip("# ").strip()
            text = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            html_parts.append(f'<h3 style="font-size:1.1rem; font-weight:700; color:#1a1a2e; margin:20px 0 8px;">{text}</h3>')
            continue
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
        safe_line = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        safe_line = safe_line.replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
        safe_line = safe_line.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
        html_parts.append(f'<p style="margin:0 0 8px;">{safe_line}</p>')

    body_html = "\n".join(html_parts)
    safe_h = headline.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    word_count = len(content.split())
    read_min = max(1, word_count // 200)

    return f"""
<div style="background:#fff; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; margin:1rem 0; font-family:Georgia,serif;">
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e); padding:24px;">
        <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:2px; color:#818cf8; margin-bottom:8px; font-family:sans-serif;">Insights</div>
        <div style="font-size:1.4rem; font-weight:700; color:#fff; line-height:1.3;">{safe_h}</div>
        <div style="font-size:0.8rem; color:rgba(255,255,255,0.5); margin-top:12px; font-family:sans-serif;">ContentEngine AI · {read_min} min read</div>
    </div>
    <div style="padding:24px; font-size:0.95rem; line-height:1.8; color:#374151;">{body_html}</div>
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
    except Exception:
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

# ── Pre-generated showcase content ─────────────────────────

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

CTA: Read the full analysis → [link]""",
        "carousel_slides": [
            {"slide_number": 1, "type": "hook", "headline": "Apple spent $100B on R&D", "body": "Their AI summarized a headline so badly it made global news."},
            {"slide_number": 2, "type": "content", "headline": "The Control Paradox", "body": "Apple's closed ecosystem built the most profitable tech company. But AI rewards speed, data, and openness."},
            {"slide_number": 3, "type": "stat", "headline": "Google: weekly updates", "body": "OpenAI: monthly breakthroughs. Apple: annual releases. In AI, annual = geological."},
            {"slide_number": 4, "type": "content", "headline": "The Data Problem", "body": "Google processes billions of queries daily. Apple deliberately doesn't access equivalent user data. Privacy is noble — but it's a training data disadvantage."},
            {"slide_number": 5, "type": "content", "headline": "Open vs. Closed", "body": "Meta open-sourced Llama. Google open-sourced Gemma. The biggest AI breakthroughs come from open research. Apple's secrecy culture is the opposite."},
            {"slide_number": 6, "type": "stat", "headline": "2-3 years behind", "body": "Not a temporary setback. A structural mismatch between Apple's DNA and what AI demands."},
            {"slide_number": 7, "type": "content", "headline": "The Real Question", "body": "Can the closed-ecosystem model survive the AI era at all? Or will the intelligence layer be built entirely in the open?"},
            {"slide_number": 8, "type": "cta", "headline": "What's your take?", "body": "Can Apple adapt, or is this a fundamental disadvantage? Comment below."},
        ],
        "distribution": {
            "timing": "Blog Monday 8AM → LinkedIn Monday 12PM → Reddit Tuesday 9AM → Email Wednesday 7AM",
            "order": ["Blog first (SEO anchor + most detail)", "LinkedIn same day (drive traffic to blog)", "Reddit next day (separate audience, peer discussion)", "Email mid-week (nurture sequence, link to blog)"],
            "cross_refs": [
                {"from": "LinkedIn", "to": "Blog", "how": "End LinkedIn post with: 'Full analysis on our blog → [link]'"},
                {"from": "Email", "to": "Blog", "how": "CTA button links directly to blog post"},
                {"from": "Reddit", "to": "None", "how": "No links — pure thought leadership, build credibility"},
            ],
            "ecosystem": "Blog is the hub. LinkedIn drives professional traffic. Reddit builds community credibility. Email nurtures existing audience. Four pieces, one narrative arc."
        }
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

CTA: See the GLP-1 cross-industry impact map → [link]""",
        "carousel_slides": [
            {"slide_number": 1, "type": "hook", "headline": "Not AI. A diabetes drug.", "body": "The most disruptive technology of 2024-2026 is a molecule, not software."},
            {"slide_number": 2, "type": "stat", "headline": "Airlines: $80M/year savings", "body": "If passengers weigh less, fuel costs drop. One carrier ran the numbers."},
            {"slide_number": 3, "type": "content", "headline": "Walmart: less food sold", "body": "GLP-1 users buy measurably less food. Not different food — less, period. Snack companies are panicking."},
            {"slide_number": 4, "type": "stat", "headline": "Surgery down 15-20%", "body": "Bariatric surgery volumes declining at major hospital systems. A $2.5B market disrupted by a weekly injection."},
            {"slide_number": 5, "type": "content", "headline": "The addiction wildcard", "body": "Users report less alcohol, gambling, nicotine cravings. GLP-1 receptors exist throughout the brain's reward system."},
            {"slide_number": 6, "type": "content", "headline": "Insurance rethinks everything", "body": "If 30% of obese adults normalize weight, mortality projections change. Actuarial tables need rewriting."},
            {"slide_number": 7, "type": "stat", "headline": "6+ industries disrupted", "body": "Airlines, food, surgery, insurance, orthopedics, addiction treatment. All from one drug class."},
            {"slide_number": 8, "type": "cta", "headline": "What effects are you watching?", "body": "Which second-order GLP-1 impact surprises you most?"},
        ],
        "distribution": {
            "timing": "Blog Monday 8AM → LinkedIn Monday 2PM → Email Tuesday 8AM → Reddit Wednesday 10AM",
            "order": ["Blog first (comprehensive analysis, SEO value)", "LinkedIn same day afternoon (data-heavy hook)", "Email next morning (drives blog traffic)", "Reddit mid-week (community discussion, no promotion)"],
            "cross_refs": [
                {"from": "LinkedIn", "to": "Blog", "how": "Link to full cross-industry analysis in first comment"},
                {"from": "Email", "to": "Blog", "how": "CTA: 'See the full GLP-1 impact map'"},
                {"from": "Reddit", "to": "None", "how": "Pure discussion — ask community for their observations"},
            ],
            "ecosystem": "Blog is the definitive resource. LinkedIn captures the stat-driven professional audience. Email nurtures subscribers with exclusive framing. Reddit generates authentic discussion and surfaces angles you missed."
        }
    },

    "🏭 Manufacturing — The $200B Reshoring Blind Spot": {
        "description": "$200B+ in new US factory investments, but nobody's talking about where the skilled workers will come from. The reshoring wave has a people problem.",
        "linkedin": PREGENERATED["linkedin"],
        "blog": PREGENERATED["blog"],
        "reddit": PREGENERATED["reddit"],
        "email": PREGENERATED["email"],
        "carousel_slides": [
            {"slide_number": 1, "type": "hook", "headline": "$200 billion blind spot", "body": "Everyone's celebrating reshoring. Nobody's asking: who's going to run these factories?"},
            {"slide_number": 2, "type": "stat", "headline": "2.1M jobs unfilled by 2030", "body": "Deloitte's projection was calculated BEFORE the current construction boom."},
            {"slide_number": 3, "type": "content", "headline": "No veterans to shadow", "body": "Greenfield factories have zero institutional knowledge. No 'ask Bob, he's been here 30 years.'"},
            {"slide_number": 4, "type": "content", "headline": "Old model is broken", "body": "6-month apprenticeships don't work when average tenure is under 3 years."},
            {"slide_number": 5, "type": "content", "headline": "Digital-first beats train-first", "body": "Embed knowledge in the workflow, not the worker's memory. Real-time guidance on the shop floor."},
            {"slide_number": 6, "type": "stat", "headline": "12 weeks → 3 weeks", "body": "One auto supplier cut onboarding by 75% with digital guidance. Quality defects down 25%."},
            {"slide_number": 7, "type": "content", "headline": "Greenfield advantage", "body": "No legacy systems. No resistance. Build digital-first from day one."},
            {"slide_number": 8, "type": "cta", "headline": "How are you handling it?", "body": "How is your factory solving knowledge transfer to new workers?"},
        ],
        "distribution": {
            "timing": "Blog Tuesday 8AM → LinkedIn Tuesday 1PM → Reddit Thursday 10AM → Email Friday 8AM",
            "order": ["Blog first (in-depth analysis with data)", "LinkedIn same day (reshoring narrative hook)", "Reddit two days later (peer discussion with plant managers)", "Email end of week (nurture with case study link)"],
            "cross_refs": [
                {"from": "LinkedIn", "to": "Blog", "how": "First comment: 'Full analysis with the Deloitte data → [blog link]'"},
                {"from": "Email", "to": "Blog", "how": "CTA: 'See how leading manufacturers are solving this'"},
                {"from": "Reddit", "to": "None", "how": "Zero promotion — ask genuine question, build credibility"},
            ],
            "ecosystem": "Blog establishes thought leadership with data. LinkedIn captures executive attention with the $200B hook. Reddit validates with practitioner community. Email converts interested readers to pipeline."
        }
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

    st.markdown("### 🧠 Knowledge Base")
    with st.expander("Company context (woven into every output)", expanded=False):
        kb_company = st.text_input("Company name:", placeholder="e.g., Workerbase, Zalando, your startup...", key="kb_company")
        kb_industry = st.text_input("Industry:", placeholder="e.g., Manufacturing SaaS, Fashion e-commerce, Fintech...", key="kb_industry")
        kb_product = st.text_area("What you do (1-2 sentences):", placeholder="e.g., Connected worker platform used in 60+ factories", height=68, key="kb_product")
        kb_audience = st.text_input("Target audience:", placeholder="e.g., Plant managers, VP Operations, CMOs...", key="kb_audience")
        kb_competitors = st.text_input("Competitors:", placeholder="e.g., Poka, Tulip, Augmentir", key="kb_competitors")
        kb_differentiator = st.text_input("Key differentiator:", placeholder="e.g., Real-time worker guidance, not just dashboards", key="kb_diff")

    # Assemble structured context
    context_parts = []
    if kb_company:
        context_parts.append(f"Company: {kb_company}")
    if kb_industry:
        context_parts.append(f"Industry: {kb_industry}")
    if kb_product:
        context_parts.append(f"Product: {kb_product}")
    if kb_audience:
        context_parts.append(f"Target audience: {kb_audience}")
    if kb_competitors:
        context_parts.append(f"Competitors: {kb_competitors}")
    if kb_differentiator:
        context_parts.append(f"Differentiator: {kb_differentiator}")

    if context_parts:
        context = "\n".join(context_parts)
    else:
        context = "General content — no specific company context provided."

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

    st.markdown("### 🌍 Output Language")
    output_lang = st.selectbox("Generate content in:", 
        ["English", "German (Deutsch)", "Turkish (Türkçe)", "Spanish (Español)", "French (Français)", "Same as input"],
        index=0, key="output_lang",
        help="All generated content will be in this language, regardless of input language.")

    st.divider()

    st.markdown("### 🖼️ AI Visuals")
    enable_images = st.checkbox("Generate images (experimental)", value=False,
        help="Auto-generate blog headers and visual assets via Pollinations.ai. Free but may be slow or unavailable.")

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
    <div class="hero-badge">Trend Radar · Pipeline · Repurpose · Data→Content · Voice Cloning · SEO · Carousel · AI Visuals</div>
</div>
""", unsafe_allow_html=True)

# Dynamic onboarding — detailed for first-time users, minimal for returning
is_first_run = "content_history" not in st.session_state or len(st.session_state.get("content_history", [])) == 0

if is_first_run:
    st.markdown("""
<div style="background: linear-gradient(135deg, #f0f4ff, #e8f0fe); border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; border: 1px solid #c3d4f7;">
    <div style="font-size: 0.95rem; color: #1e3a5f; line-height: 1.7;">
        <strong>👋 Welcome! Here's how to get started:</strong><br><br>
        <strong>🚀 Quickest start:</strong> Go to the <strong>Showcase</strong> tab → pick an industry → see full demo output (no API needed)<br><br>
        <strong>Build your own:</strong><br>
        <strong>1.</strong> <strong>Pipeline</strong> → paste text, a URL, or upload a file → get LinkedIn, blog, Reddit, and email in 60 seconds<br>
        <strong>2.</strong> <strong>Repurpose</strong> → drop a long article → get 10 platform-specific pieces<br>
        <strong>3.</strong> <strong>Trend Radar</strong> → enter your industry → discover what to write about this week<br>
        <strong>4.</strong> <strong>Data → Content</strong> → upload CSV/data → AI extracts story angles<br><br>
        <strong>💡 Pro tip:</strong> Set your company context in the sidebar (left) — it gets woven into every output.
    </div>
</div>
""", unsafe_allow_html=True)
else:
    run_count = len(st.session_state.get("content_history", []))
    st.markdown(f"""
<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:8px 16px; margin-bottom:1rem; font-size:0.85rem; color:#64748b;">
    Session: {run_count} run{'s' if run_count != 1 else ''} completed · Use sidebar to configure channels, voice, and language
</div>
""", unsafe_allow_html=True)

tab_pipeline, tab_repurpose, tab_trends, tab_data, tab_showcase, tab_architecture = st.tabs([
    "🔧 Pipeline",
    "🔄 Repurpose",
    "🔍 Trend Radar",
    "📊 Data → Content",
    "📦 Showcase",
    "🏗️ How It Works"
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
        prefill = st.session_state.pop("prefill_insight", "")
        insight_text = st.text_area(
            "Raw insight",
            value=prefill if prefill else "",
            placeholder="Paste a news headline, competitor move, customer quote, Reddit thread, press release, or any raw signal...",
            height=140,
        )
        if prefill:
            st.success("✅ Insight loaded from Data → Content tab. Hit Run Pipeline!")

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

    # SEO Target Keyword (optional)
    target_keyword = st.text_input("🎯 Target keyword (optional — for SEO scoring):",
        placeholder="e.g., connected worker platform, content marketing strategy",
        key="target_kw",
        help="If provided, the SEO panel will check keyword density, placement in title/headings/meta, and adjust the SEO score.")

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
        batch_mode = len(channels) >= 3
        est_calls = 2 if batch_mode else len(channels) + 1
        est_cost = 0.02 if batch_mode else len(channels) * 0.006 + 0.003
        st.caption(f"{len(channels)} channels · {'⚡ batch' if batch_mode else 'individual'} · ~{est_calls} API calls · ~${est_cost:.3f} · {max(0, runs_left)} runs left")

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

                # Clean language value
                lang_map = {
                    "English": "English", "German (Deutsch)": "German",
                    "Turkish (Türkçe)": "Turkish", "Spanish (Español)": "Spanish",
                    "French (Français)": "French", "Same as input": ""
                }
                clean_lang = lang_map.get(output_lang, output_lang)
                voice_profile = st.session_state.get("voice_profile", None) if voice_enabled else None

                # Try batch generation first (1 API call instead of 4)
                results = {}
                batch_used = False
                if len(channels) >= 3:
                    with st.spinner("⚡ Batch generating all channels (1 API call)..."):
                        batch_results, batch_err = generate_batch(
                            client, insight_text, context, analysis,
                            tone_desc, audience_desc, voice_profile, clean_lang
                        )
                    if batch_results:
                        # Filter to only requested channels
                        for ch in channels:
                            if ch in batch_results:
                                results[ch] = batch_results[ch]
                        batch_used = True

                # Fallback: generate missing channels individually
                missing = [ch for ch in channels if ch not in results]
                if missing:
                    progress = st.progress(0)
                    for i, ch in enumerate(missing):
                        with st.spinner(f"Generating {channel_labels[ch]}..."):
                            results[ch] = generate_content(
                                client, ch, insight_text, context,
                                tone_desc, audience_desc, voice_profile,
                                language=clean_lang, analysis=analysis
                            )
                        progress.progress((i + 1) / len(missing))
                    progress.progress((i + 1) / len(channels))

                # Save results for Content Chain and Carousel (survive reruns)
                st.session_state["pipeline_results"] = results
                st.session_state["pipeline_channel_labels"] = channel_labels

                elapsed = time.time() - start_time
                total_words = sum(len(v.split()) for v in results.values())
                wps = total_words / elapsed if elapsed > 0 else 0

                # Save to content history
                history_entry = {
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "insight": insight_text[:80] + "..." if len(insight_text) > 80 else insight_text,
                    "channels": len(channels),
                    "words": total_words,
                    "time": f"{elapsed:.1f}s",
                }
                if "content_history" not in st.session_state:
                    st.session_state["content_history"] = []
                st.session_state["content_history"].append(history_entry)

                # Stats
                st.markdown("---")
                api_calls = 1 if batch_used else len(channels)  # batch = 1 + analysis, individual = N + analysis
                cols = st.columns(5)
                stats = [
                    (str(len(channels)), "Channels"),
                    (str(total_words), "Words"),
                    (f"{elapsed:.1f}s", "Time"),
                    (f"{wps:.0f}", "Words/sec"),
                    (f"{api_calls}+1", "API Calls"),
                ]
                for col, (num, label) in zip(cols, stats):
                    with col:
                        st.markdown(f'<div class="stat-box"><div class="stat-number">{num}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)
                if batch_used:
                    st.caption("⚡ Batch mode: 4 channels generated in 1 API call (analysis + generation = 2 total)")

                st.markdown("---")

                # Output cards
                for ch in channels:
                    st.markdown(f'<div class="content-card"><div class="card-label">{channel_labels[ch]}</div></div>', unsafe_allow_html=True)

                    # AI-generated header image for blog
                    if enable_images and ch == "blog":
                        img_prompt = get_blog_header_prompt(results[ch])
                        img_url = generate_image_url(img_prompt, width=1200, height=630, seed=42)
                        show_image_with_download(img_url, "🖼️ AI-generated blog header (free via Pollinations.ai)", "pipe_blog", "blog_header.png")

                    # AI-generated visual for LinkedIn
                    if enable_images and ch == "linkedin":
                        li_prompt = f"abstract data visualization, blue gradient, minimal infographic, no text"
                        li_url = generate_image_url(li_prompt, width=1200, height=627, seed=77)
                        show_image_with_download(li_url, "🖼️ AI-generated post visual (free via Pollinations.ai)", "pipe_li", "linkedin_visual.png")

                    # Render platform mockup
                    PIPELINE_RENDERERS = {
                        "linkedin": render_linkedin_mockup,
                        "blog": render_blog_mockup,
                        "reddit": render_reddit_mockup,
                        "email": render_email_mockup,
                    }
                    renderer = PIPELINE_RENDERERS.get(ch)
                    if renderer:
                        try:
                            mockup_html = renderer(results[ch])
                            if mockup_html:
                                st.markdown(mockup_html, unsafe_allow_html=True)
                        except Exception:
                            pass

                    with st.expander(f"📋 View raw text / copy {ch}"):
                        st.text_area(
                            f"{ch} output",
                            value=results[ch],
                            height=250,
                            key=f"out_{ch}",
                            label_visibility="collapsed"
                        )
                        st.download_button(
                            f"📋 Download {ch}",
                            results[ch],
                            file_name=f"contentengine_{ch}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain",
                            key=f"dl_{ch}"
                        )

                    # SEO Readiness Panel for blog content
                    if ch == "blog":
                        seo = seo_analyze(results[ch], target_keyword=target_keyword)
                        st.markdown(render_seo_panel(seo), unsafe_allow_html=True)
                        # Copyable meta description
                        with st.expander("📋 Copy meta description"):
                            st.code(seo["meta_description"], language=None)

                # ── Export All ────────────────────────────
                st.markdown("---")
                st.markdown("### 📦 Export All")

                col_md, col_cal, col_txt = st.columns(3)

                with col_md:
                    md_bundle = build_markdown_bundle(results, insight_text, channel_labels)
                    st.download_button(
                        "📄 Markdown Bundle",
                        md_bundle,
                        file_name=f"contentengine_bundle_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="dl_md_bundle"
                    )

                with col_cal:
                    cal = build_content_calendar(results, channel_labels)
                    st.download_button(
                        "🗓️ Content Calendar",
                        cal,
                        file_name=f"content_calendar_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="dl_calendar"
                    )

                with col_txt:
                    all_txt = "\n\n".join([
                        f"=== {channel_labels.get(ch, ch).upper()} ===\n\n{content}"
                        for ch, content in results.items()
                    ])
                    st.download_button(
                        "📋 Plain Text (All)",
                        all_txt,
                        file_name=f"contentengine_all_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="dl_all_txt"
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
                            color = "#22c55e" if overall >= 7 else "#f59e0b" if overall >= 5 else "#ef4444"
                            st.markdown(f"""<div style="background:#f8fafc; border:1px solid #e2e8f0; border-left:4px solid {color}; border-radius:8px; padding:1rem; margin:0.5rem 0; font-size:0.85rem;">
<strong>{channel_labels[ch]} — {overall}/10</strong> · Hook: {scores.get('hook_strength',{}).get('score','?')} · Read: {scores.get('readability',{}).get('score','?')} · Specific: {scores.get('specificity',{}).get('score','?')} · Fit: {scores.get('channel_fit',{}).get('score','?')} · CTA: {scores.get('cta_clarity',{}).get('score','?')}<br><span style="color:#6366f1;">Improve: {scores.get('one_line_improvement','N/A')}</span></div>""", unsafe_allow_html=True)

    # ── Content Chain & Carousel (OUTSIDE if run — survives Streamlit reruns) ──
    saved_results = st.session_state.get("pipeline_results", {})
    saved_labels = st.session_state.get("pipeline_channel_labels", {})

    if saved_results:
        st.markdown("---")
        st.markdown("### 🔗 Next Steps")
        col_chain, col_carousel = st.columns(2)

        with col_chain:
            if st.button("🔗 Content Chain (distribution plan)", key="gen_chain", use_container_width=True):
                client = get_client()
                if client:
                    with st.spinner("🔗 Building distribution strategy..."):
                        chain_result, chain_err = generate_content_chain(client, saved_results, saved_labels)
                    if chain_result:
                        st.session_state["chain_result"] = chain_result
                    elif chain_err:
                        st.error(chain_err)

        with col_carousel:
            if "blog" in saved_results:
                if st.button("🎠 Carousel from Blog", key="gen_carousel", use_container_width=True):
                    client = get_client()
                    if client:
                        with st.spinner("🎠 Building carousel..."):
                            car_data, car_err = generate_carousel(client, saved_results["blog"])
                        if car_data:
                            st.session_state["carousel_result"] = car_data
                        elif car_err:
                            st.error(car_err)

        # Show Content Chain result (persists across reruns)
        if "chain_result" in st.session_state:
            chain = st.session_state["chain_result"]
            st.markdown("#### 🔗 Distribution Strategy")
            st.markdown(f"""<div style="background:#f0fdf4; border:1px solid #86efac; border-radius:10px; padding:1rem; margin:0.5rem 0;">
<strong>📅 Timing:</strong> {chain.get('timing_suggestion', 'N/A')}</div>""", unsafe_allow_html=True)
            for j, step in enumerate(chain.get("distribution_order", []), 1):
                st.markdown(f"{j}. {step}")
            st.markdown("**Cross-references:**")
            for ref in chain.get("cross_references", []):
                st.markdown(f"- **{ref.get('from', '?')}** → **{ref.get('to', '?')}**: {ref.get('how', '')}")

        # Show Carousel result (persists across reruns)
        if "carousel_result" in st.session_state:
            car = st.session_state["carousel_result"]
            st.markdown("#### 🎠 Carousel Slides")
            slides = car.get("slides", [])
            for row_start in range(0, len(slides), 2):
                cols_c = st.columns(2)
                for ci, si in enumerate(range(row_start, min(row_start + 2, len(slides)))):
                    with cols_c[ci]:
                        st.markdown(render_carousel_slide(slides[si], seed=si), unsafe_allow_html=True)
            slides_text = "\n\n".join([f"SLIDE {s.get('slide_number', i)}: {s.get('headline', '')}\n{s.get('body', '')}" for i, s in enumerate(slides, 1)])
            st.download_button("📦 Download Carousel", slides_text, file_name="carousel.txt", mime="text/plain", key="dl_carousel")

    # ── Content History (session-based) ──
    history = st.session_state.get("content_history", [])
    if history:
        st.markdown("---")
        with st.expander(f"📜 Session History ({len(history)} runs)", expanded=False):
            for idx, entry in enumerate(reversed(history)):
                st.markdown(f"""
<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 14px; margin:4px 0; font-size:0.85rem;">
    <strong>{entry['timestamp']}</strong> · {entry['channels']} channels · {entry['words']} words · {entry['time']}
    <div style="color:#64748b; margin-top:4px;">{entry['insight']}</div>
</div>""", unsafe_allow_html=True)
            if st.button("🗑️ Clear history", key="clear_history"):
                st.session_state["content_history"] = []
                st.rerun()


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

                        # AI-generated images for visual formats
                        if enable_images:
                            if "blog" in fmt.lower():
                                img_prompt = get_blog_header_prompt(content)
                                show_image_with_download(generate_image_url(img_prompt, 1200, 630, seed=i*10), "🖼️ AI header", f"rep_blog_{i}", f"blog_header_{i}.png")
                            elif "quote" in fmt.lower():
                                show_image_with_download(generate_image_url(get_quote_card_prompt(content), 1080, 1080, seed=i*20), "🖼️ Quote card background", f"rep_quote_{i}", f"quote_card_{i}.png")
                            elif "carousel" in fmt.lower():
                                show_image_with_download(generate_image_url("geometric shapes, indigo white gradient, clean slide background, no text", 1080, 1080, seed=i*30), "🖼️ Carousel slide background", f"rep_carousel_{i}", f"carousel_slide_{i}.png")

                        # Use appropriate mockup for known formats
                        if "linkedin" in fmt.lower():
                            st.markdown(render_linkedin_mockup(content), unsafe_allow_html=True)
                        elif "reddit" in fmt.lower():
                            st.markdown(render_reddit_mockup(content), unsafe_allow_html=True)
                        elif "email" in fmt.lower():
                            st.markdown(render_email_mockup(content), unsafe_allow_html=True)
                        elif "blog" in fmt.lower():
                            st.markdown(render_blog_mockup(content), unsafe_allow_html=True)
                            seo = seo_analyze(content)
                            st.markdown(render_seo_panel(seo), unsafe_allow_html=True)
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
                    st.markdown("### 📦 Export All")

                    col_md_r, col_txt_r = st.columns(2)

                    with col_md_r:
                        md_rep = build_repurpose_bundle(result)
                        st.download_button(
                            "📄 Markdown Bundle",
                            md_rep,
                            file_name=f"repurposed_bundle_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                            mime="text/markdown",
                            use_container_width=True,
                            key="dl_rep_md"
                        )

                    with col_txt_r:
                        all_content = "\n\n" + "="*60 + "\n\n"
                        all_content = all_content.join([
                            f"[{p.get('label', f'Piece {i}')}]\n\n{p.get('content', '')}"
                            for i, p in enumerate(result.get("pieces", []), 1)
                        ])
                        st.download_button(
                            "📋 Plain Text (All)",
                            all_content,
                            file_name=f"repurposed_all_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain",
                            use_container_width=True,
                            key="dl_rep_all"
                        )


# ─── TAB 3: Trend Radar ──────────────────────────────────────
with tab_trends:
    st.markdown("""
    ### 🔍 Trend Radar — What Should You Write About This Week?

    Enter your industry. AI scans for trending topics, emerging conversations,
    and content opportunities — with ready-to-use hooks and channel recommendations.
    """)

    col_ind, col_ctx = st.columns([1, 1])
    with col_ind:
        trend_industry = st.text_input(
            "Your industry/niche:",
            placeholder="e.g., B2B SaaS, Healthcare, Manufacturing, Fintech, E-commerce...",
            key="trend_industry"
        )
    with col_ctx:
        trend_context = st.text_input(
            "Your company (optional):",
            placeholder="e.g., Connected worker platform for factories",
            key="trend_context"
        )

    if st.button("🔍 Scan for Trends", type="primary", use_container_width=True, key="scan_trends"):
        if not trend_industry.strip():
            st.warning("Enter your industry to scan for trends.")
        elif not has_api_key():
            st.warning("API key required.")
        else:
            client = get_client()
            if client:
                st.session_state.setdefault("run_timestamps", []).append(time.time())

                with st.status("🔍 Scanning trending topics...", expanded=True) as status:
                    st.write("Analyzing industry conversations...")
                    st.write("Identifying content opportunities...")
                    trends_data, err = scan_trends(client, trend_industry, trend_context or context)

                    if err:
                        status.update(label="❌ Error", state="error")
                        st.error(err)
                    elif trends_data:
                        status.update(label=f"✅ Found {len(trends_data.get('trends', []))} trending topics", state="complete")

                if trends_data:
                    st.markdown("---")

                    for i, trend in enumerate(trends_data.get("trends", []), 1):
                        urgency = trend.get("urgency", "medium")
                        urgency_colors = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}
                        u_color = urgency_colors.get(urgency, "#f59e0b")

                        channels_str = " · ".join(trend.get("best_channels", []))
                        angles_html = "<br>".join([f"→ {a}" for a in trend.get("content_angles", [])])

                        st.markdown(f"""
<div class="content-card" style="border-left:4px solid {u_color};">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <div class="card-label">#{i} · {trend.get('title', 'Trend')}</div>
        <span style="background:{u_color}; color:#fff; padding:2px 8px; border-radius:10px; font-size:0.7rem; text-transform:uppercase;">{urgency}</span>
    </div>
    <div style="font-size:0.9rem; color:#374151; margin-bottom:8px;">{trend.get('summary', '')}</div>
    <div style="font-size:0.85rem; color:#6366f1; margin-bottom:8px;"><strong>Why now:</strong> {trend.get('why_now', '')}</div>
    <div style="font-size:0.85rem; margin-bottom:8px;"><strong>Content angles:</strong><br>{angles_html}</div>
    <div style="font-size:0.8rem; color:#64748b;"><strong>Best channels:</strong> {channels_str}</div>
</div>""", unsafe_allow_html=True)

                        # Ready-to-use hook
                        hook = trend.get("sample_hook", "")
                        if hook:
                            with st.expander(f"📋 Ready-to-use hook for #{i}"):
                                st.code(hook, language=None)

                    st.info("💡 **Tip:** Copy a trend summary and paste it into the Pipeline tab to generate full content across 4 channels.")


# ─── TAB 4: Data → Content ────────────────────────────────────
with tab_data:
    st.markdown("""
    ### 📊 Data → Content — Turn Numbers into Narratives

    Upload a CSV, spreadsheet export, or paste raw data. AI extracts the key insights
    and turns them into content angles — with headlines and audience suggestions.
    """)

    data_input_mode = st.radio(
        "Data source:",
        ["📋 Paste data", "📄 Upload CSV/file"],
        horizontal=True,
        key="data_input_mode"
    )

    data_text = ""
    if data_input_mode == "📄 Upload CSV/file":
        data_file = st.file_uploader("Upload data file:", type=["csv", "txt", "md", "xlsx"], key="data_file")
        if data_file:
            if data_file.name.endswith(".csv") or data_file.name.endswith(".txt") or data_file.name.endswith(".md"):
                data_text = data_file.read().decode("utf-8", errors="ignore")
                # Truncate
                lines = data_text.split("\n")
                if len(lines) > 150:
                    data_text = "\n".join(lines[:150]) + f"\n[...truncated, {len(lines)} total rows]"
                st.success(f"Loaded {len(lines)} rows")
            else:
                st.warning("For Excel files (.xlsx), export as CSV first for best results.")
    else:
        data_text = st.text_area(
            "Paste your data:",
            placeholder="Paste CSV data, survey results, metrics, KPIs, or any structured data...\n\ne.g.:\nMonth,Revenue,Churn Rate,NPS\nJan,120000,3.2%,45\nFeb,135000,2.8%,52\nMar,128000,3.5%,41",
            height=200,
            key="data_paste"
        )

    if data_text:
        st.caption(f"Data preview: {len(data_text.split(chr(10)))} rows loaded")

    col_analyze, col_generate = st.columns(2)

    with col_analyze:
        if st.button("🔍 Extract Insights", type="primary", use_container_width=True, key="extract_insights"):
            if not data_text.strip():
                st.warning("Add some data first.")
            elif not has_api_key():
                st.warning("API key required.")
            else:
                client = get_client()
                if client:
                    st.session_state.setdefault("run_timestamps", []).append(time.time())

                    with st.spinner("📊 Analyzing data patterns..."):
                        insights, err = analyze_data_for_content(client, data_text, context)

                    if err:
                        st.error(err)
                    elif insights:
                        st.session_state["data_insights"] = insights
                        st.markdown("---")
                        st.markdown(f"**Dataset:** {insights.get('data_summary', 'Analyzed')}")
                        st.markdown(f"**Overall narrative:** {insights.get('overall_narrative', '')}")
                        st.markdown("---")

                        for j, ins in enumerate(insights.get("insights", []), 1):
                            st.markdown(f"""
<div class="content-card">
    <div class="card-label">Insight #{j}: {ins.get('insight', '')}</div>
    <div style="font-size:0.85rem; margin-bottom:6px;"><strong>📊 Evidence:</strong> {ins.get('data_evidence', '')}</div>
    <div style="font-size:0.85rem; margin-bottom:6px;"><strong>📝 Story angle:</strong> {ins.get('story_angle', '')}</div>
    <div style="font-size:0.85rem; margin-bottom:6px;"><strong>💡 Headline:</strong> <em>{ins.get('headline_suggestion', '')}</em></div>
    <div style="font-size:0.8rem; color:#64748b;"><strong>🎯 Audience:</strong> {ins.get('target_audience', '')}</div>
</div>""", unsafe_allow_html=True)

                        st.info("💡 **Next step:** Copy an insight headline and paste it into the Pipeline tab to generate full content.")

    with col_generate:
        if st.button("⚡ Insight → Full Content", use_container_width=True, key="insight_to_content",
                     help="Takes the top insight and runs it through the 4-channel pipeline"):
            insights = st.session_state.get("data_insights")
            if insights and insights.get("insights"):
                top = insights["insights"][0]
                st.session_state["prefill_insight"] = f"{top.get('headline_suggestion', '')}. {top.get('insight', '')} Evidence: {top.get('data_evidence', '')}. {top.get('story_angle', '')}"
                st.info(f"✅ Top insight loaded! Switch to the **Pipeline** tab to generate content.")
            else:
                st.warning("Extract insights first (click the button on the left).")


# ─── TAB 5: Industry Showcase ─────────────────────────────────
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

        # AI-generated image for blog and linkedin showcases
        if enable_images and key == "blog":
            img_prompt = get_blog_header_prompt(demo_data[key])
            demo_seed = hash(selected_demo) % 1000
            show_image_with_download(generate_image_url(img_prompt, 1200, 630, seed=demo_seed), "🖼️ AI-generated blog header", f"sc_blog_{demo_seed}", "blog_header.png")
        elif enable_images and key == "linkedin":
            demo_seed = (hash(selected_demo) % 1000) + 100
            li_prompt = f"abstract corporate infographic, modern gradient, editorial, no text"
            show_image_with_download(generate_image_url(li_prompt, 1200, 627, seed=demo_seed), "🖼️ AI-generated post visual", f"sc_li_{demo_seed}", "linkedin_visual.png")

        renderer = MOCKUP_RENDERERS.get(key)
        if renderer:
            try:
                mockup_html = renderer(demo_data[key])
                if mockup_html:
                    st.markdown(mockup_html, unsafe_allow_html=True)
            except Exception as e:
                st.text_area(f"sc_raw_{key}", value=demo_data[key], height=250, key=f"sc_fallback_{key}_{hash(selected_demo) % 10000}", label_visibility="collapsed")

        # SEO panel for blog showcase
        if key == "blog":
            seo = seo_analyze(demo_data[key])
            st.markdown(render_seo_panel(seo), unsafe_allow_html=True)

        with st.expander("📋 View raw text / copy"):
            st.text_area(f"sc_{key}_{selected_demo[:4]}", value=demo_data[key], height=250, key=f"sc_{key}_{hash(selected_demo) % 10000}", label_visibility="collapsed")
            st.download_button(f"Copy {key}", demo_data[key], file_name=f"showcase_{key}.txt", key=f"dl_sc_{key}_{hash(selected_demo) % 10000}")
        st.markdown("---")

    # ── Carousel Slides (pre-generated) ──
    carousel_slides = demo_data.get("carousel_slides", [])
    if carousel_slides:
        st.markdown('<div class="card-label">🎠 LINKEDIN / INSTAGRAM CAROUSEL — 8 SLIDES</div>', unsafe_allow_html=True)

        for row_start in range(0, len(carousel_slides), 2):
            cols = st.columns(2)
            for col_idx, slide_idx in enumerate(range(row_start, min(row_start + 2, len(carousel_slides)))):
                with cols[col_idx]:
                    st.markdown(render_carousel_slide(carousel_slides[slide_idx], seed=slide_idx), unsafe_allow_html=True)

        # Download carousel script
        slides_text = "\n\n".join([
            f"--- SLIDE {s['slide_number']} ({s['type']}) ---\nHeadline: {s['headline']}\nBody: {s['body']}"
            for s in carousel_slides
        ])
        st.download_button("📦 Download Carousel Script", slides_text,
            file_name="carousel_script.txt", mime="text/plain",
            key=f"dl_sc_carousel_{hash(selected_demo) % 10000}")
        st.markdown("---")

    # ── Distribution Strategy (pre-generated) ──
    dist = demo_data.get("distribution", {})
    if dist:
        st.markdown('<div class="card-label">🔗 DISTRIBUTION STRATEGY</div>', unsafe_allow_html=True)

        st.markdown(f"""
<div style="background:#f0fdf4; border:1px solid #86efac; border-radius:10px; padding:1rem; margin:0.75rem 0;">
    <strong>📅 Recommended timing:</strong> {dist.get('timing', 'N/A')}
</div>""", unsafe_allow_html=True)

        st.markdown("**Publishing order:**")
        for j, step in enumerate(dist.get("order", []), 1):
            st.markdown(f"{j}. {step}")

        st.markdown("**Cross-references:**")
        for ref in dist.get("cross_refs", []):
            st.markdown(f"- **{ref.get('from', '?')}** → **{ref.get('to', '?')}**: {ref.get('how', '')}")

        st.markdown(f"""
<div style="background:linear-gradient(135deg,#f5f3ff,#ede9fe); border:1px solid #c4b5fd; border-radius:10px; padding:1rem; margin:0.75rem 0;">
    <strong>🌐 Content ecosystem:</strong><br>{dist.get('ecosystem', 'N/A')}
</div>""", unsafe_allow_html=True)
        st.markdown("---")

    st.info("💡 **Same insight → 4 channels + carousel + distribution plan.** Switch industries above to compare. Then try it yourself in the Pipeline tab.")


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
    ┌─────────────────┐     ┌──────────────┐     ┌─────────────────────┐
    │     INPUTS       │     │   ANALYSIS   │     │   BATCH GENERATE    │
    │                  │     │  (1 API call) │     │   (1 API call)      │
    │  ✍️ Text/Paste    │────→│              │────→│                     │
    │  🔗 URL Import   │     │  Extracts:   │     │  Analysis feeds     │
    │  📄 PDF Upload   │     │  · Core angle │     │  all 4 channels:    │
    │  📎 DOCX/CSV     │     │  · Pain point │     │                     │
    └─────────────────┘     │  · Hooks      │     │  ├─ LinkedIn Post   │
                             │  · Why now    │     │  ├─ Blog Draft      │
    ┌──────────────┐         └──────────────┘     │  ├─ Reddit Thread   │
    │ KNOWLEDGE    │               │               │  └─ Email Sequence  │
    │ BASE         │               │               └─────────────────────┘
    │ · Company    │               │                        │
    │ · Industry   │               ▼                   ┌────┴────┐
    │ · Audience   │────→  Consistent narrative  ←────│ OPTIMIZE │
    │ · Competitors│         across all channels       │ SEO+Score│
    │ · Voice DNA  │                                   └─────────┘
    └──────────────┘       Total: 2 API calls (was 5)
    """, language=None)

    st.markdown("---")

    st.markdown("#### Prompt-and-Pray vs. ContentEngine")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **❌ Typical AI Content**
        - "What should I write?" → guess
        - Paste into ChatGPT → generic output
        - Manually rewrite per channel
        - No brand voice
        - No SEO analysis
        - No data-driven insights
        - No distribution strategy
        """)
    with col2:
        st.markdown("""
        **✅ ContentEngine**
        - Trend Radar finds topics for you
        - Data → Content extracts insights from CSV
        - 4 channels generated simultaneously
        - Brand Voice Cloning matches anyone
        - SEO Readiness built in (free)
        - Repurpose: 1 piece → 10 outputs
        - Content Chain plans distribution
        - Visual carousel builder
        """)

    st.markdown("---")

    st.markdown("#### Full Feature Map")
    st.markdown("""
    | Feature | What It Does | Cost |
    |---|---|---|
    | **🔧 Pipeline** | Text/URL/PDF/DOCX → 4 channel content | API |
    | **🔄 Repurpose** | 1 article → 10 pieces (3 LinkedIn, thread, blog, email, Reddit, carousel, newsletter, quotes) | API |
    | **🔍 Trend Radar** | Scans trending topics → "write about this" with hooks | API |
    | **📊 Data → Content** | CSV/data → insight extraction → content angles | API |
    | **🧬 Brand Voice** | Upload samples → extract voice DNA → match in all outputs | API |
    | **📊 SEO Analysis** | Flesch-Kincaid, keywords, headings, meta description | **$0** |
    | **🎠 Carousel Builder** | Blog → 8 visual slides with progress bars | API |
    | **🔗 Content Chain** | Cross-linking + distribution strategy + timing | API |
    | **🖼️ AI Visuals** | Blog headers, LinkedIn visuals, quote cards (Pollinations.ai) | **$0** |
    | **📈 Quality Scoring** | 5-dimension scoring per output | API |
    | **📦 Export** | Markdown bundle, content calendar, plain text, PNG images | **$0** |
    | **🎨 Tone/Audience** | 5 tone × 5 audience presets | — |
    """)

    st.markdown("---")

    st.markdown("#### Next on the Roadmap")
    st.markdown("""
    **Workflow Integration** → HubSpot API (email sequences), Buffer (social scheduling),
    Slack notifications (content ready for review)

    **Performance Loop** → Track insight → content → engagement, feed data
    back into prompt optimization
    """)

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#94a3b8; font-size:0.85rem; padding:1rem;'>"
        "Built by <strong>Ata Okuzcuoglu</strong> · MSc Management & Technology @ TUM · "
        "<a href='https://linkedin.com/in/atakzcgl' style='color:#6366f1;'>LinkedIn</a>"
        "</div>",
        unsafe_allow_html=True
    )
