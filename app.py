import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

app = Flask(__name__)


# Load variables from .env
load_dotenv()

url = os.getenv("SUPABASE_URL")
api_key = os.getenv("SUPABASE_KEY")
supabase_db = create_client(url, api_key)
# ===== Supabase Client =====
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "transactions"

# ===== Health check =====
@app.route("/healthz")
def healthz():
    try:
        supabase.table(TABLE_NAME).select("*").limit(1).execute()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Add a record =====
@app.route("/add", methods=["POST"])
def add_record():
    try:
        data = request.json
        required_fields = ["userID", "date", "category", "amount"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Insert into Supabase
        response = supabase.table(TABLE_NAME).insert({
            "userID": data["userID"],
            "date": data["date"],  # expect YYYY-MM-DD
            "category": data["category"].strip().title(),
            "amount": float(data["amount"]),
            "paymentMode": data.get("paymentMode", "").strip().title(),
            "notes": data.get("notes", "").strip()
        }).execute()

        print("✅ Supabase insert response:", response)  # log Supabase response
        return jsonify({"message": "Record added successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Read / Summary =====
@app.route("/summary", methods=["GET"])
def summary():
    try:
        user_id = request.args.get("user_id")
        days = int(request.args.get("days", 0))

        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400

        # Base query
        query = supabase.table(TABLE_NAME).select("*").eq("userID", user_id)

        # Optional date filter
        if days in [7, 30]:
            cutoff = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
            query = query.gte("date", cutoff)

        expenses = query.execute().data or []

        # Calculate summary
        total_spent = sum(e["amount"] for e in expenses)
        total_by_category = {}
        for e in expenses:
            cat = e["category"]
            total_by_category[cat] = total_by_category.get(cat, 0) + e["amount"]

        dates = set(e["date"] for e in expenses)
        daily_avg = total_spent / len(dates) if dates else 0

        return jsonify({
            "total_spent": total_spent,
            "total_by_category": total_by_category,
            "daily_avg": daily_avg,
            "records_count": len(expenses)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Trend =====
@app.route("/trend", methods=["GET"])
def trend():
    try:
        user_id = request.args.get("user_id")
        days = int(request.args.get("days", 0))

        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400

        query = supabase.table(TABLE_NAME).select("*").eq("userID", user_id)
        if days in [7, 30]:
            cutoff = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
            query = query.gte("date", cutoff)

        expenses = query.execute().data or []

        trend_data = {}
        for e in expenses:
            trend_data[e["date"]] = trend_data.get(e["date"], 0) + e["amount"]

        sorted_dates = sorted(trend_data.keys())
        amounts = [trend_data[d] for d in sorted_dates]

        return jsonify({
            "dates": sorted_dates,
            "amounts": amounts,
            "records_count": len(expenses)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Prediction =====
@app.route("/prediction", methods=["GET"])
def prediction():
    try:
        user_id = request.args.get("user_id")
        days = int(request.args.get("days", 0))
        prediction_period = request.args.get("predictionPeriod", "week").lower()

        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400

        query = supabase.table(TABLE_NAME).select("*").eq("userID", user_id)
        if days in [7, 30]:
            cutoff = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
            query = query.gte("date", cutoff)

        expenses = query.execute().data or []

        daily_totals = {}
        for e in expenses:
            daily_totals[e["date"]] = daily_totals.get(e["date"], 0) + e["amount"]

        avg_daily = sum(daily_totals.values()) / len(daily_totals) if daily_totals else 0
        period_days = 7 if prediction_period == "week" else 30
        forecast = avg_daily * period_days

        return jsonify({
            "predictionPeriod": prediction_period,
            "predicted_total": forecast,
            "records_count": len(expenses)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===== Run Flask app =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
