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
Prompt Google Gemini to score give a sentiment score to each core sector in
the SP500 from -1 to 1 based on the Bloomberg Surveillance transcript.

Weakness:
This approach is a black box method for conducting sentiment analysis.
Gemini does not explicit provide reasoning for each score.

Benefit:
Due to the large amount of data used to train LLM and personal use I feel confident
in its ability to detect sentiment. The exact value is still a blackbox however
the model being used will be consistent therefore results / scoring be consistent.
