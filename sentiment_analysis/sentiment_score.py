""" 
This module will be used to prompt CHATGPT to provide 
sentiment analysis scores based on the scraped transcripts
"""
import os
from dotenv import load_dotenv
import pandas as pd
import logging
import re
from openai import OpenAI
import time

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class SentimentAgent():
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key = self.api_key)

    #---------------Complete Pipeline------------------------------
    def ConductSentimentAnalysis(self, data_folder_path: str, starting_index = 0) -> None:
        data_file_paths = self._Get_Filenames(data_folder_path)

        responses_dict ={
            "Date": [],
            "LLM Response": []
        }

        progress_counter = starting_index
        try:
            for i in range(starting_index, len(data_file_paths)):
                transcript = self._Csv_To_Text(data_file_paths[i][1])
                LLM_response = self._MakePrompt(transcript)
                responses_dict["LLM Response"].append(LLM_response)
                if data_file_paths[i][0]:
                    responses_dict["Date"].append(data_file_paths[i][0])
                else:
                    responses_dict["Date"].append("MISSING")
                progress_counter +=1
                logger.info(f"Transcript Analyzed: {progress_counter}/{len(data_file_paths)}")
                time.sleep(30)
            logger.info("Successfully Completed Analysis")
        except Exception as e:
            logger.warning(f"Sentiment Analysis Failed: {e}")
        finally:
            #Save Results in CSV
            self._SaveResponses(responses_dict)
            logger.info("Data Saved")
            return    



    #--------------Getting Scores and Saving Results----------------
    #Prompt LLM for Sentiment Analysis
    def _MakePrompt(self, transcript: str) -> str:        
        system_instructions = (
            "You are a financial analyst. Analyze the provided transcript and "
            "output sentiment scores (-1 to 1) for S&P 500 sectors in valid JSON format. Only return the JSON."
        )

        try:
            response = self.client.responses.create(
                model="gpt-5.4-mini",
                instructions = system_instructions,
                input= transcript,
            )
            return response.output_text
        except Exception as e:
            logger.warning(f"Error prompting OpenAI Model: {e}")
            return None
        

    
    #Save responses from LLMs
    def _SaveResponses(self, responses_dict: dict) -> None:
        filepath = "./sentiment_analysis/Bloomberg_Transcript_Result.csv"
        df = pd.DataFrame(responses_dict)
        
        if os.path.exists(filepath):
            df.to_csv(filepath, mode='a', header=False, index=False)
        else:
            df.to_csv(filepath, mode='w', header=True, index=False)
    

    #-------------- Getting Data --------------------
    #Loading text    
    #Converts Bloomberg transcript csv to text file
    def _Csv_To_Text(self,csv_file_path_end):        
        csv_file_path = f"./Scrapped_Bloomberg_Transcripts/{csv_file_path_end}"

        transcript_text = ''
        try:
            df = pd.read_csv(csv_file_path)
            text_list = df["Text"].to_list()
            for text in text_list:
                transcript_text+=f"{text} "
        except Exception as e:
            logger.warning(f"Error reading csv file: {e}")
        return transcript_text #Date associated with the transcript

    #Loading file paths for bloomberg transcripts csvs
    def _Get_Filenames(self, folder_path: str) -> list[tuple[str,str]]:
        everything = os.listdir(folder_path)
        
        #Extract dates from filename
        def get_date(file_name):
            pattern = r"\b(\d{1,2}_\d{1,2}_\d{2,4})\b"
            match = re.search(pattern, file_name)
            if match:
                extracted_date = match.group(1)
                parts = extracted_date.split("_")
                month = parts[0].zfill(2)        # "8"  → "08"
                day   = parts[1].zfill(2)        # "5"  → "05" (already 2 digits but safe)
                year  = parts[2]
                if len(year) == 2:               # "24" → "2024"
                    year = "20" + year
                normalized = f"{month}_{day}_{year}"
                return normalized
            else:
                #logger.warning(f"Failure to extract date from CSV: {file_name}")
                return None
        
        filenames = []
        for item in everything:
            full_path = os.path.join(folder_path, item)
            if os.path.isfile(full_path):
                date_str = get_date(item)
                filenames.append((date_str,item)) #tuple (date, filename)
                
        return filenames

        


if __name__ == "__main__":
    agent = SentimentAgent()

    folder_path = "./Test"
    agent.ConductSentimentAnalysis(folder_path, starting_index=0)



"""
Add a stop and go mechanism and a logger to track completed analysis

Use an index
"""