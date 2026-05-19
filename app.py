import os
import sys
from io import BytesIO

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, send_file, session, url_for

load_dotenv()

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, ROOT_DIR)

from backend.orchestrator import run_pipeline
from frontend.result_store import load_run, save_run
from backend.utils.pdf_export import build_grants_pdf, build_proposal_pdf

app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, "templates"),
    static_folder=os.path.join(FRONTEND_DIR, "static"),
)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "grantai-dev-secret"
)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/setup", methods=["GET", "POST"])
def setup():

    if request.method == "POST":

        domain = request.form.get("domain", "").strip()
        budget = request.form.get("budget", "").strip()
        location = request.form.get("location", "").strip()
        goals = request.form.get("goals", "").strip()
        org_name = request.form.get("org_name", "").strip()

        if not domain or not goals:
            return render_template(
                "setup.html",
                error="Please fill all required fields."
            )

        query = (
            f"Domain: {domain}. "
            f"Location: {location}. "
            f"Budget: {budget}. "
            f"Goals: {goals}"
        )

        try:

            result = run_pipeline(
                query,
                org_name=org_name,
                location=location,
                budget=budget,
                domain=domain,
            )

            run_id = save_run(result)

            session["last_run_id"] = run_id

            return redirect(url_for("results"))

        except Exception as e:

            print(f"[app] Pipeline error: {e}")

            return render_template(
                "setup.html",
                error=str(e),
            )

    return render_template("setup.html")


@app.route("/results")
def results():

    data = load_run(session.get("last_run_id"))

    if not data:
        return redirect(url_for("setup"))

    proposal = data.get("proposal", "")

    return render_template(
        "results.html",
        grants=data.get("grants", []),
        proposal=proposal,
        metrics=data.get("metrics", {}),
        org_name=data.get("org_name", ""),
        query=data.get("query", ""),
        domain=data.get("domain", ""),
        has_proposal=bool(
            proposal and
            not proposal.startswith("Error")
        ),
    )


@app.route("/results/download.pdf")
def download_pdf():

    data = load_run(session.get("last_run_id"))

    if not data:
        return redirect(url_for("setup"))

    pdf = build_proposal_pdf(data)

    return send_file(
        BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="proposal.pdf",
    )


@app.route("/results/download-grants.pdf")
def download_grants_pdf():

    data = load_run(session.get("last_run_id"))

    if not data:
        return redirect(url_for("setup"))

    pdf = build_grants_pdf(data)

    return send_file(
        BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="grants.pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)