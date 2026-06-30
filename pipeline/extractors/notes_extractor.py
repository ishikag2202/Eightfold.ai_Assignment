import re

EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}')
LINKEDIN_RE = re.compile(r'linkedin\.com/in/[\w-]+')
GITHUB_RE = re.compile(r'github\.com/[\w-]+')
YEARS_EXP_RE = re.compile(r'(\d+)\+?\s*years?\s+(?:of\s+)?(?:total\s+)?experience', re.IGNORECASE)

# Lightweight keyword list — free text is noisy, so we only flag skills that
# appear as standalone, clearly-stated technical terms rather than trying to
# do full NLP extraction. Deliberately conservative: better to miss a skill
# than to hallucinate one from loose text.
KNOWN_SKILL_KEYWORDS = [
    "python", "java", "javascript", "kubernetes", "docker", "react",
    "node.js", "nodejs", "aws", "go", "golang", "sql", "pytorch",
    "tensorflow", "machine learning", "ml", "c++", "rust",
]


def extract(filepath):
    """Extract whatever can be confidently pulled from free-text recruiter notes."""
    try:
        with open(filepath, encoding='utf-8') as f:
            text = f.read()

        emails = list(dict.fromkeys(EMAIL_RE.findall(text)))

        linkedin_matches = LINKEDIN_RE.findall(text)
        github_matches = GITHUB_RE.findall(text)

        skills_found = []
        text_lower = text.lower()
        for keyword in KNOWN_SKILL_KEYWORDS:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                skills_found.append(keyword)

        years_match = YEARS_EXP_RE.search(text)
        years_mentioned = int(years_match.group(1)) if years_match else None

        return {
            "emails": emails,
            "skills": skills_found,
            "links": {
                "linkedin": f"https://{linkedin_matches[0]}" if linkedin_matches else None,
                "github": f"https://{github_matches[0]}" if github_matches else None,
            },
            "years_experience_mentioned": years_mentioned,
            "raw_text": text,
            "_source": "notes_txt",
        }
    except FileNotFoundError as e:
        print(f"[notes_extractor] failed on {filepath}: {e}")
        return {}