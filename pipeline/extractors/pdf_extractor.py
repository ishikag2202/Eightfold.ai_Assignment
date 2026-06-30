import re
import pdfplumber

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'\+?\d[\d\s\-\(\)]{8,}\d')
LINKEDIN_RE = re.compile(r'linkedin\.com/in/[\w-]+')
GITHUB_RE = re.compile(r'github\.com/[\w-]+')

# Resume convention: a "SUMMARY" section header followed by 1-2 sentences
SUMMARY_RE = re.compile(r'SUMMARY\s*\n(.+?)(?:\n[A-Z]{4,}|\Z)', re.DOTALL)

# Loose city/state/country pattern, e.g. "San Francisco, CA, USA"
LOCATION_RE = re.compile(r'([A-Z][a-zA-Z\s]+,\s*[A-Z]{2},\s*[A-Z]{2,})')


def extract(filepath):
    """Extract candidate fields from a resume PDF via text + regex parsing."""
    try:
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"

        emails = list(dict.fromkeys(EMAIL_RE.findall(text)))
        phones_raw = PHONE_RE.findall(text)
        phones = [re.sub(r'\s+', ' ', p).strip() for p in phones_raw]

        linkedin_matches = LINKEDIN_RE.findall(text)
        github_matches = GITHUB_RE.findall(text)

        # Headline: first sentence of the SUMMARY section, if present
        # Headline: first sentence of the SUMMARY section, if present.
        # Collapse internal whitespace (incl. line-wrap newlines from the PDF's
        # text layer) the same way phones[] is cleaned above -- otherwise a
        # summary sentence that wraps mid-PDF-line ends up with a literal "\n"
        # baked into the headline field.
        summary_match = SUMMARY_RE.search(text)
        headline = None
        if summary_match:
            summary_text = re.sub(r'\s+', ' ', summary_match.group(1)).strip()
            first_sentence = summary_text.split(". ")[0].strip()
            headline = first_sentence if first_sentence else None

        # Location: first city/state/country-shaped match in the header area
        location_match = LOCATION_RE.search(text)
        location_raw = location_match.group(1).strip() if location_match else None

        return {
            "emails": emails,
            "phones": phones[:3],
            "raw_text": text,
            "headline": headline,
            "location_raw": location_raw,
            "links": {
                "linkedin": f"https://{linkedin_matches[0]}" if linkedin_matches else None,
                "github": f"https://{github_matches[0]}" if github_matches else None,
            },
            "_source": "resume_pdf",
        }
    except Exception as e:
        print(f"[pdf_extractor] failed on {filepath}: {e}")
        return {}