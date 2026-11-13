from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st 


# 1. Page Configuration
st.set_page_config(
  page_title="SEWA Peak Load Forecaasting",
  page_icon="⚡",
  layout="wide"
) 

st.title("⚡ SEWA Electricity Peak Load Forecasting")
st.write(
  "A machine learning application for estimating daily "
  "electricity peak demand using historical SEWA data"
)

# 2. Load Model and Data

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = PROJECT_ROOT / "models" / "sewa_linear_regression.joblib"
DATA_PATH = (
  PROJECT_ROOT
  / "data"
  / "processed"
  / "sewa_daily_modelling_dataset.csv"
)

if not MODEL_PATH.exists():
  st.error("Trained model not found. Save your model in the models folder.")
  st.stop()
  
if not DATA_PATH.exists():
  st.error("Processed dataset not found. Check the data/processed folder.")
  st.stop()
  
model = joblib.load(MODEL_PATH)

df = pd.read_csv(DATA_PATH, parse_dates=["Date"])
df = df.sort_values("Date").reset_index(drop=True)

# 3. PREPARE HISTORICAL INFORMATION

latest_record = df.iloc[-1]
latest_date = latest_record["Date"]

latest_peak_load = float(latest_record["SEWA Peak Load(MW)"])

rolling_7_load = float(
  df["SEWA Peak Load(MW)"].tail(7).mean()
)

default_weather = {
  "MAX Tem": float(df["MAX Tem"].median()),
  "Min Tem": float(df["Min Tem"].median()),
  "Max Hum": float(df["Max Hum"].median()),
  "Min Hum": float(df["Min Hum"].median()),
  "Temp": float(df["Temp"].median()),
  "Hum": float(df["Hum"].median())
}

# 4. Sidebar Navigation

st.sidebar.title("Navigation")

page = st.sidebar.radio(
  "Select a page",
  [
    "Dashboard",
    "Peak Load Forecast",
    "Historical Demand",
    "Model Performance"
  ]
)

# 5. Dashboard

if page == "Dashboard":
  
  st.subheader("Project Overview")
  
  col1, col2, col3 = st.columns(3)
  
  col1.metric(
    "Total Daily Records",
    f"{len(df):,}"
  )
  
  col2.metric(
    "Average Peak Load",
    f"{df['SEWA Peak Load(MW)'].mean():,.2f} MW"
  )
  
  col3.metric(
    "Highest Recorded Peak",
    f"{df['SEWA Peak Load(MW)'].max():,.2f} MW"
  )
  
  st.markdown("### About this project")
  
  st.write(
    "I developed this application to explore historical "
    "SEWA electricity demand and etimate daily peak load "
    "using a trained Linear Regression model"
  )
  
  st.markdown("### Dataset Information")
  
  st.write(f"Data coverage: {df["Date"].min().date()} to {latest_date.date()}")
  st.write("Forecasting target: Daily SEWA Peak Load (MW)")
  st.write("selected model: Linear Regression")
  
  st.markdown("### Recent Peak Load Records")
  
  st.dataframe(
    df[["Date", "SEWA Peak Load(MW)"]].tail(10),
    use_container_width=True
  )
  
# 6. Peak Load Forecast

