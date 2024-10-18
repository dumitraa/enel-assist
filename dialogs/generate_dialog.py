import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QPushButton, QFileDialog, QMessageBox
from qgis.core import QgsProject
import pandas as pd

class GenerateExcelDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generate Excel Files")
        self.layout = QVBoxLayout()

        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)

        self.run_button = QPushButton("Generate Excel Files", self)
        self.run_button.clicked.connect(self.__exec__)
        self.layout.addWidget(self.run_button)

        self.setLayout(self.layout)

    def __exec__(self):
        # Dictionary mapping shapefile names (case-insensitive) to desired Excel file names
        layer_mapping = {
            'auxiliar': 'AUXILIAR',
            'bmpnou': 'BMP',
            'cutii': 'CD',
            'stalpi': 'DERIV_CT',
            'inc_linii': 'INC_LINI',
            'leg_noduri': 'LEG_NODURI',
            'leg_nrstr': 'LEG_NRSTR',
            'numar_postal': 'NR_STR',
            'ramuri_noduri': 'RAMURI_NODURI'
        }
        
        # Directory prompt for saving Excel files
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not output_dir:
            return  # If user cancels, do nothing

        total_steps = len(layer_mapping)
        self.progress_bar.setMaximum(total_steps)
        step = 0

        # Iterate through the layer mappings and export the tables
        for layer_name, excel_name in layer_mapping.items():
            layer = self.get_layer_by_name(layer_name)
            
            if layer:
                try:
                    # Export to Excel
                    self.export_layer_to_excel(layer, os.path.join(output_dir, f'{excel_name}.xlsx'))
                    step += 1
                    self.progress_bar.setValue(step)
                except Exception as e:
                    # Show an error message if there’s an issue with export
                    QMessageBox.critical(self, "Error", f"Failed to export {layer_name} to {excel_name}.xlsx: {str(e)}")
            else:
                # Show an error message if the layer doesn't exist
                QMessageBox.warning(self, "Layer Missing", f"Layer '{layer_name}' not found!")
                continue

        # Notify user when all exports are complete
        QMessageBox.information(self, "Complete", "Excel file generation completed!")

    def get_layer_by_name(self, name):
        """
        Helper function to retrieve a layer by name in a case-insensitive manner.
        """
        # Get all layers in the current project
        all_layers = QgsProject.instance().mapLayers().values()
        
        # Search for the layer by name (case-insensitive)
        for layer in all_layers:
            if layer.name().lower() == name.lower():
                return layer
        return None

    def export_layer_to_excel(self, layer, output_path):
        """
        Helper function to export the attribute table of a layer to an Excel file.
        """
        # Get the fields and features (attributes) from the layer
        field_names = [field.name() for field in layer.fields()]
        features = [feat.attributes() for feat in layer.getFeatures()]

        # Create a DataFrame using the fields and features
        df = pd.DataFrame(features, columns=field_names)
        
        # Export to Excel using pandas
        df.to_excel(output_path, index=False)
