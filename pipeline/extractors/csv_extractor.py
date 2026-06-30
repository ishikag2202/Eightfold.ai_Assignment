import csv


def extract(filepath):
    """Extract candidate fields from a recruiter CSV export."""
    try:
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            return {}
        row = rows[0]
        return {
            "full_name": row.get("name", "").strip(),
            "emails": [row["email"].strip()] if row.get("email") else [],
            "phones": [row["phone"].strip()] if row.get("phone") else [],
            "current_company": row.get("current_company", "").strip(),
            "title": row.get("title", "").strip(),
            "_source": "recruiter_csv",
        }
    except (FileNotFoundError, csv.Error, KeyError) as e:
        print(f"[csv_extractor] failed on {filepath}: {e}")
        return {}