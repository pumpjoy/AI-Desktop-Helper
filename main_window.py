import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt

from helper.local_llm_connector import LocalLLMConnector

from asset.page_translator import TranslatorPage
from asset.page_summary_text import TextSummaryPage
from asset.page_summary_video import VideoSummaryPage

from asset.sidebar_button import SidebarButton

class MainWindow(QMainWindow):
    """Main window of the application with the sidebar and stacked content."""
    def __init__(self, llm_connector):
        super().__init__()
        self.llm_connector = llm_connector
        
        self.setWindowTitle(f"Local LLM Utility Hub - Model: {self.llm_connector.model}")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central Widget and Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar Widget (Left Drawer)
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #2C3E50; border-right: 1px solid #1abc9c;")
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setSpacing(10)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)

        # 2. Stacked Widget (Right Content Area)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #F8F9F9;")
        
        # --- Create Pages and add to Stacked Widget (PASSING CONNECTOR) ---
        self.translator_page = TranslatorPage(self.llm_connector) 
        self.summary_page = TextSummaryPage(self.llm_connector)
        self.video_page = VideoSummaryPage(self.llm_connector)
        
        self.stacked_widget.addWidget(self.translator_page)
        self.stacked_widget.addWidget(self.summary_page)
        self.stacked_widget.addWidget(self.video_page)
        
        # --- Create Sidebar Buttons and connect ---
        
        # Button 1: Translator 
        self.btn_translator = SidebarButton("<=>", "Translator")
        self.btn_translator.clicked.connect(lambda: self.switch_page(0))
        
        # Button 2: Text Summary
        self.btn_summary = SidebarButton("---", "Text Summary")
        self.btn_summary.clicked.connect(lambda: self.switch_page(1))
        
        # Button 3: Video Summary
        self.btn_video = SidebarButton("[>]", "Youtube Summary")
        self.btn_video.clicked.connect(lambda: self.switch_page(2))
        
        # Add buttons to sidebar layout
        sidebar_layout.addWidget(self.btn_translator)
        sidebar_layout.addWidget(self.btn_summary)
        sidebar_layout.addWidget(self.btn_video)
        
        # Ensure only one button is checked at a time
        self.button_group = [self.btn_translator, self.btn_summary, self.btn_video]
        for button in self.button_group:
            button.clicked.connect(lambda checked, b=button: self.update_button_states(b))
            
        # Initial state: select the first button
        self.btn_translator.setChecked(True)
        self.update_button_states(self.btn_translator) # Apply initial style
        
        # --- Final Layout Assembly ---
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)

    def update_button_states(self, current_button):
        """Ensures only the clicked button remains checked/active."""
        for button in self.button_group:
            if button is not current_button:
                button.setChecked(False)
            else:
                button.setChecked(True)

    def switch_page(self, index):
        """Switches the page displayed in the QStackedWidget."""
        self.stacked_widget.setCurrentIndex(index)

    def closeEvent(self, event):
        """Checks for active threads before allowing the window to close."""
        # Check all your pages for active threads
        pages = [self.translator_page, self.summary_page, self.video_page]
        
        for page in pages:
            if hasattr(page, 'thread') and page.thread and page.thread.isRunning():
                # Ask the thread to stop gracefully by exiting its event loop
                page.thread.quit()
                # Wait a small amount of time for the thread to finish
                page.thread.wait(1000) # Wait up to 1s
                
                # If the thread is still running after the wait, it's a serious problem,
                # but we've done our best for graceful exit.                
                if page.thread.isRunning():
                    print(f"Warning: Thread on {page.__class__.__name__} is still running and will be terminated.")

            # IMPORTANT: If a new thread is created before the old one finishes, 
            # the old one's reference in self.thread will be overwritten.
            # If your OllamaWorker is a QThread, this cleanup should work.

        # Allow the close event to proceed
        event.accept()

if __name__ == '__main__':
    # --- LLM initialization ---
    MODEL_TO_USE = "ibm/granite3.2:8b"
    llm_connector = LocalLLMConnector(model_name=MODEL_TO_USE)
    
    # 1. Blocking Model Check/Pull: Ensures the model is ready before the UI starts
    is_ready = llm_connector.is_available_and_pull_if_needed()

    if not is_ready:
        QMessageBox.critical(None, "Fatal Error", 
                             f"The required Ollama model '{MODEL_TO_USE}' could not be made available. "
                             "Please ensure the Ollama service is running and check the console output.", 
                             QMessageBox.StandardButton.Ok)
        sys.exit(1)

    # 2. Start the PyQt Application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow(llm_connector)
    window.show()
    sys.exit(app.exec())