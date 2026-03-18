"""ContentEngine AI — Settings & Constants."""

MODEL = "claude-sonnet-4-20250514"
DAILY_LIMIT = 10


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

