import os
from urllib import response #allows python to read variables from the .env file
import requests #handles HTTP requests to get data from the API
import pandas as pd #allows us to manipulate the data we get from the API to reduce time taken
from flask import Flask, jsonify, render_template #allows us to create a web application and return data in JSON format anf render HTML templates
from dotenv import load_dotenv #loads the .env file and makes the variables available to the script

load_dotenv() #loads the .env variables

app = Flask(__name__) #creates a new Flask web application instance

API_KEY = os.getenv("ALPHA_VANTAGE_KEY") #gets the API key from the .env file without revealing it in the code

import time

CACHE = {}  #empty dictionary that stores each ticker fetched and the time it was fetched, along with the processed data.
CACHE_DURATION_SECONDS = 300  #how long a cached result stays valid (5 minutes)

def detect_crossovers(df): #standalone function that takes a DataFrame as input and returns a list of crossover points
    """
    Given a DataFrame with 'SMA_20', 'SMA_50', and 'close' columns,
    return a list of dicts marking every point where SMA_20 crosses
    above (golden cross) or below (death cross) SMA_50.
    """
    df = df.copy()  # acreates an independant copy of the data frame to avoid modifying the original DataFrame in place
    df['sma20_above_sma50'] = df['SMA_20'] > df['SMA_50'] #evaluates whether the 20-day SMA is above the 50-day SMA for each row in the DataFrame and stores the result as a boolean column
    df['crossover'] = df['sma20_above_sma50'].diff() #1, 0, or -1 values when the boolean switches from true to false or vice versa, indicating a crossover event

    crossovers = [] #empty list to store detected crossover event
    for date, row in df[df['crossover'].notna() & (df['crossover'] != False)].iterrows(): #filters dataframe to only keep the rows where a crossover happened
        crossovers.append({ #makes formatted dictionary
            "date": date.strftime('%Y-%m-%d'),
            "price": round(row['close'], 2),
            "type": "golden" if row['sma20_above_sma50'] else "death"
        })
    return crossovers


def fetch_and_process_stock(symbol):

    symbol = symbol.upper()  #"aapl" and "AAPL" share the same cache entry

    if symbol in CACHE:
        age = time.time() - CACHE[symbol]["timestamp"] #age is the time since the data was cached in seconds
        if age < CACHE_DURATION_SECONDS: #if the cached data is still valid (less than 5 minutes old), return it
            print("Cache Accessed.")
            return CACHE[symbol]["data"], None  #uses cache not API 

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}" #where to get stock data from
    response = requests.get(url) #sends a GET request to the API and stores the response in a variable

    if response.status_code != 200: #checks if the request was successful as 200 is success code
        return None, "Failed to connect to market data provider (alphavantage)"

    data = response.json() #converts the json response into a python dictionary

    if "Time Series (Daily)" not in data: #checks if the expected data is present in the response
        if "Note" in data or "Information" in data: #means the api has reaches the free limit for the day (first checked for note but now checked for both after debugging)
                    return None, "Daily API rate limit reached (25 requests/day on the free tier). Please try again tomorrow."
        return None, f"Invalid symbol or data unavailable for '{symbol}'." #if we dont have time series daily and we dont have note then we have an invalid symbol or the data is unavailable

    time_series = data["Time Series (Daily)"] #extracts the daily time series data from the response data

    # 1. Convert python dictionary into a pandas DataFrame for easier manipulation and analysis and treat dates as table rows
    df = pd.DataFrame.from_dict(time_series, orient='index')
    
    # 2. Clean up column names (Alpha Vantage names columns like '4. close')
    df = df.rename(columns={
        '1. open': 'open', #renames 1. open to open and so on
        '2. high': 'high',
        '3. low': 'low',
        '4. close': 'close',
        '5. volume': 'volume'
    })
    
    # 3. Convert string numbers into actual floating-point numbers as JSON returns numbers as strings and we need to do math on them
    df['close'] = pd.to_numeric(df['close'])
    df['open'] = pd.to_numeric(df['open'])
    
    # 4. Sort dates chronologically (Alpha Vantage gives newest-first)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    
    # 5. PANDAS MATH: Calculate 20-day Simple Moving Average (SMA)
    df['SMA_20'] = df['close'].rolling(window=20).mean() # sliding window of 20 consecutive days and mean finds the average of the closing prices
    
    # 6. PANDAS MATH: Calculate 50-day Simple Moving Average (SMA)
    df['SMA_50'] = df['close'].rolling(window=50).mean()

    # 6a. PANDAS MATH: Daily percentage change (how much the price moved vs the previous day)
    df['daily_pct_change'] = df['close'].pct_change() * 100 #the daily percentage change column is calculated by using the close price and calculating the percentage change across days

    # 6b. PANDAS MATH: volatility is the standard deviation of daily % change over a 20-day window
    df['volatility'] = df['daily_pct_change'].rolling(window=20).std() #sliding window of 20 consecutive days and std finds the standard deviation of the daily percentage change

    # 6c. Detect moving average crossovers: find where SMA_20 changes from below to above SMA_50, or vice versa
    crossovers = detect_crossovers(df)


    # 7. Format clean output dictionary to send to frontend
    processed_data = {
        "symbol": symbol.upper(), #capitalises the symbol to make it look nice on the frontend
        "dates": df.index.strftime('%Y-%m-%d').tolist(), #turns dates into clean text strings
        "prices": df['close'].tolist(), # extracts the closing prices from the DataFrame and converts them into a list
        "sma_20": df['SMA_20'].fillna("").tolist(),  # marks first 19 days as not a number and turns into empty strings to avoid confusion on the frontend and converts them into a list
        "sma_50": df['SMA_50'].fillna("").tolist(),
        "latest_change_pct": round(df['daily_pct_change'].iloc[-1], 2),  # most recent day's % change, rounded to 2 decimal places
        "volatility": round(df['volatility'].iloc[-1], 2),  # most recent volatility figure, rounded to 2 decimal places
        "crossovers": crossovers  # list of detected crossovers
    }

    CACHE[symbol] = {"data": processed_data, "timestamp": time.time()}  # store this result using data processed and time accessed for future requests
    return processed_data, None # returns the processed data and None for error message since there is no error


@app.route('/') #when my url is opened def home() is called and the return value is sent to the browser
def home():
    return render_template('index.html') #render template index.html which is the main page of the web application and sends it to the browser

@app.route('/api/stock/<symbol>') #when the url is opened with a symbol like /api/stock/IBM def get_stock_data(symbol) is called and the return value is sent to the browser
def get_stock_data(symbol):
    data, error = fetch_and_process_stock(symbol) #format that we receive processed_data and error message from the function fetch_and_process_stock
    
    if error:
        return jsonify({"success": False, "error": error}), 400
        
    return jsonify({"success": True, "data": data}) #jsonify converts the python dictionary into a JSON response that can be sent to the frontend

if __name__ == '__main__':
    app.run(debug=True, port=5000) #http://127.0.0.1:5000 is the default address and port for the flask app to run on. debug=True allows us to see errors in the console when we make a mistake in the code