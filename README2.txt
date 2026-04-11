Sentiment Analysis Notes:

Transcript Data has commercial which can add noise.

Core sectors in the SP500
1. Information Technology
2. Health Care
3. Financials
4. Consumers Discretionary
5. Communication Services 
6. Industrials 
7. Consumer Staples
8. Energy
9. Utilities
10. RealEstate
11. Materials 


Approach: 
Prompt Chatgpt to score give a sentiment score to each core sector in
the SP500 from -1 to 1 based on the Bloomberg Surveillance transcript.

Weakness:
This approach is a black box method for conducting sentiment analysis.
LLM does not explicit provide methodology for each score.

Benefit:
Unlike word by word sentiment analysis. LLM is able to return a score taking into account context and attempt to tailor scores for 
specific sector of the economy providing more informed results compared to just an average goog/bad word count. 
