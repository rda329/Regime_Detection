""" 
This module will be used to prompt google gemini to provide 
sentiment analysis scores based on the scraped transcripts
"""
import os
from dotenv import load_dotenv
import pandas as pd
import logging
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class SentimentAgent():
    def __init__(self):
            self.timeout = 10
            self.driver = webdriver.Chrome()
            self.wait = WebDriverWait(self.driver, self.timeout)
    
    def GetSentimentScores(self,csv_file_path):
        transcript_text = self._Csv_To_Text(csv_file_path)
        response = self._MakePrompt(transcript_text)

    #Prompts Gemini Model
    def _MakePrompt(self, transcript):
        system_instructions = (
            "You are a financial analyst. Analyze the provided transcript and "
            "output sentiment scores (-1 to 1) for S&P 500 sectors in valid JSON format."
        )
        full_prompt = f"{system_instructions}\n\nTranscript to analyze: {transcript}"

        try:
            self.driver.get("https://gemini.google.com/app")

            # Wait for the input box to load
            wait = WebDriverWait(self.driver, 20)
            input_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )

            # Type the prompt
            input_box.click()
            input_box.send_keys(full_prompt)
            time.sleep(1)  # Brief pause before sending

            # Submit with Enter
            input_box.send_keys(Keys.ENTER)

            # Wait for the response to finish generating
            # Gemini shows a stop button while generating — wait for it to disappear
            wait.until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "button[aria-label='Stop response']"))
            )
            time.sleep(2)  # Extra buffer for final render

            # Grab the last response block
            response_blocks = self.driver.find_elements(By.CSS_SELECTOR, "message-content")
            if not response_blocks:
                raise ValueError("No response found on page")

            raw_text = response_blocks[-1].text
            return raw_text

        except Exception as e:
            logger.warning(f"Error prompting Gemini: {e}")
            return None

        finally:
            self.driver.quit()
    
    #Converts Bloomberg transcript csv to text file
    def _Csv_To_Text(self,csv_file_path):
        transcript_text = ''
        try:
            df = pd.read_csv(csv_file_path)
            text_list = df["Text"].to_list()
            for text in text_list:
                transcript_text+=f"{text} "
        except Exception as e:
            logger.warning(f"Error reading csv file: {e}")
        return transcript_text
       
        


if __name__ == "__main__":
    agent = SentimentAgent()

    file_path = "Scrapped_Bloomberg_Transcripts\Bloomberg Surveillance 01_02_2025.csv"
    scores = agent.GetSentimentScores(file_path)
    print(scores)
    
