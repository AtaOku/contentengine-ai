"""ContentEngine AI — Brand Voice & Scoring."""

import json
from config.prompts import VOICE_EXTRACT_PROMPT
from config.settings import MODEL

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
