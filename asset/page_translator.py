import sys
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel,
    QTextEdit, QComboBox 
) 
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from helper.ollama_worker import OllamaWorkerTranslate # MUST be the updated worker
from base_page import BasePage 

class TranslatorPage(BasePage):
    """Page for the Language Translation feature."""
    def __init__(self, llm_connector):
        super().__init__(llm_connector)
        
        # --- UI Initialization ---
        self.detection_label = QLabel("Language detected: *Awaiting input*")
        self.detection_label.setFont(QFont("Segoe UI", 10))

        layout = QVBoxLayout(self)
        self.input_text = QTextEdit()
        self.output_text = QTextEdit()
        self.translate_button = QPushButton("Translate") 
        self.target_language_combo = QComboBox()

        # ASCII Icon: <=> (Exchange)
        title = QLabel(f"<=> Language Translator (Model: {self.llm_connector.model})")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # Language Selection Dropdown Setup 
        languages = [
            "English (EN)", 
            "Japanese (JA)", 
            "Korean (KO)", 
            "Chinese (ZH)",
            "Spanish (ES)", 
            "Portuguese (PT)", 
            "Italian (IT)", 
            "French (FR)", 
            "German (DE)", 
            "Arabic (AR)", 
            "Czech (CS)", 
            "Dutch (NL)", 
        ]

        lang_selection_layout = QHBoxLayout()
        # Display detection label
        lang_selection_layout.addWidget(self.detection_label) 
        lang_selection_layout.addStretch()
        
        target_label = QLabel("Translate to:")
        target_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.target_language_combo.addItems(languages)
        self.target_language_combo.setCurrentText("English (EN)")
        self.target_language_combo.setMinimumWidth(150)
        
        lang_selection_layout.addSpacing(40)
        lang_selection_layout.addWidget(target_label)
        lang_selection_layout.addWidget(self.target_language_combo)
        lang_selection_layout.addStretch()

        # Input/Output Styling
        self.input_text.setPlaceholderText("Enter text to translate...")
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Translation will appear here.")
        self.translate_button.setFixedSize(200, 40)
        self.translate_button.setStyleSheet("background-color: #2ECC71; color: white; border-radius: 5px;")
        
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.translate_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Layout Assembly
        layout.addWidget(self.input_text)
        layout.addLayout(lang_selection_layout)
        layout.addLayout(h_layout)
        layout.addWidget(self.output_text)

        layout.setContentsMargins(50, 20, 50, 20)

        # --- LLM INTEGRATION ---
        self.translate_button.clicked.connect(self.run_translation)
        
        # Disable button if LLM is not ready
        if not self.llm_connector.is_model_ready:
            self.translate_button.setDisabled(True)
            self.output_text.setText("LLM is not ready. Check console for model pull status.")

    def run_translation(self):
        """Starts the non-blocking translation process (Detection + Translation)."""
        source_text = self.input_text.toPlainText().strip()
        # The worker handles source language detection internally
        target_lang = self.target_language_combo.currentText().split(' (')[0]
        
        if not source_text:
            self.output_text.setText("Please enter text to translate.")
            return

        self.output_text.setText(f"Detecting language, then translating to {target_lang}...")
        self.detection_label.setText("Language detected: *Detecting...*") # Set status immediately
        self.translate_button.setDisabled(True)

        # Instantiate the updated worker with text and target language
        self.thread = OllamaWorkerTranslate(
            client=self.llm_connector.client,
            model_name=self.llm_connector.model,
            source_text=source_text, # Passed as source_text
            target_lang=target_lang  # Passed as target_lang
        )
        
        self.thread.language_detected.connect(self.display_detected_language) 
        
        # Connect existing signals
        self.thread.result_ready.connect(self.display_translation)
        self.thread.error_occurred.connect(self.handle_llm_error)
        self.thread.finished.connect(self.thread_finished_cleanup)

        self.thread.start()

    def display_detected_language(self, language):
        """Updates the label with the language detected by the LLM (called mid-process)."""
        self.detection_label.setText(f"Language detected: **{language}**")
        self.output_text.setText(f"Language **{language}** detected. Starting translation...")


    def display_translation(self, translation):
        """Handles the successful result from the worker thread (final output)."""
        self.output_text.setText(translation)
        self.translate_button.setDisabled(False) 

    def thread_finished_cleanup(self):
        """Cleans up the QThread object after it has fully finished and emitted 'finished'."""
        
        if self.thread:
            self.thread.wait() 
        
        self.thread = None
    
    def handle_llm_error(self, error_message):
        """Custom handler to reset UI after an error."""
        super().handle_llm_error(error_message, title="Translation Error")
        self.output_text.setText("Translation failed. See error details above.")
        self.translate_button.setDisabled(False)