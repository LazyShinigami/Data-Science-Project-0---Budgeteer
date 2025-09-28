import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from sklearn.linear_model import LinearRegression
from prophet import Prophet

app = Flask(__name__)

# Load variables from .env
load_dotenv()

url = os.getenv('SUPABASE_URL')
api_key = os.getenv('SUPABASE_KEY')
supabase_db = create_client(url, api_key)
# ===== Supabase Client =====
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = 'transactions'

# ===== Health check =====
@app.route('/healthz')
def healthz():
    try:
        supabase.table(TABLE_NAME).select('*').limit(1).execute()
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== Add a record =====
@app.route('/add', methods=['POST'])
def add_record():
    try:
        data = request.json
        required_fields = ['userID', 'date', 'category', 'amount']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Insert into Supabase
        response = supabase.table(TABLE_NAME).insert({
            'userID': data['userID'],
            'date': data['date'],  # expect YYYY-MM-DD
            'category': data['category'].strip().title(),
            'amount': float(data['amount']),
            'paymentMode': data.get('paymentMode', '').strip().title(),
            'notes': data.get('notes', '').strip()
        }).execute()

        print('✅ Supabase insert response:', response)  # log Supabase response
        return jsonify({'message': 'Record added successfully!'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== Read / Summary =====
@app.route('/summary', methods=['GET'])
def summary():
    try:
        user_id = request.args.get('user_id')
        days = int(request.args.get('days', 0))

        if not user_id:
            return jsonify({'error': 'user_id parameter is required'}), 400

        # Base query
        query = supabase.table(TABLE_NAME).select('*').eq('userID', user_id)

        # Optional date filter
        if days in [7, 30]:
            cutoff = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
            query = query.gte('date', cutoff)

        expenses = query.execute().data or []

        # converting received data to dataframe
        df = pd.DataFrame(expenses)
        df['amount'] = df['amount'].astype(float)

        # --- Total spent ---
        total_spent = df['amount'].sum()

        # --- Total by category ---
        total_by_category = df.groupby('category')['amount'].sum().to_dict()
        

        # --- Daily average ---
        unique_dates = df['date'].nunique()
        daily_avg = (total_spent / unique_dates) if unique_dates > 0 else 0

        return jsonify({
            'total_spent': total_spent,
            'total_by_category': total_by_category,
            'daily_avg': daily_avg,
            'records_count': len(expenses),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== Trend =====
@app.route('/trend', methods=['GET'])
def trend():
    try:
        user_id = request.args.get('user_id')
        days = int(request.args.get('days', 0))

        if not user_id:
            return jsonify({'error': 'user_id parameter is required'}), 400

        query = supabase.table(TABLE_NAME).select('*').eq('userID', user_id)
        if days in [7, 30]:
            cutoff = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
            query = query.gte('date', cutoff)

        expenses = query.execute().data or []


        # converting received data to dataframe
        df = pd.DataFrame(expenses)
        
        # making sure amount is in float
        df['amount']= df['amount'].astype(float)

        # daily trend
        everyday_total = df.groupby('date').sum().to_dict()
        columns = sorted(everyday_total.keys())
        columns_on_each_date = [everyday_total[d] for d in columns]
        
        # total spend per category
        category_total = df.groupby('category')['amount'].sum().to_dict()
        # average spend on category
        category_avg =df.groupby('category')['amount'].mean().round(2).to_dict()
         
        # Three records of transactions where the amount is the largest {amount: abc, category: def, date: ghi}
        top3Transactions = (df.nlargest(3, 'amount')[['category', 'date', 'amount']].to_dict(orient='records')
            #nlargest basically takes the records of the largest < 3 > values present in the < amount column >
        )

        # Three records of transactions where the total spend is the largest {amount: abc, date: def}
        top3Dates = df.groupby('date')['amount'].sum().nlargest(3).to_dict()

        #total spend
        total_spent = df['amount'].sum()

        return jsonify({
            'columns': columns,
            'columns_on_each_date': columns_on_each_date,
            'records_count': len(expenses),
            'category_wise_total': category_total,
            'category_wise_average': category_avg,
            'three_highest_spends': top3Transactions,
            'three_highest_dates': top3Dates,
            'total_spent': total_spent,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== Prediction =====

# @app.route("/prediction", methods=["GET"])
# def prediction():
#     try:
#         user_id = request.args.get("user_id")
#         days = int(request.args.get("days", 0))
#         prediction_period = int(request.args.get("predictionPeriod", 7))  # 7 or 30

#         if not user_id:
#             return jsonify({"error": "user_id parameter is required"}), 400

#         query = supabase.table(TABLE_NAME).select("*").eq("userID", user_id)
#         if days in [7, 30]:
#             cutoff = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
#             query = query.gte("date", cutoff)

#         expenses = query.execute().data or []

#         if not expenses:
#             return jsonify({"error": "No expenses found for this user"}), 404

#         # Load into DataFrame
#         df = pd.DataFrame(expenses)

#         # === PRE-PROCESSING ===
#         # Convert date column to datetime
#         df["date"] = pd.to_datetime(df["date"])

#         # Ensure amount is float
#         df["amount"] = df["amount"].astype(float)

#         # Group by day (summing total expenses per day)
#         daily_totals = df.groupby("date")["amount"].sum().reset_index()
        

#         # Prepare features for regression
#         daily_totals["day_index"] = range(len(daily_totals))  # x = sequential days; # basically getting the total spending of everyday
#         X = daily_totals[["day_index"]] # output 0, 1, 2 ,3
#         y = daily_totals["amount"]
#         print(daily_totals.head())

#         # Train simple linear regression model
#         model = LinearRegression()
#         model.fit(X, y) # we use .fit to fit our data into the model we trained - model = LinearRegression()

#         # Predict future expenses for given period
#         last_index = daily_totals["day_index"].max()
#         future_indices = np.arange(last_index + 1, last_index + prediction_period + 1).reshape(-1, 1)
#         predictions = model.predict(future_indices)

#         # Map predictions to future dates
#         last_date = daily_totals["date"].max()
#         future_dates = [last_date + timedelta(days=i) for i in range(1, prediction_period + 1)]
#         forecast = {str(d.date()): round(float(p), 2) for d, p in zip(future_dates, predictions)}

#         return jsonify({
#             'test a - daily totals': str(daily_totals),
#             'test b - X': str(X),
#             'test c - y': str(y),
#             # 'test d - type of model': type(model),

#             "predictionPeriod": prediction_period,
#             "predicted_points": forecast,
#             "records_count": len(expenses)
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500



# -----------------------------
# Helper: prepare daily totals
# -----------------------------
def prepare_data(expenses):
    df = pd.DataFrame(expenses)
    if df.empty:
        return pd.DataFrame(columns=["date", "amount"])

    # Convert date to datetime & aggregate
    df["date"] = pd.to_datetime(df["date"])
    df = df.groupby("date")["amount"].sum().reset_index()

    # Fill missing dates with 0
    all_days = pd.date_range(df["date"].min(), df["date"].max())
    df = df.set_index("date").reindex(all_days, fill_value=0).rename_axis("date").reset_index()

    return df

# -----------------------------
# 1. Linear Regression forecast
# -----------------------------
def forecast_linear(df, horizon):
    df["t"] = np.arange(len(df))  # time index
    X, y = df[["t"]], df["amount"]

    model = LinearRegression()
    model.fit(X, y)

    future_t = np.arange(len(df), len(df) + horizon).reshape(-1, 1)
    preds = model.predict(future_t)

    # Use standard deviation of residuals for bounds
    residuals = y - model.predict(X)
    std_err = residuals.std()
    lower = preds - 1.96 * std_err
    upper = preds + 1.96 * std_err

    future_dates = pd.date_range(df["date"].max() + timedelta(days=1), periods=horizon)

    forecast = pd.DataFrame({
        "date": future_dates,
        "predicted": preds,
        "lower": lower,
        "upper": upper
    })
    return forecast


# -----------------------------
# 2. ARIMA forecast
# -----------------------------
def forecast_arima(df, horizon):
    model = ARIMA(df["amount"], order=(2, 1, 2))
    fit = model.fit()

    forecast_res = fit.get_forecast(steps=horizon)
    pred_mean = forecast_res.predicted_mean
    conf_int = forecast_res.conf_int()

    future_dates = pd.date_range(df["date"].max() + timedelta(days=1), periods=horizon)

    forecast = pd.DataFrame({
        "date": future_dates,
        "predicted": pred_mean.values,
        "lower": conf_int.iloc[:, 0].values,
        "upper": conf_int.iloc[:, 1].values
    })
    return forecast



# -----------------------------
# 3. Prophet forecast
# -----------------------------
def forecast_prophet(df, horizon):
    df_prophet = df.rename(columns={"date": "ds", "amount": "y"})

    model = Prophet()
    model.fit(df_prophet)

    future = model.make_future_dataframe(periods=horizon)
    forecast_res = model.predict(future)

    forecast = pd.DataFrame({
        "date": forecast_res["ds"].tail(horizon),
        "predicted": forecast_res["yhat"].tail(horizon),
        "lower": forecast_res["yhat_lower"].tail(horizon),
        "upper": forecast_res["yhat_upper"].tail(horizon)
    })
    return forecast






# -----------------------------
# Main prediction endpoint
# -----------------------------
@app.route("/prediction", methods=["GET"])
def prediction():
    try:
        user_id = request.args.get("user_id")
        prediction_period = int(request.args.get("days", 7))  # 7 or 30
        model_choice = request.args.get("model", "arima").lower()  # "arima", "linear", "prophet"

        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400

        # Fetch expenses from Supabase
        query = supabase.table(TABLE_NAME).select("*").eq("userID", user_id)
        expenses = query.execute().data or []

        df = prepare_data(expenses)

        if df.empty:
            return jsonify({"error": "No data available"}), 400

        # Select model
        if model_choice == "linear":
            forecast = forecast_linear(df, prediction_period)
        elif model_choice == "prophet":
            forecast = forecast_prophet(df, prediction_period)
        else:  # default ARIMA
            forecast = forecast_arima(df, prediction_period)


        history = (
            df.assign(date=pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d"))
            .rename(columns={"amount": "actual"})
            .to_dict("records")
        )

        # Detect whether forecast has "ds" (Prophet) or "date" (ARIMA / Linear Regression)
        date_col = "ds" if "ds" in forecast.columns else "date"
        forecast = (
            forecast.assign(**{date_col: pd.to_datetime(forecast[date_col]).dt.strftime("%Y-%m-%d")})
                    .to_dict("records")
        )

        # Format response
        result = {
            "predictionPeriod": prediction_period,
            "model": model_choice,
            "history": history,
            "forecast": forecast,
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


# ===== Run Flask app =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
