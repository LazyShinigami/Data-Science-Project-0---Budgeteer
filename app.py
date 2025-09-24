from flask import Flask, jsonify
from crud import CRUD

app = Flask(__name__)

crud = CRUD()


# === Defining Endpoints ===

# --- Landing Page ---
@app.route("/")
def home():
    return "Flask app is running!"

# --- Displaying Data Page ---
@app.route("/read", methods=["GET"])
def read_record():
    """Endpoint to read records from Supabase"""
    try:
        data = crud.readRecord()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), 'data': data}), 500


print(crud.readRecord())

if __name__ == "__main__":
    app.run(debug=True)