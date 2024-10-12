# Stock Checker RSI

## Description

Stock Checker RSI is a Python-based tool that calculates and analyzes the Relative Strength Index (RSI) for given stocks. It leverages financial data from Yahoo Finance to compute RSI values and can provide visual analysis through plots.

The script performs the following key functions:
1. Fetches historical stock data for specified symbols using the yfinance library.
2. Calculates the RSI for each stock.
3. Can generate line plots of the RSI values over time, allowing for visual trend analysis.
4. Saves the calculated RSI data to CSV files for further analysis or record-keeping.

This tool is designed to assist traders and investors in technical analysis by providing RSI calculations, which can be used to identify potential overbought or oversold conditions in the market.

## Sample Output

Below is a sample output of the RSI analysis for a stock:

![Sample RSI Output](sample_output.png)

## Features

- Fetch stock data using yfinance
- Calculate RSI for specified stocks
- Plot RSI values over time
- Save RSI data to CSV files

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/stock-checker-rsi.git
   cd stock-checker-rsi
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To use the Stock Checker RSI tool, modify the `symbols` list in the `stock_checker_rsi.py` file:

python
symbols = ['AAPL', 'GOOGL', 'MSFT'] # Add or remove stock symbols as needed

Then run the script:

python stock_checker_rsi.py


