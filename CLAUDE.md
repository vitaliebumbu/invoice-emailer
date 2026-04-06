# CLAUDE.md — Invoice Emailer (Acadia Craft)

## Project Purpose

Automates sending staged billing invoice request emails for Acadia Craft projects.
The user searches for a project by name or code, the app finds the latest proposal
PDF from Dropbox, and opens a pre-filled email in Outlook ready to send.

Three+ invoice stages are supported per project. All emails go to the same recipients.

| Stage                        | Description                         |
|------------------------------|-------------------------------------|
| 10% Deposit                  | Initial deposit invoice request     |
| 50% Deposit                  | Mid-project deposit                 |
| Remaining Balance            | Final balance                       |
| Cabinet Balance + 50% Install| Split payment stage                 |
| Remaining Install            | Final install payment               |

**Email routing (fixed, never changes):**
- From: vitalie@acadiacraft.com
- To: billing@acadiacraft.com
- CC: denis@acadiacraft.com

**Email body template:**
> Hi Denis,
> Please send an invoice for [stage] for [project name] based on the attached proposal.
> Thank you, Vitalie

---

## Architecture

| Layer        | Choice                          | Reason                                              |
|--------------|---------------------------------|-----------------------------------------------------|
| Web          | Flask                           | Lightweight local tool, single user                 |
| Database     | SQLite (`sqlite3` stdlib)        | Simple log of sent invoices, no concurrency needed  |
| Email        | `win32com` → Outlook COM API    | SMTP auth blocked by M365; opens Outlook directly   |
| Dropbox      | Local filesystem search         | Dropbox synced to `C:\Acadia Craft Dropbox\`        |
| Credentials  | `.env` + `python-dotenv`        | Not needed for Outlook COM but kept for future use  |

### Why Outlook COM instead of SMTP
Microsoft 365 business accounts block SMTP AUTH by default and require admin
access to enable. Using `win32com.client` to drive the locally-running Outlook
app bypasses this entirely — the email opens pre-filled and the user clicks Send.

### Project structure

```
invoice-emailer/
├── app.py               # Flask routes
├── db.py                # SQLite schema + helpers (invoice log)
├── emailer.py           # Opens Outlook via win32com COM API
├── dropbox_search.py    # Searches Dropbox for proposal PDFs
├── templates/
│   ├── base.html        # Shared Bootstrap 5 layout
│   ├── index.html       # Search box + recent invoices
│   ├── results.html     # Multiple search results list
│   └── project.html     # Project detail + stage buttons
├── .env                 # Secrets (gitignored)
├── .env.example         # Credential template
├── requirements.txt     # flask, python-dotenv, pywin32
└── CLAUDE.md
```

### Dropbox path
```
C:\Acadia Craft Dropbox\1 AC Jobs\
  ├── 1 Quotes\{ProjectFolder}\Proposal\{CODE} Proposal - {Name} - {ver}.pdf
  └── 2 IN PRODUCTION\...\{ProjectFolder}\Proposal\...
```

- Project code (`DQ74`, `DS50`, etc.) may appear at the start OR middle of the filename
- Latest version = highest trailing number (`-003.pdf` > `-002.pdf`)
- `Old/` subfolders are skipped
- Project name = folder containing the `Proposal/` subfolder

---

## Coding Conventions

- Python 3.10+, `venv` for isolation
- No ORM — `sqlite3` with parameterized queries only
- No abstractions for one-off things — keep it flat and readable
- Recipients and Dropbox root path are constants defined at the top of their modules
- COM must be initialized per-thread: always call `pythoncom.CoInitialize()` before
  `win32com.client.Dispatch("Outlook.Application")`

---

## Common Tasks

### Running the app
```bash
cd C:\Users\vitaly\invoice-emailer
venv\Scripts\activate
python app.py
```
Open `http://localhost:5000`

### Searching for projects
- Type any part of the project name: `massey`, `ALH`, `bellevue`
- Or type the project code: `DQ74`, `DT48`
- Code search matches the code **anywhere** in the filename (not just prefix)

### Adding a new invoice stage
1. Add the label string to `ALL_STAGES` list in `db.py`
2. It appears automatically as a button on the project page — no other changes needed

### Debugging Outlook COM errors
- `CoInitialize has not been called` → ensure `pythoncom.CoInitialize()` is called
  at the top of `open_invoice_email()` before dispatching
- `Outlook.Application` not found → Outlook must be running/installed on this PC
- Test in isolation: `python -c "import emailer; emailer.open_invoice_email('Test', '10% Deposit', r'C:\path\to\file.pdf')"`

### Debugging search (project not found)
- Run `python dropbox_search.py` and test `search_projects("query")` directly
- Check if the project folder has a `Proposal/` subfolder with at least one `.pdf`
- Verify the Dropbox path constant `JOBS_ROOT` in `dropbox_search.py` is correct

---

## What to Avoid

- Do not add SMTP — M365 blocks it without admin access; use Outlook COM
- Do not hardcode recipients outside `emailer.py`
- Do not store the Dropbox path in more than one place (`dropbox_search.py` only)
- Do not add amount/total value tracking — removed by design; billing handles amounts
