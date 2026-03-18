"""ContentEngine AI — Content Extractors."""

import requests
from bs4 import BeautifulSoup

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
