from flask import Flask, render_template


app = Flask(__name__, template_folder="templates", static_folder="static")


NAV_ITEMS = [
    {"endpoint": "home", "label": "Start"},
    {"endpoint": "setup", "label": "Setup"},
    {"endpoint": "results", "label": "Results"},
]

SAMPLE_GRANTS = [
    {
        "id": 1,
        "name": "Rural Water Access Innovation Grant",
        "sponsor": "Water Access Foundation",
        "amount": "INR 5-25 lakh",
        "deadline": "Jul 21, 2026",
        "fit": 94,
        "type": "NGO",
    },
    {
        "id": 2,
        "name": "Climate Resilience Community Fund",
        "sponsor": "Global Impact Partners",
        "amount": "USD 20k-75k",
        "deadline": "Aug 12, 2026",
        "fit": 88,
        "type": "Community",
    },
    {
        "id": 3,
        "name": "Startup Social Impact Accelerator",
        "sponsor": "Civic Ventures Lab",
        "amount": "USD 10k-50k",
        "deadline": "Sep 03, 2026",
        "fit": 81,
        "type": "Startup",
    },
]

RESULT_METRICS = [
    {"label": "Active Grants Found", "value": "5"},
    {"label": "Best Eligibility Fit", "value": "94%"},
    {"label": "Drafts Ready", "value": "3"},
    {"label": "Deadline Window", "value": "67 days"},
]


@app.context_processor
def inject_navigation():
    return {"nav_items": NAV_ITEMS}


@app.route("/")
def home():
    return render_template("home.html", active_page="home")


@app.route("/setup")
def setup():
    return render_template("setup.html", active_page="setup")


@app.route("/results")
def results():
    return render_template(
        "results.html",
        active_page="results",
        grants=SAMPLE_GRANTS,
        result_metrics=RESULT_METRICS,
    )


if __name__ == "__main__":
    app.run(debug=True)
