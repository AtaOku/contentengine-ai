"""ContentEngine AI — SEO Analysis Engine."""

import re
import math
from collections import Counter

def calculate_flesch_kincaid(text):
    """Calculate Flesch-Kincaid readability grade level."""
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    words = text.split()
    if not sentences or not words:
        return 0, 0

    syllable_count = 0
    for word in words:
        word = word.lower().strip(".,!?;:'\"()-")
        if not word:
            continue
        # Simple syllable counter
        count = 0
        vowels = "aeiouy"
        if word[0] in vowels:
            count += 1
        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count = 1
        syllable_count += count

    num_sentences = len(sentences)
    num_words = len(words)

    # Flesch Reading Ease
    ease = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllable_count / num_words)
    # Flesch-Kincaid Grade Level
    grade = 0.39 * (num_words / num_sentences) + 11.8 * (syllable_count / num_words) - 15.59

    return round(max(0, min(100, ease)), 1), round(max(0, grade), 1)


def extract_keywords(text, top_n=10):
    """Extract top keywords by frequency (excluding stop words)."""
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "shall", "it", "its", "this",
        "that", "these", "those", "i", "you", "he", "she", "we", "they", "them",
        "their", "my", "your", "his", "her", "our", "not", "no", "if", "when",
        "what", "which", "who", "how", "where", "why", "all", "each", "every",
        "both", "few", "more", "most", "other", "some", "such", "than", "too",
        "very", "just", "about", "also", "into", "over", "after", "before",
        "between", "through", "during", "without", "again", "further", "then",
        "once", "here", "there", "so", "as", "up", "out", "off", "down", "only",
        "own", "same", "don", "now", "s", "t", "re", "ve", "ll", "d", "m",
    }
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    filtered = [w for w in words if w not in stop_words]
    counter = Counter(filtered)
    return counter.most_common(top_n)


def analyze_heading_structure(text):
    """Analyze heading hierarchy in blog content."""
    lines = text.strip().split("\n")
    headings = []
    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            headings.append(("H1", line.lstrip("# ")))
        elif line.startswith("## "):
            headings.append(("H2", line.lstrip("## ")))
        elif line.startswith("### "):
            headings.append(("H3", line.lstrip("### ")))

    issues = []
    h1_count = sum(1 for h in headings if h[0] == "H1")
    h2_count = sum(1 for h in headings if h[0] == "H2")

    if h1_count == 0:
        issues.append("Missing H1 headline")
    elif h1_count > 1:
        issues.append(f"Multiple H1s ({h1_count}) — use only one")
    if h2_count == 0:
        issues.append("No H2 subheadings — add 2-3 for scannability")
    elif h2_count < 2:
        issues.append("Only 1 H2 — add more for better structure")

    return headings, issues


def generate_meta_description(text, max_len=155):
    """Generate a meta description from content."""
    # Get first meaningful paragraph (skip headline)
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("**"):
            continue
        if len(line) > 50:
            # Truncate to max_len at word boundary
            if len(line) <= max_len:
                return line
            truncated = line[:max_len]
            last_space = truncated.rfind(" ")
            if last_space > 100:
                return truncated[:last_space] + "..."
            return truncated + "..."
    return text[:max_len].strip() + "..."


def seo_analyze(text, target_keyword=""):
    """Complete SEO readiness analysis for blog content."""
    words = text.split()
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    avg_sentence_len = round(word_count / max(1, len(sentences)), 1)

    reading_ease, grade_level = calculate_flesch_kincaid(text)
    keywords = extract_keywords(text)
    headings, heading_issues = analyze_heading_structure(text)
    meta_desc = generate_meta_description(text)

    # Word count assessment
    if word_count < 300:
        wc_status = "⚠️ Too short"
        wc_note = "Under 300 words — aim for 600-1500 for SEO"
    elif word_count < 600:
        wc_status = "🟡 Acceptable"
        wc_note = "Could be longer for competitive keywords"
    elif word_count <= 1500:
        wc_status = "✅ Optimal"
        wc_note = "Sweet spot for most blog content"
    else:
        wc_status = "✅ Long-form"
        wc_note = "Great for in-depth topics, ensure it stays focused"

    # Readability assessment
    if reading_ease >= 60:
        read_status = "✅ Easy to read"
    elif reading_ease >= 40:
        read_status = "🟡 Moderate"
    else:
        read_status = "⚠️ Complex"

    # Sentence length
    if avg_sentence_len <= 20:
        sent_status = "✅ Good"
    elif avg_sentence_len <= 25:
        sent_status = "🟡 Slightly long"
    else:
        sent_status = "⚠️ Too long — break up sentences"

    # Overall SEO score (0-100)
    score = 50  # base
    if 600 <= word_count <= 1500:
        score += 15
    elif 300 <= word_count < 600:
        score += 8
    if reading_ease >= 50:
        score += 15
    elif reading_ease >= 35:
        score += 8
    if len(headings) >= 3:
        score += 10
    elif len(headings) >= 2:
        score += 5
    if not heading_issues:
        score += 10
    else:
        score += max(0, 10 - len(heading_issues) * 3)

    # Target keyword analysis
    kw_data = None
    if target_keyword and target_keyword.strip():
        kw = target_keyword.strip().lower()
        text_lower = text.lower()
        kw_count = text_lower.count(kw)
        kw_density = round((kw_count / max(1, word_count)) * 100, 2)

        # Check keyword placement
        kw_in_title = any(kw in h[1].lower() for h in headings if h[0] == "H1")
        kw_in_headings = any(kw in h[1].lower() for h in headings)
        kw_in_meta = kw in meta_desc.lower()
        kw_in_first_100 = kw in " ".join(words[:100]).lower()

        # Density assessment
        if 0.5 <= kw_density <= 2.5:
            density_status = "✅ Optimal"
        elif kw_density < 0.5:
            density_status = "⚠️ Low — use keyword more"
        else:
            density_status = "⚠️ High — risk of keyword stuffing"

        # Keyword score contribution
        kw_score = 0
        if kw_count > 0: kw_score += 3
        if kw_in_title: kw_score += 5
        if kw_in_headings: kw_score += 3
        if kw_in_meta: kw_score += 2
        if kw_in_first_100: kw_score += 2
        if 0.5 <= kw_density <= 2.5: kw_score += 5
        score += kw_score

        kw_data = {
            "keyword": target_keyword.strip(),
            "count": kw_count,
            "density": kw_density,
            "density_status": density_status,
            "in_title": kw_in_title,
            "in_headings": kw_in_headings,
            "in_meta": kw_in_meta,
            "in_first_100": kw_in_first_100,
            "placement_checks": sum([kw_in_title, kw_in_headings, kw_in_meta, kw_in_first_100]),
        }

    score = min(100, max(0, score))

    return {
        "score": score,
        "word_count": word_count,
        "wc_status": wc_status,
        "wc_note": wc_note,
        "reading_ease": reading_ease,
        "grade_level": grade_level,
        "read_status": read_status,
        "avg_sentence_len": avg_sentence_len,
        "sent_status": sent_status,
        "keywords": keywords,
        "headings": headings,
        "heading_issues": heading_issues,
        "meta_description": meta_desc,
        "sentence_count": len(sentences),
        "target_keyword": kw_data,
    }


