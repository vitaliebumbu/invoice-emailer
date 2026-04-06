"""
Searches the local Acadia Craft Dropbox for proposal PDFs.

Supports two search modes:
  - By code prefix (e.g. "DQ74") — matches filename prefix
  - By project name (e.g. "massey") — partial, case-insensitive folder name match
"""

import os
import re

JOBS_ROOT = r"C:\Acadia Craft Dropbox\1 AC Jobs"


def _all_proposal_folders():
    """
    Yield (project_name, proposal_dir) for every folder named 'Proposal'
    that contains at least one PDF, skipping 'Old' subfolders.
    """
    for dirpath, dirnames, filenames in os.walk(JOBS_ROOT):
        # Skip folders named "Old"
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
        m = re.search(r"-\s*(\d+)\.pdf$", fname, re.IGNORECASE)
        return int(m.group(1)) if m else 0

    best = max(pdfs, key=version_key)
    return best, os.path.join(proposal_dir, best)


def search_projects(query):
    """
    Search projects by code prefix OR partial project name.

    Returns a list of dicts (sorted by project name):
        [{"project_name", "filename", "pdf_path", "code"}]
    """
    q = query.strip()
    if not q:
        return []

    q_upper = q.upper()
    q_lower = q.lower()

    # Decide search mode: looks like a code (letters+digits, ≤6 chars) → code search first
    is_code = bool(re.match(r'^[A-Z]{1,3}\d{1,4}$', q_upper))

    results = []
    seen = set()

    for project_name, proposal_dir, pdfs in _all_proposal_folders():
        matched = False

        if is_code:
            # Match if any PDF filename contains the query code anywhere
            for f in pdfs:
                if q_upper in f.upper():
                    matched = True
                    break

        if not matched:
            # Partial project name match (case-insensitive)
            if q_lower in project_name.lower():
                matched = True

        if matched and project_name not in seen:
            seen.add(project_name)
            filename, pdf_path = _latest_pdf(pdfs, proposal_dir)
            # Try to extract code from filename
            code_match = re.match(r'^([A-Z]{2}\d{2,4})\s', filename, re.IGNORECASE)
            code = code_match.group(1).upper() if code_match else ""
            results.append({
                "project_name": project_name,
                "filename":     filename,
                "pdf_path":     pdf_path,
                "code":         code,
            })

    results.sort(key=lambda x: x["project_name"].lower())
    return results


def find_proposals(code):
    """Search proposals by project code. Returns list of matches sorted by project name."""
    return search_projects(code)


def find_latest_proposal(code):
    """Return the single best matching proposal for a code, or None."""
    results = search_projects(code)
    return results[0] if results else None
