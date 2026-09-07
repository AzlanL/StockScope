import pandas as pd #allows us to manipulate the data we get from yfinance to reduce time taken
import yfinance as yf #fetches live stock market data, no API key required
from flask import Flask, jsonify, render_template #allows us to create a web application and return data in JSON format anf render HTML templates

app = Flask(__name__) #creates a new Flask web application instance

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

    ticker = yf.Ticker(symbol) #ticker object using yfinance library to fetch data for the given symbol
    df = ticker.history(period="6mo")  #6 months of daily price history as a pandas dataframe

    if df.empty:  #yfinance returns an empty DataFrame for invalid tickers, rather than an error
        return None, f"Invalid symbol or data unavailable for '{symbol}'."

    df = df.rename(columns={'Close': 'close', 'Open': 'open'})  #match the lowercase column names used elsewhere in this function
    
    # 1. PANDAS MATH: Calculate 20-day Simple Moving Average (SMA)
    df['SMA_20'] = df['close'].rolling(window=20).mean() #sliding window of 20 consecutive days and mean finds the average of the closing prices
    
    # 2. PANDAS MATH: Calculate 50-day Simple Moving Average (SMA)
    df['SMA_50'] = df['close'].rolling(window=50).mean()

    # 2a. PANDAS MATH: Daily percentage change (how much the price moved vs the previous day)
    df['daily_pct_change'] = df['close'].pct_change() * 100 #the daily percentage change column is calculated by using the close price and calculating the percentage change across days

    # 2b. PANDAS MATH: volatility is the standard deviation of daily % change over a 20-day window
    df['volatility'] = df['daily_pct_change'].rolling(window=20).std() #sliding window of 20 consecutive days and std finds the standard deviation of the daily percentage change

    # 2c. Detect moving average crossovers: find where SMA_20 changes from below to above SMA_50, or vice versa
    crossovers = detect_crossovers(df)


    # 3. Format clean output dictionary to send to frontend
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