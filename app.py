"""
ContentEngine AI — Multi-Format Content Pipeline
Built by Ata Okuzcuoglu as a working proof-of-concept for Workerbase.

Takes a raw insight (news, trend, competitor move, customer quote) and produces
publish-ready content across 4 channels in under 60 seconds.
"""

import streamlit as st
import anthropic
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import io

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="ContentEngine AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=DM+Sans:wght@400;500;700&display=swap');

    .stApp { font-family: 'DM Sans', sans-serif; }

    .hero-header {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.05);
        position: relative;
        overflow: hidden;
    }
    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #fff;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: rgba(255,255,255,0.6);
        margin-top: 0.5rem;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(99,102,241,0.2);
        color: #818cf8;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 1rem;
        border: 1px solid rgba(99,102,241,0.3);
    }

    .content-card {
        background: #fafafa;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .card-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #6366f1;
        margin-bottom: 0.75rem;
        font-weight: 700;
    }

    .stat-box {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .stat-number {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a;
    }
    .stat-label { font-size: 0.75rem; color: #64748b; margin-top: 2px; }

    .analysis-card {
        background: linear-gradient(135deg, #fefce8 0%, #fef9c3 100%);
        border: 1px solid #fde047;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .analysis-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 700;
        color: #854d0e;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Prompt Templates ─────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert B2B content strategist specializing in manufacturing technology, 
Industry 4.0, and connected worker platforms. You write for technical decision-makers 
(plant managers, VP Operations, CTO) who are pragmatic, time-constrained, and skeptical of hype.

Your tone: authoritative but not academic. Direct. Data-aware. You understand factory floors, 
not just boardrooms. You never use generic marketing fluff.

Company context: You're creating content for a manufacturing SaaS company that provides 
a connected worker platform used in 60+ factories (customers include Bosch, Porsche, BASF, 
thyssenkrupp). The platform connects people, machines, and processes in real-time to boost 
productivity 20%+. They're entering the US market and doing category creation.

CRITICAL RULES:
- Never use buzzwords without substance
- Every claim should be backed by a specific example or data point
- Write like someone who has actually visited a factory floor
- Be contrarian when appropriate — challenge conventional wisdom
- Manufacturing audience hates fluff — be concrete"""

FORMAT_PROMPTS = {
    "linkedin": """Create a LinkedIn post based on this insight. Requirements:
- Hook in the first line (pattern interrupt — question, bold claim, or surprising stat)
- 150-250 words max
- Use line breaks for readability (LinkedIn format)
- End with a question or call-to-action that invites discussion
- Include 3-5 relevant hashtags at the end
- Tone: thought leadership, not salesy. Like a plant manager sharing what they learned.
- NO emojis in the body text. Professional tone.

Raw insight: {insight}

Industry context: {context}

Return ONLY the post text, nothing else.""",

    "blog": """Create a blog post draft based on this insight. Requirements:
- Compelling headline (specific, not generic)
- 400-600 word draft
- Opening paragraph that hooks with a specific problem or scenario
- 2-3 subheadings that break up the content
- Include at least one specific example or data point
- End with a clear takeaway or next step
- SEO-friendly but not keyword-stuffed
- Write for VP Operations / Plant Managers who scan, don't read

Raw insight: {insight}

Industry context: {context}

Return the full blog post with headline.""",

    "reddit": """Create a Reddit post for r/manufacturing or r/industry40 based on this insight. Requirements:
- Title that feels native to Reddit (not promotional)
- 100-200 word body that shares a genuine observation or question
- Conversational, peer-to-peer tone
- Ask for input from the community
- NO company mentions — this is thought leadership, not promotion
- Feel like a manufacturing engineer sharing something interesting
- Include a TL;DR at the end

Raw insight: {insight}

Industry context: {context}

Return the title on the first line, then a blank line, then the body.""",

    "email": """Create a nurture email sequence hook (1 email) based on this insight. Requirements:
- Subject line (A/B test: give 2 options)
- Preview text (40-90 chars)
- 100-150 word body
- One clear CTA (not hard sell — think "See how Factory X solved this")
- Tone: helpful peer, not vendor
- For manufacturing operations leaders

Raw insight: {insight}

Industry context: {context}

Format:
Subject A: ...
Subject B: ...
Preview: ...

[body]

CTA: ...""",
}

ANALYSIS_PROMPT = """Analyze this raw insight for content potential. Return a JSON object with:
{{
    "core_angle": "The main content angle in one sentence",
    "audience_pain": "What pain point does this address for manufacturing leaders?",
    "contrarian_take": "What's the non-obvious perspective here?",
    "content_hooks": ["hook1", "hook2", "hook3"],
    "trending_relevance": "Why does this matter RIGHT NOW?",
    "suggested_channels": ["ranked list of best channels for this content"]
}}

Raw insight: {insight}
Industry context: {context}

Return ONLY valid JSON, no markdown formatting, no backticks."""


# ── Helpers ──────────────────────────────────────────────────

def fetch_url_content(url):
    """Fetch and extract main text content from a URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ContentEngine/1.0"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        # Try article tag first, then main, then body
        content = soup.find("article") or soup.find("main") or soup.find("body")
        if not content:
            return None, "Could not extract content from the page."

        text = content.get_text(separator="\n", strip=True)

        # Clean up: remove excessive blank lines, limit length
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        clean_text = "\n".join(lines)

        # Truncate to ~3000 chars to keep prompt manageable
        if len(clean_text) > 3000:
            clean_text = clean_text[:3000] + "\n\n[...truncated]"

        # Get title
        title = soup.find("title")
        title_text = title.get_text(strip=True) if title else ""

        if title_text:
            clean_text = f"Title: {title_text}\n\n{clean_text}"

        return clean_text, None
    except requests.exceptions.Timeout:
        return None, "Request timed out. Try a different URL."
    except requests.exceptions.RequestException as e:
        return None, f"Failed to fetch URL: {str(e)[:100]}"
    except Exception as e:
        return None, f"Error extracting content: {str(e)[:100]}"


def extract_file_content(uploaded_file):
    """Extract text from uploaded files (PDF, TXT, DOCX, CSV, MD)."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".txt") or name.endswith(".md"):
            return uploaded_file.read().decode("utf-8", errors="ignore"), None

        elif name.endswith(".csv"):
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            # Truncate large CSVs
            lines = content.split("\n")
            if len(lines) > 100:
                content = "\n".join(lines[:100]) + f"\n\n[...truncated, {len(lines)} total rows]"
            return content, None

        elif name.endswith(".pdf"):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                pages = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        pages.append(f"[Page {i+1}]\n{text}")
                full_text = "\n\n".join(pages)
                if len(full_text) > 4000:
                    full_text = full_text[:4000] + "\n\n[...truncated]"
                if not full_text.strip():
                    return None, "PDF appears to be image-based (no extractable text)."
                return full_text, None
            except ImportError:
                return None, "PyPDF2 not available. Install with: pip install PyPDF2"

        elif name.endswith(".docx"):
            try:
                import docx
                doc = docx.Document(io.BytesIO(uploaded_file.read()))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                full_text = "\n\n".join(paragraphs)
                if len(full_text) > 4000:
                    full_text = full_text[:4000] + "\n\n[...truncated]"
                return full_text, None
            except ImportError:
                return None, "python-docx not available. Install with: pip install python-docx"

        else:
            return None, f"Unsupported file type: {name.split('.')[-1]}"

    except Exception as e:
        return None, f"Error reading file: {str(e)[:100]}"


# ── Tone & Audience Configs ──────────────────────────────────

TONE_OPTIONS = {
    "🎯 Thought Leadership": "Authoritative, insight-driven. You're the expert sharing what you've learned. No selling.",
    "⚡ Provocative / Contrarian": "Challenge conventional wisdom. Be bold. Make people disagree in the comments.",
    "📊 Data-Driven / Analytical": "Lead with numbers, benchmarks, and evidence. Minimal opinion, maximum proof.",
    "🤝 Conversational / Peer": "Talk like a colleague over coffee. Casual but smart. First person.",
    "📚 Educational / How-To": "Teach something specific. Step-by-step. Practical and actionable.",
}

AUDIENCE_OPTIONS = {
    "👔 C-Suite / VP": "Time-constrained executives. Lead with business impact, ROI, risk. Skip technical details.",
    "🔧 Ops / Engineering": "Hands-on practitioners. They want specifics, not buzzwords. Technical credibility matters.",
    "📈 Marketing / Growth": "Growth-oriented marketers. Speak their language: CAC, LTV, conversion, attribution.",
    "🏭 Industry / Domain Expert": "Deep domain knowledge. Don't explain basics. Peer-to-peer expert conversation.",
    "🌍 General / Mixed": "Broad audience. Balance accessibility with depth. Define jargon when used.",
}


def get_client():
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)

def generate_content(client, format_type, insight, context, tone_desc="", audience_desc=""):
    prompt = FORMAT_PROMPTS[format_type].format(insight=insight, context=context)

    # Inject tone and audience into prompt
    modifiers = ""
    if tone_desc:
        modifiers += f"\n\nTONE INSTRUCTION: {tone_desc}"
    if audience_desc:
        modifiers += f"\nAUDIENCE: {audience_desc}"

    if modifiers:
        prompt = prompt + modifiers

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_insight(client, insight, context):
    prompt = ANALYSIS_PROMPT.format(insight=insight, context=context)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return json.loads(text.strip())
    except:
        return None


# ── Demo Insights ────────────────────────────────────────────

DEMO_INSIGHTS = {
    "🤖 GenAI Hits the Factory Floor": {
        "insight": "Google Cloud and manufacturing companies recently demonstrated Generative AI use cases for factory floors — converting static PDF manuals into dynamic step-by-step work instructions, and using historical process data to predict machine setup times. Companies like MAN Truck & Bus, GKN, and Knorr-Bremse participated. The key finding: workers don't need AI expertise — they need AI that fits into existing workflows.",
        "context": "Connected Worker platforms are the natural delivery layer for factory AI. The skills gap in manufacturing is widening — 2.1M unfilled jobs projected by 2030 in the US alone. Training new workers faster is existential for many factories. AI-generated work instructions could cut onboarding time by 40-60%."
    },
    "📉 Skills Crisis — 2.1M Jobs Unfilled by 2030": {
        "insight": "A Deloitte study shows 2.1 million manufacturing jobs will go unfilled by 2030 due to the skills gap. Meanwhile, average factory worker tenure has dropped below 3 years. The old model of 6-month apprenticeships doesn't work when your workforce turns over every 2-3 years. Some factories are now onboarding workers in days instead of months using digital guidance systems.",
        "context": "Connected Worker platforms address this directly by embedding knowledge into the workflow. Instead of training workers to memorize procedures, the system guides them in real-time. Factories using this approach report 30-50% faster onboarding and 25% fewer quality defects from new workers."
    },
    "🔧 Lean is Broken — Toyota's Model Can't Keep Up": {
        "insight": "Toyota's lean production system was revolutionary 40 years ago. But lean was designed for stable, high-volume production. Today's reality: batch sizes are shrinking, product variants are exploding, and customer demand shifts weekly. A German auto supplier went from 12 product variants to 200+ in five years. Their lean system couldn't keep up.",
        "context": "This is the core argument for Dynamic Process Execution: manufacturing needs to shift from pre-planned, rigid workflows to adaptive, real-time orchestration. Lean was like a railway schedule — efficient but inflexible. DPE is like ride-sharing — it responds to demand in real time."
    },
    "🇺🇸 US Reshoring Wave — $200B Problem": {
        "insight": "The CHIPS Act, IRA, and supply chain security concerns are driving a massive reshoring wave in US manufacturing. Over $200B in new factory investments announced since 2022. But here's the problem nobody's talking about: these new factories need workers, and the US manufacturing workforce is older and smaller than ever. You can build a $20B chip fab, but who's going to run it?",
        "context": "This is directly relevant to US market entry. New factories being built need connected worker solutions from day one — they can't rely on institutional knowledge that doesn't exist yet. Greenfield factories are the perfect entry point: no legacy systems, no change management resistance, and an urgent need for digital-first worker enablement."
    }
}

# ── Pre-generated Workerbase content ─────────────────────────

PREGENERATED = {
    "linkedin": """Your factory has 200 years of accumulated knowledge.

Your average worker has been there 2.7 years.

That's the gap nobody's talking about in the "reshoring" conversation.

Washington announced $200B+ in new factory investments since 2022. The CHIPS Act. The IRA. Supply chain security. Great.

But buildings don't make products. People do.

And the US manufacturing workforce is older and smaller than it's been in decades. The workers who knew every machine sound, every quality trick, every shortcut — they're retiring.

The new workers? They're capable. But they don't have 20 years of tribal knowledge in their heads.

This is why the real infrastructure investment isn't in concrete and steel. It's in the systems that capture knowledge and deliver it to the right person, at the right moment, on the factory floor.

The factories that win the reshoring wave won't be the ones with the most automation. They'll be the ones that figured out how to make a day-one worker perform like a year-five veteran.

That's not a training problem. That's an architecture problem.

How is your factory handling knowledge transfer to new workers?

#Manufacturing #Reshoring #Industry40 #ConnectedWorker #ManufacturingTech""",

    "blog": """# The $200 Billion Blind Spot: Why New Factories Need Digital Workers Before Day One

**The reshoring math has a people problem.**

Since 2022, over $200 billion in new US factory investments have been announced. The CHIPS Act and Inflation Reduction Act are fueling the largest manufacturing construction boom in a generation. Politicians love the photo ops. Investors love the projections.

But walk into any of these construction sites and ask the operations team one question: *Where are you going to find the workers?*

The silence is deafening.

## The Knowledge Gap Is the Real Infrastructure Problem

The US manufacturing workforce has been shrinking for decades. The average factory worker's tenure has dropped below three years. The experienced operators who could troubleshoot a production line by listening to the machines — they're retiring faster than we can replace them.

Deloitte projects 2.1 million manufacturing jobs will go unfilled by 2030. That number was calculated *before* the reshoring wave added hundreds of new facilities to the demand side.

Here's what makes this different from previous labor shortages: these new facilities are greenfield builds. There is no institutional knowledge. No veteran worker to shadow. No "ask Bob, he's been here 30 years."

## Why Digital-First Beats Train-First

The old manufacturing playbook says: hire workers, train them for months, pair them with veterans, and hope the knowledge transfers through osmosis. That model assumed stability — low turnover, long careers, gradual complexity increases.

None of those assumptions hold anymore.

The factories that will actually succeed in the reshoring wave are designing their operations around a different principle: embed the knowledge into the workflow, not into the worker's memory.

This means real-time digital guidance that walks a day-one operator through complex procedures. It means AI-powered work instructions that adapt to the specific machine, product variant, and worker skill level. It means capturing every process improvement digitally so it's available to every worker instantly — not locked in someone's head.

## The Greenfield Advantage

Ironically, new factories have an advantage here. No legacy systems to replace. No "we've always done it this way" resistance. They can build digital-first from the ground up.

The smart ones are doing exactly that. They're making connected worker platforms part of the factory design — not an afterthought bolted on after the first quality crisis.

**The takeaway:** The reshoring wave will be won or lost not by who builds the biggest factory, but by who figures out how to make new workers productive fastest. The infrastructure that matters most isn't concrete — it's digital.""",

    "reddit": """Has anyone else noticed the massive disconnect in the reshoring conversation?

I've been following the US manufacturing reshoring wave pretty closely — $200B+ in new factory investments, CHIPS Act money flowing, everyone's excited.

But I keep running into the same problem when I talk to ops people at these new facilities: where are the workers coming from?

I visited a greenfield facility last month. Beautiful building, latest equipment, impressive automation. Asked the plant manager about staffing. He basically said they're planning to hire people with zero manufacturing experience and train them on the job. For complex assembly processes.

The old model was: hire someone, pair them with a 20-year veteran for 6 months, and let the knowledge transfer through osmosis. But these new plants don't HAVE veterans. There's no institutional knowledge to transfer.

Some places are starting to use digital guidance systems that walk new workers through procedures step-by-step on tablets/wearables. Basically embedding the expertise into the system instead of relying on worker memory. Seems promising but I'm curious about real-world results.

Anyone working at a greenfield facility dealing with this? How are you handling onboarding when there's no "tribal knowledge" to lean on?

TL;DR: Reshoring wave is building tons of new factories but nobody's talking about where the skilled workers will come from. Old apprenticeship model doesn't work at greenfield sites. Digital guidance systems seem like the answer but want to hear real experiences.""",

    "email": """Subject A: The reshoring problem nobody's solving (yet)
Subject B: Your new factory needs workers. Where will they come from?
Preview: 2.1M unfilled jobs by 2030. New approach inside.

Hi [First Name],

Quick question: if you're building or expanding a factory in the US right now, where are you finding experienced workers?

The reshoring numbers are impressive — $200B+ in new investments. But every ops leader I talk to says the same thing: the buildings are going up faster than the workforce is materializing.

Deloitte's 2.1M unfilled jobs projection was calculated before the current construction boom. The gap is only widening.

The factories figuring this out aren't waiting for the labor market to fix itself. They're redesigning onboarding around digital systems that make a week-one worker perform like a month-six worker.

One automotive supplier cut new worker onboarding from 12 weeks to 3 using real-time digital guidance on the shop floor. Quality defects from new workers dropped 25%.

CTA: See how leading manufacturers are solving the skills gap → [link]"""
}

# ── Pre-generated GENERIC content (SaaS product launch) ─────

PREGENERATED_GENERIC = {
    "insight_used": "Apple Vision Pro sales have reportedly slowed to under 100K units per quarter. Meanwhile, Meta is shipping Quest 3 at $499 and enterprise AR adoption is quietly accelerating. The consumer VR/AR dream might be stalling, but the B2B use case — remote assistance, training, digital twins — is growing 40% YoY.",

    "linkedin": """Everyone's writing obituaries for spatial computing because Vision Pro isn't selling.

They're looking at the wrong market.

Consumer AR/VR? Sure, it's struggling. Vision Pro reportedly moved fewer than 100K units last quarter. The $3,500 price tag was never going to create a mass market.

But here's what nobody's covering:

Enterprise AR adoption is growing 40% year-over-year. Quietly. Without the hype cycle.

A Fortune 500 manufacturer told me their remote assistance tool paid for itself in 3 months. One fewer expert flight per week = $150K/year savings. Per site.

A surgical training platform reduced procedure errors by 30% in their first clinical trial.

A logistics company cut warehouse onboarding from 2 weeks to 3 days using AR-guided picking.

The pattern: spatial computing works when it solves a specific, expensive problem for someone who doesn't care about "the metaverse."

Consumer tech analysts keep asking "will people watch movies in VR?"

The better question: "How much does it cost when your field technician can't fix the problem remotely?"

The enterprise AR market doesn't need a viral moment. It needs ROI spreadsheets. And those are looking very good.

Where are you seeing enterprise AR/VR actually deliver value?

#SpatialComputing #EnterpriseAR #B2BTech #DigitalTransformation #Innovation""",

    "blog": """# Everyone's Wrong About Spatial Computing — The Real Market Isn't Consumers

**The headlines say VR is dead. The spreadsheets say otherwise.**

Apple Vision Pro reportedly shipped fewer than 100,000 units last quarter. Tech Twitter declared spatial computing over. Investors who poured billions into "the metaverse" are quietly writing it off.

But if you're only watching the consumer market, you're missing the story entirely.

## The Enterprise Market Nobody's Covering

While consumer VR stalls, enterprise AR adoption is growing 40% year-over-year. The use cases aren't glamorous — they don't make for exciting keynotes — but they're solving real problems with measurable ROI.

A Fortune 500 manufacturer implemented remote assistance and eliminated one expert travel trip per week. At $3,000 per trip, that's $150K per site per year. The hardware paid for itself in a single quarter.

A medical training platform reduced procedural errors by 30% in clinical trials. A logistics company cut warehouse onboarding time from two weeks to three days using AR-guided picking workflows.

## Why Enterprise Wins Where Consumer Fails

The consumer VR pitch requires convincing millions of people to change their daily habits for marginal entertainment upgrades. That's an incredibly hard sell at any price point, let alone $3,500.

The enterprise pitch is fundamentally different: here's a tool that saves you money, reduces errors, and solves a problem you're already spending six figures on. The ROI calculation does the selling.

Enterprise buyers don't need spatial computing to be "cool." They need it to be cheaper than flying a technician to a remote site. They need it to train new employees faster than classroom sessions. They need it to reduce costly errors in high-stakes procedures.

## What This Means for the Market

The spatial computing industry is going through the same phase that cloud computing did in 2008. Consumer cloud apps were struggling to monetize. Meanwhile, AWS was quietly building a $100B business serving enterprises.

The companies that will win in spatial computing aren't building the flashiest headsets. They're building the most boring, reliable, ROI-positive enterprise tools.

**The takeaway:** Stop watching Vision Pro sales numbers. Start watching enterprise AR deployment rates. That's where the real market is being built — one unglamorous ROI spreadsheet at a time.""",

    "reddit": """Is enterprise AR/VR quietly succeeding while consumer VR gets all the "it's dead" headlines?

I keep seeing articles about how Vision Pro is flopping and VR is over. But in my world (B2B tech), AR adoption is actually accelerating.

Few examples I've come across recently:

- A manufacturing client implemented remote assistance for field technicians. Saved $150K/year per site by cutting expert travel. Hardware ROI in one quarter.
- Talked to a logistics ops manager who cut warehouse onboarding from 2 weeks to 3 days with AR-guided workflows.
- Medical training platform reporting 30% fewer procedural errors in clinical trials.

None of this is "metaverse" stuff. It's boring, practical, ROI-driven tooling. The use case isn't "explore virtual worlds" — it's "how do I fix this machine without flying someone 2,000 miles."

Feels like the whole industry is being judged by consumer adoption numbers when the enterprise side is telling a completely different story.

Anyone else seeing this disconnect? Curious what AR/VR deployments look like in your industry.

TL;DR: Consumer VR struggling but enterprise AR/VR growing 40% YoY. Boring use cases (remote assistance, training, onboarding) with strong ROI. Industry might be looking at the wrong metrics.""",

    "email": """Subject A: Spatial computing isn't dead — you're watching the wrong market
Subject B: The AR market growing 40% that nobody covers
Preview: Enterprise AR is quietly winning while consumer VR stumbles.

Hi [First Name],

Quick take: every "VR is dead" headline is looking at consumer sales. The enterprise market tells a very different story.

While Vision Pro shipments slow, enterprise AR adoption is growing 40% year-over-year. The use cases aren't flashy — remote assistance, guided training, digital twins — but the ROI is undeniable.

One manufacturing deployment: remote expert assistance eliminated one field visit per week. $150K annual savings per site. Hardware paid for itself in 90 days.

The pattern is consistent: spatial computing works when it solves a specific, expensive operational problem. Not when it tries to replace your TV.

We put together a breakdown of the 5 enterprise AR use cases with the fastest payback periods.

CTA: See the enterprise AR ROI breakdown → [link]"""
}


# ── Sidebar ──────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input(
        "Claude API Key",
        type="password",
        help="Your Anthropic API key. Session only — never stored.",
        key="api_key"
    )

    st.divider()

    st.markdown("### 🏭 Context Injection")
    default_ctx = "B2B SaaS company. Customize this context for your industry — it gets injected into every generation to ensure domain-relevant output."
    context = st.text_area("Background context (injected into every prompt)", value=default_ctx, height=120)

    st.divider()

    st.markdown("### 📊 Output Channels")
    gen_linkedin = st.checkbox("LinkedIn Post", value=True)
    gen_blog = st.checkbox("Blog Draft", value=True)
    gen_reddit = st.checkbox("Reddit Thread", value=True)
    gen_email = st.checkbox("Email Sequence", value=True)

    st.divider()

    st.markdown(
        "<div style='font-size:0.75rem; color:#94a3b8; font-family: JetBrains Mono, monospace;'>"
        "Built by Ata Okuzcuoglu<br>"
        "MSc Management & Technology @ TUM<br>"
        "<br>"
        "Pipeline: Insight → Analysis → 4 Channels<br>"
        "Powered by Claude API<br>"
        "Prompt-chained, not prompt-and-pray"
        "</div>",
        unsafe_allow_html=True
    )


# ── Main Content ─────────────────────────────────────────────

st.markdown("""
<div class="hero-header">
    <div class="hero-title">⚡ ContentEngine AI</div>
    <div class="hero-subtitle">
        Raw insight in. Publish-ready content out. Four channels. Under 60 seconds.
    </div>
    <div class="hero-badge">PIPELINE v1.1 — Text · URL · PDF · DOCX · Tone & Audience Controls</div>
</div>
""", unsafe_allow_html=True)

tab_pipeline, tab_generic, tab_workerbase, tab_architecture = st.tabs([
    "🔧 Live Pipeline",
    "📦 Generic Demo",
    "🏭 Industry Demo: Workerbase",
    "🏗️ Architecture"
])


# ─── TAB 1: Live Pipeline ────────────────────────────────────
with tab_pipeline:
    st.markdown("### 📥 Drop Your Raw Insight")

    input_mode = st.radio(
        "Input method:",
        ["✍️ Write / Paste", "🔗 URL", "📄 Upload File", "📦 Demo"],
        horizontal=True,
    )

    if input_mode == "📦 Demo":
        demo_choice = st.selectbox(
            "Select a demo insight:",
            list(DEMO_INSIGHTS.keys()),
        )
        demo = DEMO_INSIGHTS[demo_choice]
        insight_text = st.text_area("Raw insight", value=demo["insight"].strip(), height=140)
        context = demo["context"].strip()

    elif input_mode == "🔗 URL":
        url_input = st.text_input(
            "Article / post URL",
            placeholder="https://techcrunch.com/2026/... — any article, blog post, or news page",
        )
        if url_input:
            with st.spinner("🔗 Fetching article content..."):
                fetched_text, error = fetch_url_content(url_input)
            if error:
                st.error(error)
                insight_text = ""
            else:
                st.success(f"Extracted {len(fetched_text.split())} words from URL")
                insight_text = st.text_area(
                    "Extracted content (edit if needed):",
                    value=fetched_text,
                    height=200,
                )
        else:
            insight_text = ""

    elif input_mode == "📄 Upload File":
        uploaded = st.file_uploader(
            "Upload a document",
            type=["pdf", "txt", "md", "csv", "docx"],
            help="Supports PDF, TXT, Markdown, CSV, DOCX. Content is extracted and used as the raw insight."
        )
        if uploaded:
            with st.spinner(f"📄 Extracting content from {uploaded.name}..."):
                file_text, error = extract_file_content(uploaded)
            if error:
                st.error(error)
                insight_text = ""
            else:
                st.success(f"Extracted {len(file_text.split())} words from {uploaded.name}")
                insight_text = st.text_area(
                    "Extracted content (edit if needed):",
                    value=file_text,
                    height=200,
                )
        else:
            insight_text = ""

    else:  # Write / Paste
        insight_text = st.text_area(
            "Raw insight",
            placeholder="Paste a news headline, competitor move, customer quote, Reddit thread, press release, or any raw signal...",
            height=140,
        )

    # ── Tone & Audience Controls ──────────────────────────────
    st.markdown("---")
    st.markdown("### 🎨 Content Controls")
    col_tone, col_audience = st.columns(2)

    with col_tone:
        selected_tone = st.selectbox(
            "Tone",
            list(TONE_OPTIONS.keys()),
            index=0,
            help="Controls the voice and style of all generated content."
        )
        tone_desc = TONE_OPTIONS[selected_tone]

    with col_audience:
        selected_audience = st.selectbox(
            "Target Audience",
            list(AUDIENCE_OPTIONS.keys()),
            index=4,  # Default: General / Mixed
            help="Adjusts complexity, jargon, and framing for the target reader."
        )
        audience_desc = AUDIENCE_OPTIONS[selected_audience]

    st.caption(f"**Tone:** {tone_desc}  \n**Audience:** {audience_desc}")

    st.markdown("---")

    channels = []
    if gen_linkedin: channels.append("linkedin")
    if gen_blog: channels.append("blog")
    if gen_reddit: channels.append("reddit")
    if gen_email: channels.append("email")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run = st.button("⚡ Run Pipeline", type="primary", use_container_width=True)
    with col_info:
        st.caption(f"{len(channels)} channels selected · ~{len(channels) * 8 + 5}s estimated")

    if run:
        if not insight_text.strip():
            st.warning("Please enter a raw insight to process.")
        elif not api_key:
            st.warning("Please enter your Claude API key in the sidebar.")
        else:
            client = get_client()
            if client:
                start_time = time.time()

                # Step 1: Analysis
                with st.status("🔍 Analyzing insight...", expanded=True) as status:
                    st.write("Extracting core angle, pain points, and content hooks...")
                    analysis = analyze_insight(client, insight_text, context)

                    if analysis:
                        status.update(label="✅ Analysis complete", state="complete")
                        st.markdown(f"""
<div class="analysis-card">
    <div class="analysis-title">📊 Content Analysis</div>
    <p><strong>Core Angle:</strong> {analysis.get('core_angle', 'N/A')}</p>
    <p><strong>Audience Pain:</strong> {analysis.get('audience_pain', 'N/A')}</p>
    <p><strong>Contrarian Take:</strong> {analysis.get('contrarian_take', 'N/A')}</p>
    <p><strong>Why Now:</strong> {analysis.get('trending_relevance', 'N/A')}</p>
</div>""", unsafe_allow_html=True)
                        hooks = analysis.get('content_hooks', [])
                        if hooks:
                            st.markdown("**Content Hooks:**")
                            for h in hooks:
                                st.markdown(f"- {h}")
                    else:
                        status.update(label="⚠️ Analysis skipped — generating directly", state="complete")

                # Step 2: Generate
                st.markdown("---")
                st.markdown("### 📤 Generated Content")

                channel_labels = {
                    "linkedin": "💼 LinkedIn Post",
                    "blog": "📝 Blog Draft",
                    "reddit": "🟠 Reddit Thread",
                    "email": "📧 Email Sequence"
                }

                results = {}
                progress = st.progress(0)
                for i, ch in enumerate(channels):
                    with st.spinner(f"Generating {channel_labels[ch]}..."):
                        results[ch] = generate_content(client, ch, insight_text, context, tone_desc, audience_desc)
                    progress.progress((i + 1) / len(channels))

                elapsed = time.time() - start_time

                # Stats
                st.markdown("---")
                cols = st.columns(4)
                total_words = sum(len(v.split()) for v in results.values())
                wps = total_words / elapsed if elapsed > 0 else 0
                stats = [
                    (str(len(channels)), "Channels"),
                    (str(total_words), "Words Generated"),
                    (f"{elapsed:.1f}s", "Pipeline Time"),
                    (f"{wps:.0f}", "Words/sec")
                ]
                for col, (num, label) in zip(cols, stats):
                    with col:
                        st.markdown(f'<div class="stat-box"><div class="stat-number">{num}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

                st.markdown("---")

                # Output cards
                for ch in channels:
                    st.markdown(f'<div class="content-card"><div class="card-label">{channel_labels[ch]}</div></div>', unsafe_allow_html=True)
                    st.text_area(
                        f"{ch} output",
                        value=results[ch],
                        height=300,
                        key=f"out_{ch}",
                        label_visibility="collapsed"
                    )
                    st.download_button(
                        f"📋 Download {ch}",
                        results[ch],
                        file_name=f"contentengine_{ch}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        key=f"dl_{ch}"
                    )


# ─── TAB 2: Generic Demo ──────────────────────────────────────
with tab_generic:
    st.markdown("""
    ### 📦 Generic Demo — Enterprise Tech Content

    This demonstrates the pipeline on a **non-manufacturing insight** to show
    it works across any B2B domain. No API key needed — content is pre-generated.

    **Input insight:** Enterprise AR/VR is quietly growing 40% YoY while consumer
    VR gets "it's dead" headlines. The real market is boring, ROI-driven tooling.
    """)

    st.markdown("---")

    generic_config = [
        ("💼 LINKEDIN POST", "linkedin", 380),
        ("📝 BLOG DRAFT", "blog", 500),
        ("🟠 REDDIT THREAD", "reddit", 350),
        ("📧 EMAIL SEQUENCE", "email", 280),
    ]

    for label, key, height in generic_config:
        st.markdown(f'<div class="content-card"><div class="card-label">{label}</div></div>', unsafe_allow_html=True)
        st.text_area(f"generic_{key}", value=PREGENERATED_GENERIC[key], height=height, key=f"gen_{key}", label_visibility="collapsed")
        st.download_button(f"📋 Copy {key}", PREGENERATED_GENERIC[key], file_name=f"generic_{key}.txt", key=f"dl_gen_{key}")
        st.markdown("---")

    st.info("💡 **Same pipeline, different domain.** Swap the system prompt and context injection to adapt for any industry — SaaS, fintech, healthcare, logistics.")


# ─── TAB 3: Workerbase Industry Demo ─────────────────────────
with tab_workerbase:
    st.markdown("""
    ### 🏭 Industry Demo — Manufacturing / Workerbase

    Pre-generated content for a **Connected Worker platform** entering the US market.
    Shows the pipeline configured with manufacturing domain expertise.

    **Input insight:** US Manufacturing Reshoring Wave — $200B+ in new factory investments,
    but nobody's talking about where the skilled workers will come from.

    *One raw insight → four channel-native outputs → under 60 seconds.*
    """)

    st.markdown("---")

    channel_config = [
        ("💼 LINKEDIN POST — Ready to Publish", "linkedin", 350),
        ("📝 BLOG DRAFT — Ready for Editorial Review", "blog", 500),
        ("🟠 REDDIT THREAD — Native Tone, Zero Promotion", "reddit", 350),
        ("📧 EMAIL SEQUENCE — With A/B Subject Lines", "email", 280),
    ]

    for label, key, height in channel_config:
        st.markdown(f'<div class="content-card"><div class="card-label">{label}</div></div>', unsafe_allow_html=True)
        st.text_area(key, value=PREGENERATED[key], height=height, key=f"show_{key}", label_visibility="collapsed")
        st.download_button(f"📋 Copy {key}", PREGENERATED[key], file_name=f"workerbase_{key}.txt", key=f"dl_show_{key}")
        st.markdown("---")

    st.info("💡 **All four outputs came from the same raw insight.** The pipeline maintains narrative consistency while adapting tone, format, and CTA for each channel.")


# ─── TAB 4: Architecture ─────────────────────────────────────
with tab_architecture:
    st.markdown("""
    ### 🏗️ How ContentEngine Works

    This isn't a wrapper around ChatGPT. It's a **structured pipeline** with
    domain-specific prompt engineering at every stage.
    """)

    st.markdown("---")

    st.markdown("#### Pipeline Flow")
    st.code("""
    ┌─────────────────┐
    │     INPUTS       │
    │                  │
    │  ✍️ Text/Paste    │     ┌──────────────┐     ┌─────────────────────┐
    │  🔗 URL Import   │────→│   ANALYSIS   │────→│  PARALLEL GENERATE  │
    │  📄 PDF Upload   │     │  (AI layer)  │     │  + Tone & Audience  │
    │  📎 DOCX/CSV     │     └──────────────┘     │                     │
    │  📦 Demo         │           │               │  ├─ LinkedIn Post    │
    └─────────────────┘      Extracts:            │  ├─ Blog Draft       │
                              · Core angle         │  ├─ Reddit Thread    │
              ┌───────┐       · Pain point         │  └─ Email Sequence   │
              │ TONE  │       · Contrarian take     └─────────────────────┘
              │ CTRL  │       · Content hooks                │
              └───┬───┘       · Channel ranking        ┌─────┴─────┐
              ┌───┴────┐                               │  4 OUTPUTS │
              │AUDIENCE │                              │  < 60 sec  │
              │  CTRL   │                              └───────────┘
              └────────┘
    """, language=None)

    st.markdown("---")

    st.markdown("#### Prompt-and-Pray vs. Pipeline")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **❌ Prompt-and-Pray**
        - Open ChatGPT
        - "Write me a LinkedIn post"
        - Get generic output
        - Manually rewrite for other channels
        - No domain expertise baked in
        - Inconsistent across channels
        """)
    with col2:
        st.markdown("""
        **✅ ContentEngine Pipeline**
        - Structured input → analysis → generation
        - Domain-specific system prompt (swappable)
        - Format-specific prompt per channel
        - Anti-fluff rules at system level
        - One insight → consistent narrative × 4
        - Channel-native tone automatically
        """)

    st.markdown("---")

    st.markdown("#### Technical Stack")
    st.markdown("""
    | Layer | Detail |
    |---|---|
    | **Model** | Claude Sonnet 4 (`claude-sonnet-4-20250514`) |
    | **Prompt Architecture** | System prompt (domain) + Format prompts (channel) + Context injection (company) |
    | **Analysis Layer** | JSON-structured insight extraction before content generation |
    | **Anti-fluff System** | Rules at system prompt level — no buzzwords without data, domain-specific perspective required |
    | **Extensibility** | New channel = new format prompt + 15 minutes of work |
    | **Deployment** | Streamlit Cloud — zero-config, shareable link |
    """)

    st.markdown("---")

    st.markdown("#### Scaling Roadmap")
    st.markdown("""
    **v2 — Monitoring Layer** → RSS feeds from industry news, competitor blog monitors,
    Reddit/HN keyword alerts → auto-surface insights for human review

    **v3 — Workflow Integration** → HubSpot API (email sequences), Buffer (social scheduling),
    Slack notifications (content ready for review), content calendar auto-population

    **v4 — Performance Loop** → Track insight → content → engagement, feed performance data
    back into prompt optimization, A/B test system prompts based on channel metrics
    """)

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#94a3b8; font-size:0.85rem; padding:1rem;'>"
        "Built by <strong>Ata Okuzcuoglu</strong> · MSc Management & Technology @ TUM · "
        "<a href='https://linkedin.com/in/atakzcgl' style='color:#6366f1;'>LinkedIn</a>"
        "</div>",
        unsafe_allow_html=True
    )
