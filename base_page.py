from PyQt6.QtWidgets import (
    QWidget, QMessageBox
) 

class BasePage(QWidget):
    """Base class to simplify page creation and LLM connector passing."""
    def __init__(self, llm_connector, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_connector = llm_connector
        self.thread = None # To hold the worker thread

    def handle_llm_error(self, error_message, title="Ollama LLM Error"):
        """Displays a modal box for LLM-related errors."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText("A critical error occurred while communicating with the local LLM.")
        msg.setInformativeText("Please ensure the Ollama service is running and the selected model is installed.")
        msg.setDetailedText(error_message)
        msg.exec()
        if self.thread:
            self.thread = None