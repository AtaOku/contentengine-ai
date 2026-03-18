"""ContentEngine AI — Export Functions."""

from datetime import datetime

def build_markdown_bundle(results, insight_text="", channel_labels=None):
    """Build a complete Markdown document with all generated content."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not channel_labels:
        channel_labels = {
            "linkedin": "LinkedIn Post", "blog": "Blog Draft",
            "reddit": "Reddit Thread", "email": "Email Sequence"
        }

    md = f"""# ContentEngine AI — Export Bundle
**Generated:** {now}
**Source insight:** {insight_text[:200]}{'...' if len(insight_text) > 200 else ''}

---

"""
    for ch, content in results.items():
        label = channel_labels.get(ch, ch)
        md += f"## {label}\n\n{content}\n\n---\n\n"

    return md


def build_content_calendar(results, channel_labels=None):
    """Build a simple content calendar as a Markdown table."""
    if not channel_labels:
        channel_labels = {
            "linkedin": "LinkedIn Post", "blog": "Blog Draft",
            "reddit": "Reddit Thread", "email": "Email Sequence"
        }

    now = datetime.now()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Assign each piece to a day
    channels = list(results.keys())
    cal = "# Content Calendar\n\n"
    cal += "| Day | Channel | Content Preview | Status |\n"
    cal += "|---|---|---|---|\n"

    for i, ch in enumerate(channels):
        day = days[i % len(days)]
        label = channel_labels.get(ch, ch)
        # First 80 chars as preview
        preview = results[ch][:80].replace("\n", " ").replace("|", "/") + "..."
        cal += f"| {day} | {label} | {preview} | 📝 Draft |\n"

    cal += "\n---\n\n"

    # Full content below
    cal += "## Full Content\n\n"
    for ch, content in results.items():
        label = channel_labels.get(ch, ch)
        cal += f"### {label}\n\n{content}\n\n---\n\n"

    return cal


def build_repurpose_bundle(result):
    """Build a Markdown bundle from repurpose output."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# ContentEngine AI — Repurpose Bundle
**Generated:** {now}
**Source:** {result.get('title_summary', 'Content repurposed')}
**Pieces:** {len(result.get('pieces', []))}

---

"""
    for i, piece in enumerate(result.get("pieces", []), 1):
        label = piece.get("label", f"Piece {i}")
        content = piece.get("content", "")
        md += f"## {i}. {label}\n\n{content}\n\n---\n\n"

    return md
