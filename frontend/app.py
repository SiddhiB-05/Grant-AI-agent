import sys
import os

# Make sure Python can find the backend folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from flask import Flask, render_template, request, redirect, url_for

import sys
import os

# Make sure Python can find the backend folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from flask import Flask, render_template, request, redirect, url_for
from backend.orchestrator import run_pipeline

app = Flask(__name__)

# Navigation items injected into every template via base.html
NAV_ITEMS = [
    {"label": "Home",    "endpoint": "home"},
    {"label": "Search",  "endpoint": "setup"},
    {"label": "Results", "endpoint": "results"},
]


@app.context_processor
def inject_nav():
    return {"nav_items": NAV_ITEMS}


@app.route("/")
def home():
    return render_template("home.html", active_page="home")


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        domain   = request.form.get("domain", "").strip()
        budget   = request.form.get("budget", "").strip()
        location = request.form.get("location", "").strip()
        goals    = request.form.get("goals", "").strip()
        org_name = request.form.get("org_name", "").strip()

        if not domain or not goals:
            return render_template(
                "setup.html",
                active_page="setup",
                error="Please fill in at least the Project Domain and Goals fields."
            )

        # Build a rich query string for the agents
        user_query = (
            f"Domain: {domain}. "
            f"Location: {location}. "
            f"Budget: {budget}. "
            f"Goals: {goals}"
        )

        try:
            pipeline_result = run_pipeline(user_query, org_name=org_name, location=location, budget=budget)
        except Exception as e:
            print(f"[app] Pipeline error: {e}")
            return render_template(
                "setup.html",
                active_page="setup",
                error=f"Something went wrong: {str(e)}"
            )

        return render_template(
            "results.html",
            active_page="results",
            grants=pipeline_result.get("grants", []),
            proposal=pipeline_result.get("proposal", ""),
            query=user_query
        )

    return render_template("setup.html", active_page="setup")


@app.route("/results")
def results():
    # Direct visit to /results without running the pipeline → redirect to setup
    return redirect(url_for("setup"))


if __name__ == "__main__":
    app.run(debug=True)
from backend.orchestrator import run_pipeline

app = Flask(__name__)

# Navigation items injected into every template via base.html
NAV_ITEMS = [
    {"label": "Home",    "endpoint": "home"},
    {"label": "Search",  "endpoint": "setup"},
    {"label": "Results", "endpoint": "results"},
]


@app.context_processor
def inject_nav():
    return {"nav_items": NAV_ITEMS}


@app.route("/")
def home():
    return render_template("home.html", active_page="home")


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        domain   = request.form.get("domain", "").strip()
        budget   = request.form.get("budget", "").strip()
        location = request.form.get("location", "").strip()
        goals    = request.form.get("goals", "").strip()

        if not domain or not goals:
            return render_template(
                "setup.html",
                active_page="setup",
                error="Please fill in at least the Project Domain and Goals fields."
            )

        # Build a rich query string for the agents
        user_query = (
            f"Domain: {domain}. "
            f"Location: {location}. "
            f"Budget: {budget}. "
            f"Goals: {goals}"
        )

        try:
            pipeline_result = run_pipeline(user_query)
        except Exception as e:
            print(f"[app] Pipeline error: {e}")
            return render_template(
                "setup.html",
                active_page="setup",
                error=f"Something went wrong: {str(e)}"
            )

        return render_template(
            "results.html",
            active_page="results",
            grants=pipeline_result.get("grants", []),
            proposal=pipeline_result.get("proposal", ""),
            query=user_query
        )

    return render_template("setup.html", active_page="setup")


@app.route("/results")
def results():
    # Direct visit to /results without running the pipeline → redirect to setup
    return redirect(url_for("setup"))


if __name__ == "__main__":
    app.run(debug=True)