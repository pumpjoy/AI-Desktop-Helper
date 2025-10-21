import sys
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel,
    QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from helper.ollama_worker import VideoSummaryWorker
from base_page import BasePage 

class VideoSummaryPage(BasePage):
    """Page for the Video Summary feature."""
    thread = None
    
    def __init__(self, llm_connector):
        super().__init__(llm_connector)
        layout = QVBoxLayout(self)
        
        # ASCII Icon: [>] (Play Button)
        title = QLabel(f"[>] Youtube Summarizer (Model: {self.llm_connector.model})")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.rate_limit_warning = QLabel(
            "⚠️ **Warning:** Fetching transcripts relies on an external API (YouTube). "
            "Avoid sending rapid, repeated requests to prevent temporary rate limits."
        )
        self.rate_limit_warning.setFont(QFont("Segoe UI", 10))
        # Style the text for emphasis (e.g., a subtle orange/yellow background or strong text)
        self.rate_limit_warning.setStyleSheet("""
            QLabel {
                color: #B8860B; /* Dark Goldenrod/Warning Color */
                padding: 5px;
                border: 1px solid #FFD700;
                background-color: #FFFACD; /* Light yellow background */
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.rate_limit_warning)

        self.url_input = QLineEdit() # Store as self attribute for access
        self.url_input.setPlaceholderText("Paste video URL (e.g., YouTube) here...")
        self.url_input.setMinimumHeight(40)
        
        layout.addWidget(self.url_input)
        
        self.fetch_button = QPushButton("Fetch and Summarize Video") # Store as self attribute
        self.fetch_button.setFixedSize(250, 40)
        self.fetch_button.setStyleSheet("background-color: #E74C3C; color: white; border-radius: 5px;")
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.fetch_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(h_layout)

        self.summary_output = QTextEdit() # Store as self attribute
        self.summary_output.setReadOnly(True)
        self.summary_output.setPlaceholderText("Summary of the video content will appear here.")
        
        layout.addWidget(self.summary_output)
        layout.setContentsMargins(50, 20, 50, 20)
        
        # --- LLM Integration ---
        self.fetch_button.clicked.connect(self.run_video_summary)
        
        if not self.llm_connector.is_model_ready:
            self.fetch_button.setDisabled(True)
            self.summary_output.setText("LLM is not ready. Check console for model pull status.")

    # --- Core Logic Methods ---
    def run_video_summary(self):
        """Starts the non-blocking video fetching and summarization process."""
        video_url = self.url_input.text().strip()
        
        if not video_url:
            self.summary_output.setText("Please enter a video URL.")
            return

        self.summary_output.setText("Starting video processing...")
        self.fetch_button.setDisabled(True)

        # Initialize and start the worker thread
        self.thread = VideoSummaryWorker(
            client=self.llm_connector.client,
            model_name=self.llm_connector.model,
            video_url=video_url
        )
        
        # Connect signals
        self.thread.progress_update.connect(self.display_progress)
        self.thread.result_ready.connect(self.display_summary)
        self.thread.error_occurred.connect(self.handle_llm_error)
        self.thread.finished.connect(self.thread_finished_cleanup)

        self.thread.start()

    # --- Slot Handles ---
    def display_progress(self, message):
        """Updates the output text with the current step (e.g., fetching or summarizing)."""
        self.summary_output.setText(message)

    def display_summary(self, summary):
        """Handles the successful result from the worker thread."""
        self.summary_output.setText(summary)
        self.fetch_button.setDisabled(False) 

    def handle_llm_error(self, error_message):
        """Custom handler to reset UI after an error."""
        super().handle_llm_error(error_message, title="Video Summary Error")
        self.summary_output.setText(f"Video summary failed. Details: {error_message}")
        self.fetch_button.setDisabled(False)
        
    def thread_finished_cleanup(self):
        """Cleans up the QThread object after it has fully finished."""
        
        if self.thread:
            self.thread.wait() 
        
        self.thread = None