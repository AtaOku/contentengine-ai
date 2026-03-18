"""ContentEngine AI — Core Pipeline Engine."""

import json
from config.prompts import SYSTEM_PROMPT, FORMAT_PROMPTS, ANALYSIS_PROMPT, BATCH_PROMPT
from config.settings import MODEL

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
