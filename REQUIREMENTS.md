# StockScope - Requirements

## Purpose
A single-ticker stock dashboard demonstrating full-stack development:
a Python backend fetching and processing live financial data, served
to an interactive frontend for visualization.

## Core features
- User enters a US stock ticker (e.g. AAPL, TSLA) into an input field
- Backend fetches daily price history from Alpha Vantage
- Backend computes:
	- 20-day and 50-day simple moving averages
	- Daily percentage change
	- Rolling volatility (standard deviation of daily returns)
	- Moving-average crossover points (golden cross / death cross)
- Frontend displays:
	- A price chart (Chart.js) with both moving averages overlaid
	- Crossover points marked visually on the chart
	- A stats panel: latest price, daily % change, volatility figure
- Dark, trading-desk visual theme

## Explicitly out of scope
- Multiple tickers / comparison view
- Backtesting or strategy simulation
- News feed or sentiment data
- Cryptocurrency tickers
- User accounts, saved watchlists, or persistence of any kind

## Tech stack
- Backend: Python, Flask, pandas, requests, python-dotenv
- Frontend: HTML, CSS, JavaScript, Chart.js
- Data source: Alpha Vantage free API

## Success criteria
A user can enter a valid ticker and see, within a few seconds, an
accurate price chart with moving averages, crossover markers, and
key stats - with sensible handling of invalid tickers or API errors.
