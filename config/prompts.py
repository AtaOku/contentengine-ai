"""ContentEngine AI — All Prompt Templates."""

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
