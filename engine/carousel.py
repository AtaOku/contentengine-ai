"""ContentEngine AI — Carousel Builder."""

import json
from config.prompts import CAROUSEL_PROMPT
from config.settings import MODEL

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
