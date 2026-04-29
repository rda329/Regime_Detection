Project Notes

The goal of this project is to create a regime detection bot. Regime are classified
by the market participant sensitivity to headline news related to the markets.

Part 1: Create a headline scrapper
 - Scrape the text from the Bloomberg Surveillance Youtube Video
 - Classify each phrase as positive, neutral, negative
 - Score the broadcast's sentiment as a whole 


Part 1.5: Look at the scraped data
- Learn about sentiment analysis guidelines and pitfalls
- Clean and Explore the scrapped data
- Learn a little bit about each core sector in the SP500
- Overlay Intraday volality with sentiment scores

Part 2: Estimate the market sensitivity to headlines 

 Expectation is 
 Neutral news = Low volatilty
 Very positive / negative news = High Vol. 

 How do we define / measure very positive / negative news

Part 3: Compute latent sensitivity factor using Kalman Filter
- Intraday volatilty = sensitivity factor * News Sentiment analysis measure

stdev / N = meu 

if meu = 1 , norm : normal b    
if meu large high vol but low rel. news pressure : high sensitivity to news
if meu small low vol. but large rel. new pressure : low sensetivity to news

MODEL: Realized volatilty / Sentiment Score


Part 4: Regimes

 Low sensitivity to news:= Very pos./neg. news but low vol.
 High sensitivity to news:= Neutral news but high vol. 
 Standard:= Behavior as expected


 Motivation:
 I was inspired by a comment made while watching Bloomberg Surveillance that markets were
 very steady even with news of tariffs, job losses, and war. 

 I was curious how sensitive market participants were to news.
 I was inspired by friction in physics. Friction is the resisting force to motion.
 Friction equals a friction coefficient and the weight/force of the object. 
 I want to measure market sensitivity to news (friction coefficient) based on the news (Weight).
 This market sensetivity coefficient is latent so I want to use Kalman's filter to 
 estimate it based on Intraday volality as my signal. 


 Limitations In Approach

- Sentiment Analysis is done on individual sentence from the transcript.
This is a naive approach since it may leave out context or not establish connection between
related statements.