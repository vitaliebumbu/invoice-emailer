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
from difflib import SequenceMatcher

JOBS_ROOT = os.environ.get("JOBS_ROOT", r"C:\Acadia Craft Dropbox\1 AC Jobs")
DEFAULT_SEARCH_FOLDERS = [
    r"2 IN PRODUCTION",
    r"1 Quotes",
    r"1 Quotes\_Acadia Inquiry",
]
PROJECT_PDF_NAME_HINTS = ("proposal", "estimate", "quote")
GENERIC_QUERY_TERMS = {
    "engineering",
    "queue",
    "proposal",
    "production",
    "drawing",
    "drawings",
    "phase",
    "online",
    "order",
}


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


def _all_project_folders():
    """Yield likely direct project folders from the configured search roots."""
    skip_names = {"old", "- templates", "- punch list"}
    for search_root in _search_roots():
        try:
            entries = os.scandir(search_root)
        except OSError:
            continue

        with entries:
            for entry in entries:
                if not entry.is_dir():
                    continue
                if entry.name.strip().lower() in skip_names:
                    continue
                yield entry.name, entry.path


def _pdfs_under(folder):
    """Return proposal-like PDFs under a project folder, skipping Old folders."""
    matches = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if d.lower() != "old"]

        for filename in filenames:
            if not filename.lower().endswith(".pdf"):
                continue

            path = os.path.join(dirpath, filename)
            name_lower = filename.lower()
            folder_lower = os.path.basename(dirpath).lower()
            score = 0
            if folder_lower == "proposal":
                score += 100
            if any(hint in name_lower for hint in PROJECT_PDF_NAME_HINTS):
                score += 50
            matches.append((score, filename, path))

    return matches


def _latest_pdf(pdfs, proposal_dir):
    """Return the PDF with the highest trailing version number."""

    def version_key(fname):
        match = re.search(r"-\s*(\d+)\.pdf$", fname, re.IGNORECASE)
        return int(match.group(1)) if match else 0

    best = max(pdfs, key=version_key)
    return best, os.path.join(proposal_dir, best)


def _latest_scored_pdf(scored_pdfs):
    """Return highest-scored, newest-version PDF from scored PDF tuples."""

    def version_key(item):
        score, filename, path = item
        match = re.search(r"-\s*(\d+)\.pdf$", filename, re.IGNORECASE)
        version = int(match.group(1)) if match else 0
        try:
            modified = os.path.getmtime(path)
        except OSError:
            modified = 0
        return score, version, modified

    score, filename, path = max(scored_pdfs, key=version_key)
    return filename, path


def _query_terms(query):
    return [
        term.lower()
        for term in re.split(r"[^A-Za-z0-9]+", query)
        if (
            len(term) >= 3
            and not re.fullmatch(r"[A-Z]{1,3}\d{1,4}", term.upper())
            and term.lower() not in GENERIC_QUERY_TERMS
        )
    ]


def _project_folder_matches(folder_name, query, is_code):
    folder_lower = folder_name.lower()
    query_lower = query.lower()
    if not is_code and query_lower in folder_lower:
        return True

    terms = _query_terms(query)
    if not terms:
        return False

    return _is_close_match(folder_name, query)


def _similarity_score(folder_name, query):
    folder_terms = set(_query_terms(folder_name))
    query_terms = set(_query_terms(query))
    if not folder_terms or not query_terms:
        return 0

    exact = 0
    partial = 0
    for query_term in query_terms:
        if query_term in folder_terms:
            exact += 1
        elif any(_terms_are_close(query_term, folder_term) for folder_term in folder_terms):
            partial += 1

    return exact * 10 + partial * 4


def _terms_are_close(left, right):
    if left in right or right in left:
        return True
    if min(len(left), len(right)) < 5:
        return False
    return SequenceMatcher(None, left, right).ratio() >= 0.82


def _is_close_match(folder_name, query):
    query_terms = set(_query_terms(query))
    folder_terms = set(_query_terms(folder_name))
    if not query_terms:
        return False

    matched = 0
    for query_term in query_terms:
        if query_term in folder_terms or any(_terms_are_close(query_term, folder_term) for folder_term in folder_terms):
            matched += 1

    required = len(query_terms) if len(query_terms) <= 2 else len(query_terms) - 1
    return matched >= required


def _code_variants(code):
    variants = {code.upper()}
    match = re.match(r"^([A-Z])O(\d{2,4})$", code.upper())
    if match:
        variants.add(f"{match.group(1)}{match.group(2)}")
    return variants


