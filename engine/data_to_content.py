"""ContentEngine AI — Data to Content."""

import json
from config.prompts import DATA_TO_CONTENT_PROMPT
from config.settings import MODEL

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
