'''
LAYERS NEEDED = ['1InceputLinie', '2Cutii', '3Stalpi', '4BMPnou', 'ReteaJT']

STEP 1. Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou (ORDER MATTERS) > NODURI
> merge from process_dialog.py
STEP 2. Merge Vector Layers - ReteaJT > RAMURI
> merge from process_dialog.py
STEP 3. Join Attributes by Location - RAMURI > NODURI - ONE TO MANY > RAMURI_NODURI
> join from process_dialog.py
STEP 4. Add Column to RAMURI_NODURI - count target_fid
> add column from process_dialog.py
'''

from .process_dialog import ProcessDialog
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem, QMessageBox
from qgis.core import QgsProject, QgsMessageLog, Qgis # type: ignore
from qgis.PyQt.QtCore import Qt # type: ignore

class PreVerifyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.processor = ProcessDialog()
        
        self.setWindowTitle("Pre-verify Data")

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
            "2. Merge Vector Layers - RAMURI",
            "3. Adauga coloana TARGET_FID - RAMURI",
            "4. Adauga coloana TARGET_FID - NODURI",
            "5. Join Attributes by Location - RAMURI_NODURI",
            "6. Adauga coloana Count_ID - RAMURI_NODURI"
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
        
        self.update_layer_names()  # Rename layers to match the expected names

        # Automated layer retrieval
        self.layers = self.processor.get_layers()
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
        success = self.processor.merge_layers([self.layers['1InceputLinie'], self.layers['2Cutii'], self.layers['3Stalpi'], self.layers['4BMPnou']], "NODURI", self.base_dir, self.layers)
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 0, success)
        
        # NOTE 2. Merge Vector Layers - RAMURI
        success = self.processor.merge_layers([self.layers['ReteaJT']], "RAMURI", self.base_dir, self.layers)
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 1, success)
        
        # NOTE 3. Adauga coloana TARGET_FID - RAMURI
        success = self.processor.add_target_fid_column(self.layers['RAMURI'].name())
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 2, success)
        
        # NOTE 4. Adauga coloana TARGET_FID - NODURI
        success = self.processor.add_target_fid_column(self.layers['NODURI'].name())
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 3, success)
        
        
        # NOTE 5. Join Attributes by Location - RAMURI_NODURI
        success = self.processor.join_attributes_by_location(self.layers['RAMURI'], self.layers['NODURI'], 'RAMURI_NODURI', 'One-to-Many', self.base_dir, self.layers)
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 4, success)
        
        # NOTE 6. Adauga coloana Count_ID - RAMURI_NODURI
        success = self.processor.add_count_id_column(self.layers['RAMURI_NODURI'].name())
        step += 1
        self.progress_bar.setValue(step)
        self.processor.update_step(self.steps_list, 5, success)
        
        # NOTE 7. Rename layers without the numbers
        for layer in self.layers.values():
            if layer is not None:
                layer.setName(layer.name().replace("1", "").replace("2", "").replace("3", "").replace("4", "").replace("5", "").replace("6", ""))
                
        self.close_button.setEnabled(True)
        
        
    # Retrieve layers by name from the QGIS project
    def get_layers(self):
        '''
        Get layers by name from the QGIS project and add them to self.layers
        '''
        QgsMessageLog.logMessage("Retrieving layers from the QGIS project...", "EnelAssist", level=Qgis.Info)
        layers = {}
        layer_names = ['1InceputLinie', '2Cutii', '3Stalpi', '4BMPnou', 'ReteaJT', 'NOD_NRSTR', '5AUXILIAR', '6pct_vrtx', "Numar_Postal", "NODURI", "RAMURI", "RAMURI_NODURI", "LEG_NODURI", "NODURI_AUX_VRTX", "RAMURI_AUX_VRTX", "LEG_NRSTR", "Coloana"]

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
    
    def update_layer_names(self):
        '''
        Rename layer names - InceputLinie = 1InceputLinie, Cutii = 2Cutii, Stalpi = 3Stalpi, BMPnou = 4BMPnou, AUXILIAR = 5AUXILIAR, pct_vrtx = 6pct_vrtx
        '''
        
        # Get all layers in the current QGIS project
        qgis_layers = QgsProject.instance().mapLayers().values()
        # QgsMessageLog.logMessage(f"----------- QGIS LAYERS: {qgis_layers}", "EnelAssist", level=Qgis.Info)
        
        # Iterate through the actual layer objects
        for layer in qgis_layers:
            layer_name = layer.name()
            if layer_name.endswith('InceputLinie'):
                layer.setName('1InceputLinie')
            elif layer_name.endswith('Cutii'):
                layer.setName('2Cutii')
            elif layer_name.endswith('Stalpi'):
                layer.setName('3Stalpi')
            elif layer_name.endswith('BMPnou'):
                layer.setName('4BMPnou')
            elif layer_name.endswith('AUXILIAR'):
                layer.setName('5AUXILIAR')
            elif layer_name.endswith('pct_vrtx'):
                layer.setName('6pct_vrtx')
            else:
                pass
            # QgsMessageLog.logMessage(f"Layer renamed: {layer_name}", "EnelAssist", level=Qgis.Info)
        