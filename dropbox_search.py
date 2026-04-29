"""
Searches the local Acadia Craft Dropbox for proposal PDFs.

Supports two search modes:
  - By code prefix, e.g. "DQ74", matching PDF filename text
  - By project name, e.g. "massey", matching project folder text

The Dropbox root is configurable because each teammate may sync Dropbox to a
different drive or folder.
"""

import os
import re

JOBS_ROOT = os.environ.get("JOBS_ROOT", r"C:\Acadia Craft Dropbox\1 AC Jobs")
DEFAULT_SEARCH_FOLDERS = [
    r"2 IN PRODUCTION",
    r"1 Quotes",
    r"1 Quotes\_Acadia Inquiry",
]


def _configured_search_folders():
    raw = os.environ.get("JOB_SEARCH_FOLDERS", "").strip()
    if not raw:
        return DEFAULT_SEARCH_FOLDERS
    return [item.strip() for item in raw.split(";") if item.strip()]


def _search_roots():
    roots = []
    for folder in _configured_search_folders():
        root = folder if os.path.isabs(folder) else os.path.join(JOBS_ROOT, folder)
        if os.path.isdir(root):
            roots.append(root)

    if not roots and os.path.isdir(JOBS_ROOT):
        roots.append(JOBS_ROOT)

    return roots


def _all_proposal_folders():
    """
    Yield (project_name, proposal_dir, pdfs) for every folder named Proposal
    that contains at least one PDF, skipping folders named Old.
    """
    for search_root in _search_roots():
        for dirpath, dirnames, filenames in os.walk(search_root):
            dirnames[:] = [d for d in dirnames if d.lower() != "old"]

            if os.path.basename(dirpath).lower() != "proposal":
                continue

            pdfs = [f for f in filenames if f.lower().endswith(".pdf")]
            if not pdfs:
                continue

            project_name = os.path.basename(os.path.dirname(dirpath))
            yield project_name, dirpath, pdfs


def _latest_pdf(pdfs, proposal_dir):
    """Return the PDF with the highest trailing version number."""

    def version_key(fname):
        match = re.search(r"-\s*(\d+)\.pdf$", fname, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    best = max(pdfs, key=version_key)
    return best, os.path.join(proposal_dir, best)


def search_projects(query):
    """
    Search projects by code prefix or partial project name.

    Returns:
        [{"project_name", "filename", "pdf_path", "code"}]
    """
    q = query.strip()
    if not q:
        return []

    q_upper = q.upper()
    q_lower = q.lower()
    is_code = bool(re.match(r"^[A-Z]{1,3}\d{1,4}$", q_upper))

    results = []
    seen = set()

    for project_name, proposal_dir, pdfs in _all_proposal_folders():
        matched = False

        if is_code:
            matched = any(q_upper in filename.upper() for filename in pdfs)

        if not matched and q_lower in project_name.lower():
            matched = True

        if matched and project_name not in seen:
            seen.add(project_name)
            filename, pdf_path = _latest_pdf(pdfs, proposal_dir)
            code_match = re.match(r"^([A-Z]{2}\d{2,4})\s", filename, re.IGNORECASE)
            code = code_match.group(1).upper() if code_match else ""
            results.append(
                {
                    "project_name": project_name,
                    "filename": filename,
                    "pdf_path": pdf_path,
                    "code": code,
                }
            )

    results.sort(key=lambda x: x["project_name"].lower())
    return results


def find_proposals(code):
    """Search proposals by project code. Returns list of matches sorted by project name."""
    return search_projects(code)


def find_latest_proposal(code):
    """Return the single best matching proposal for a code, or None."""
    results = search_projects(code)
    return results[0] if results else None
