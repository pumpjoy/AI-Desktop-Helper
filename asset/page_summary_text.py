from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel,
    QTextEdit, QSizePolicy, 
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from helper.ollama_worker import TextSummaryWorker
from base_page import BasePage 

class TextSummaryPage(BasePage):
    """Page for the Text Summary feature."""
    
    # Instance variable to hold the active worker thread
    thread = None 
    
    def __init__(self, llm_connector):
        super().__init__(llm_connector)
        layout = QVBoxLayout(self)
        
        # ASCII Icon: --- (List/Document)
        title = QLabel(f"--- Text Summarizer (Model: {self.llm_connector.model})")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Paste a large document or article text here...")
        self.input_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        self.summary_output.setPlaceholderText("The summarized text will be displayed here.")
        self.summary_output.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout.addWidget(self.input_text)
        
        self.summarize_button = QPushButton("Generate Summary")
        self.summarize_button.setFixedSize(200, 40)
        self.summarize_button.setStyleSheet("background-color: #3498DB; color: white; border-radius: 5px;")
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.summarize_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(h_layout)
        
        layout.addWidget(self.summary_output)
        layout.setContentsMargins(50, 20, 50, 20)
        
        # --- LLM Integration ---
        self.summarize_button.clicked.connect(self.run_summarization)
        
        if not self.llm_connector.is_model_ready:
            self.summarize_button.setDisabled(True)
            self.summary_output.setText("LLM is not ready. Check console for model pull status.")

    # --- Core Logic Methods ---
    def run_summarization(self):
        """Starts the non-blocking summarization process."""
        source_text = self.input_text.toPlainText().strip()
        
        if not source_text:
            self.summary_output.setText("Please paste text into the input box to summarize.")
            return

        self.summary_output.setText("Generating summary using local LLM...")
        self.summarize_button.setDisabled(True)

        # Define the specific system instruction for the LLM task
        # This prompt asks the model to output the summary in English by default.
        system_prompt = (
            "You are an expert text summarizer. "
            "Your task is to analyze the user's input text and generate a concise, "
            "well-structured summary of the key information. "
            "The final summary **must be in English**, and you must **only** output the summary text."
        )

        # Initialize and start the worker thread
        # Note: We use the existing OllamaWorker, passing the prompt and system prompt.
        self.thread = TextSummaryWorker(
            client=self.llm_connector.client,
            model_name=self.llm_connector.model,
            prompt=source_text,
            system_prompt=system_prompt
        )
        
        # Connect signals
        self.thread.result_ready.connect(self.display_summary)
        self.thread.error_occurred.connect(self.handle_llm_error)
        
        # CRITICAL: Connect the finished signal for cleanup
        self.thread.finished.connect(self.thread_finished_cleanup)

        self.thread.start()

    # --- Slot handles ---
    def display_summary(self, summary):
        """Handles the successful result from the worker thread."""
        self.summary_output.setText(summary)
        self.summarize_button.setDisabled(False) 

    def handle_llm_error(self, error_message):
        """Custom handler to reset UI after an error."""
        # Assuming BasePage has a generic handler, call it first
        super().handle_llm_error(error_message, title="Summarization Error")
        self.summary_output.setText("Summary generation failed. See error details above.")
        self.summarize_button.setDisabled(False)
        
    def thread_finished_cleanup(self):
        """Cleans up the QThread object after it has fully finished."""
        
        # The safest pattern to prevent QThread destruction errors
        if self.thread:
            self.thread.wait() 
        
        self.thread = None