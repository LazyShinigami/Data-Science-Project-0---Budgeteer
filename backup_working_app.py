from flask import Flask, jsonify
from crud import CRUD
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

crud = CRUD()


# === Defining Endpoints ===

# --- Landing Page ---
@app.route("/")
def home():
    return "Flask app is running!"

print('++++++++++++++++++++++++++++++++++  ',datetime.now(timezone.utc).date())
# --- Displaying Data Page ---
@app.route("/read", methods=["GET"])
def read_record():
    """Endpoint to read records from Supabase"""
    try:
        data = crud.readAllRecords(userID='hello@world.com')   # accept the value from the query string called in the flutter app - 
                                                                #- example - api_url.com/read?userID=hello@world.com
        temp = data
        return jsonify({"success": True, "fetched_DATA": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# TESTING DATA SCIENCE SHIT HERE SO WE CAN IMPLEMENT IT THROUGH FLUTTER SOMEHOW

# print(crud.readRecord())

if __name__ == "__main__":
    app.run(debug=True)