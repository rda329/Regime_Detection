It has proven difficult/not free to obtain intraday ticker data.

Shifted analysis to a interday market sensetivity to news. 

Goal:

Detect change in sensitivity to news by market participants
- Implement a Kalman filter that will update dynamically overtime
- Use a state space that represents the sentiment scores for the past week 


NOTES:
In notebook2 I plotted the 5 day return volatilities and the sentiment scores.

Input: sentiment score
Output: past 5 day volatility
Latent variable being measured by Kalman filter: Market sensitivity to news

Based on the initial plotting typically sentiment score and volatility should move
together. For my regime detection I am interested when they dont, this may indicate
a regime shift signalling reduced or increased senstivity to news by market participants.

