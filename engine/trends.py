"""ContentEngine AI — Trend Radar."""

import json
from config.prompts import TREND_RADAR_PROMPT
from config.settings import MODEL

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
