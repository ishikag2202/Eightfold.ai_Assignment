import re
import uuid
from pipeline.normalizers.phone import normalize_e164
from pipeline.normalizers.date import normalize_yyyy_mm
from pipeline.normalizers import skills as skills_norm
from pipeline.normalizers.years import calculate_years_experience
from pipeline.normalizers.location import normalize_location
from pipeline.confidence import (
    pick_field_winner, score_field, weighted_overall_confidence
)

EMAIL_VALIDATION_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

def _normalize_name(name):
    if not name:
        return name
    return re.sub(r'\s+', ' ', name).strip()


def merge(extracted_records):
    name_candidates = []
    headline_candidates = []
    location_candidates = []
    all_emails, all_phones, all_skills = [], [], []
    all_experience, all_education = [], []
    all_links = {}
    provenance = []
    conflicts = []
    field_confidences = {}

    for record in extracted_records:
        if not record:
            continue
        src = record.get("_source", "unknown")

        if record.get("full_name"):
            name_candidates.append((_normalize_name(record["full_name"]), src))

        if record.get("headline"):
            headline_candidates.append((record["headline"], src))

        if record.get("location_raw"):
            location_candidates.append((record["location_raw"], src))

        if record.get("links"):
            for k, v in record["links"].items():
                if v:
                    all_links[k] = v

        for ph in record.get("phones", []):
            normalized = normalize_e164(ph)
            all_phones.append((normalized, src, ph, normalized is not None))

        for em in record.get("emails", []):
            if em and EMAIL_VALIDATION_RE.match(em.strip()):
                all_emails.append((em.lower().strip(), src))

        for sk in record.get("skills", []):
            all_skills.append((sk, src))

        for exp in record.get("experience", []):
            exp = dict(exp)
            exp["start"] = normalize_yyyy_mm(exp.get("start"))
            exp["end"] = normalize_yyyy_mm(exp.get("end"))
            all_experience.append(exp)

        all_education.extend(record.get("education", []))

    # ---- full_name ----
    best_name, name_src = pick_field_winner("full_name", name_candidates)
    if name_src:
        distinct_values = {v for v, _ in name_candidates}
        has_conflict = len(distinct_values) > 1
        agreeing = sum(1 for v, s in name_candidates if v == best_name and s != name_src)
        conf = score_field("full_name", name_src, agreeing_source_count=agreeing, has_conflict=has_conflict)
        field_confidences["full_name"] = conf
        provenance.append({
            "field": "full_name", "source": name_src, "method": "field_priority",
            "normalization": "whitespace_cleanup", "confidence": conf
        })
        if has_conflict:
            conflicts.append({
                "field": "full_name",
                "values": [{"value": v, "source": s} for v, s in name_candidates],
                "resolved_to": best_name,
                "method": "field_priority",
            })

    # ---- headline ----
    best_headline, headline_src = pick_field_winner("headline", headline_candidates)
    if headline_src:
        distinct_values = {v for v, _ in headline_candidates}
        has_conflict = len(distinct_values) > 1
        agreeing = sum(1 for v, s in headline_candidates if v == best_headline and s != headline_src)
        conf = score_field("headline", headline_src, agreeing_source_count=agreeing, has_conflict=has_conflict)
        field_confidences["headline"] = conf
        provenance.append({
            "field": "headline", "source": headline_src, "method": "field_priority",
            "normalization": "none", "confidence": conf
        })

    # ---- location ----
    best_location_raw, location_src = pick_field_winner("location", location_candidates)
    location_value = normalize_location(best_location_raw) if best_location_raw else None
    if location_src:
        distinct_values = {v for v, _ in location_candidates}
        has_conflict = len(distinct_values) > 1
        agreeing = sum(1 for v, s in location_candidates if v == best_location_raw and s != location_src)
        conf = score_field("location", location_src, agreeing_source_count=agreeing, has_conflict=has_conflict)
        field_confidences["location"] = conf
        provenance.append({
            "field": "location", "source": location_src, "method": "field_priority",
            "normalization": "city_region_country_split", "confidence": conf
        })

    # ---- emails: union + dedup ----
    seen_emails = {}
    for val, src in all_emails:
        seen_emails.setdefault(val, []).append(src)
    unique_emails = list(seen_emails.keys())
    email_field_scores = []
    for val, sources in seen_emails.items():
        _, winner_src = pick_field_winner("emails", [(val, s) for s in sources])
        winner_src = winner_src or sources[0]
        conf = score_field("emails", winner_src, agreeing_source_count=len(sources) - 1)
        email_field_scores.append(conf)
        provenance.append({
            "field": "emails", "source": winner_src, "method": "union_dedup",
            "normalization": "lowercase_trim", "confidence": conf
        })
    if email_field_scores:
        field_confidences["emails"] = round(sum(email_field_scores) / len(email_field_scores), 2)

    # ---- phones: union + dedup ----
    seen_phones = {}
    for normalized, src, raw, norm_ok in all_phones:
        if normalized is None:
            continue
        seen_phones.setdefault(normalized, []).append((src, norm_ok))
    unique_phones = list(seen_phones.keys())
    phone_field_scores = []
    for val, source_pairs in seen_phones.items():
        sources = [s for s, _ in source_pairs]
        _, winner_src = pick_field_winner("phones", [(val, s) for s in sources])
        winner_src = winner_src or sources[0]
        conf = score_field("phones", winner_src, agreeing_source_count=len(sources) - 1,
                            normalization_succeeded=True)
        phone_field_scores.append(conf)
        provenance.append({
            "field": "phones", "source": winner_src, "method": "union_dedup",
            "normalization": "E164", "confidence": conf
        })
    if phone_field_scores:
        field_confidences["phones"] = round(sum(phone_field_scores) / len(phone_field_scores), 2)

    # ---- skills: canonicalize + dedup ----
    # NOTE: "sources" is a dict used as an insertion-ordered set (keys only, values
    # unused/None). A plain set() here would make iteration order depend on Python's
    # string hash randomization (PYTHONHASHSEED), so the same input could produce a
    # different sources[] order across separate runs -- breaking the "same inputs
    # produce the same output" determinism requirement. dict preserves insertion order
    # (guaranteed since Python 3.7), so sources always come out in first-seen order.
    skill_sources_map = {}
    for raw_skill, src in all_skills:
        canonical = skills_norm.canonicalize(raw_skill)
        if canonical:
            skill_sources_map.setdefault(canonical.lower(), {"name": canonical, "sources": {}})
            skill_sources_map[canonical.lower()]["sources"][src] = None

    skills_with_conf = []
    skill_field_scores = []
    for entry in skill_sources_map.values():
        sources_list = list(entry["sources"].keys())
        _, winner_src = pick_field_winner("skills", [(entry["name"], s) for s in sources_list])
        winner_src = winner_src or sources_list[0]
        conf = score_field("skills", winner_src, agreeing_source_count=len(sources_list) - 1)
        skill_field_scores.append(conf)
        skills_with_conf.append({
            "name": entry["name"],
            "confidence": conf,
            "sources": sources_list,
        })
    if skill_field_scores:
        field_confidences["skills"] = round(sum(skill_field_scores) / len(skill_field_scores), 2)

    # ---- experience / education ----
    if all_experience:
        exp_sources = {r.get("_source") for r in extracted_records if r and r.get("experience")}
        if exp_sources:
            _, winner_src = pick_field_winner("experience", [(True, s) for s in exp_sources])
            winner_src = winner_src or list(exp_sources)[0]
            conf = score_field("experience", winner_src, agreeing_source_count=len(exp_sources) - 1)
            field_confidences["experience"] = conf
            provenance.append({
                "field": "experience", "source": winner_src, "method": "field_priority",
                "normalization": "date_to_YYYY-MM", "confidence": conf
            })

    if all_education:
        edu_sources = {r.get("_source") for r in extracted_records if r and r.get("education")}
        if edu_sources:
            _, winner_src = pick_field_winner("education", [(True, s) for s in edu_sources])
            winner_src = winner_src or list(edu_sources)[0]
            conf = score_field("education", winner_src, agreeing_source_count=len(edu_sources) - 1)
            field_confidences["education"] = conf
            provenance.append({
                "field": "education", "source": winner_src, "method": "field_priority",
                "normalization": "none", "confidence": conf
            })

    if all_links:
        link_sources = {r.get("_source") for r in extracted_records if r and r.get("links")}
        if link_sources:
            winner_src = list(link_sources)[0]
            conf = score_field("links", winner_src, agreeing_source_count=len(link_sources) - 1)
            field_confidences["links"] = conf

    # ---- years_experience: inferred, not directly sourced ----
    years_exp = calculate_years_experience(all_experience)

    # ---- overall_confidence ----
    overall_confidence = weighted_overall_confidence(field_confidences)

    contributing_sources = {r.get("_source") for r in extracted_records if r}

    return {
        "candidate_id": str(uuid.uuid4()),
        "full_name": best_name,
        "emails": unique_emails,
        "phones": unique_phones,
        "location": location_value,
        "links": all_links,
        "headline": best_headline,
        "years_experience": years_exp,
        "skills": skills_with_conf,
        "experience": all_experience,
        "education": all_education,
        "provenance": provenance,
        "conflicts": conflicts,
        "overall_confidence": overall_confidence,
        "source_count": len(contributing_sources),
    }