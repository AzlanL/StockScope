import pandas as pd #need to build fake dataframes to test the crossover detection function
from app import detect_crossovers #imports same function used in app.py

def test_detect_golden_and_death_crossovers():
    # Setup fake dates and moving average values
    dates = pd.date_range(start="2024-01-01", periods=4, freq="D") #produces 4 dates starting from 2024-01-01 one day apart
    data = {
        "close": [100.0, 105.0, 110.0, 108.0], #fake closing prices for the 4 days
        "SMA_20": [10.0, 15.0, 25.0, 18.0],  # Starts below SMA_50, goes above, drops back below to have 2 crossovers
        "SMA_50": [20.0, 20.0, 20.0, 20.0]
    }
    df = pd.DataFrame(data, index=dates) #builds dataframe with the fake data and the dates as the index

    # Run function
    results = detect_crossovers(df) #runs real function

    # Assertions: assert checks whether a condition is true, if not it raises an AssertionError
    assert len(results) == 2 #checks to see if 2 crossovers were detected (is list length 2)
    assert results[0]["type"] == "golden"
    assert results[0]["date"] == "2024-01-03"
    assert results[1]["type"] == "death"
    assert results[1]["date"] == "2024-01-04"

def test_no_crossovers(): #same process as above but with no crossovers in test data
    dates = pd.date_range(start="2024-01-01", periods=3, freq="D")
    data = {
        "close": [100.0, 101.0, 102.0],
        "SMA_20": [25.0, 26.0, 27.0],  # Consistently above SMA_50
        "SMA_50": [20.0, 20.0, 20.0]
    }
    df = pd.DataFrame(data, index=dates)

    results = detect_crossovers(df)

    assert len(results) == 0