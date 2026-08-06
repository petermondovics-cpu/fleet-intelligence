from flask import Flask, jsonify

app = Flask(__name__)

# Simple health endpoint
@app.route("/", methods=["GET"])
def index():
    return "Fleet Intelligence — app.py is running\n", 200

# Example endpoint returning placeholder offers
@app.route("/offers", methods=["GET"])
def offers():
    sample_offers = [
        {"id": 1, "vehicle": "Truck A", "price": 12500, "currency": "USD"},
        {"id": 2, "vehicle": "Van B", "price": 9800, "currency": "USD"},
    ]
    return jsonify(sample_offers)

if __name__ == "__main__":
    # Run in debug mode for local development. In production, use a WSGI server.
    app.run(host="0.0.0.0", port=8000, debug=True)
