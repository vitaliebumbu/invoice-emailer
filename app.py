import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

import db
import emailer
from dropbox_search import search_projects

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

db.init_db()


@app.route("/")
def index():
    recent = db.get_recent_invoices()
    return render_template("index.html", recent=recent)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return redirect(url_for("index"))

    results = search_projects(query)

    if not results:
        flash(f'No projects found for "{query}". Try a different name or code.', "error")
        return redirect(url_for("index"))

    if len(results) == 1:
        # Single match — go straight to project page
        r = results[0]
        return redirect(url_for("project",
                                name=r["project_name"],
                                pdf=r["pdf_path"]))

    # Multiple matches — show selection list
    return render_template("results.html", query=query, results=results)


@app.route("/project")
def project():
    project_name = request.args.get("name", "").strip()
    pdf_path     = request.args.get("pdf", "").strip()

    if not project_name or not pdf_path:
        return redirect(url_for("index"))

    invoices = db.get_invoices_for_project(project_name)

    return render_template("project.html",
                           project_name=project_name,
                           pdf_path=pdf_path,
                           pdf_filename=os.path.basename(pdf_path),
                           stages=db.ALL_STAGES,
                           invoices=invoices)


@app.route("/send", methods=["POST"])
def send_invoice():
    project_name = request.form.get("project_name", "").strip()
    pdf_path     = request.form.get("pdf_path", "").strip()
    stage        = request.form.get("stage", "").strip()

    if stage not in db.ALL_STAGES:
        flash("Please select a stage.", "error")
        return redirect(url_for("project", name=project_name, pdf=pdf_path))

    if not os.path.isfile(pdf_path):
        flash("Proposal PDF not found on disk.", "error")
        return redirect(url_for("project", name=project_name, pdf=pdf_path))

    try:
        emailer.open_invoice_email(project_name, stage, pdf_path)
        db.log_invoice_email(project_name, stage, os.path.basename(pdf_path))
        flash(f"Outlook opened — review and click Send: {stage} — {project_name}", "success")
    except Exception as e:
        flash(f"Failed to send email: {e}", "error")

    return redirect(url_for("project", name=project_name, pdf=pdf_path))


if __name__ == "__main__":
    app.run(debug=True)
