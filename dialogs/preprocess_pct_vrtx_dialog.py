'''
LAYERS NEEDED = ['InceputLinie', 'Cutii', 'Stalpi', 'BMPnou', 'ReteaJT', 'NOD_NRSTR', 'AUXILIAR', 'pct_vrtx', "Numar_Postal"]

STEP 1. Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou > NODURI
> merge from process_dialog.py
STEP 2. Extract Vertices - ReteaJT > VERTICES
STEP 3. Difference - VERTICES, NODURI > DIFFERENCE
STEP 4. Add Geometry Attributes - DIFFERENCE > pct_vrtx
STEP 5. Delete rows without coordinates (xcoord, ycoord)

'''
from .process_dialog import ProcessDialog
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem, QApplication, QMessageBox
from qgis.core import QgsProject, QgsMessageLog, Qgis, edit # type: ignore
import processing # type: ignore
from qgis.PyQt.QtCore import Qt # type: ignore

class PreProcessPctVrtxDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.processor = ProcessDialog()
        
        self.setWindowTitle("Pre-process Data - pct_vrtx")

        # Set fixed dimensions for the window
        self.setFixedSize(400, 250)

        self.layout = QVBoxLayout()
        
        # Label
        self.progress_text = QLabel("Steps to do:")
        self.layout.addWidget(self.progress_text)

        # Create a list to display the steps visually
        self.steps_list = QListWidget(self)
        
        self.steps_list.setStyleSheet("""
            QListWidget::item {
                color: black;  # Keep text color black
                background-color: #f0f0f0;  # Default background for light mode
            }
            QListWidget::item:selected {
                background-color: #d0e0f0;  # Slightly different background for selected items
            }
        """)

        # Define the steps
        self.steps = [
            "1. Merge Vector Layers - VERTICES",
            "2. Extract Vertices - ReteaJT",
            "3. Difference - VERTICES, NODURI > DIFFERENCE",
            "4. Add Geometry Attributes - pct_vrtx",
            "5. Sterge randurile fara coordonate",
        ]

        # Add steps to the list, making them non-interactive
        for step in self.steps:
            item = QListWidgetItem(step)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)  # Make items non-interactive but visible
            self.steps_list.addItem(item)
            QgsMessageLog.logMessage(f"{self.steps_list}", "EnelAssist", level=Qgis.Info)

        self.layout.addWidget(self.steps_list)

        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)

        self.btn_layout = QHBoxLayout()
        
        self.run_button = QPushButton("Run", self)
        self.run_button.clicked.connect(self.__exec__)
        self.btn_layout.addWidget(self.run_button)
        
        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(self.close)
        self.btn_layout.addWidget(self.close_button)
        self.layout.addLayout(self.btn_layout)
        
        self.setLayout(self.layout)
        
    def __exec__(self):
        QgsMessageLog.logMessage("Starting data preprocessing...", "EnelAssist", level=Qgis.Info)
        
        # error-checking: no layers present, show a DIALOG BOX with the error message
        if not QgsProject.instance().mapLayers().values():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Error")
            msg_box.setText("No layers are present in the project.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            if msg_box.exec_() == QMessageBox.Ok:
                self.close()
            return
        
        # Automated layer retrieval
        self.layers = self.get_layers()
        if not self.layers:
            QgsMessageLog.logMessage("No layers found matching the required names.", "EnelAssist", level=Qgis.Critical)
            return
        
        # Update progress bar
        total_steps = len(self.steps_list) # Total number of processing steps
        self.progress_bar.setMaximum(total_steps)
        step = 0
        self.base_dir = QFileDialog.getExistingDirectory(None, "Select Folder")
        if not self.base_dir:
            return
        os.makedirs(self.base_dir, exist_ok=True)  # Ensure directory exists
        
        self.run_button.setEnabled(False)
        self.close_button.setEnabled(False)
        
        # NOTE 1. Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou > NODURI
        success = self.processor.merge_layers([self.layers['AUXILIAR'], self.layers['InceputLinie'], self.layers['Cutii'], self.layers['Stalpi'], self.layers['BMPnou']], "NODURI", self.base_dir, self.layers)
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 0, success)
        
        # NOTE 2. Extract Vertices - ReteaJT > VERTICES
        success = self.extract_vertices(self.layers['ReteaJT'], "VERTICES")
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 1, success)
        
        # NOTE 3. Difference - VERTICES, NODURI > DIFFERENCE
        success = self.difference_layers(self.layers['VERTICES'], self.layers['NODURI'], "DIFFERENCE")
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 2, success)
        
        # NOTE 4. Add Geometry Attributes - DIFFERENCE > pct_vrtx
        success = self.add_geometry_attributes(self.layers['DIFFERENCE'], "pct_vrtx")
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 3, success)
        
        # NOTE 5. Delete rows without coordinates (point_x, point_y)
        success = self.delete_rows_without_coordinates(self.layers['pct_vrtx'])
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 4, success)
        
        self.delete_layer([self.layers['VERTICES'], self.layers['DIFFERENCE']])
        
        self.close_button.setEnabled(True)
        
        
    def get_layers(self):
        '''
        Get layers by name from the QGIS project and add them to self.layers
        '''
        QgsMessageLog.logMessage("Retrieving layers from the QGIS project...", "EnelAssist", level=Qgis.Info)
        layers = {}
        layer_names = ['InceputLinie', 'Cutii', 'Stalpi', 'BMPnou', 'ReteaJT', 'NOD_NRSTR', 'AUXILIAR', 'pct_vrtx', "Numar_Postal", "NODURI", "RAMURI", "RAMURI_NODURI", "LEG_NODURI", "DIFFERENCE", "VERTICES", "LEG_NRSTR", "Coloana"]

        # Get all layers in the current QGIS project (keep the layer objects)
        qgis_layers = QgsProject.instance().mapLayers().values()
        QgsMessageLog.logMessage(f"----------- QGIS LAYERS: {qgis_layers}", "EnelAssist", level=Qgis.Info)

        # Iterate through the actual layer objects
        for layer_name in layer_names:
            layer = next((l for l in qgis_layers if l.name() == layer_name), None)
            layers[layer_name] = layer  # Add the layer if found, else None
            # QgsMessageLog.logMessage(f"Layer found: key: {layer_name}, value: {layer}", "EnelAssist", level=Qgis.Info)

        # QgsMessageLog.logMessage(f"Layers found with IDs: {layers}", "EnelAssist", level=Qgis.Info)
        return layers
        
    def extract_vertices(self, input_layer, output):
        if not input_layer:
            return False

        try:
            output = os.path.join(self.base_dir, f"{output}.shp")
            processing.run("native:extractvertices", {
                'INPUT': input_layer,
                'OUTPUT': output
            })
            self.processor.add_layer_to_project(output)
            self.layers.update(self.get_layers())
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in extract_vertices: {e}", "EnelAssist", level=Qgis.Critical)
            return False

    def difference_layers(self, input_layer, overlay_layer, output):
        if not input_layer or not overlay_layer:
            QgsMessageLog.logMessage("No input or overlay layer provided.", "EnelAssist", level=Qgis.Critical)
            return False

        try:
            output = os.path.join(self.base_dir, f"{output}.shp")
            processing.run("native:difference", {
                'INPUT': input_layer,
                'OVERLAY': overlay_layer,
                'OUTPUT': output
            })
            self.processor.add_layer_to_project(output)
            self.layers.update(self.get_layers())
            
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in calc_difference: {e}", "EnelAssist", level=Qgis.Critical)
            return False

    def add_geometry_attributes(self, input_layer, output):
        if not input_layer:
            QgsMessageLog.logMessage("No input layer provided.", "EnelAssist", level=Qgis.Critical)
            return False


        try:
            output = os.path.join(self.base_dir, f"{output}.shp")
            processing.run("qgis:exportaddgeometrycolumns", {  # Corrected the algorithm ID
                'INPUT': input_layer,
                'CALC_METHOD': 0,  # Planimetric calculation
                'OUTPUT': output
            })
            self.processor.add_layer_to_project(output)
            self.layers.update(self.get_layers())
            return True

        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_geometry_attributes: {e}", "EnelAssist", level=Qgis.Critical)
            return False

    def delete_rows_without_coordinates(self, layer):
        if not layer:
            return False

        try:
            with edit(layer):
                for feature in layer.getFeatures():
                    if feature['xcoord'] in [None, "NULL", 'nan'] and feature['ycoord'] in [None, "NULL", 'nan']:
                        QgsMessageLog.logMessage(f"Deleting feature: {feature.id()}", "EnelAssist", level=Qgis.Info)
                        layer.deleteFeature(feature.id())
            layer.updateExtents()
            layer.commitChanges()
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in delete_rows: {e}", "EnelAssist", level=Qgis.Critical)
            return False
        
        
    def delete_layer(self, layer_list):
        # remove layer from project and os
        for layer in layer_list:
            QgsProject.instance().removeMapLayer(layer)
        return True
            
        