def _clean_search_query(query):
    clean = " ".join(str(query or "").split())
    match = re.search(r"\b[A-Z]{1,3}\d{1,4}\b", clean, re.IGNORECASE)
    if not match:
        return clean

    code = match.group(0).upper()
    after_code = clean[match.end():]
    title = re.split(
        r"\b(?:CV|DRAWING|PROPOSAL|PROJECT INFO|Name:|Manager:|Customer:|Location:|Due Date:|clear info)\b",
        after_code,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    title = title.strip(" :-")
    return f"{code} {title}".strip()


def _text_has_code(value, code_variants):
    text = value.upper()
    return any(
        re.search(rf"(?<![A-Z0-9]){re.escape(code)}(?![A-Z0-9])", text)
        for code in code_variants
    )


def _title_without_code(query):
    clean = _clean_search_query(query)
    return re.sub(r"\b[A-Z]{1,3}\d{1,4}\b", "", clean, count=1, flags=re.IGNORECASE).strip(" :-")


def search_projects(query):
    """
    Search projects by code prefix or partial project name.

    Returns:
        [{"project_name", "filename", "pdf_path", "code"}]
    """
    q = _clean_search_query(query)
    if not q:
        return []

    q_upper = q.upper()
    q_lower = q.lower()
    is_code = bool(re.match(r"^[A-Z]{1,3}\d{1,4}$", q_upper))
    code_variants = _code_variants(q_upper) if is_code else {q_upper}

    results = []
    seen = set()

    for project_name, proposal_dir, pdfs in _all_proposal_folders():
        matched = False
        matched_pdfs = pdfs

        if is_code:
            matched_pdfs = [
                filename
                for filename in pdfs
                if _text_has_code(filename, code_variants)
            ]
            matched = bool(matched_pdfs)

        if not matched and _project_folder_matches(project_name, q, is_code):
            matched = True
            matched_pdfs = pdfs

        if matched:
            seen.add(project_name)
            filename, pdf_path = _latest_pdf(matched_pdfs, proposal_dir)
            code_match = re.search(r"\b([A-Z]{1,3}\d{2,4})\b", filename, re.IGNORECASE)
            code = code_match.group(1).upper() if code_match else ""
            results.append(
                {
                    "project_name": project_name,
                    "filename": filename,
                    "pdf_path": pdf_path,
                    "code": code,
                }
            )

    for project_name, project_dir in _all_project_folders():
        if project_name in seen:
            continue

        scored_pdfs = _pdfs_under(project_dir)
        if not scored_pdfs:
            continue

        matched = False
        matched_scored_pdfs = scored_pdfs
        if is_code:
            matched_scored_pdfs = [
                item
                for item in scored_pdfs
                if _text_has_code(item[1], code_variants)
            ]
            matched = bool(matched_scored_pdfs)
            if matched:
                matched_scored_pdfs = scored_pdfs

        if not matched:
            matched = _project_folder_matches(project_name, q, is_code)
            matched_scored_pdfs = scored_pdfs

        if matched:
            seen.add(project_name)
            filename, pdf_path = _latest_scored_pdf(matched_scored_pdfs)
            code_match = re.search(r"\b([A-Z]{1,3}\d{2,4})\b", filename, re.IGNORECASE)
            code = code_match.group(1).upper() if code_match else q_upper if is_code else ""
            results.append(
                {
                    "project_name": project_name,
                    "filename": filename,
                    "pdf_path": pdf_path,
                    "code": code,
                }
            )

    if not results and is_code:
        title_query = _title_without_code(q)
        if title_query:
            similar_matches = []
            for project_name, project_dir in _all_project_folders():
                scored_pdfs = _pdfs_under(project_dir)
                if not scored_pdfs:
                    continue
                if not _is_close_match(project_name, title_query):
                    continue
                score = _similarity_score(project_name, title_query)
                filename, pdf_path = _latest_scored_pdf(scored_pdfs)
                code_match = re.search(r"\b([A-Z]{1,3}\d{2,4})\b", filename, re.IGNORECASE)
                code = code_match.group(1).upper() if code_match else q_upper
                similar_matches.append(
                    (
                        score,
                        {
                            "project_name": project_name,
                            "filename": filename,
                            "pdf_path": pdf_path,
                            "code": code,
                        },
                    )
                )
            similar_matches.sort(key=lambda item: (-item[0], item[1]["project_name"].lower()))
            results.extend(match for _, match in similar_matches[:5])

    results.sort(key=lambda x: x["project_name"].lower())
    return results


def find_proposals(code):
    """Search proposals by project code. Returns list of matches sorted by project name."""
    return search_projects(code)


def find_latest_proposal(code):
    """Return the single best matching proposal for a code, or None."""
    results = search_projects(code)
    return results[0] if results else None
