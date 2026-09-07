"""Check a local documentation portfolio; never connect to or publish to GitHub.

This helper was created while organizing the portfolio, not during the research.
It is a limited guardrail, not a comprehensive secret or copyright scanner.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
import unicodedata


APPROVAL_FIELDS = (
    "publication_approval",
    "ownership_confirmation",
    "license_review",
    "sensitive_material_review",
)
BLOCKED_SUFFIXES = (
    ".pem", ".key", ".pt", ".pth", ".ckpt", ".safetensors", ".log",
    ".tar", ".tar.gz", ".zip",
)
PRIVATE_PATTERNS = (
    re.compile(r"/(?:home|mnt|Users)/[^\s`]+"),
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"(?<![\w.])1[3-9]\d{9}(?!\w)"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
)
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SVG_TAGS = {"svg", "defs", "marker", "rect", "text", "g", "path", "title", "desc"}


class MarkdownHTML(HTMLParser):
    """Collect links and anchors in the small HTML subset used by READMEs."""
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.errors = []
        self.details_depth = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"script", "iframe", "object", "embed", "style"}:
            self.errors.append("active HTML is not allowed")
        if any(k.startswith("on") for k in values):
            self.errors.append("active HTML attribute is not allowed")
        for key in ("href", "src"):
            if values.get(key):
                self.links.append(values[key])
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "details":
            self.details_depth += 1

    def handle_endtag(self, tag):
        if tag == "details":
            self.details_depth -= 1
            if self.details_depth < 0:
                self.errors.append("unbalanced details block")


def markdown_anchors(content):
    """GitHub-style anchors for this portfolio's plain, unique headings."""
    anchors, used = set(), {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", content, re.MULTILINE):
        slug = "".join(c for c in heading.lower() if c in "-_ " or unicodedata.category(c)[0] in "LN").replace(" ", "-")
        count = used.get(slug, 0)
        used[slug] = count + 1
        anchors.add(slug if count == 0 else slug + "-" + str(count))
    parser = MarkdownHTML()
    parser.feed(content)
    return anchors | parser.ids


def audit_results(root):
    """Validate transcribed counts and the exact SVG chart bound to them."""
    path = root / "data/results.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        records = data["records"]
        errors = []
        for record in records:
            for condition in record.get("conditions", [record]):
                total = condition["total"]
                if type(total) is not int or total <= 0:
                    errors.append("invalid result total")
                for value in condition["successes"].values():
                    if type(value) is not int or not 0 <= value <= total:
                        errors.append("invalid result count")
        gwp = next(r for r in records if r["id"] == "gwp-place-dual-shoes")
        pair = gwp["paired"]
        counts = [pair[k] for k in ["both_success", "baseline_only", "candidate_only", "both_failure"]]
        if any(type(n) is not int or n < 0 for n in counts) or sum(counts) != gwp["total"]:
            errors.append("paired total mismatch")
        if pair["both_success"] + pair["baseline_only"] != gwp["successes"][pair["baseline"]]:
            errors.append("paired baseline mismatch")
        if pair["both_success"] + pair["candidate_only"] != gwp["successes"][pair["candidate"]]:
            errors.append("paired candidate mismatch")
        chart = ET.parse(root / "assets/diagrams/paired-results.svg")
        nodes = {n.attrib["id"]: n for n in chart.iter() if "id" in n.attrib}
        for key, count in gwp["successes"].items():
            if nodes["value-" + key].text != str(count) or float(nodes["bar-" + key].attrib["width"]) != count * 6:
                errors.append("chart count/scale mismatch: " + key)
        for key in ["both_success", "baseline_only", "candidate_only", "both_failure"]:
            if nodes["paired-" + key].text != str(pair[key]):
                errors.append("chart paired mismatch: " + key)
        return errors
    except (OSError, ValueError, KeyError, TypeError, StopIteration, ET.ParseError):
        return ["invalid results data or missing chart binding"]


def audit_svg(content):
    """Restrict diagrams to inert, self-contained vector primitives."""
    if "<!DOCTYPE" in content.upper() or "<!ENTITY" in content.upper():
        return ["SVG declarations are not allowed"]
    try:
        tree = ET.fromstring(content)
    except ET.ParseError:
        return ["invalid SVG XML"]
    if tree.tag != "{http://www.w3.org/2000/svg}svg":
        return ["invalid SVG root"]
    errors = []
    ids = {node.attrib["id"] for node in tree.iter() if "id" in node.attrib}
    for node in tree.iter():
        tag = node.tag.removeprefix("{http://www.w3.org/2000/svg}")
        if tag not in SVG_TAGS:
            errors.append("unsupported SVG element")
        for key, value in node.attrib.items():
            key = key.rsplit("}", 1)[-1].lower()
            if key.startswith("on") or key in {"href", "style", "base"}:
                errors.append("active or external SVG attribute")
            if "url(" in value.lower():
                reference = re.fullmatch(r"url\(#([^()]+)\)", value)
                if reference is None or reference.group(1) not in ids:
                    errors.append("invalid SVG resource reference")
    return errors


def audit_experiment_exports(root):
    """Check extraction hashes, row counts, and recompute episode summaries."""
    folder = root / "data/experiments"
    manifest_file = folder / "manifest.json"
    if not manifest_file.exists():
        return []
    errors = []
    try:
        manifest = json.loads(manifest_file.read_text())
        for name, entry in manifest["exports"].items():
            path = (folder / name).resolve()
            if path.parent != folder.resolve() or not path.is_file():
                errors.append("invalid experiment export path: " + name)
                continue
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                errors.append("experiment export hash mismatch: " + name)
            if path.suffix == ".csv":
                with path.open() as file:
                    count = len(list(csv.DictReader(file)))
            else:
                data = json.loads(path.read_text())
                count = len(data["workers"]) if name == "lingbot-ruler-eval.json" else len(data)
            if entry["rows"] is not None and count != entry["rows"]:
                errors.append("experiment export row mismatch: " + name)
            if any(sid not in manifest["sources"] for sid in entry["source_ids"]):
                errors.append("experiment export source missing: " + name)
        runs = json.loads((folder / "memory-runs.json").read_text())
        with (folder / "memory-episodes.csv").open() as file:
            episodes = list(csv.DictReader(file))
        ids = {r["run_id"] for r in runs}
        if len(ids) != len(runs) or any(e["run_id"] not in ids for e in episodes):
            errors.append("memory run identity mismatch")
        for run in runs:
            selected = [e for e in episodes if e["run_id"] == run["run_id"]]
            if len(selected) != run["num_evals"] or len({e["layout_id"] for e in selected}) != len(selected):
                errors.append("memory layout count mismatch")
            elif (sum(e["success"] == "True" for e in selected) != run["successes"]
                  or abs(sum(float(e["score"]) for e in selected) / len(selected) - run["mean_score"]) > 1e-9):
                errors.append("memory result mismatch")
            if run["baseline_run_id"] is not None and run["baseline_run_id"] not in ids:
                errors.append("memory baseline reference missing")
        with (folder / "gwp-paired.csv").open() as file:
            paired = list(csv.DictReader(file))
        if (len({r["seed"] for r in paired}) != 64
            or sum(r["baseline_success"] == "True" for r in paired) != 34
            or sum(r["candidate_success"] == "True" for r in paired) != 35):
            errors.append("GWP episode count mismatch")
        if (folder / "lingbot-formal-evals.json").exists():
            formal = json.loads((folder / "lingbot-formal-evals.json").read_text())
            if {r["run_id"] for r in formal} != {"exp005", "exp007", "exp010", "exp016"} or len(formal) != 4:
                errors.append("RL formal run identity mismatch")
            for run in formal:
                workers = run["workers"]
                if (len({w["worker_id"] for w in workers}) != 4
                    or sum(w["successes"] for w in workers) != run["successes"]
                    or sum(w["episodes"] for w in workers) != run["episodes"]
                    or not run["episodes"] == run["expected"] == run["completed"] == 16
                    or abs(run["success_rate"] - run["successes"] / 16) > 1e-9):
                    errors.append("RL formal worker count mismatch")
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError):
        errors.append("invalid experiment export data")
    return errors