elif page == "Peak Load Forecast":
  
  st.subheader("Daily Peak Load Estimate")
  
  st.info(
    f"Latest available historical record:"
    f"{latest_date.date()}. "
    "The application uses its peak load and the previous "
    "seven day's average as historical input features."
  )
  
  forecast_date = st.date_input(
    "Select estimation date",
    value=(latest_date + pd.Timedelta(days=1)).date(),
    min_value=(latest_date + pd.Timedelta(days=1)).date()
  )
  
  st.markdown("### Weather Inputs")
  
  col1, col2, col3 = st.columns(3)
  
  with col1:
    max_temp = st.number_input(
      "Maximum Temperature",
      value=default_weather["MAX Tem"]
    )
    
    min_temp = st.number_input(
      "Minimum Temperature",
      value=default_weather["Min Tem"]
    )
    
    with col2:
      max_humidity = st.number_input(
        "Maximum Humidity (%)",
        value=default_weather["Max Hum"]
      )
      
      min_humidity = st.number_input(
        "Minimum Humidity (%)",
        value=default_weather["Min Hum"]
      )
      
      with col3:
        temperature = st.number_input(
          "Average Temperature",
          value=default_weather["Temp"]
        
        )
        
        humidity = st.number_input(
          "Average Humidity (%)",
          value=default_weather["Hum"]
        )
        
        st.markdown("### Historical Demand Features")
        
        col1, col2 = st.columns(2)
        
        col1.metric(
          "Previous Day's Peak Load",
          f"{latest_peak_load:,.2f}"
        )
        
        col2.metric(
          "Previous 7-Day Average",
          f"{rolling_7_load:,.2f} MW"
        )
        
        if st.button("Estimate Peak Load", type="primary"):
          
          selected_date = pd.Timestamp(forecast_date)
          
          # Construct input features in the exact training order
          input_data = pd.DataFrame([{
            "MAX Tem": max_temp,
            "Min Tem": min_temp,
            "Max Hum": max_humidity,
            "Min Hum": min_humidity,
            "Temp": temperature,
            "Hum": humidity,
            "Year": selected_date.year,
            "Month": selected_date.month,
            "Day_of_Week_Num": selected_date.dayofweek,
            "Is_Weekend": int(selected_date.dayofweek >=5),
            "Peak_Load_Lag_1": latest_peak_load,
            "Peak_Load_Rolling_7": rolling_7_load
          }])
          
          prediction = model.predict(input_data)[0]
          
          st.success("Peak load estimate generated succefully.")
          
          st.metric(
            "Estimated Daily Peak Load",
            f"{prediction:,.2f} MW"
          )
          
          st.caption(
            "This is a model estimate based on the supplied"
            "weather inputs and the latest available historical"
            "demand features. It is not a live utility forecast."
          )
          
# 7. Historical Demand

elif page == "Historical Demand":
  
  st.subheader("Historical Electricity Demand")
  
  st.markdown("### Daily Peak Load Trend")
  
  fig, ax = plt.subplots(figsize=(8, 4))
  
  ax.plot(
    df["Date"],
    df["SEWA Peak Load(MW)"],
    linewidth=1
  )
  
  ax.set_xlabel("Date")
  ax.set_ylabel("Peak Load (MW)")
  ax.set_title("Daily SEWA peak Electricity Demand")
  ax.grid(alpha=0.3)
  
  st.pyplot(fig)
  plt.close(fig)
  
  st.markdown("### Monthly Average Peak Load")
  
  monthly = (
    df.groupby(df["Date"].dt.month)["SEWA Peak Load(MW)"]
    .mean()
  )
  
  fig, ax = plt.subplots(figsize=(8, 4))
  
  monthly.plot(kind="bar", ax=ax)
  
  ax.set_xlabel("Month")
  ax.set_ylabel("Average Peak Load (MW)")
  ax.set_title("Monthly Average Electricity Peak Load")
  ax.grid(axis="y", alpha=0.3)
  
  st.pyplot(fig)
  plt.close(fig)
  
# 8. Model Performance

elif page == "Model Performance":
  
  st.subheader("Forecasting Model Comparison")
  
  performance = pd.DataFrame({
    "Model": [
      "Baseline",
      "Linear Regression",
      "Random Forest"
    ],
    "MAE (MW)": [
      56.35,
      42.53,
      49.99
    ],
    "RMSE (MW)": [
      75.24,
      55.09,
      62.78
    ],
    "R²":[
      0.9761,
      0.9872,
      0.9834
    ]
  })
  
  st.dataframe(
    performance,
    use_container_width=True,
    hide_index=True
  )
  
  st.markdown("### Selected Method")
  
  st.success("Linear Regression achieved the best test-set performance.")
  
  st.write(
    "I selected Linear Regression because it achieved the lowest"
    "MAE and RMSE and the highest R² among the three evaluated models"
  )
  
  st.markdown("### Evaluation Metrics")
  
  st.write("**MAE:** Mean Absolute Error. It measures the average absolute prediction errors.")
  
  st.write("**RMSE:** Root Mean Squared Error. It gives more weight to larger prediction errors.")
  
  st.write("**R²:** Coefficient of Determination. It measures how well the model explains variation in the target on the test dataset.")
  
        
        
  