SKILL_ALIASES = {
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "python": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "docker": "Docker",
    "aws": "AWS",
    "go": "Go",
    "golang": "Go",
    "sql": "SQL",
    # Below: GitHub Linguist language names that .title() would otherwise
    # mangle (e.g. "css".title() -> "Css", not "CSS"). These show up via
    # github_extractor's repo.get("language") values, so anyone whose repos
    # include these languages would hit the same casing bug as CSS/HTML did.
    "css": "CSS",
    "html": "HTML",
    "php": "PHP",
    "c": "C",
    "c++": "C++",
    "c#": "C#",
    "objective-c": "Objective-C",
    "tex": "TeX",
    "ruby": "Ruby",
    "shell": "Shell",
    "vim script": "Vim Script",
    "jupyter notebook": "Jupyter Notebook",
}

def canonicalize(skill):
    """Map a raw skill string to its canonical display name."""
    if not skill:
        return None
    key = skill.lower().strip()
    return SKILL_ALIASES.get(key, skill.strip().title())


def deduplicate(skills):
    """Canonicalize and deduplicate a list of raw skill strings, case-insensitively."""
    seen = set()
    result = []
    for raw in skills:
        canonical = canonicalize(raw)
        if canonical and canonical.lower() not in seen:
            seen.add(canonical.lower())
            result.append(canonical)
    return result