import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QPushButton, QFileDialog, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
import pandas as pd

from .validate_dialog import ShpProcessor

class GenerateExcelDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generate Excel Files")
        self.layout = QVBoxLayout()
        self.processor = None

        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)

        self.run_button = QPushButton("Generate Excel Files", self)
        self.run_button.clicked.connect(self.__exec__)
        self.layout.addWidget(self.run_button)

        self.setLayout(self.layout)

    def __exec__(self):
        self.process_data()
        QgsMessageLog.logMessage(f"Executing export process at time {pd.Timestamp.now()}", "EnelAssist", level=Qgis.Info)
        
        # Directory prompt for saving Excel files
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return  # If user cancels, do nothing

        parser_ids = set(id(parser) for parser in self.processor.parsers)
        QgsMessageLog.logMessage(f"Unique parser IDs: {parser_ids}", "EnelAssist", level=Qgis.Info)

        for parser in self.processor.parsers:
            QgsMessageLog.logMessage(f"Exporting {parser.get_name()} data to Excel... There are {len(parser.data)} elements to export.. The parsers are {self.processor.parsers}", "EnelAssist", level=Qgis.Info)
            parser.export_to_excel(output_dir, parser.get_name())

        # Notify user when all exports are complete
        QMessageBox.information(self, "Complete", "Excel file generation completed!")

                
    def process_data(self):
        QgsMessageLog.logMessage("*******************************************Processing data...", "EnelAssist", level=Qgis.Info)
        source_paths = [layer.source() for layer in QgsProject.instance().mapLayers().values() if isinstance(layer, QgsVectorLayer)]
        if not source_paths:
            QgsMessageLog.logMessage("No vector layers found in the project.", "EnelAssist", level=Qgis.Warning)
            return

        if self.processor:
            QgsMessageLog.logMessage("Clearing existing parsers...!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", "EnelAssist", level=Qgis.Info)
            self.processor = None # Clear out any existing parsers to avoid duplicates
        self.processor = ShpProcessor(source_paths, validate=False)
