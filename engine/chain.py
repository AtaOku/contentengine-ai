"""ContentEngine AI — Content Chain."""

import json
from config.prompts import CONTENT_CHAIN_PROMPT
from config.settings import MODEL

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
