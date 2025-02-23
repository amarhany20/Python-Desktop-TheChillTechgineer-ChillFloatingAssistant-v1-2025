# src/main.py

import sys
from PySide6.QtWidgets import QApplication
from src.state.state_manager import StateManager
from src.ui.widget import FloatingWidget

def main():
    # Initialize the PySide6 application
    app = QApplication(sys.argv)
    
    # Load configuration and initialize the state manager
    state_manager = StateManager()
    
    # Create and show the floating widget
    widget = FloatingWidget(state_manager=state_manager)
    widget.show()
    
    # Run the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
