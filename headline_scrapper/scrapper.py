"""
This module will be scrape the youtube transcript of the Bloomberg Survelliance 
show
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
from pathlib import Path
import re
import csv
import signal 

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class TranscriptSegment:
    timestamp: str
    text: str
    seconds: int = field(init=False)

    def __post_init__(self):
        self.seconds = self._parse_timestamp(self.timestamp)

    @staticmethod
    def _parse_timestamp(ts: str) -> int:
        parts = list(map(int, ts.strip().split(":")))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return 0

    def __str__(self):
        return f"[{self.timestamp}] {self.text}"


# ── Selectors ─────────────────────────────────────────────────────────────────

SELECTORS = {
    "expand_btn":       (By.XPATH, '//*[@id="expand"]'),
    "transcript_btn":   (By.XPATH, '//*[@id="primary-button"]//button'),
    "contents":         (By.XPATH, '//*[@id="contents"]'),
    "segment_tag":      "transcript-segment-view-model",
    "timestamp_class":  "ytwTranscriptSegmentViewModelTimestamp",
    # ↓ updated: direct span child, not yt-formatted-string
    "text_xpath":       ".//span[@role='text']",
    "vid_title": (By.XPATH, '//*[@id="title"]/h1/yt-formatted-string'), 
    "url_playlist" : (By.XPATH, '//*[@id="contents"]/ytd-playlist-video-list-renderer')
}


# ── Scraper class ─────────────────────────────────────────────────────────────
class Scraper:
    def __init__(self, url: str, timeout: int = 10):
        self.vid_title = None
        self.url = url #Youtube playlist of videos to be scrapped
        self.timeout = timeout
        self.driver = self._init_driver()
        self.wait = WebDriverWait(self.driver, timeout)
        self.progress_counter = None #Last scrapped url index in case force quit

        #Handles saving progress upon program termination
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    # -- Setup -----------------------------------------------------------------
    def _handle_exit(self,sig, frame):
        start_index_file_name = "start_index.txt"
        with open(start_index_file_name, mode="w") as file:
            file.write(f"{self.progress_counter}")
        
        logger.info(f"Interrupted — {self.progress_counter} transcripts scraped so far.")
        raise SystemExit(0)


    @staticmethod
    def _init_driver() -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument("--mute-audio")
        return webdriver.Chrome(options=options)

    # -- Navigation ------------------------------------------------------------

    def _click_expand(self) -> None:
        """Open the video description ('...more')."""
        try:
            btn = self.wait.until(EC.element_to_be_clickable(SELECTORS["expand_btn"]))
            btn.click()
            logger.info("Expanded video description.")
        except TimeoutException:
            logger.warning("Expand button not found — description may already be open.")

    def _click_transcript(self) -> None:
        """Click the 'Show transcript' button inside the description."""
        try:
            btn = self.wait.until(EC.element_to_be_clickable(SELECTORS["transcript_btn"]))
            btn.click()
            logger.info("Transcript panel opened.")
            # Give the panel time to render before we query segments
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, SELECTORS["segment_tag"]))
            )
        except TimeoutException:
            logger.error("Transcript button not found or panel failed to load.")
            raise

    # -- Extraction ------------------------------------------------------------
    def _get_title(self) -> Optional[str]:
        try:
            el = self.wait.until(EC.presence_of_element_located(SELECTORS["vid_title"]))
            self.vid_title = el.text
        except TimeoutException:
            logger.warning("Could not find video title.")

    def _extract_segment(self, el) -> Optional[TranscriptSegment]:
        try:
            timestamp = el.find_element(
                By.CLASS_NAME, SELECTORS["timestamp_class"]
            ).text.strip()

            # Match the exact span structure from the real DOM
            text_el = el.find_element(By.XPATH, SELECTORS["text_xpath"])

            # Clean up the ">>" speaker-change markers Bloomberg adds
            text = text_el.text.strip().replace("&gt;&gt;", ">>")

            if not timestamp or not text:
                return None

            return TranscriptSegment(timestamp=timestamp, text=text)

        except (NoSuchElementException, StaleElementReferenceException) as e:
            logger.debug("Skipping segment — %s", e)
            return None
        
    def _scroll_transcript_panel(self) -> None:
        """
        Scroll the transcript panel until no new segments appear.
        Walks up from a known segment to find the scrollable ancestor
        (the ytd-macro-markers-list-renderer or its scrollable parent).
        """
        panel = self.driver.execute_script("""
            // Start from the list renderer that wraps all chapters
            const listRenderer = document.querySelector('ytd-macro-markers-list-renderer');
            if (!listRenderer) return null;

            // Walk up to find the scrollable ancestor
            let el = listRenderer.parentElement;
            while (el && el !== document.body) {
                const style = window.getComputedStyle(el);
                const overflow = style.overflowY;
                if ((overflow === 'auto' || overflow === 'scroll') && el.scrollHeight > el.clientHeight) {
                    return el;
                }
                el = el.parentElement;
            }

            // Fallback: the list renderer itself may scroll
            return listRenderer;
        """)

        if not panel:
            logger.warning("Could not locate transcript scroll container — skipping scroll.")
            return

        last_count = 0
        stall_count = 0
        max_stalls = 3

        while stall_count < max_stalls:
            self.driver.execute_script(
                "arguments[0].scrollTop += arguments[0].offsetHeight;", panel
            )
            time.sleep(0.6)

            current_count = len(
                self.driver.find_elements(By.TAG_NAME, SELECTORS["segment_tag"])
            )

            if current_count == last_count:
                stall_count += 1
                logger.debug("No new segments (stall %d/%d)", stall_count, max_stalls)
            else:
                stall_count = 0
                logger.debug("Segments so far: %d", current_count)

            last_count = current_count

        logger.info("Scrolling complete. Total segments in DOM: %d", last_count)

    def _collect_segments(self, retries: int = 2) -> list[TranscriptSegment]:
        self._scroll_transcript_panel()

        for attempt in range(1, retries + 2):
            try:
                els = self.driver.find_elements(By.TAG_NAME, SELECTORS["segment_tag"])

                if not els:
                    logger.warning("No transcript segments found.")
                    return []

                segments = [seg for el in els if (seg := self._extract_segment(el))]
                segments.sort(key=lambda s: s.seconds)
                logger.info("Extracted %d segments.", len(segments))
                return segments

            except StaleElementReferenceException:
                if attempt <= retries:
                    logger.warning("Stale DOM — retrying (attempt %d)…", attempt)
                    time.sleep(1)
                else:
                    logger.error("Stale DOM retries exhausted.")
                    raise
            except TimeoutException:
                logger.error("Timed out waiting for transcript segments.")
                raise

        return []

    def _ScrapePlaylist(self,):
        self.driver.get(self.url)
        try:
            # Wait for the playlist container to load
            container = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="contents"]/ytd-playlist-video-list-renderer'))
            )

            # Scroll to load all videos
            last_count = 0
            stale_scrolls = 0
            max_stale = 5

            while stale_scrolls < max_stale:
                # Collect currently loaded video elements
                video_elements = self.driver.find_elements(By.XPATH, '//ytd-playlist-video-renderer//a[@id="video-title"]')
                current_count = len(video_elements)

                if current_count == last_count:
                    stale_scrolls += 1
                else:
                    stale_scrolls = 0
                    last_count = current_count

                # Scroll the last video into view to trigger lazy loading
                if video_elements:
                    self.driver.execute_script("arguments[0].scrollIntoView();", video_elements[-1])
                time.sleep(1.5)

            # Extract URLs from all loaded video elements
            video_elements = self.driver.find_elements(By.XPATH, '//ytd-playlist-video-renderer//a[@id="video-title"]')
            urls = []
            for el in video_elements:
                href = el.get_attribute("href")
                if href and "watch?v=" in href:
                    # Strip playlist params, keep only the video ID
                    urls.append(href.split("&")[0])

            logger.info(f"Scraped {len(urls)} videos from playlist")
            return urls

        except TimeoutException:
            logger.warning("Could not find playlist container")
            return []

    
    #This method saves data as a pandas df
    def _Save_Data(self, segments: list) -> None:
        data = {
            "Time Stamp": [segment.timestamp for segment in segments],
            "Text": [segment.text for segment in segments],
        }

        output_dir = Path("./Scrapped_Bloomberg_Transcripts")
        output_dir.mkdir(parents=True, exist_ok=True)

        safe_title = re.sub(r'[\\/*?:"<>|]', "_", self.vid_title)
        file_path = output_dir / f"{safe_title}.csv"
        pd.DataFrame(data).to_csv(file_path, index=False)

    def _scrape_transcript(self, start_index, lst_of_urls):
        """
        Full pipeline: load page → expand description →
        open transcript panel → extract segments.
        """
        #Scrape list of urls to be scrapped
        self.progress_counter = start_index

        #Check if scraped list of url exists      
        for index in range(start_index, len(lst_of_urls)):
            self.driver.get(lst_of_urls[index])
            self._get_title()
            self._click_expand()
            self._click_transcript()
            segments = self._collect_segments()
            self._Save_Data(segments)
            self.progress_counter+=1
            logger.info(f"Transcripts Scrapped: {self.progress_counter}/{len(lst_of_urls)}")
        logger.info(f"Data Scraping Completed")


    # -- Public API ------------------------------------------------------------

    def New_Scrape(self,):
        lst_of_urls = self._ScrapePlaylist()
        url_lst_file_path = "./headline_scrapper/url_lst.txt"
        with open(url_lst_file_path, mode='w') as file:
            for url in lst_of_urls:
                file.write(f"{url}\n")

        self._scrape_transcript(0, lst_of_urls)   
    
    def Resume_Scrape(self, url_lst_file_path, last_scrapped_index_file):
        #Retrieve list of urls to be scrapped
        url_lst = []
        try:
            with open(url_lst_file_path, mode="r") as file:
                url_lst = file.readlines() #Expects 1 url per line
        except Exception as e:
            logger.warning(f"Error obtaining saved list of URLs: {e}")

        start_index = None
        try:
            with open(last_scrapped_index_file, mode='r') as file:
                start_index = int(file.readline())
            
            self._scrape_transcript(start_index, url_lst)
        except Exception as e:
            logger.warning(f"Error obtaining saved starting index: {e}")
            logger.warning("Scrape was not executed")
    
    def Scrape_Specific_Urls(self, list_urls = None):
        self._scrape_transcript(0, list_urls)


    def close(self) -> None:
        self.driver.quit()

    # Context-manager support: `with Scraper(url) as s:`
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ── Output helpers ────────────────────────────────────────────────────────────

def to_plain_text(segments: list[TranscriptSegment]) -> str:
    return " ".join(s.text for s in segments)

def to_timestamped_text(segments: list[TranscriptSegment]) -> str:
    return "\n".join(str(s) for s in segments)

def to_srt(segments: list[TranscriptSegment]) -> str:
    def fmt(sec):
        h, r = divmod(sec, 3600)
        m, s = divmod(r, 60)
        return f"{h:02}:{m:02}:{s:02},000"

    return "\n".join(
        f"{i}\n{fmt(s.seconds)} --> {fmt(s.seconds + 3)}\n{s.text}\n"
        for i, s in enumerate(segments, 1)
    )

#Creating a pandas dataframe with text and timestamps



#Write code to scrape URL from all videos in this playlist
# https://www.youtube.com/playlist?list=PLGaYlBJIOoa-qaI1saEniG3cR9V0Mu-PE



if __name__ == "__main__":
    URL = "https://www.youtube.com/watch?v=3D8PMRAyZY0"
    # Option 1 — context manager (driver auto-closes on exit)
    with Scraper(URL) as scraper:
        segments = scraper.scrape_transcript()
        print(scraper.vid_title)
        
        # output = to_timestamped_text(segments)
     
        # with open("transcript.txt", "w", encoding="utf-8") as f:
        #     f.write(output)
        
        # logger.info("Transcript saved to transcript.txt (%d segments)", len(segments))


