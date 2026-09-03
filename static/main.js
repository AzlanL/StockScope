let stockChart = null; //global variable to hold the Chart.js instance so it can be destroyed and recreated when a new stock is searched

document.getElementById('search-btn').addEventListener('click', () => { //listens for when the user clicks the "Analyse stoc" button and calls fetchstockdata
    const symbol = document.getElementById('ticker-input').value.trim().toUpperCase();
    if (symbol) {
        fetchStockData(symbol);
    }
});

async function fetchStockData(symbol) { //fetches stock data from the backend API and handles errors
    const errorDiv = document.getElementById('error-message');
    errorDiv.style.display = 'none'; //hide the error message by default

    try {
        const response = await fetch(`/api/stock/${symbol}`); //fetches stock data from the backend API for the given stock symbol and stores the response in a variable called response
        const result = await response.json(); //parses the response as JSON and stores it in a variable called result




        if (!result.success) {
            errorDiv.textContent = result.error || 'Failed to fetch stock data.'; //if results is not a success, display the error message in the error div and make it visible
            errorDiv.style.display = 'block';
            return;
        }

        renderChart(result.data); //renders the stock chart using the data returned from the API
        updateStatsPanel(result.data); //updated the stats panel with the latest price, daily change, and volatility using the data returned from the API
    } catch (err) { //any other errors that occur during the fetch or parsing process are caught and displayed in the error div
        errorDiv.textContent = 'Network error. Please try again.';
        errorDiv.style.display = 'block';
    }
}
 //display of the key stats is updated with the latest data from the API
function updateStatsPanel(data) { //updates the three stat boxes with the latest price, daily % change, and volatility
    const latestPrice = data.prices[data.prices.length - 1]; //the last item in the prices array is the most recent closing price
    document.getElementById('stat-price').textContent = `$${latestPrice.toFixed(2)}`; //formats the latest price to two decimal places and adds a dollar sign in front

    const changeEl = document.getElementById('stat-change'); //changeEl is the element that will display the daily percentage change in price
    const change = data.latest_change_pct; //the latest_change_pct is the most recent day's percentage change in price, which is calculated in the backend and sent to the frontend as part of the API response
    changeEl.textContent = `${change > 0 ? '+' : ''}${change}%`; //adds a + sign in front if positive, negative numbers already show their own minus sign
    changeEl.className = 'stat-value ' + (change >= 0 ? 'positive' : 'negative'); //applies the green or red class depending on sign

    document.getElementById('stat-volatility').textContent = `${data.volatility}%`; //formats the volatility to two decimal places and adds a percentage sign
}


function renderChart(data) { //renders the stock chart using Chart.js with the data returned from the API
    const ctx = document.getElementById('stockChart').getContext('2d'); //ctx is the context of the canvas element where the chart will be drawn

    const goldenCrosses = data.dates.map(date => { //new array of prices where a golden cross occurred, or null if no golden cross occurred on that date
        const match = data.crossovers.find(c => c.date === date && c.type === 'golden'); //finds the crossover entry for the given date and type (date and golden)
        return match ? match.price : null;
    });
    const deathCrosses = data.dates.map(date => { //
        const match = data.crossovers.find(c => c.date === date && c.type === 'death'); //finds the crossover entry for the given date and type
        return match ? match.price : null;
    });



    if (stockChart) { //if a chart already exists, destroy it before creating a new one to avoid overlapping charts
        stockChart.destroy();
    }

    stockChart = new Chart(ctx, { //creates a new Chart.js instance and assigns it to the global variable stockChart which we made at the beginning
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [ //array of datasets to be plotted on the chart, each with its own label, data, and styling options
                { //below makes a line graph with blue for daily close, orange for 20-day SMA, and green for 50-day SMA
                    label: `${data.symbol} Daily Close`, //daily close is the price of the stock at the end of the trading day
                    data: data.prices,
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    pointRadius: 0
                },
                {
                    label: '20-Day SMA', //20 day average of the average price of the stock over the past 20 days
                    // Convert empty strings from Pandas into null so Chart.js skips plotting them
                    data: data.sma_20.map(val => val === "" ? null : val),
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    pointRadius: 0
                },
                {
                    label: '50-Day SMA', //50 days average of the average price of the stock over the past 50 days
                    // Convert empty strings from Pandas into null so Chart.js skips plotting them
                    data: data.sma_50.map(val => val === "" ? null : val),
                    borderColor: '#10b981',
                    borderWidth: 1.5,
                    pointRadius: 0
                },
                {
                    label: 'Golden Cross', //point where 20 day SMA crosses above 50 day SMA, which is a bullish signal that the stock price may rise
                    data: goldenCrosses,
                    borderColor: '#10b981',
                    backgroundColor: '#10b981',
                    pointRadius: 8,
                    pointStyle: 'triangle',
                    showLine: false // only show the marker dots, not a connecting line for all null values
                },
                {
                    label: 'Death Cross', //point where 20 day SMA crosses below 50 day SMA, which is a bearish signal that the stock price may fall
                    data: deathCrosses,
                    borderColor: '#ef4444',
                    backgroundColor: '#ef4444',
                    pointRadius: 8,
                    pointStyle: 'triangle',
                    rotation: 180, // flips the triangle upside-down to visually distinguish it from golden crosses
                    showLine: false
                }
            ]
        },
        options: { //styling options, responsive scaling, hover interaction, grid and tick colors, and legend label colors
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#f8fafc' }
                }
            }
        }
    });
}

fetchStockData('IBM'); //calls the fuction when the page loads so the chart isnt empty when you first open the site