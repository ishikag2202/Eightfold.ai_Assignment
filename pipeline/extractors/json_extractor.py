import json


def extract(filepath):
    """Extract candidate fields from an ATS JSON blob with non-standard field names."""
    try:
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)

        experience = []
        for job in data.get("work_history", []):
            experience.append({
                "company": job.get("employer", ""),
                "title": job.get("position", ""),
                "start": job.get("from"),
                "end": job.get("to"),
                "summary": None,
            })

        education = []
        for edu in data.get("education", []):
            education.append({
                "institution": edu.get("school", ""),
                "degree": edu.get("degree", ""),
                "field": edu.get("major", ""),
                "end_year": edu.get("year"),
            })

        return {
            "full_name": data.get("applicant_name", "").strip(),
            "emails": [data["contact_email"]] if data.get("contact_email") else [],
            "phones": [data["mobile"]] if data.get("mobile") else [],
            "skills": data.get("skills_list", []),
            "experience": experience,
            "education": education,
            "_source": "ats_json",
        }
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[json_extractor] failed on {filepath}: {e}")
        return {}