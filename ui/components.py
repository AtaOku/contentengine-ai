"""ContentEngine AI — Shared UI Components."""

import streamlit as st
import urllib.parse

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
