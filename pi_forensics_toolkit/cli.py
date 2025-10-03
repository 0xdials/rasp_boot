import click
import json
import os
from pathlib import Path
from .artifacts import find_image, collect_boot_files, compute_hashes_for_files, load_binwalk_summary
from .parse_strings import extract_indicators
from .report import render_markdown, render_html
from .utils import now_timestamp, sha256_of_file, ensure_dir

PACKAGE_VERSION = "0.1.0"

@click.group()
def main():
    """pi-forensics — Raspberry Pi read-only forensics toolkit"""
    pass

@main.command()
@click.option("--root", required=True, help="Output root directory (e.g. output/<ts>)")
def summarize(root):
    """Parse artifacts, aggregate hashes, extract candidate hostnames/urls/ips, produce JSON + CSV summaries"""
    rootp = Path(root)
    if not rootp.exists():
        click.echo(f"Root {root} does not exist.", err=True)
        raise SystemExit(2)
    # imaging
    image = find_image(str(root))
    imaging = None
    if image:
        try:
            sha = sha256_of_file(image)
            imaging = {"image": image, "sha256": sha}
        except Exception:
            imaging = {"image": image, "sha256": None}
    # boot files
    boot_mount_copy = rootp / "boot_partition_copy"
    boot_files = {}
    if boot_mount_copy.exists():
        files = list(collect_boot_files(str(root), str(boot_mount_copy)))
        hashes = compute_hashes_for_files(files, str(rootp / "analysis" / "hashes" / "boot_sha256.txt"))
        # reduce keys to basenames for report
        for p, h in hashes.items():
            boot_files[os.path.basename(p)] = h
    # collect strings analysis (strings/*.txt)
    strings_dir = rootp / "analysis" / "strings"
    bigtext = ""
    if strings_dir.exists():
        for p in strings_dir.glob("*.txt"):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    bigtext += "\n" + fh.read()
            except Exception:
                continue
    else:
        # try binwalk extracted strings
        pass

    indicators = extract_indicators(bigtext) if bigtext else {}

    binwalk_summary = load_binwalk_summary(str(root))

    summary = {
        "generated": now_timestamp(),
        "version": PACKAGE_VERSION,
        "root": str(rootp),
        "imaging": imaging,
        "boot_files": boot_files,
        "indicators": indicators,
        "binwalk_summary": binwalk_summary
    }
    # write JSON summary
    ensure_dir(str(rootp / "analysis"))
    with open(rootp / "analysis" / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    click.echo(f"Summary written to {rootp / 'analysis' / 'summary.json'}")

@main.command()
@click.option("--root", required=True, help="Output root directory")
@click.option("--format", "fmt", type=click.Choice(["md", "html"]), default="md")
def report(root, fmt):
    """Build a human-readable report from summaries to output/<ts>/reports/report.md (and html if requested)"""
    rootp = Path(root)
    summary_path = rootp / "analysis" / "summary.json"
    if not summary_path.exists():
        click.echo("Summary JSON not found; run `pi-forensics summarize` first.", err=True)
        raise SystemExit(2)
    with open(summary_path, "r", encoding="utf-8") as fh:
        summary = json.load(fh)
    out_md = rootp / "reports" / "report.md"
    ensure_dir(str(rootp / "reports"))
    md_path = render_markdown(str(rootp), summary, str(out_md))
    click.echo(f"Markdown report: {md_path}")
    if fmt == "html":
        out_html = rootp / "reports" / "report.html"
        try:
            render_html(str(md_path), str(out_html))
            click.echo(f"HTML report: {out_html}")
        except Exception as e:
            click.echo(f"Failed to render HTML: {e}", err=True)

