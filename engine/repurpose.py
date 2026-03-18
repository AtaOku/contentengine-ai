"""ContentEngine AI — Repurpose Engine."""

import json
from config.prompts import SYSTEM_PROMPT, REPURPOSE_PROMPT
from config.settings import MODEL

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
