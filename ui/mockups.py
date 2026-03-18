"""ContentEngine AI — Platform Mockups."""

def render_linkedin_mockup(content):
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""
<div style="background:#fff; border:1px solid #e0e0e0; border-radius:8px; overflow:hidden; margin:1rem 0; font-family:-apple-system,system-ui,sans-serif;">
    <div style="padding:12px 16px; display:flex; align-items:center; gap:10px;">
        <div style="width:48px; height:48px; border-radius:50%; background:linear-gradient(135deg,#0a66c2,#004182); display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:18px; flex-shrink:0;">CE</div>
        <div>
            <div style="font-weight:600; color:#000; font-size:0.9rem;">ContentEngine AI</div>
            <div style="color:#666; font-size:0.75rem;">Generated via Pipeline · Just now</div>
        </div>
    </div>
    <div style="padding:0 16px 16px; font-size:0.9rem; line-height:1.6; color:#333; white-space:pre-wrap;">{safe}</div>
    <div style="padding:8px 16px; border-top:1px solid #e0e0e0; display:flex; justify-content:space-around; color:#666; font-size:0.8rem;">
        <span>👍 Like</span><span>💬 Comment</span><span>🔄 Repost</span><span>📤 Send</span>
    </div>
</div>"""


def render_reddit_mockup(content):
    lines = content.strip().split("\n")
    title = lines[0] if lines else "Untitled"
    body = "\n".join(lines[2:]) if len(lines) > 2 else ""
    safe_t = title.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    safe_b = body.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f"""
<div style="background:#fff; border:1px solid #ccc; border-radius:4px; overflow:hidden; margin:1rem 0; font-family:-apple-system,system-ui,sans-serif;">
    <div style="display:flex;">
        <div style="background:#f8f9fa; padding:8px; display:flex; flex-direction:column; align-items:center; gap:4px; min-width:40px;">
            <span style="color:#878a8c; font-size:0.75rem;">▲</span>
            <span style="color:#1a1a1b; font-weight:700; font-size:0.85rem;">247</span>
            <span style="color:#878a8c; font-size:0.75rem;">▼</span>
        </div>
        <div style="padding:8px 12px; flex:1;">
            <div style="font-size:0.75rem; color:#787c7e; margin-bottom:4px;"><strong style="color:#1c1c1c;">r/marketing</strong> · Posted by u/contentengine · 2h</div>
            <div style="font-size:1.1rem; font-weight:600; color:#1a1a1b; margin-bottom:8px;">{safe_t}</div>
            <div style="font-size:0.9rem; line-height:1.5; color:#1a1a1b; white-space:pre-wrap;">{safe_b}</div>
        </div>
    </div>
    <div style="padding:4px 12px 8px; font-size:0.75rem; color:#878a8c; display:flex; gap:12px;">
        <span>💬 42 Comments</span><span>📤 Share</span><span>⭐ Save</span>
    </div>
</div>"""


def render_email_mockup(content):
    safe = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    subject = "Your weekly insight"
    for line in content.split("\n"):
        if line.startswith("Subject A:"):
            subject = line.replace("Subject A:","").strip()
            break
    safe_s = subject.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f"""
<div style="background:#fff; border:1px solid #dadce0; border-radius:8px; overflow:hidden; margin:1rem 0; font-family:-apple-system,system-ui,sans-serif; max-width:600px;">
    <div style="background:#f2f2f2; padding:8px 16px; font-size:0.8rem; color:#5f6368; border-bottom:1px solid #dadce0;">
        📥 Inbox → <span style="color:#202124; font-weight:600;">ContentEngine</span>
    </div>
    <div style="padding:12px 16px; font-size:1rem; font-weight:600; color:#202124; border-bottom:1px solid #f0f0f0;">{safe_s}</div>
    <div style="padding:8px 16px; font-size:0.8rem; color:#5f6368;">From: content@company.com · To: [First Name] · Now</div>
    <div style="padding:16px; font-size:0.9rem; line-height:1.7; color:#202124; white-space:pre-wrap;">{safe}</div>
</div>"""


def render_blog_mockup(content):
    import re
    lines = content.strip().split("\n")
    headline = lines[0].lstrip("# ").strip() if lines else "Untitled"
    body_lines = lines[1:]

    html_parts = []
    for line in body_lines:
        line = line.strip()
        if not line:
            html_parts.append("<br>")
            continue
        if line.startswith("## "):
            text = line.lstrip("# ").strip()
            text = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            html_parts.append(f'<h3 style="font-size:1.1rem; font-weight:700; color:#1a1a2e; margin:20px 0 8px;">{text}</h3>')
            continue
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
        safe_line = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        safe_line = safe_line.replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
        safe_line = safe_line.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
        html_parts.append(f'<p style="margin:0 0 8px;">{safe_line}</p>')

    body_html = "\n".join(html_parts)
    safe_h = headline.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    word_count = len(content.split())
    read_min = max(1, word_count // 200)

    return f"""
<div style="background:#fff; border:1px solid #e5e7eb; border-radius:12px; overflow:hidden; margin:1rem 0; font-family:Georgia,serif;">
    <div style="background:linear-gradient(135deg,#1a1a2e,#16213e); padding:24px;">
        <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:2px; color:#818cf8; margin-bottom:8px; font-family:sans-serif;">Insights</div>
        <div style="font-size:1.4rem; font-weight:700; color:#fff; line-height:1.3;">{safe_h}</div>
        <div style="font-size:0.8rem; color:rgba(255,255,255,0.5); margin-top:12px; font-family:sans-serif;">ContentEngine AI · {read_min} min read</div>
    </div>
    <div style="padding:24px; font-size:0.95rem; line-height:1.8; color:#374151;">{body_html}</div>
</div>"""


MOCKUP_RENDERERS = {
    "linkedin": render_linkedin_mockup,
    "blog": render_blog_mockup,
    "reddit": render_reddit_mockup,
    "email": render_email_mockup,
}
