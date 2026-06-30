import click
import json
import os

from pipeline.extractors import csv_extractor, json_extractor, github_extractor, pdf_extractor, notes_extractor
from pipeline.merger import merge
from pipeline.projector import project
from pipeline.validator import validate_canonical, validate_projection


@click.command()
@click.option("--csv", "csv_path", default=None, help="Path to recruiter CSV export")
@click.option("--json", "json_path", default=None, help="Path to ATS JSON blob")
@click.option("--pdf", "pdf_path", default=None, help="Path to resume PDF")
@click.option("--github", "github_user", default=None, help="GitHub username")
@click.option("--notes", "notes_path", default=None, help="Path to recruiter notes .txt file")
@click.option("--config", "config_path", default=None, help="Path to runtime output config JSON")
@click.option("--output", "output_path", default="outputs/profile.json", help="Where to write the result")
def run(csv_path, json_path, pdf_path, github_user, config_path, output_path, notes_path):
    """Run the candidate profile normalization pipeline end-to-end."""
    records = []

    if csv_path:
        records.append(csv_extractor.extract(csv_path))
    if json_path:
        records.append(json_extractor.extract(json_path))
    if pdf_path:
        records.append(pdf_extractor.extract(pdf_path))
    if github_user:
        records.append(github_extractor.extract(github_user))
    if notes_path:
        records.append(notes_extractor.extract(notes_path))

    if not records:
        click.echo("No input sources provided. Use --csv, --json, --pdf, and/or --github.")
        return

    canonical = merge([r for r in records if r])

    warnings = validate_canonical(canonical)
    if warnings:
        click.echo(f"Canonical record warnings: {warnings}")

    final_output = canonical
    if config_path:
        with open(config_path) as f:
            config = json.load(f)
        final_output = project(canonical, config)
        errors = validate_projection(final_output, config)
        if errors:
            click.echo(f"Projection validation errors: {errors}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(final_output, f, indent=2)

    click.echo(f"Profile written to {output_path}")
    click.echo(json.dumps(final_output, indent=2))


if __name__ == "__main__":
    run()