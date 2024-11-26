'''
LAYERS NEEDED = ['InceputLinie', 'Cutii', 'Stalpi', 'BMPnou', 'ReteaJT', 'NOD_NRSTR', 'AUXILIAR', 'pct_vrtx', "Numar_Postal"]

STEP 1. Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou > NODURI
STEP 2. Snap geometries to layer - ReteaJT, NODURI // Tolerance - 1, Behavior - End points to end points only > ReteaJT (overwrite)
STEP 3. Merge Vector Layers - BMPnou, Numar_Postal > LEG_NODURI
STEP 4. Snap geometries to layer - NOD_NRSTR, LEG_NODURI // Tolerance - 1, Behavior - End points to end points only > NOD_NRSTR (overwrite)
STEP 5. Snap geometries to layer - AUXILIAR, ReteaJT // Tolerance - 1, Behavior - Prefer alignment nodes, don't insert new vertices > AUXILIAR (overwrite)

'''

from .process_dialog import ProcessDialog
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem, QMessageBox
from qgis.core import QgsProject, QgsMessageLog, Qgis, QgsVectorLayer, QgsCoordinateReferenceSystem # type: ignore
from qgis.PyQt.QtCore import Qt # type: ignore
from qgis.analysis import QgsGeometrySnapper # type: ignore
import processing # type: ignore

class PreProcessSnapDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.processor = ProcessDialog()
        
        self.setWindowTitle("Pre-process Data - SNAP")

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
            "1. Merge Vector Layers - NODURI",
            "2. Snap geometries to layer - ReteaJT",
            "3. Merge Vector Layers - LEG_NODURI",
            "4. Snap geometries to layer - NOD_NRSTR",
            "5. Snap geometries to layer - AUXILIAR"
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
        
        # NOTE 1. Merge Vector Layers - NODURI
        success = self.processor.merge_layers([self.layers['InceputLinie'], self.layers['Cutii'], self.layers['Stalpi'], self.layers['BMPnou']], 'NODURI', self.base_dir, self.layers)
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 0, success)
        
        # NOTE 2. Snap geometries to layer - ReteaJT
        success = self.snap_geometries(self.layers['ReteaJT'], self.layers['NODURI'], 6) # 6 = End points to end points only
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 1, success)
        
        # NOTE 3. Merge Vector Layers - LEG_NODURI
        success = self.processor.merge_layers([self.layers['BMPnou'], self.layers['Numar_Postal']], 'LEG_NODURI', self.base_dir, self.layers)
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 2, success)
        
        # NOTE 4. Snap geometries to layer - NOD_NRSTR
        success = self.snap_geometries(self.layers['NOD_NRSTR'], self.layers['LEG_NODURI'], 6) # 6 = End points to end points only
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 3, success)
        
        # NOTE 5. Snap geometries to layer - AUXILIAR
        success = self.snap_geometries(self.layers['AUXILIAR'], self.layers['ReteaJT'], 2) # 2 = Prefer alignment nodes, don't insert new vertices
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 4, success)
        
        self.close_button.setEnabled(True)
        
        # Retrieve layers by name from the QGIS project
    def get_layers(self):
        '''
        Get layers by name from the QGIS project and add them to self.layers
        '''
        QgsMessageLog.logMessage("Retrieving layers from the QGIS project...", "EnelAssist", level=Qgis.Info)
        layers = {}
        layer_names = ['InceputLinie', 'Cutii', 'Stalpi', 'BMPnou', 'ReteaJT', 'NOD_NRSTR', 'AUXILIAR', 'pct_vrtx', "Numar_Postal", "NODURI", "RAMURI", "RAMURI_NODURI", "LEG_NODURI", "NODURI_AUX_VRTX", "RAMURI_AUX_VRTX", "LEG_NRSTR", "Coloana"]

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
        

    def snap_geometries(self, input_layer, reference_layer, behavior):
        if not input_layer or not reference_layer:
            return False

        try:
            result = processing.run("native:snapgeometries", {
                'INPUT': input_layer,
                'REFERENCE_LAYER': reference_layer,
                'TOLERANCE': 1.0,
                'BEHAVIOR': behavior,
                'OUTPUT': 'memory:'
            })

            # Update input layer with the result
            input_layer.dataProvider().deleteFeatures([f.id() for f in input_layer.getFeatures()])
            input_layer.dataProvider().addFeatures(result['OUTPUT'].getFeatures())
            input_layer.updateFields()
            input_layer.updateExtents()
            return True

        except Exception as e:
            QgsMessageLog.logMessage(f"Error in snap_geometries: {e}", "EnelAssist", level=Qgis.Critical)
            return False