def render_seo_panel(seo_data):
    """Render SEO analysis as HTML panel."""
    score = seo_data["score"]
    color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"

    keywords_html = ", ".join([f"<strong>{kw}</strong> ({c})" for kw, c in seo_data["keywords"][:8]])
    headings_html = " → ".join([f"{h[0]}" for h in seo_data["headings"]]) if seo_data["headings"] else "<em>None found</em>"
    issues_html = " · ".join(seo_data["heading_issues"]) if seo_data["heading_issues"] else "✅ Good structure"

    # Target keyword section
    kw_section = ""
    kw = seo_data.get("target_keyword")
    if kw:
        checks = []
        checks.append(f"{'✅' if kw['in_title'] else '❌'} In title")
        checks.append(f"{'✅' if kw['in_headings'] else '❌'} In headings")
        checks.append(f"{'✅' if kw['in_first_100'] else '❌'} In first 100 words")
        checks.append(f"{'✅' if kw['in_meta'] else '❌'} In meta description")
        checks_html = " · ".join(checks)
        kw_section = f"""
    <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px; padding:10px; margin:8px 0;">
        <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#2563eb; font-weight:700; margin-bottom:6px;">🎯 Target Keyword: "{kw['keyword']}"</div>
        <div style="font-size:0.85rem; margin-bottom:4px;">Count: <strong>{kw['count']}</strong> · Density: <strong>{kw['density']}%</strong> {kw['density_status']} · Placement: <strong>{kw['placement_checks']}/4</strong></div>
        <div style="font-size:0.8rem; color:#374151;">{checks_html}</div>
    </div>"""

    return f"""
<div style="background:linear-gradient(135deg,#f8fafc,#f0f4ff); border:1px solid #c3d4f7; border-left:4px solid {color}; border-radius:12px; padding:1.25rem; margin:0.75rem 0;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; color:#4f46e5; font-weight:700;">📊 SEO Readiness Report</span>
        <span style="background:{color}; color:#fff; padding:4px 12px; border-radius:20px; font-family:'JetBrains Mono',monospace; font-size:0.85rem; font-weight:700;">{score}/100</span>
    </div>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:12px; font-size:0.85rem;">
        <div><strong>Words:</strong> {seo_data['word_count']} {seo_data['wc_status']}</div>
        <div><strong>Readability:</strong> {seo_data['reading_ease']} {seo_data['read_status']}</div>
        <div><strong>Avg sentence:</strong> {seo_data['avg_sentence_len']} words {seo_data['sent_status']}</div>
    </div>{kw_section}
    <div style="font-size:0.85rem; margin-bottom:8px;">
        <strong>Top keywords:</strong> {keywords_html}
    </div>
    <div style="font-size:0.85rem; margin-bottom:8px;">
        <strong>Heading structure:</strong> {headings_html} — {issues_html}
    </div>
    <div style="background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-top:8px;">
        <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:#6366f1; font-weight:700; margin-bottom:4px;">Auto-generated Meta Description</div>
        <div style="font-size:0.85rem; color:#374151; line-height:1.5;">{seo_data['meta_description']}</div>
        <div style="font-size:0.7rem; color:#9ca3af; margin-top:4px;">{len(seo_data['meta_description'])} / 155 chars</div>
    </div>
</div>"""
