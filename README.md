# Candidate Profile Normalization Pipeline

Turns messy, multi-source candidate data (recruiter CSV, ATS JSON, GitHub profile,
resume PDF) into one clean, canonical, confidence-scored candidate profile.

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

## Run — default schema (full canonical profile)

```bash
python main.py --csv data/sample_recruiter.csv --json data/sample_ats.json --pdf data/sample_resume.pdf --github octocat
```

Writes the full canonical profile to `outputs/profile.json`.

## Run — custom output config

```bash
python main.py --csv data/sample_recruiter.csv --json data/sample_ats.json --pdf data/sample_resume.pdf --github octocat --config configs/default_config.json --output outputs/profile_custom.json
```

Same engine, reshaped output — see `configs/default_config.json` for the config format
(field selection, renaming, per-field normalization, missing-value behavior).

## Run tests

```bash
pytest tests/ -v
```

## Architecture

Six stages: extract → normalize → identity-aware merge → confidence/provenance →
project → validate. See `<YourName>_<YourEmail>_Eightfold.pdf` for full design rationale.

- `pipeline/extractors/` — one parser per source type, each fails safely (returns `{}`)
  rather than crashing on a missing/malformed source.
- `pipeline/normalizers/` — phone (E.164), date (YYYY-MM), skills (canonical lexicon),
  years-of-experience calculation.
- `pipeline/merger.py` — unions list fields (emails/phones/skills) with dedup, resolves
  scalar fields (name/headline) via source priority, logs every resolved conflict.
- `pipeline/projector.py` — reshapes the canonical record per a runtime JSON config,
  with no code changes required.
- `pipeline/validator.py` — checks the canonical record and projected output before
  they're returned.

## Assumptions & notes

- GitHub's API `name` field is treated as a display name, not a verified identity
  source — it is deprioritized for `full_name` resolution but still used for skills,
  bio, and links, since it's machine-verified and hard to fake for those fields.
- `years_experience` sums all listed job durations; overlapping employment periods
  (e.g. concurrent freelance + full-time work) would currently be overcounted — a
  known, documented limitation rather than a silent bug.
- LinkedIn scraping was descoped (no stable public API); GitHub is the primary
  unstructured-API source instead.

## Demo video

<link here, ~2 min, shows default + custom-config run plus one design decision and
one edge case>
