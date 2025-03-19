
import os
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile, QTextStream

class MacOSStyleLoader:
    def __init__(self):
        self.style_dir = os.path.join(os.path.dirname(__file__), 'styles')
        
    def load_stylesheet(self, theme='light'):
        """Load MacOS style stylesheet based on theme"""
        style_file = os.path.join(self.style_dir, f'macOS_{theme}.qss')
        
        if os.path.exists(style_file):
            file = QFile(style_file)
            file.open(QFile.ReadOnly | QFile.Text)
            stream = QTextStream(file)
            stylesheet = stream.readAll()
            file.close()
            return stylesheet
        else:
            return ""
            
    def apply_stylesheet(self, app, theme='light'):
        """Apply MacOS stylesheet to QApplication"""
        if not isinstance(app, QApplication):
            raise TypeError("Expected QApplication instance")
            
        stylesheet = self.load_stylesheet(theme)
        app.setStyleSheet(stylesheet)
        
    def get_available_themes(self):
        """Get list of available MacOS themes"""
        themes = []
        for file in os.listdir(self.style_dir):
            if file.startswith('macOS_') and file.endswith('.qss'):
                theme = file.replace('macOS_', '').replace('.qss', '')
                themes.append(theme)
        return themes
