""" 
This file implements a pipeline to feed sentiment and volatility data to 
scikit-learn Hidden Markov Model implementation to detect different regimes.

Assuming the conditional distribution of the observation given the state is a mixture model
having components from the sentiment score and the volatility

2 Possible scenarios / 
State 1 : Sentiment score and volatility are highly correlated
State 2 : Sentiment score and volatility are more independent
"""
import numpy as np
import pandas as pd
import logging
from hmmlearn import hmm
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import warnings

import plotly.io as pio
pio.renderers.default = "browser"  #Opens 3D vis in browser

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class HMM_Pipeline:
    def __init__(self, num_regimes: int, n_mix: int = 2):
        self.num_regimes = num_regimes
        self.n_mix = n_mix
        self.soft_classifications = None

    def HMM_pipeline(self, sector: str, ticker: str, training_data: pd.DataFrame, testing_data: pd.DataFrame, num_iterations) -> pd.DataFrame:
        trained_model = self._Fit(training_data.loc[:, [sector, f"{ticker} Volatility"]], num_iterations) #Fit model

        predicted_states = self._Predict(testing_data.loc[:, [sector, f"{ticker} Volatility"]], trained_model)

        testing_data["Predicted States"] = predicted_states

        self._StateMetrics(testing_data)
        return testing_data

#----------------Helper Functions------------------
    def _Fit(self, data_df: pd.DataFrame, iterations: int) -> hmm.GMMHMM: 
        model = hmm.GMMHMM(n_components = self.num_regimes, n_mix = self.n_mix, n_iter = iterations)
        model.fit(data_df)
        return model
    
    def _Predict(self, observation_cols: pd.DataFrame,trained_model: hmm.GMMHMM) -> np.array:
        self.soft_classifications = trained_model.predict_proba(observation_cols)
        return trained_model.predict(observation_cols) #Returns array of hidden states and probability of belonging
        
    def _CheckConvergence(self, data_df, max_iter):
        model = hmm.GMMHMM(self.num_regimes, n_iter=max_iter)
        model.fit(data_df)
        history = model.monitor_.history

        plt.plot(range(1, len(history) + 1), history)
        plt.xlabel("Iteration")
        plt.ylabel("Log-Likelihood")
        plt.title("HMM Convergence")
        plt.tight_layout()
        plt.show()

    #Function to print stats of labels            
    def _StateMetrics(self, testing_data: pd.DataFrame) -> None:
        state_0 = testing_data.loc[testing_data["Predicted States"] == 0, :]
        state_1 = testing_data.loc[testing_data["Predicted States"] == 1, :]

        numeric_cols = [col for col in testing_data.columns if col not in ("Date", "Predicted States")]

        for state, df in {"State 0": state_0, "State 1": state_1}.items():
            print(f"\n{'='*40}")
            print(f"  {state} (n={len(df)})")
            print(f"{'='*40}")

            print("\nMeans:")
            print(df[numeric_cols].mean().to_string())

            print("\nCovariance Matrix:")
            print(df[numeric_cols].cov().to_string())

            print("\nCorrelation Matrix:")
            print(df[numeric_cols].corr().to_string())

        
    def _Visualize_Results(self, test_results_df: pd.DataFrame, sector: str, ticker: str):
        col_title = sector
        ticker_vol_title = f"{ticker} Volatility"
        test_results_df["Date"] = pd.to_datetime(test_results_df["Date"])

        colors = {0: "#378ADD", 1: "#E24B4A"}  # blue, red

        fig = go.Figure()

        for state, color in colors.items():
            mask = test_results_df["Predicted States"] == state
            subset = test_results_df[mask]

            fig.add_trace(go.Scatter3d(
                x=subset["Date"].astype(np.int64) // 10**9,
                y=subset[col_title],
                z=subset[ticker_vol_title],
                mode="markers",
                name=f"State {state}",
                marker=dict(size=5, color=color, opacity=0.7),
                text=subset["Date"].dt.strftime("%Y-%m-%d"),
                hovertemplate=(
                    "<b>Date:</b> %{text}<br>"
                    f"<b>Sentiment:</b> %{{y:.3f}}<br>"
                    f"<b>Volatility:</b> %{{z:.3f}}<br>"
                    "<extra>State " + str(state) + "</extra>"
                )
            ))

        date_range = pd.date_range(
            test_results_df["Date"].min(),
            test_results_df["Date"].max(),
            periods=6
        )
        tick_vals = date_range.astype(np.int64) // 10**9
        tick_text = date_range.strftime("%b %Y").tolist()

        fig.update_layout(
            title=f"3D Regime Analysis: {sector} — {ticker}",
            scene=dict(
                xaxis=dict(title="Date", tickvals=tick_vals.tolist(), ticktext=tick_text),
                yaxis=dict(title="Sentiment Score"),
                zaxis=dict(title=ticker_vol_title),
            ),
            legend_title="Predicted State",
            margin=dict(l=0, r=0, b=0, t=40),
            height=700
        )

        fig.show()


if __name__ == "__main__":
    pass