#Class for accessing daily ticker data using alpha vantage api
import pandas as pd
import yfinance as yf
import numpy as np
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class YF_TickerData():
    def __init__(self, ticker_lst: list[str]):
        self.tickers = ticker_lst #List of tickers to access

    def GetData(self, start_date: str, end_date: str, lag: int):
        df_lst = [] #individual ticker dfs
        
        counter = 0 #Progress

        for ticker in self.tickers:
            df = self._RequestData(ticker, start_date, end_date)
            df = self._ComputeDailyLogReturn(ticker, df)
            df = self._ComputeWeeklyVolatility(ticker, lag, df)
            df_lst.append(df)
            df.to_csv(f"./TickerData/{ticker}.csv", index=False)
            counter+=1
            logger.info(f"Tickers Processed: {counter}/{len(self.tickers)}")
            time.sleep(60)
        
        #Merging Individual Ticker dfs
        df_lst = [df.set_index("Date") for df in df_lst]

        # 2. Join them side-by-side
        df_final = pd.concat(df_lst, axis=1)

        # 3. Move Date back to a column
        df_final.reset_index(inplace=True)

        #Save data as csv
        try:
            df_final.to_csv("./TickerData/ticker_data.csv", index=False)
        except Exception as e:
            logger.warning(f"Error saving ticker data: {e}")

        return df_final

#---------------------Helper Functions---------------------------
    #Request ticker data from yfinance api
    def _RequestData(self,ticker_str: str, start_date: str, end_date: str)-> pd.DataFrame:
        #auto_adjust param auto adjusts for splits and dividens        
        data = yf.download(ticker_str,start = start_date, end= end_date, interval = "1d", auto_adjust = True)
        
        #Extracting daily closing prices and dates
        new_df = data["Close"][ticker_str].reset_index()
        new_df.columns = ["Date", f"{ticker_str} Closing Price"]
        
        return new_df #Returns filtered df with daily closing prices and dates
    
    #Get Daily Log Returns
    def _ComputeDailyLogReturn(self, ticker_str: str, df: pd.DataFrame)->pd.DataFrame:
        # np.log(P_t / P_{t-1})
        df[f"{ticker_str} Log Return"] = np.log(df[f"{ticker_str} Closing Price"] / df[f"{ticker_str} Closing Price"].shift(1))
        return df
    
    #Volatility equals the STDEV of the returns for rolling window
    def _ComputeWeeklyVolatility(self, ticker_str: str, lag: int, df: pd.DataFrame)-> pd.DataFrame:
        # .rolling(window=lag) creates the sliding window for you
        df[f"{ticker_str} Volatility"] = df[f"{ticker_str} Log Return"].rolling(window=lag).std()
        return df.dropna(axis=0) #drop rows with NaN values





if __name__ == "__main__":
    ticker_lst = ["XLC", "XLY", "XLP", "XLE", "XLF", "XLV", "XLI", "XLK", "XLB", "XLRE"]
    alpha = YF_TickerData(ticker_lst)

    start_date = "2024-01-06"
    end_date = "2026-03-24"

    lag = 5 #Number of days used to compute volatiliy "stdev"

    response = alpha._(start_date, end_date, lag)