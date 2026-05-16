from flask import Flask, jsonify
from orchestrator import run_pipeline

app = Flask(__name__)

@app.route("/api/full-workflow")
def workflow():

    result = run_pipeline()

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)