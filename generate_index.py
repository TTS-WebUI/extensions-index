#!/usr/bin/env python3
"""Generate a static PEP 503 'simple' pip index from a lightweight manifest.

Input: packages.txt (lines like "name @ url [; marker] [# comment]")
Output: simple/ directory with index.html and per-package pages.

This is intentionally minimal and avoids external dependencies.
"""
from pathlib import Path
import re
import html
import sys

ROOT = Path(__file__).parent
MANIFESTS = [ROOT / "packages.txt", ROOT / "flash_attention.txt"]
OUT = ROOT / "simple"

NAME_URL_RE = re.compile(r"^\s*([^\s@]+)\s*@\s*(\S+)(?:\s*;[^#\n]*)?(?:\s*#(.*))?$")


def canonicalize(name: str) -> str:
    """PEP 503 canonical name: normalize to lowercase, replace runs of [._-] with '-'."""
    name = name.lower()
    name = re.sub(r"[._]+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name


def parse_manifest(path: Path):
    entries = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = NAME_URL_RE.match(line)
        if not m:
            print(f"Warning: skipping unrecognized line {i}: {line}", file=sys.stderr)
            continue
        name, url, comment = m.group(1), m.group(2), m.group(3)
        entries.append((name, url, (comment or "").strip()))
    return entries


def write_index(entries, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    # global index with alphabetical package links
    packages = {}
    for name, url, comment in entries:
        canon = canonicalize(name)
        packages.setdefault(canon, []).append((name, url, comment))

    # write root index.html
    idx_lines = ["<!doctype html>", "<html><head><meta charset=\"utf-8\"><title>simple index</title></head><body>", "<h1>Simple Index</h1>", "<ul>"]
    for pkg in sorted(packages.keys()):
        idx_lines.append(f'<li><a href="{html.escape(pkg)}/">{html.escape(pkg)}</a></li>')
    idx_lines.extend(["</ul>", "</body></html>"])
    (outdir / "index.html").write_text("\n".join(idx_lines), encoding="utf-8")

    # per-package pages
    for pkg, items in packages.items():
        pkgdir = outdir / pkg
        pkgdir.mkdir(parents=True, exist_ok=True)
        lines = ["<!doctype html>", "<html><head><meta charset=\"utf-8\"><title>Links for %s</title></head><body>" % html.escape(pkg), f"<h1>Links for {html.escape(pkg)}</h1>", "<ul>"]
        for name, url, comment in items:
            text = f"{html.escape(name)} - {html.escape(comment)}" if comment else html.escape(name)
            lines.append(f'<li><a href="{html.escape(url)}">{text}</a></li>')
        lines.extend(["</ul>", "</body></html>"])
        (pkgdir / "index.html").write_text("\n".join(lines), encoding="utf-8")


def main():
    all_entries = []
    for manifest in MANIFESTS:
        if not manifest.exists():
            print(f"Manifest {manifest} not found, skipping.")
            continue
        print(f"Processing {manifest}...")
        entries = parse_manifest(manifest)
        all_entries.extend(entries)

    if not all_entries:
        print("No entries found in any manifest.")
        return
    write_index(all_entries, OUT)
    print(f"Wrote simple index to: {OUT}")


if __name__ == '__main__':
    main()
