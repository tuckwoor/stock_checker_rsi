import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import os
from requests.exceptions import HTTPError
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime, timedelta

class StockRSIAnalyzer:
    def __init__(self, ticker, period="5y", interval="1d", rsi_window=14, smoothing_window=10, method='sma'):
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.rsi_window = rsi_window
        self.smoothing_window = smoothing_window
        self.method = method
        self.stock_name = self._get_stock_name()
        self.data = self._get_stock_data()
        if self.data is not None and not self.data.empty:
            self._calculate_rsi()
            self._smooth_rsi()
            self._analyze_rsi()
        else:
            self.current_rsi = None
            self.rsi_status = "No data"
            self.current_smoothed_rsi = None
            self.current_double_smoothed_rsi = None
            self.signal = "No data available"

    def _get_stock_name(self):
        try:
            stock = yf.Ticker(self.ticker)
            return stock.info.get('longName', self.ticker)
        except HTTPError as e:
            if e.response.status_code == 401:
                print(f"Unauthorized access for {self.ticker}. Using ticker as name.")
            else:
                print(f"Error fetching info for {self.ticker}: {str(e)}")
            return self.ticker

    def _get_stock_data(self):
        try:
            data = yf.download(self.ticker, period=self.period, interval=self.interval)
            if data.empty:
                print(f"No data available for {self.ticker}")
                return None
            return data
        except Exception as e:
            print(f"Error downloading data for {self.ticker}: {str(e)}")
            return None

    def _calculate_rsi(self):
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_window).mean()
        rs = gain / loss
        self.data['RSI'] = 100 - (100 / (1 + rs))

    def _smooth_data(self, data, window):
        if self.method == 'sma':
            return data.rolling(window=window).mean()
        elif self.method == 'ema':
            return data.ewm(span=window, adjust=False).mean()

    def _smooth_rsi(self):
        self.data['Smoothed_RSI'] = self._smooth_data(self.data['RSI'], self.smoothing_window)
        self.data['Double_Smoothed_RSI'] = self._smooth_data(self.data['Smoothed_RSI'], self.smoothing_window)

    def _find_last_crossover(self):
        smoothed_rsi = self.data['Smoothed_RSI']
        double_smoothed_rsi = self.data['Double_Smoothed_RSI']
        cross_down = (smoothed_rsi < double_smoothed_rsi) & (smoothed_rsi.shift(1) > double_smoothed_rsi.shift(1))
        cross_up = (smoothed_rsi > double_smoothed_rsi) & (smoothed_rsi.shift(1) < double_smoothed_rsi.shift(1))
        cross = cross_down | cross_up
        if cross.any():
            return smoothed_rsi[cross].index[-1]
        return None

    def _analyze_rsi(self):
        self.current_rsi = self.data['RSI'].iloc[-1]
        self.current_smoothed_rsi = self.data['Smoothed_RSI'].iloc[-1]
        self.current_double_smoothed_rsi = self.data['Double_Smoothed_RSI'].iloc[-1]
        self.crossover_date = self._find_last_crossover()
        two_weeks_ago = datetime.now() - timedelta(weeks=2)
        self.recent_crossover = self.crossover_date and self.crossover_date.to_pydatetime() > two_weeks_ago

        if self.current_rsi > 70:
            self.rsi_status = "Overbought"
        elif self.current_rsi < 30:
            self.rsi_status = "Oversold"
        else:
            self.rsi_status = "Neutral"

        if self.current_smoothed_rsi < self.current_double_smoothed_rsi:
            self.signal = f"Weakening, last crossover occurred on {self.crossover_date.date()}"
            self.trend = "Weakening"
        elif self.current_smoothed_rsi > self.current_double_smoothed_rsi:
            self.signal = f"Strengthening, last crossover occurred on {self.crossover_date.date()}"
            self.trend = "Strengthening"
        else:
            self.signal = "Neutral, no recent crossover"
            self.trend = "Neutral"

    def get_analysis_summary(self):
        return {
            'ticker': self.ticker,
            'stock_name': self.stock_name,
            'current_rsi': self.current_rsi,
            'rsi_status': self.rsi_status,
            'current_smoothed_rsi': self.current_smoothed_rsi,
            'current_double_smoothed_rsi': self.current_double_smoothed_rsi,
            'signal': self.signal,
            'trend': self.trend,
            'recent_crossover': self.recent_crossover
        }

    def print_analysis(self):
        print(f"Stock: {self.stock_name} ({self.ticker})")
        if self.current_rsi is not None:
            print(f"Current RSI: {self.current_rsi:.2f} ({self.rsi_status})")
            print(f"Current Smoothed RSI: {self.current_smoothed_rsi:.2f}")
            print(f"Current Double Smoothed RSI: {self.current_double_smoothed_rsi:.2f}")
            print(f"Signal: {self.signal}")
        else:
            print("No data available for analysis")

    def plot_stock_rsi(self):
        if self.data is None or self.data.empty:
            print(f"No data available to plot for {self.ticker}")
            return None

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        ax1.set_ylabel('Stock Price', color='tab:blue')
        ax1.plot(self.data.index, self.data['Close'], label='Close Price', color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.set_title(f'{self.stock_name} ({self.ticker}) Stock Price and RSI')

        ax2.set_xlabel('Date')
        ax2.set_ylabel('RSI', color='tab:red')
        ax2.plot(self.data.index, self.data['RSI'], label='RSI', color='tab:red', alpha=0.3)
        ax2.plot(self.data.index, self.data['Smoothed_RSI'], label=f'Smoothed RSI ({self.method.upper()})', color='tab:green', linewidth=2)
        ax2.plot(self.data.index, self.data['Double_Smoothed_RSI'], label=f'Double Smoothed RSI ({self.method.upper()})', color='tab:purple', linewidth=2, linestyle='--')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        ax2.axhline(y=70, color='gray', linestyle='--')
        ax2.axhline(y=30, color='gray', linestyle='--')
        ax2.set_ylim(0, 100)
        ax2.text(0.02, 0.95, f'RSI Window: {self.rsi_window}, Smoothed Window: {self.smoothing_window} ({self.method.upper()})', 
                 transform=ax2.transAxes, verticalalignment='top', fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
        ax2.legend()

        plt.tight_layout()
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        plt.close()
        return img_buffer

    def get_analysis_text(self):
        text = f"Stock: {self.stock_name} ({self.ticker})\n"
        if self.current_rsi is not None:
            text += f"Current RSI: {self.current_rsi:.2f} ({self.rsi_status})\n"
            text += f"Current Smoothed RSI: {self.current_smoothed_rsi:.2f}\n"
            text += f"Current Double Smoothed RSI: {self.current_double_smoothed_rsi:.2f}\n"
            text += f"Signal: {self.signal}\n"
        else:
            text += "No data available for analysis\n"
        return text

    def _get_next_filename(self, base_filename):
        index = 1
        while True:
            filename = f"{base_filename}_{index}.png"
            if not os.path.exists(filename):
                return filename
            index += 1

# Example usage in main script:
# analyzer = StockRSIAnalyzer("RR.L", rsi_window=100, smoothing_window=200, method='ema') - i like the longer smoothing windows
# analyzer.print_analysis()
# analyzer.plot_stock_rsi()