import os #allows python to read variables from the .env file
import requests #handles HTTP requests to get data from the API
from dotenv import load_dotenv #loads the .env file and makes the variables available to the script

load_dotenv() #loads the .env file
API_key = os.getenv("ALPHA_VANTAGE_KEY") #gets the API key from the .env file without revealing it in the code
SYMBOL = "IBM" #symbol for the stock we want to get data for

url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={SYMBOL}&apikey={API_key}" #makes a request to the Alpha Vantage API to get daily time series data for the specified stock symbol

print(f"Fetching daily time series data for {SYMBOL}...") #prints a message to indicate that the data is being fetched
response = requests.get(url) #sends a GET request to the API and stores the response in a variable

if response.status_code == 200: #checks if the request was successful
    data = response.json() #parses the JSON response into a Python dictionary

    if "Time Series (Daily)" in data: #checks if the expected data is present in the response
        time_series = data["Time Series (Daily)"] #extracts the daily time series data from the response
        latest_date = list(time_series.keys())[0] #makes a list of all dates in the time series and gets the latest date (the first one in the list)
        latest_data = time_series[latest_date] #gets the data for the latest date

        print("\n--- Success! Data Retrieved ---")
        print(f"Latest Available Date: {latest_date}")
        print(f"Open Price:  ${latest_data['1. open']}")
        print(f"Close Price: ${latest_data['4. close']}")
        print(f"Volume:      {latest_data['5. volume']}")
    elif "Note" in data: #handling error situations where the API call limit has been reached
        print("\nAPI Call Limit Reached:", data["Note"])
    elif "Error Message" in data: #handing error situations where the symbol is invalid or the API request is incorrect
            print("\nInvalid Symbol or API Request:", data["Error Message"])
    else:
        print("\nUnexpected Response Format:", data)
else: #in case of response status like 404 or 500, print the status code to help with debugging
    print(f"Failed to fetch data. Status code: {response.status_code}")