def contained_file(root, base, raw_path):
    """Return whether a relative target resolves to a file inside root."""
    path = (base / unquote(raw_path)).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return path.is_file()


def audit(root, release=False):
    root = Path(root).resolve()
    errors = []
    if not root.is_dir():
        return ["portfolio root is not a directory"]
    try:
        manifest = json.loads((root / "portfolio.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ["portfolio.json is missing or invalid JSON"]
    if not isinstance(manifest, dict):
        return ["portfolio.json must contain an object"]
    if manifest.get("schema_version") != 1:
        errors.append("unsupported schema_version")
    if not (root / "README.md").is_file():
        errors.append("README.md is missing")

    projects = manifest.get("projects")
    if not isinstance(projects, list) or not projects:
        errors.append("projects must be a non-empty list")
        projects = []
    identifiers = set()
    for project in projects:
        if not isinstance(project, dict):
            errors.append("each project must be an object")
            continue
        identifier = project.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append("project id must be a non-empty string")
            continue
        if identifier in identifiers:
            errors.append("duplicate project id: " + identifier)
        identifiers.add(identifier)
        target = project.get("path")
        if not isinstance(target, str) or not contained_file(root, root, target):
            errors.append("invalid project path: " + identifier)

    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__"} for part in relative.parts):
            continue
        if path.is_symlink():
            errors.append("symlink requires manual review: " + str(relative))
            continue
        if not path.is_file():
            continue
        if path.name.startswith(".env") or path.name.lower().endswith(BLOCKED_SUFFIXES):
            errors.append("blocked artifact type: " + str(relative))
        if path.suffix not in {".md", ".json", ".svg", ".csv", ".jsonl", ".txt", ".yaml", ".yml"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append("cannot read text file: " + str(relative))
            continue
        if any(pattern.search(content) for pattern in PRIVATE_PATTERNS):
            errors.append("potential private detail in: " + str(relative))
        if path.suffix == ".svg":
            errors.extend(e + " in: " + str(relative) for e in audit_svg(content))
        if path.suffix != ".md":
            continue
        parser = MarkdownHTML()
        parser.feed(content)
        errors.extend(e + " in: " + str(relative) for e in parser.errors)
        if parser.details_depth:
            errors.append("unbalanced details block in: " + str(relative))
        targets = [m.group(1) for m in MARKDOWN_LINK.finditer(content)] + parser.links
        for raw_target in targets:
            target = raw_target.strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            parsed = urlsplit(target)
            if parsed.scheme in {"http", "https", "mailto"}:
                continue  # Offline check: external URLs are not fetched.
            if parsed.scheme or parsed.netloc:
                errors.append("unsupported link type in: " + str(relative))
            elif parsed.path and not contained_file(root, path.parent, parsed.path):
                errors.append("missing/outside local link in: " + str(relative))
            elif parsed.fragment:
                destination = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                if destination.suffix == ".md" and unquote(parsed.fragment) not in markdown_anchors(destination.read_text(encoding="utf-8")):
                    errors.append("missing local anchor in: " + str(relative))

    errors.extend(audit_results(root))
    errors.extend(audit_experiment_exports(root))

    if release:
        if manifest.get("release_status") != "ready":
            errors.append("release_status is not ready")
        for field in APPROVAL_FIELDS:
            if manifest.get(field) != "confirmed":
                errors.append("human confirmation pending: " + field)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    errors = audit(args.root, args.release)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print("PASS: local structure and document checks")
    if not args.release:
        print("Draft check only; no publication approval is implied.")
    else:
        print("Declared confirmations checked; no upload or publication performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
