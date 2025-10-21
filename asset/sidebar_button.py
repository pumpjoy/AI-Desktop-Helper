from PyQt6.QtWidgets import QPushButton 
from PyQt6.QtGui import QFont

class SidebarButton(QPushButton):
    """Custom button for the sidebar with fixed size and hover effects."""
    def __init__(self, icon_text, label_text, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 60)
        # Use a larger, bold font for the simplified text approach
        self.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        
        # Change to simple text concatenation, removing all rich text formatting
        self.setText(f"{icon_text}  {label_text}")
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #2C3E50; 
                color: #ECF0F1; 
                border: none; 
                text-align: left;
                padding-left: 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #34495E;
            }
            QPushButton:checked {
                background-color: #1ABC9C; /* Active color */
                border-left: 5px solid #1ABC9C;
                color: white;
            }
        """)
        self.setCheckable(True)