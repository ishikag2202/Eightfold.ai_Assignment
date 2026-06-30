# Multi-Source Candidate Data Transformer

Eightfold Engineering Intern Assignment (Jul–Dec 2026) — Step 2 implementation.

Turns messy, conflicting candidate data from multiple sources into one clean, confidence-scored, fully-auditable canonical profile — then reshapes that profile into whatever output a runtime config asks for, with no code changes.

The accompanying one-page technical design document (Step 1) covers the reasoning behind these choices in more depth; this README covers how to actually run the thing.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Setup](#setup)
- [Pipeline Overview](#pipeline-overview)
- [Canonical Output Schema](#canonical-output-schema)
- [Merge / Conflict-Resolution Policy](#merge--conflict-resolution-policy)
- [Confidence Scoring](#confidence-scoring)
- [Runtime Custom-Output Config](#runtime-custom-output-config)
- [CLI Reference](#cli-reference)
- [Sample Data](#sample-data)
- [Running the Tests](#running-the-tests)
- [Known Gaps & Descoped Items](#known-gaps--descoped-items)
- [Project Structure](#project-structure)

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py --csv data/sample_recruiter.csv --json data/sample_ats.json --pdf data/sample_resume.pdf --notes data/sample_notes.txt --config configs/default_config.json --output outputs/profile.json
```

That's it — this runs the full pipeline on the provided sample inputs and writes a schema-valid candidate profile to `outputs/profile.json`. Full setup and every other command are below.

---

## Setup

**Requirements:** Python 3.12 or 3.13. Tested on both Windows and Linux.

1. Clone the repo and `cd` into it.

2. (Recommended) Create a virtual environment:
```bash
   python -m venv venv
```
   Activate it:
   - Windows (PowerShell): `venv\Scripts\Activate.ps1`
   - macOS / Linux: `source venv/bin/activate`

3. Install dependencies:
```bash
   pip install -r requirements.txt
```

   | Package | Used for |
   |---|---|
   | `phonenumbers` | Phone number parsing and E.164 normalization |
   | `pdfplumber` | Extracting text from resume PDFs |
   | `requests` | Calling the GitHub REST API |
   | `python-dateutil` | Flexible date parsing for the date normalizer |
   | `click` | The CLI in `main.py` |
   | `pytest` | The test suite |

No API keys are required. The GitHub extractor calls the public, unauthenticated GitHub API, which is rate-limited to 60 requests/hour per IP — see [Known Gaps](#known-gaps--descoped-items) if you hit this.

---

## Pipeline Overview

Five independent extractors feed a shared `normalize → merge + confidence → project → validate` chain. Each extractor wraps its own source in a try/except and returns an empty dict on failure instead of raising — a missing or malformed source degrades the run, it never crashes it.

![Pipeline flowchart](docs/pipeline_flowchart.png)

| Stage | What it does | Code |
|---|---|---|
| **Extract** | One parser per source type. Always returns a dict, even on failure (`{}`). | `pipeline/extractors/` |
| **Normalize** | Dates → `YYYY-MM`, phones → E.164, skill names → a canonical lexicon, location → `{city, region, country}`. | `pipeline/normalizers/` |
| **Merge + Confidence** | List fields are unioned and deduplicated; scalar fields use a fixed source-priority winner. Every conflict is logged. | `pipeline/merger.py`, `pipeline/confidence.py` |
| **Project** | A separate layer reshapes the canonical record into whatever shape the runtime config requests. | `pipeline/projector.py` |
| **Validate** | The projected output is re-checked against the requested schema (types + required fields) before being returned. | `pipeline/validator.py` |

Supported sources (the assignment requires at least one structured + one unstructured — this implementation covers both groups and then some):

| Source | Group | Flag |
|---|---|---|
| Recruiter CSV export | Structured | `--csv` |
| ATS JSON blob | Structured | `--json` |
| GitHub profile | Unstructured | `--github` |
| Resume PDF | Unstructured | `--pdf` |
| Recruiter notes (.txt) | Unstructured | `--notes` |

---

## Canonical Output Schema

This is the internal, fixed-shape record every config projection is derived from. It matches the assignment's default schema, plus two additions noted in bold.

| Field | Type / Shape | Notes |
|---|---|---|
| `candidate_id` | `string` | UUID, generated fresh each merge run |
| `full_name` | `string` | Whitespace-normalized; source-priority winner across sources |
| `emails[]` | `string[]` | Lowercased, trimmed, regex-validated, deduplicated; malformed values are dropped, never invented |
| `phones[]` | `string[]` | E.164 format (e.g. `+14155550192`); defaults to US region if no country code is present |
| `location` | `{city, region, country}` | `country` is mapped to `"US"` when the source says USA/US; other countries currently pass through unmapped (see [Known Gaps](#known-gaps--descoped-items)) |
| `links` | `{linkedin, github, portfolio, other[]}` | Extracted from resume text, recruiter notes, and the GitHub API; last-write-wins on conflict (the one field without conflict logging) |
| `headline` | `string` or `null` | Best available short title/summary; source-priority winner |
| `years_experience` | `number` or `null` | Inferred from summed `experience[]` date ranges, not directly sourced from any one input |
| `skills[]` | `{name, confidence, sources[]}` | Canonicalized + deduplicated skill names; `sources[]` lists every source that mentioned this skill |
| `experience[]` | `{company, title, start, end, summary}` | Dates normalized to `YYYY-MM`; concatenated across sources, not yet cross-source deduplicated (see [Known Gaps](#known-gaps--descoped-items)) |
| `education[]` | `{institution, degree, field, end_year}` | Same as `experience[]` — concatenated, not yet cross-source deduplicated |
| `provenance[]` | `{field, source, method, normalization, confidence}` | One entry per resolved field — the audit trail for every value in the record |
| **`conflicts[]`** | `{field, values[], resolved_to, method}` | **Addition beyond the brief's schema** — logs every overridden value, not just the winner, so a merge decision is auditable rather than silent |
| `overall_confidence` | `number` | Weight-normalized mean of populated field scores, scaled by a completeness factor |
| **`source_count`** | `number` | **Addition beyond the brief's schema** — count of distinct sources that contributed to this record |

---

## Merge / Conflict-Resolution Policy

The match key is the candidate as a whole — this is a single-candidate-per-run pipeline, not a cross-candidate identity-resolution system. For each scalar field, every source's value competes; a fixed, field-specific priority order picks the winner. A source not listed for a given field ranks below every listed source, never above.

| Field | Priority order (highest → lowest) |
|---|---|
| `full_name` | `github_api` → `recruiter_csv` → `resume_pdf` → `ats_json` |
| `emails` / `phones` | `resume_pdf` → `recruiter_csv` → `ats_json` (winner is credited in provenance; all valid values are still unioned regardless) |
| `skills` | `notes_txt` → `resume_pdf` → `github_api` → `ats_json` |
| `experience` / `education` | `ats_json` → `resume_pdf` |
| `location` | `resume_pdf` → `ats_json` |
| `headline` | `resume_pdf` → `github_api` → `ats_json` → `recruiter_csv` → `notes_txt` |

List fields (`emails`, `phones`, `skills`) are unioned and deduplicated rather than picking one winner — losing a valid alternate contact or a real skill is worse than carrying a duplicate.

---

## Confidence Scoring
confidence = (source_reliability × extraction_confidence × normalization_success)
+ agreement_bonus − conflict_penalty,
clamped to [0, 1]

| Source | Reliability |
|---|---|
| `ats_json` | 0.95 |
| `github_api` | 0.92 |
| `recruiter_csv` | 0.90 |
| `resume_pdf` | 0.85 |
| `notes_txt` | 0.70 |

- **Agreement bonus:** `+0.05` if one other source agrees on a value, `+0.10` if two or more agree.
- **Conflict penalty:** `−0.10` when sources disagree on a scalar field. Every competing value is still logged in `conflicts[]`, not just the winner.
- **`overall_confidence`** is the weight-normalized mean of every populated field's confidence score, then scaled down by a completeness factor — a thin profile (few fields populated) can never outscore a complete one, even if the few fields it does have are individually very reliable.

---

## Runtime Custom-Output Config

The canonical record (internal, fixed shape) and the projection (output, config-shaped) are kept strictly separate — the projector only ever reads the canonical record, it never mutates it. This means the same merge engine can serve any number of different output shapes just by pointing it at a different config file.

Each field in a config supports:

| Key | Meaning |
|---|---|
| `path` | The key name in the output |
| `from` | Where to read the value from the canonical record. Supports a plain field (`full_name`), an array index (`emails[0]`), or an array-of-objects extraction (`skills[].name`) |
| `type` | Expected output type, checked at validation time |
| `normalize` | Optional — re-applies a normalizer (`E164`, `canonical`) at projection time |
| `required` | If `true` and the field can't be resolved, behavior is governed by `on_missing` |

Top-level config options:

| Key | Meaning |
|---|---|
| `include_confidence` | If `true`, attaches `overall_confidence` and `provenance` to the projected output |
| `on_missing` | `"null"` / `"omit"` / `"error"` — what happens when a field can't be resolved |

**Example — `configs/default_config.json`:**
```json
{
  "fields": [
    { "path": "full_name", "type": "string", "required": true },
    { "path": "primary_email", "from": "emails[0]", "type": "string", "required": true },
    { "path": "phone", "from": "phones[0]", "type": "string", "normalize": "E164" },
    { "path": "skills", "from": "skills[].name", "type": "string[]", "normalize": "canonical" }
  ],
  "include_confidence": true,
  "on_missing": "null"
}
```

This repo also includes a second, structurally different config at `configs/recruiter_card_config.json`, which renames fields, pulls in `years_experience`/`experience`/`education`, turns confidence **off**, and uses `on_missing: "omit"` instead of `"null"` — see the [CLI Reference](#cli-reference) below to run it.

The projected output is always re-validated against the requested config's `type`/`required` rules before being returned — a malformed config produces a clear error, not a silently wrong profile.

---

## CLI Reference
| Flag | Meaning |
|---|---|
| `--csv TEXT` | Path to recruiter CSV export |
| `--json TEXT` | Path to ATS JSON blob |
| `--pdf TEXT` | Path to resume PDF |
| `--github TEXT` | GitHub username |
| `--notes TEXT` | Path to recruiter notes `.txt` file |
| `--config TEXT` | Path to runtime output config JSON |
| `--output TEXT` | Where to write the result |

All source flags are optional and can be combined freely — only one source from each group (structured / unstructured) is required by the assignment, but you can pass all five at once, as the examples below do.

### Run with the default config

```bash
python main.py --csv data/sample_recruiter.csv --json data/sample_ats.json --pdf data/sample_resume.pdf --notes data/sample_notes.txt --config configs/default_config.json --output outputs/profile_default_config.json
```

### Run with the custom config

```bash
python main.py --csv data/sample_recruiter.csv --json data/sample_ats.json --pdf data/sample_resume.pdf --notes data/sample_notes.txt --config configs/recruiter_card_config.json --output outputs/profile_recruiter_card_config.json
```

### Include the GitHub source

```bash
python main.py --csv data/sample_recruiter.csv --json data/sample_ats.json --github octocat --pdf data/sample_resume.pdf --notes data/sample_notes.txt --config configs/default_config.json --output outputs/profile_with_github.json
```

GitHub's public API is unauthenticated and rate-limited to 60 requests/hour per IP. If this call fails or times out, the pipeline does **not** crash — the GitHub extractor logs a warning and returns an empty result, and the run continues on whatever sources did succeed. This is intentional, not a bug; see [Known Gaps](#known-gaps--descoped-items).

### Run on a deliberately broken/partial input set

```bash
python main.py --csv data/broken_recruiter.csv --json data/broken_ats.json --output outputs/profile_degraded.json
```

`data/broken_recruiter.csv` contains a malformed email with no domain; `data/broken_ats.json` is invalid JSON. This demonstrates graceful degradation — the run completes, the malformed email never makes it into the output, and the broken JSON source contributes nothing rather than crashing the pipeline.

---

## Sample Data

| File | Purpose |
|---|---|
| `data/sample_recruiter.csv` | Valid recruiter CSV export |
| `data/sample_ats.json` | Valid ATS JSON blob, field names deliberately different from the canonical schema |
| `data/sample_resume.pdf` | Valid resume PDF |
| `data/sample_notes.txt` | Valid free-text recruiter notes |
| `data/broken_recruiter.csv` | CSV with a malformed email (no domain) — used to test graceful degradation |
| `data/broken_ats.json` | Deliberately invalid JSON — used to test that one bad source doesn't crash the run |

---

## Running the Tests

```bash
pytest tests/ -v
```

53 tests total. **51 are fully deterministic and have no external dependencies.** The remaining 2 (`test_github_extractor.py::test_extract_real_user` and `test_merger.py::test_merge_all_real_sources`) make a live call to the public GitHub API and can fail due to network conditions or GitHub's unauthenticated rate limit (60 req/hour/IP) — this is a known limitation of testing against a live external API, not a defect in the pipeline logic itself. If either of those two fails, the rest of the suite passing is what actually demonstrates correctness.

To run only the fully deterministic tests:
```bash
pytest tests/ -k "not test_extract_real_user and not test_merge_all_real_sources" -v
```

---

## Known Gaps & Descoped Items

Documented here in the same spirit as the `conflicts[]` field — surfaced explicitly rather than left for a reviewer to discover on their own.

- **`experience[]` / `education[]` cross-source merge.** These two fields are deduplicated within the normal field-priority flow but are not entity-matched against each other across sources — two sources reporting the same job with slightly different titles would currently produce two separate entries. This isn't exercised by the provided sample data, since only the ATS JSON extractor currently populates structured `experience`/`education` at all. Would need a `(company, title)`-normalized matching key before a second structured source contributing this data is added.
- **`links` has no conflict logging.** Every other field that can disagree across sources goes through the priority + `conflicts[]` path; `links` is currently last-write-wins.
- **`location.country` is not full ISO 3166 alpha-2.** Only `USA`/`US`/`United States` is mapped to `"US"`; other countries currently pass through as whatever string the source provided, uppercased.
- **No cross-candidate identity matching.** This pipeline assumes every input record describes the same person. There's no email/phone/fuzzy-name check to catch two different candidates' data being merged together.
- **GitHub API is unauthenticated.** Subject to a 60 requests/hour/IP rate limit from GitHub's side. The extractor handles this gracefully (logs and returns an empty result rather than crashing), but a production version would use an authenticated token for a much higher limit.

---

## Project Structure
eightfold-pipeline/
├── main.py                          # CLI entry point
├── requirements.txt
├── configs/
│   ├── default_config.json          # The brief's example projection config
│   └── recruiter_card_config.json   # A structurally different second config
├── data/                            # Sample + deliberately-broken input fixtures
├── docs/
│   └── pipeline_flowchart.png
├── pipeline/
│   ├── extractors/                  # One file per source type
│   ├── normalizers/                 # One file per normalized field type
│   ├── merger.py                    # Cross-source merge + conflict logging
│   ├── confidence.py                # Source priority + confidence scoring
│   ├── projector.py                 # Runtime config → output projection
│   └── validator.py                 # Schema validation (canonical + projected)
├── tests/                           # 53 tests, one file per module
└── outputs/                         # Generated profiles land here
