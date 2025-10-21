import sys
from PyQt6.QtCore import pyqtSignal, QThread

try:
    import ollama
except ImportError:
    print("Error: The 'ollama' Python package is required.")
    print("Please install it using: pip install ollama")
    sys.exit(1)


class OllamaWorkerTranslate(QThread):
    """Worker thread to handle sequential LLM tasks (Detection then Translation)."""
    # Signal to update the main output (translation result)
    result_ready = pyqtSignal(str) 
    # Signal to update the Language Detected label
    language_detected = pyqtSignal(str) 
    # Signal for errors
    error_occurred = pyqtSignal(str)

    def __init__(self, client, model_name, source_text, target_lang):
        super().__init__()
        self.client = client
        self.model = model_name
        self.source_text = source_text
        self.target_lang = target_lang
        self.detected_lang = "" # Store the detected language

    def _call_llm(self, messages):
        """Helper to make the synchronous Ollama API call."""
        # This part remains similar to your original run() logic
        response = self.client.chat(model=self.model, messages=messages)
        return response['message']['content'].strip()

    def run(self):
        """Performs language detection (Step 1) and then translation (Step 2)."""
        try:
            # --- STEP 1: Language Detection ---
            detection_prompt = "Detect the language of the following text. Respond with ONLY the language name (e.g., 'English' or 'French') and nothing else."
            
            messages_detect = [
                {"role": "system", "content": detection_prompt},
                {"role": "user", "content": self.source_text}
            ]
            
            # Call LLM for detection
            detected_lang_raw = self._call_llm(messages_detect)
            
            # Simple cleanup, ensuring it's a single word/phrase
            self.detected_lang = detected_lang_raw.split('\n')[0].strip()
            
            # Emit the detected language back to the UI
            self.language_detected.emit(self.detected_lang)

            # --- STEP 2: Translation ---
            system_prompt = (
                f"You are a professional language translator. Translate the user's text from {self.detected_lang} to {self.target_lang}. "
                "Only provide the translated text and nothing else."
            )
            
            messages_translate = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.source_text}
            ]
            
            # Call LLM for translation
            translation = self._call_llm(messages_translate)
            
            # Emit the final translation result
            self.result_ready.emit(translation)

        except Exception as e:
            # Catch any API or connection errors
            self.error_occurred.emit(f"LLM operation failed. Details: {e}")


# --- Simple Ollama worker ---
class TextSummaryWorker(QThread):
    """Worker thread for simple, one-shot LLM tasks (like Summarization)."""
    result_ready = pyqtSignal(str) 
    error_occurred = pyqtSignal(str)

    def __init__(self, client, model_name, prompt, system_prompt):
        super().__init__()
        self.client = client
        self.model = model_name
        # Note the parameter names here: prompt and system_prompt
        self.prompt = prompt
        self.system_prompt = system_prompt

    def run(self):
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
            
        messages.append({"role": "user", "content": self.prompt})

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            self.result_ready.emit(response['message']['content'])
        
        except ollama.ResponseError as e:
            self.error_occurred.emit(f"Ollama API Error (Model '{self.model}'): {e}")
        except Exception as e:
            self.error_occurred.emit(f"Connection Error: Is the Ollama service running? Details: {e}")

# --- Ollama Worker for Video Summary ---
# Only transcript so its similar to text

# Import the external library needed for YouTube transcripts
# pip install youtube-transcript-api

from youtube_transcript_api import YouTubeTranscriptApi   
from urllib.parse import urlparse, parse_qs

class VideoSummaryWorker(QThread):
    """Worker thread to fetch a YouTube transcript and summarize it with an LLM."""
    result_ready = pyqtSignal(str) 
    progress_update = pyqtSignal(str) # To update the UI on step changes
    error_occurred = pyqtSignal(str)

    def __init__(self, client, model_name, video_url):
        super().__init__()
        self.client = client
        self.model = model_name
        self.video_url = video_url

        try:
            self.yt_api_client = YouTubeTranscriptApi()
        except Exception as e:
            # Handle potential initialization errors (e.g., if the __init__ requires more)
            print(f"Error initializing YouTubeTranscriptApi: {e}")
            self.yt_api_client = None 

        self.system_prompt = (
            "You are an expert video summarizer. The following text is a video transcript. "
            "Analyze the transcript and generate a concise, detailed summary of the key topics, "
            "arguments, and conclusions. The final summary **must be in English**, and you "
            "must **only** output the summary text."
        )

    def _get_youtube_id(self, url):
        """Extracts the YouTube video ID from a URL.""" 
        parsed_url = urlparse(url)
        if parsed_url.netloc == 'youtu.be':
            return parsed_url.path[1:]
        if parsed_url.netloc in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query).get('v', [None])[0]
        return None

    def _call_llm(self, text_to_summarize):
        """Helper to make the Ollama API call for summarization."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": text_to_summarize}
        ]
        response = self.client.chat(model=self.model, messages=messages)
        return response['message']['content'].strip()

    def run(self):
        if self.yt_api_client is None:
            self.error_occurred.emit("Video Transcript API failed to initialize.")
            return

        video_id = self._get_youtube_id(self.video_url)
        if not video_id:
            self.error_occurred.emit("Invalid or unsupported video URL. Must be a valid YouTube link.")
            return

        transcript_text = ""
        try:
            # --- STEP 1: Fetch Transcript ---
            self.progress_update.emit("Fetching video transcript (Step 1/2)...")
            
            # Call fetch() on the instance (self.yt_api_client)
            fetched_transcript_obj = self.yt_api_client.fetch(video_id)
            
            # The fetched object is NOT a simple list, it's a FetchedTranscript object.
            raw_data_list = fetched_transcript_obj.to_raw_data()
            
            # Join the text parts into a single string
            transcript_text = " ".join([item['text'] for item in raw_data_list])
            
            if not transcript_text:
                self.error_occurred.emit("Transcript fetched, but it was empty.")
                return

            # --- STEP 2: Summarize with LLM ---
            self.progress_update.emit("Sending transcript to LLM for summarization (Step 2/2)...")
            
            # Call LLM for summarization
            summary = self._call_llm(transcript_text)
            
            # Emit the final result
            self.result_ready.emit(summary)

        except Exception as e:
            # Catch errors like no transcript available, network issues, or LLM failure
            self.error_occurred.emit(f"Failed to process video. Check if subtitles/transcript are available. Error: {e}")
