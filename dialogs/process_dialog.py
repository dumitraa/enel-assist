"""
- LAYERS NEEDED - ['1InceputLinie', '2Cutii', '3Stalpi', '4BMPnou', 'ReteaJT', 'NOD_NRSTR', '5AUXILIAR', '6pct_vrtx', "Numar_Postal", "Coloana"]


STEP 1. Calculate geometry for all shp files - X, Y coord line start and end
    > start_point($geometry)
    > end_point($geometry)
    > example:
        >   layer = iface.activeLayer()
            field_name = 'START_X'
            layer.startEditing()
            expression = QgsExpression('x(start_point($geometry))')
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
            index = layer.fields().indexOf(field_name)

            for feature in layer.getFeatures():
                context.setFeature(feature)
                value = expression.evaluate(context)
                layer.changeAttributeValue(feature.id(), index, value)
            layer.commitChanges()

STEP 2. Calculate geometry for ReteaJT - START_X, START_Y, END_X, END_Y

STEP 2. ReteaJT - Add 'lungime', 'id' columns - double
    > calculate length in "lungime" - length($geometry)
    > id - field calculator - FID - OK
    > example:
        >   layer.dataProvider().addAttributes([QgsField('lungime', QVariant.Double)])
            layer.updateFields()
            # calc length with length($geometry)

STEP 3. NOD_NRSTR - Add 'id' - double, Delete GlobalId (raman doar ID si FID)
    > id - field calculator - FID - OK
    
STEP 4 - Merge Vector Layers - 1InceputLinie / 2Cutii / 3Stalpi / 4BMPnou > folder - NODURI
STEP 5 - Merge Vector Layers - ReteaJT > folder - RAMURI

    > Use qgis:mergevectorlayers from the QGIS Processing Toolbox.
    > example:
        >   processing.run("qgis:mergevectorlayers", {
                'LAYERS': [layer1, layer2, layer3],  # list of layers to merge
                'CRS': 'EPSG:3844',  # Optional CRS
                'OUTPUT': '/path/to/output/layer.shp'
            })

STEP 6. Join Attributes by Location - RAMURI > NODURI - ONE TO MANY > RAMURI_NODURI
STEP 7. Join Attributes by Location - NOD_NRSTR > 4BMPnou - ONE TO ONE > LEG_NODURI
STEP 8. Join Attributes by Location - NOD_NRSTR > Numar_Postal - ONE TO ONE > LEG_NRSTR
    
    > Use qgis:joinattributesbylocation for spatial joins.
    > example:
        >   processing.run("qgis:joinattributesbylocation", {
                'INPUT': 'ramuri.shp',   # Input layer
                'JOIN': 'noduri.shp',    # Layer to join with
                'PREDICATE': [0],        # Spatial relation (0 = intersects)
                'JOIN_FIELDS': [],       # List of fields to join
                'METHOD': 1,             # Join type (1 = One-to-Many)
                'DISCARD_NONMATCHING': False,
                'OUTPUT': '/path/to/output.shp'
            })
            
STEP 9. Merge Vector Layers - 1InceputLinie, 2Cutii, 3Stalpi, 4BMPnou, 5AUXILIAR, 6pct_vrtx > folder - NODURI_AUX_VRTX

STEP 10. Join Attributes by Location - ramuri > noduri_aux_vrtx - ONE TO MANY > RAMURI_AUX_VRTX

STEP 11. RAMURI_AUX_VRTX - Add 'SEI' column - text
    > CASE 
        WHEN "nr_nod" THEN 3
        ELSE 1
      END

STEP 12. for each Join Attributes by Location - add Join_Count column with all values '1'

"""

import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem, QApplication, QMessageBox
from qgis.core import (QgsExpression, QgsExpressionContext, QgsExpressionContextUtils,  # type: ignore
                       QgsField, QgsProject, QgsMessageLog, Qgis, QgsVectorLayer)
from qgis.PyQt.QtGui import QColor, QFont # type: ignore
from qgis.PyQt.QtCore import QVariant, Qt # type: ignore
import processing # type: ignore

class ProcessDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Data")

        # Set fixed dimensions for the window
        self.setFixedSize(500, 350)  # Example dimensions: 600x400 pixels

        self.layout = QVBoxLayout()

        self.update_layer_names()  # Rename layers to match the expected names
        
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
            "1. Calculeaza X, Y la toate geometriile",
            "2. Calculeaza START_X, START_Y, END_X, END_Y pentru ReteaJT",
            "3. Adauga coloane 'lungime' si 'id' pentru ReteaJT",
            "4. Adauga coloana 'id' pentru NOD_NRSTR",
            "5. Merge Vector Layers - NODURI",
            "6. Merge Vector Layers - RAMURI",
            "7. Join Attributes by Location - RAMURI_NODURI",
            "8. Join Attributes by Location - LEG_NODURI",
            "9. Join Attributes by Location - LEG_NRSTR",
            "10. Merge Vector Layers - NODURI_AUX_VRTX",
            "11. Join Attributes by Location - RAMURI_AUX_VRTX",
            "12. Adauga coloana 'Count_ID' pentru 'RAMURI_AUX_VRTX'",
            "13. Adauga coloana 'SEI' pentru RAMURI_AUX_VRTX",
            "14. Adauga coloana 'Join_Count' pentru toate join-urile",
            "15. Sorteaza 'LEG_NRSTR' si 'LEG_NODURI' dupa 'ID'"
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
        layers_valid = [layer for layer in self.layers.values() if layer is not None]
        total_steps = len(self.steps) - 2 + len(layers_valid) - 2 # Total number of processing steps
        self.progress_bar.setMaximum(total_steps)
        step = 0
        self.base_dir = QFileDialog.getExistingDirectory(None, "Select Folder")
        if not self.base_dir:
            return
        os.makedirs(self.base_dir, exist_ok=True)  # Ensure directory exists

        # Execute all processing steps
        QgsMessageLog.logMessage("-------- START OF DATA PREPROCESSING --------", "EnelAssist", level=Qgis.Info)
        
        self.run_button.setEnabled(False)
        self.close_button.setEnabled(False)
        
        # NOTE 1. Calculate X. Y for layers
        for layer in self.layers.values():
            # QgsMessageLog.logMessage(f"Calculating geometry for layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
            if layer is not None and layer.name() in ["ReteaJT", "NOD_NRSTR"]:
                # QgsMessageLog.logMessage(f"Skipping layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
                continue
            elif layer is not None and layer.name() in ["6pct_vrtx"]:
                success = self.calculate_geometry(layer, "POINT_X", "POINT_Y")
                step += 1
                self.progress_bar.setValue(step)
            elif layer is not None:
                success = self.calculate_geometry(layer, "POINT_X", "POINT_Y", "POINT_Z", "POINT_M")
                # QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
                step += 1
                self.progress_bar.setValue(step)
        
        self.update_step(self.steps_list, 0, success)  # Mark step 1 as done
            
            
        # NOTE 2. Calculate START_X, START_Y, END_X, END_Y for ReteaJT
        success = self.calculate_geometry(self.layers["ReteaJT"], None, None, None, None, 'START_X', 'START_Y', 'END_X', 'END_Y')
        # QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
        step += 1
        self.progress_bar.setValue(step)
        self.update_step(self.steps_list, 1, success)  # Mark step 2 as done

        # NOTE 3. Add 'lungime' and 'id' columns to ReteaJT and calculate geometry length
        success = self.add_length_and_id(self.layers['ReteaJT'], 'lungime_', 'TARGET_FID')
        self.update_step(self.steps_list, 2, success)  # Mark step 3 as done
        # QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
        step += 1
        self.progress_bar.setValue(step)

        # NOTE 4. Manage NOD_NRSTR columns
        success = self.modify_nod_nrstr(self.layers['NOD_NRSTR'])
        self.update_step(self.steps_list, 3, success)  # Mark step 4 as done
        # QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
        step += 1
        self.progress_bar.setValue(step)

        # NOTE 5. Merge layers for NODURI
        success = self.merge_layers([self.layers['1InceputLinie'], self.layers['2Cutii'], self.layers['3Stalpi'], self.layers['4BMPnou']], 'NODURI', self.base_dir, self.layers)
        self.update_step(self.steps_list, 4, success)  # Mark step 5 as done
        step += 1
        self.progress_bar.setValue(step)

        # NOTE 6. Merge layers for RAMURI
        success = self.merge_layers([self.layers['ReteaJT'], self.layers['Coloana']], 'RAMURI', self.base_dir, self.layers)
        self.update_step(self.steps_list, 5, success)  # Mark step 6 as done
        step += 1
        self.progress_bar.setValue(step)

        # NOTE 7. Join Attributes by Location - RAMURI_NODURI
        success = self.join_attributes_by_location(self.layers['RAMURI'], self.layers['NODURI'], 'RAMURI_NODURI', 'One-to-Many', self.base_dir, self.layers)
        self.update_step(self.steps_list, 6, success)  # Mark step 7 as done
        step += 1
        self.progress_bar.setValue(step)

        # NOTE 8. Join Attributes by Location - LEG_NODURI
        success = self.join_attributes_by_location(self.layers['NOD_NRSTR'], self.layers['4BMPnou'], 'LEG_NODURI', 'One-to-One', self.base_dir, self.layers)
        self.update_step(self.steps_list, 7, success)  # Mark step 8 as done
        step += 1
        self.progress_bar.setValue(step)
        
        # NOTE 9. Join Attributes by Location - LEG_NRSTR
        success = self.join_attributes_by_location(self.layers['NOD_NRSTR'], self.layers['Numar_Postal'], 'LEG_NRSTR', 'One-to-One', self.base_dir, self.layers)
        self.update_step(self.steps_list, 8, success)  # Mark step 9 as done
        step += 1
        self.progress_bar.setValue(step)

        # NOTE 10. Merge layers for NODURI_AUX_VRTX
        success = self.merge_layers([self.layers['1InceputLinie'], self.layers['2Cutii'], self.layers['3Stalpi'], self.layers['4BMPnou'], self.layers['5AUXILIAR'], self.layers['6pct_vrtx']], 'NODURI_AUX_VRTX', self.base_dir, self.layers)
        self.update_step(self.steps_list, 9, success)  # Mark step 10 as done
        step += 1
        self.progress_bar.setValue(step)

        # NOTE 11. Join Attributes by Location - RAMURI_AUX_VRTX
        success = self.join_attributes_by_location(self.layers['RAMURI'], self.layers['NODURI_AUX_VRTX'], 'RAMURI_AUX_VRTX', 'One-to-Many', self.base_dir, self.layers)
        self.update_step(self.steps_list, 10, success)  # Mark step 11 as done
        step += 1
        self.progress_bar.setValue(step)
        
        # NOTE 12. Add 'Count_ID' for 'RAMURI_AUX_VRTX' - how many of each 'TARGET_FID' are there - identical
        success = self.add_count_id_column(self.layers['RAMURI_AUX_VRTX'].name())
        self.update_step(self.steps_list, 11, success)  # Mark step 12 as done
        step += 1
        self.progress_bar.setValue(step)

        # NOTE 13. Add 'SEI' column with conditional values
        success = self.add_sei_column(self.layers['RAMURI_AUX_VRTX'].name())
        self.update_step(self.steps_list, 12, success)  # Mark step 12 as done
        step += 1
        self.progress_bar.setValue(step)

        # NOTE 14. Add 'Join_Count' column for all joins with value '1'
        success1 = self.add_join_count_column(self.layers['RAMURI_NODURI'].name())
        success2 = self.add_join_count_column(self.layers['LEG_NODURI'].name())
        success3 = self.add_join_count_column(self.layers['LEG_NRSTR'].name())
        
        if success1 and success2 and success3:
            success = True
        elif success1 is False or success2 is False or success3 is False:
            success = None
        else:
            success = False
        self.update_step(self.steps_list, 13, success)  # Mark step 13 as done
        step += 1
        # QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
        self.progress_bar.setValue(step)
        
        # NOTE 15. Sort "LEG_NRSTR" and "LEG_NODURI" by "ID"
        success1 = self.sort_layer_by_field(self.layers['LEG_NRSTR'], 'ID')
        success2 = self.sort_layer_by_field(self.layers['LEG_NODURI'], 'ID')
        
        if success1 and success2:
            success = True
        elif success1 is False or success2 is False:
            success = None
        else:
            success = False
        self.update_step(self.steps_list, 14, success)  # Mark step 14 as done
        step += 1
        self.progress_bar.setValue(step)
        
        self.close_button.setEnabled(True)

    def update_step(self, steps_list, index, success=True):
        """Marks a step as done by updating the list item."""
        try:
            item = steps_list.item(index)
            # QgsMessageLog.logMessage(f"Updating step {index}: {item.text()}", "EnelAssist", level=Qgis.Info)
            if success:
                item.setText("✓ " + item.text())  # Add a checkmark
                item.setForeground(QColor("green"))  # Change text color to green to indicate completion
            elif success is None:
                item.setText("⚠ " + item.text())
                item.setForeground(QColor("orange"))  # Change text color to orange to indicate partial completion
            else:
                item.setText("✗ " + item.text())
                item.setForeground(QColor("red"))  # Change text color to red to indicate failure
            item.setFont(QFont("Arial", 10, QFont.Bold))  # Make the completed step bold
            QApplication.processEvents()  # Force UI update after each step
        except Exception as e:
            QgsMessageLog.logMessage(f"Error updating step {index}: {e}", "EnelAssist", level=Qgis.Critical)
            pass

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
            QgsMessageLog.logMessage(f"Layer found: key: {layer_name}, value: {layer}", "EnelAssist", level=Qgis.Info)

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

    def add_layer_to_project(self, layer_path):
        try:
            # Get the name of the layer without the file extension and the full path
            layer_name = os.path.splitext(os.path.basename(layer_path))[0]
            
            # Load the merged layer from the output path
            merged_layer = QgsVectorLayer(layer_path, layer_name, 'ogr')
            
            # Check if the layer is valid
            if not merged_layer.isValid():
                QgsMessageLog.logMessage(f"Invalid layer: {layer_path}", "EnelAssist", level=Qgis.Critical)
                return
            
            # Add the layer to the project with the proper name
            QgsProject.instance().addMapLayer(merged_layer)
            # QgsMessageLog.logMessage(f"Layer added to project with name '{layer_name}': {layer_path}", "EnelAssist", level=Qgis.Info)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error adding layer to project: {e}", "EnelAssist", level=Qgis.Critical)


    # Geometry Calculation for X, Y, Z, and M coords
    def calculate_geometry(self, layer, x=None, y=None, z=None, m=None, start_x=None, start_y=None, end_x=None, end_y=None):
        if layer is None:
            QgsMessageLog.logMessage(f"Layer not found - calc geometry: {layer}", "EnelAssist", level=Qgis.Warning)
            return False
            
        try:
            # Collect existing fields in the layer
            existing_fields = [field.name() for field in layer.fields()]

            # Determine which fields need to be added based on provided parameters
            fields_to_add = [
                (name, QgsField(name, QVariant.Double))
                for name in [x, y, z, m, start_x, start_y, end_x, end_y]
                if name and name not in existing_fields
            ]

            # Add fields if needed
            if fields_to_add:
                layer.startEditing()
                layer.dataProvider().addAttributes([field for _, field in fields_to_add])
                layer.updateFields()

            # Ensure the layer is editable before making changes
            if not layer.isEditable():
                layer.startEditing()

            # Prepare expressions
            expressions = {
                'x': QgsExpression('round(x($geometry), 6)') if x else None,
                'y': QgsExpression('round(y($geometry), 6)') if y else None,
                'z': QgsExpression('round(z($geometry), 6)') if z else None,
                'm': QgsExpression("round(coalesce(m($geometry), 1))") if m else None,
                'start_x': QgsExpression('round(x(start_point($geometry)), 6)') if start_x else None,
                'start_y': QgsExpression('round(y(start_point($geometry)), 6)') if start_y else None,
                'end_x': QgsExpression('round(x(end_point($geometry)), 6)') if end_x else None,
                'end_y': QgsExpression('round(y(end_point($geometry)), 6)') if end_y else None
            }

            # Set up the context for expressions
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))

            # Iterate over features and calculate values
            for feature in layer.getFeatures():
                context.setFeature(feature)
                updated_values = {}

                # Evaluate expressions and collect values to update
                for key, expr in expressions.items():
                    if expr:
                        value = expr.evaluate(context)
                        if expr.hasEvalError():
                            error_message = expr.evalErrorString()
                            QgsMessageLog.logMessage(f"Error evaluating '{key}' for feature ID {feature.id()}: {error_message}", "GeometryCalc", level=Qgis.Warning)
                        else:
                            field_name = locals()[key]
                            updated_values[field_name] = value
                            # QgsMessageLog.logMessage(f"Calculated value for '{field_name}': {value} for feature ID {feature.id()}", "GeometryCalc", level=Qgis.Info)

                # Update feature attributes in bulk
                if updated_values:
                    layer.dataProvider().changeAttributeValues({
                        feature.id(): {
                            layer.fields().indexFromName(field): value
                            for field, value in updated_values.items()
                        }
                    })

            # Commit the changes to the layer
            layer.commitChanges()
            # QgsMessageLog.logMessage("Geometry calculation and updates completed successfully.", "GeometryCalc", level=Qgis.Info)
            return True

        except Exception as e:
            QgsMessageLog.logMessage(f"Error in calculate_geometry: {str(e)}", "GeometryCalc", level=Qgis.Critical)
            layer.rollBack()
            return False



    # Add 'lungime' and 'id' fields
    def add_length_and_id(self, layer, length_field, id_field):
        if layer is None:
            QgsMessageLog.logMessage(f"Layer not found - add length and id: {layer}", "EnelAssist", level=Qgis.Warning)
            return False
        
        # QgsMessageLog.logMessage(f"Entered add_length_and_id with layer: {layer.name()} and fields: {length_field}, {id_field}", "EnelAssist", level=Qgis.Info)
        try:
            # QgsMessageLog.logMessage(f"Adding length and ID fields for layer: {layer.name()}", "EnelAssist", level=Qgis.Info)

            # Check if the fields already exist
            existing_fields = [field.name() for field in layer.fields()]
            if all(field in existing_fields for field in [length_field, id_field]):
                QgsMessageLog.logMessage(f"Fields already exist. Skipping adding length and ID fields for layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
                return True

            layer.startEditing()
            layer.dataProvider().addAttributes([QgsField(length_field, QVariant.Double), QgsField(id_field, QVariant.Int)])
            layer.updateFields()

            expression = QgsExpression('length($geometry)')
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))

            for feature in layer.getFeatures():
                context.setFeature(feature)
                length_value = expression.evaluate(context)
                fid_value = feature.id()

                layer.changeAttributeValue(feature.id(), layer.fields().indexOf(length_field), length_value)
                layer.changeAttributeValue(feature.id(), layer.fields().indexOf(id_field), fid_value)

            layer.commitChanges()
            return True
        
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_length_and_id: {e}", "EnelAssist", level=Qgis.Critical)
            return False

    # Modify 'NOD_NRSTR'
    def modify_nod_nrstr(self, layer):
        if layer is None:
            QgsMessageLog.logMessage(f"Layer not found - modify nod nrstr: {layer}", "EnelAssist", level=Qgis.Warning)
            return False
        
        # QgsMessageLog.logMessage(f"Entered modify_nod_nrstr with layer: {layer.name()}, {layer}", "EnelAssist", level=Qgis.Info)
        try:
            # QgsMessageLog.logMessage(f"Modifying layer: {layer.name()}", "EnelAssist", level=Qgis.Info)

            layer.startEditing()

            # Step 1: Remove 'GlobalId' if it exists
            if 'GlobalId' in [field.name() for field in layer.fields()]:
                layer.dataProvider().deleteAttributes([layer.fields().indexOf('GlobalId')])
                layer.updateFields()
                # QgsMessageLog.logMessage(f"Removed 'GlobalId' from layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
            
            # Step 2: Add 'id' field if it doesn't exist
            if 'id' not in [field.name() for field in layer.fields()]:
                layer.dataProvider().addAttributes([QgsField('id', QVariant.Double)])
                layer.updateFields()
                # QgsMessageLog.logMessage(f"Added 'id' field to layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
            
            # Step 3: Populate 'id' field with 'FID' values
            for feature in layer.getFeatures():
                feature['id'] = feature.id()  # Using feature.id() to get FID
                layer.updateFeature(feature)
            
            layer.commitChanges()
            # QgsMessageLog.logMessage(f"Successfully modified layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
            
            return True
            
        except Exception as e:
            layer.rollBack()  # Rollback any changes if there's an error
            QgsMessageLog.logMessage(f"Error in modify_nod_nrstr: {e}", "EnelAssist", level=Qgis.Critical)
            return False

    # Merge Vector Layers
    def merge_layers(self, layer_list, folder, base_dir, layers):
        QgsMessageLog.logMessage(f"Entered merge_layers with layer_list: {layer_list} and folder: {folder}", "EnelAssist", level=Qgis.Info)
        if not layer_list:
            QgsMessageLog.logMessage(f"No valid layers found for merging in layer_list: {layer_list}", "EnelAssist", level=Qgis.Warning)
            return False
        
        # QgsMessageLog.logMessage(f"Entered merge_layers with layer_list: {layer_list} and folder: {folder}", "EnelAssist", level=Qgis.Info)
        try:
            # Populating input_layers
            # QgsMessageLog.logMessage(f"Input layers are: {layer_list}", "EnelAssist", level=Qgis.Info)
            if not layer_list:
                QgsMessageLog.logMessage(f"No valid layers found for merging in layer_list: {layer_list}", "EnelAssist", level=Qgis.Warning)
                return False
            
            # QgsMessageLog.logMessage(f"Merging layers: {layer_list}", "EnelAssist", level=Qgis.Info)
            valid_layers = [layer for layer in layer_list if layer is not None]
            output = os.path.join(base_dir, f"{folder}.shp")
            if output and not QgsVectorLayer(output, '', 'ogr').isValid():
                processing.run("qgis:mergevectorlayers", {
                    'LAYERS': valid_layers, 
                    'CRS': 'EPSG:3844', 
                    'OUTPUT': output
                })
                self.add_layer_to_project(output)
                layers.update(self.get_layers())
            else:
                QgsMessageLog.logMessage(f"Merge output already exists and is valid: {output}", "EnelAssist", level=Qgis.Info)
                
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in merge_layers: {e}", "EnelAssist", level=Qgis.Critical)
            return False


    # Join Attributes by Location
    def join_attributes_by_location(self, input_file, join_file, output_name, method, base_dir, layers):
        if not input_file or not join_file:
            QgsMessageLog.logMessage(f"No valid layers found for joining in input_file: {input_file} and join_file: {join_file} for the layers - {layers}", "EnelAssist", level=Qgis.Warning)
            return False
        
        QgsMessageLog.logMessage(f"Entered join_attributes_by_location with input_file: {input_file}, join_file: {join_file}, output_name: {output_name}, method: {method}", "EnelAssist", level=Qgis.Info)
        try:
            # Check if the layer already exists
            existing_layer = QgsProject.instance().mapLayersByName(output_name)
            if existing_layer:
                QgsMessageLog.logMessage(f"Layer '{output_name}' already exists. Skipping join.", "EnelAssist", level=Qgis.Info)
                return True

            # QgsMessageLog.logMessage(f"Joining attributes by location: {input_file} with {join_file}", "EnelAssist", level=Qgis.Info)
            output = os.path.join(base_dir, f"{output_name}.shp")
            if output:
                processing.run("qgis:joinattributesbylocation", {
                    'INPUT': input_file,
                    'JOIN': join_file,
                    'PREDICATE': [0],  # intersects
                    'JOIN_FIELDS': [''],
                    'METHOD': 0 if method == 'One-to-Many' else 1,  # One-to-Many or One-to-One
                    'DISCARD_NONMATCHING': False,
                    'OUTPUT': output
                })
                self.add_layer_to_project(output)
                layers.update(self.get_layers())
                
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in join_attributes_by_location: {e}", "EnelAssist", level=Qgis.Critical)
            return False

    # Add 'NR.CRT' column and calculate values (start with one, increment by one)
    def add_nr_crt_column(self, layer):
        if not layer:
            QgsMessageLog.logMessage(f"No valid layers found for adding NR.CRT column in layer_name: {layer}", "EnelAssist", level=Qgis.Warning)
            return False
        
        try:
            layer = QgsProject.instance().mapLayersByName(layer)[0]
            if layer.fields().indexOf('NR.CRT') != -1:
                QgsMessageLog.logMessage(f"NR.CRT column already exists for layer: {layer}", "EnelAssist", level=Qgis.Info)
                return True
            
            layer.startEditing()
            # Add 'NR.CRT' column as integer
            layer.dataProvider().addAttributes([QgsField('NR.CRT', QVariant.Int)])
            layer.updateFields()
            
            # Expression to add the incremental values
            nr_crt_expr = QgsExpression(' $id + 1 ')
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
            
            for feature in layer.getFeatures():
                context.setFeature(feature)
                nr_crt_value = nr_crt_expr.evaluate(context)
                layer.changeAttributeValue(feature.id(), layer.fields().indexOf('NR.CRT'), nr_crt_value)
                
            layer.commitChanges()
            return True
        
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_nr_crt_column: {e}", "EnelAssist", level=Qgis.Critical)
            return False


    # Add 'SEI' column and calculate values
    def add_sei_column(self, layer):
        if not layer:
            QgsMessageLog.logMessage(f"No valid layers found for adding SEI column in layer_name: {layer}", "EnelAssist", level=Qgis.Warning)
            return False
        
        try:
            # QgsMessageLog.logMessage(f"Adding SEI column for layer: {layer_name}", "EnelAssist", level=Qgis.Info)
            layer = QgsProject.instance().mapLayersByName(layer)[0]
            if layer.fields().indexOf('SEI') != -1:
                QgsMessageLog.logMessage(f"SEI column already exists for layer: {layer}", "EnelAssist", level=Qgis.Info)
                return True
            
            layer.startEditing()
            # Add 'SEI' column as text
            layer.dataProvider().addAttributes([QgsField('SEI', QVariant.String)])
            layer.updateFields()

            # Expression to add the conditional values
            sei_expr = QgsExpression('CASE WHEN "nr_nod" THEN 3 ELSE 1 END')
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))

            for feature in layer.getFeatures():
                context.setFeature(feature)
                sei_value = sei_expr.evaluate(context)
                layer.changeAttributeValue(feature.id(), layer.fields().indexOf('SEI'), sei_value)

            layer.commitChanges()
            
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_sei_column: {e}", "EnelAssist", level=Qgis.Critical)
            return False
        
    def add_count_id_column(self, layer_name):
        if not layer_name:
            QgsMessageLog.logMessage(f"No valid layers found for adding Count_ID column in layer_name: {layer_name}", "EnelAssist", level=Qgis.Warning)
            return False

        try:
            layer = QgsProject.instance().mapLayersByName(layer_name)[0]
            if not layer:
                QgsMessageLog.logMessage(f"Layer {layer_name} not found!", "EnelAssist", level=Qgis.Critical)
                return False

            if layer.fields().indexOf('Count_ID') != -1:
                QgsMessageLog.logMessage(f"Count_ID column already exists for layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
                return True

            # Add the Count_ID field
            layer.startEditing()
            layer.dataProvider().addAttributes([QgsField('Count_ID', QVariant.Int)])
            layer.updateFields()

            # Create a dictionary to count occurrences of each TARGET_FID
            target_fid_counts = {}

            # Populate the dictionary with counts
            for feature in layer.getFeatures():
                target_fid = feature['TARGET_FID']
                if target_fid not in target_fid_counts:
                    target_fid_counts[target_fid] = 0
                target_fid_counts[target_fid] += 1

            # Update the Count_ID field with the count for each TARGET_FID
            for feature in layer.getFeatures():
                target_fid = feature['TARGET_FID']
                count = target_fid_counts.get(target_fid, 0)
                layer.changeAttributeValue(feature.id(), layer.fields().indexOf('Count_ID'), count)

            layer.commitChanges()
            QgsMessageLog.logMessage(f"Successfully added Count_ID column for layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
            return True

        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_count_id_column: {e}", "EnelAssist", level=Qgis.Critical)
            return False


    # Add 'Join_Count' column
    def add_join_count_column(self, layer):
        if not layer:
            QgsMessageLog.logMessage(f"No valid layers found for adding Join_Count column in layer_name: {layer}", "EnelAssist", level=Qgis.Warning)
            return False
            
        try:
            # QgsMessageLog.logMessage(f"Adding Join_Count column for layer: {layer_name}", "EnelAssist", level=Qgis.Info)
            layer = QgsProject.instance().mapLayersByName(layer)[0]
            if layer.fields().indexOf('Join_Count') != -1:
                QgsMessageLog.logMessage(f"Join_Count column already exists for layer: {layer}", "EnelAssist", level=Qgis.Info)
                return True
            
            layer.startEditing()
            layer.dataProvider().addAttributes([QgsField('Join_Count', QVariant.Int)])
            layer.updateFields()

            for feature in layer.getFeatures():
                layer.changeAttributeValue(feature.id(), layer.fields().indexOf('Join_Count'), 1)

            layer.commitChanges()
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_join_count_column: {e} for layer: {layer}", "EnelAssist", level=Qgis.Critical)
            return False
        
    def add_target_fid_column(self, layer):
        if layer is None:
            QgsMessageLog.logMessage(f"Layer not found - add target fid: {layer}", "EnelAssist", level=Qgis.Warning)
            return False
        
        try:
            # QgsMessageLog.logMessage(f"Adding target_fid column for layer: {layer_name}", "EnelAssist", level=Qgis.Info)
            layer = QgsProject.instance().mapLayersByName(layer)[0]
            if layer.fields().indexOf('TARGET_FID') != -1:
                QgsMessageLog.logMessage(f"TARGET_FID column already exists for layer: {layer}", "EnelAssist", level=Qgis.Info)
                return True
            
            layer.startEditing()
            layer.dataProvider().addAttributes([QgsField('TARGET_FID', QVariant.Int)])
            layer.updateFields()

            for feature in layer.getFeatures():
                layer.changeAttributeValue(feature.id(), layer.fields().indexOf('TARGET_FID'), feature.id())

            layer.commitChanges()
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_target_fid_column: {e}", "EnelAssist", level=Qgis.Critical)
            return False

    def sort_layer_by_field(self, layer, field):
        if layer is None:
            QgsMessageLog.logMessage(f"Layer not found - sort by field: {layer}", "EnelAssist", level=Qgis.Warning)
            return False

        # Check if the field exists in the layer
        if field not in [f.name() for f in layer.fields()]:
            QgsMessageLog.logMessage(f"Field '{field}' not found in layer fields.", "EnelAssist", level=Qgis.Warning)
            return False

        try:
            # Fetch features sorted by the specified field
            sorted_features = sorted(layer.getFeatures(), key=lambda f: f[field])

            # Start editing the layer
            layer.startEditing()
            
            # Delete all current features
            layer.deleteFeatures([feat.id() for feat in layer.getFeatures()])

            # Add sorted features back to the layer
            layer.addFeatures(sorted_features)
            layer.commitChanges()

            QgsMessageLog.logMessage(f"Layer sorted by field '{field}' successfully.", "EnelAssist", level=Qgis.Info)
            return True
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in sort_layer_by_field: {e}", "EnelAssist", level=Qgis.Critical)
            return False