"""
- LAYERS NEEDED - ['InceputLinie', 'Cutii', 'Stalpi', 'BMPnou', 'ReteaJT', 'NOD_NRSTR', 'AUXILIAR', 'pct_vrtx', "Numar_Postal"]


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

STEP 2. ReteaJT - Add 'lungime', 'id' columns - double
    > calculate length in "lungime" - length($geometry)
    > id - field calculator - FID - OK
    > example:
        >   layer.dataProvider().addAttributes([QgsField('lungime', QVariant.Double)])
            layer.updateFields()
            # calc length with length($geometry)

STEP 3. NOD_NRSTR - Add 'id' - double, Delete GlobalId (raman doar ID si FID)
    > id - field calculator - FID - OK
    
STEP 4 - Merge Vector Layers - InceputLinie / Cutii / Stalpi / BMPnou > folder - NODURI
STEP 5 - Merge Vector Layers - ReteaJT > folder - RAMURI

    > Use qgis:mergevectorlayers from the QGIS Processing Toolbox.
    > example:
        >   processing.run("qgis:mergevectorlayers", {
                'LAYERS': [layer1, layer2, layer3],  # list of layers to merge
                'CRS': 'EPSG:3844',  # Optional CRS
                'OUTPUT': '/path/to/output/layer.gpkg'
            })

STEP 6. Join Attributes by Location - RAMURI > NODURI - ONE TO MANY > RAMURI_NODURI
STEP 7. Join Attributes by Location - NOD_NRSTR > BMPnou - ONE TO ONE > LEG_NODURI
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
            
STEP 9. Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou, AUXILIAR, pct_vrtx > folder - NODURI_AUX_VRTX

STEP 10. Join Attributes by Location - ramuri > noduri_aux_vrtx - ONE TO MANY > RAMURI_AUX_VRTX

STEP 11. RAMURI_AUX_VRTX - Add 'SEI' column - text
    > CASE 
        WHEN "nr_nod" THEN 3
        ELSE 1
      END

STEP 12. for each Join Attributes by Location - add Join_Count column with all values '1'

"""

import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem, QApplication
from qgis.core import (QgsExpression, QgsExpressionContext, QgsExpressionContextUtils, 
                       QgsField, QgsProject, QgsMessageLog, Qgis, QgsVectorLayer)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QVariant, Qt
import processing
import logging

from .validate_dialog import ShpProcessor

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='preprocess_debug.log')

class PreProcessDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preprocess Data")
        self.layout = QVBoxLayout()
        
        # Label
        self.progress_text = QLabel("Steps to do:")
        self.layout.addWidget(self.progress_text)

        # Create a list to display the steps visually
        self.steps_list = QListWidget(self)
        
        self.steps_list.setStyleSheet("""
            QListWidget::item {
                color: black;  # Keep text color normal (change to white for dark mode)
                background-color: #f0f0f0;  # Default background for light mode
            }
            QListWidget::item:selected {
                background-color: #d0e0f0;  # Slightly different background for selected items
            }
        """)  # This makes sure that the list looks normal even when disabled.

        # Define the steps
        self.steps = [
            "1. Calculeaza X, Y la toate geometriile",
            "2. Calculeaza START_X, START_Y, END_X, END_Y pentru ReteaJT",
            "3. Adauga coloane 'lungime' si 'id' pentru ReteaJT",
            "4. Adauga coloana 'id' pentru NOD_NRSTR",
            "5. Uneste straturile pentru NODURI",
            "6. Uneste straturile pentru RAMURI",
            "7. Join Attributes by Location - RAMURI_NODURI",
            "8. Join Attributes by Location - LEG_NODURI",
            "9. Join Attributes by Location - LEG_NRSTR",
            "10. Uneste straturile pentru NODURI_AUX_VRTX",
            "11. Join Attributes by Location - RAMURI_AUX_VRTX",
            "12. Adauga coloana 'SEI' pentru RAMURI_AUX_VRTX",
            "13. Adauga coloana 'Join_Count' pentru toate join-urile",
            "14. Salveaza datele"
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

        self.run_button = QPushButton("Run", self)
        self.run_button.clicked.connect(self.__exec__)
        self.layout.addWidget(self.run_button)

        self.setLayout(self.layout)

    def __exec__(self):
        QgsMessageLog.logMessage("Starting data preprocessing...", "EnelAssist", level=Qgis.Info)
        try:
            # Automated layer retrieval
            self.layers = self.get_layers()
            if not self.layers:
                QgsMessageLog.logMessage("No layers found matching the required names.", "EnelAssist", level=Qgis.Critical)
                logging.error("No layers found matching the required names.")
                return
            
            # Update progress bar
            total_steps = 11  + (len(self.layers)*2) - 2 # Total number of processing steps
            self.progress_bar.setMaximum(total_steps)
            step = 0
            self.base_dir = QFileDialog.getExistingDirectory(None, "Select Folder")
            os.makedirs(self.base_dir, exist_ok=True)  # Ensure directory exists

            # Execute all processing steps
            QgsMessageLog.logMessage("-------- START OF DATA PREPROCESSING --------", "EnelAssist", level=Qgis.Info)
            logging.info("-------- START OF DATA PREPROCESSING --------")

            # 1. Calculate X. Y for layers
            try:
                for layer in self.layers.values():
                    QgsMessageLog.logMessage(f"Calculating geometry for layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
                    if layer.name() in ["ReteaJT", "NOD_NRSTR"]:
                        QgsMessageLog.logMessage(f"Skipping layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
                    elif layer.name() in ["pct_vrtx"]:
                        self.calculate_geometry(layer, "POINT_X", "POINT_Y")
                        QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
                        step += 1
                        self.progress_bar.setValue(step)
                    else:
                        self.calculate_geometry(layer, "POINT_X", "POINT_Y", "POINT_Z", "POINT_M")
                        QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
                        step += 1
                        self.progress_bar.setValue(step)
                
                self.update_step(0)  # Mark step 1 as done
            except Exception as e:
                QgsMessageLog.logMessage(f"Error calculating geometry (X, Y, M, Z) for layers: {e}", "EnelAssist", level=Qgis.Critical)
                
                
            # 2. Calculate START_X, START_Y, END_X, END_Y for ReteaJT
            try:
                self.calculate_geometry(self.layers["ReteaJT"], None, None, None, None, 'START_X', 'START_Y', 'END_X', 'END_Y')
                QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
                step += 1
                self.progress_bar.setValue(step)
                self.update_step(1)  # Mark step 2 as done
            except Exception as e:
                QgsMessageLog.logMessage(f"Error calculating geometry (start, end) for layers: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error calculating geometry for layers: {e}")
                return

            # 3. Add 'lungime' and 'id' columns to ReteaJT and calculate geometry length
            try:
                self.add_length_and_id(self.layers['ReteaJT'], 'lungime_', 'id_')
                self.update_step(2)  # Mark step 3 as done
                QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
                step += 1
                self.progress_bar.setValue(step)
            except KeyError:
                QgsMessageLog.logMessage(f"Layer 'ReteaJT' not found. The layers are {self.layers.keys()}", "EnelAssist", level=Qgis.Critical)
                logging.error("Layer 'ReteaJT' not found.")
                return
            except Exception as e:
                QgsMessageLog.logMessage(f"Error adding length and id columns: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error adding length and id columns: {e}")
                return

            # 4. Manage NOD_NRSTR columns
            try:
                self.modify_nod_nrstr(self.layers['NOD_NRSTR'])
                self.update_step(3)  # Mark step 4 as done
                QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
                step += 1
                self.progress_bar.setValue(step)
            except KeyError:
                QgsMessageLog.logMessage("Layer 'NOD_NRSTR' not found.", "EnelAssist", level=Qgis.Critical)
                logging.error("Layer 'NOD_NRSTR' not found.")
                return
            except Exception as e:
                QgsMessageLog.logMessage(f"Error modifying 'NOD_NRSTR' columns: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error modifying 'NOD_NRSTR' columns: {e}")
                return

            # 5. Merge layers for NODURI
            try:
                self.merge_layers([self.layers['InceputLinie'], self.layers['Cutii'], self.layers['Stalpi'], self.layers['BMPnou']], 'NODURI')
                self.update_step(4)  # Mark step 5 as done
                step += 1
                self.progress_bar.setValue(step)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error merging layers for NODURI: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error merging layers for NODURI: {e}")
                return

            # 6. Merge layers for RAMURI
            try:
                self.merge_layers([self.layers['ReteaJT']], 'RAMURI')
                self.update_step(5)  # Mark step 6 as done
                step += 1
                self.progress_bar.setValue(step)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error merging layers for RAMURI: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error merging layers for RAMURI: {e}")
                return

            # 7. Join Attributes by Location - RAMURI_NODURI
            try:
                self.join_attributes_by_location(self.layers['RAMURI'], self.layers['NODURI'], 'RAMURI_NODURI', 'One-to-Many')
                self.update_step(6)  # Mark step 7 as done
                step += 1
                self.progress_bar.setValue(step)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error joining attributes by location for RAMURI_NODURI: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error joining attributes by location for RAMURI_NODURI: {e}")
                return

            # 8. Join Attributes by Location - LEG_NODURI
            try:
                self.join_attributes_by_location(self.layers['NOD_NRSTR'], self.layers['BMPnou'], 'LEG_NODURI', 'One-to-One')
                self.update_step(7)  # Mark step 8 as done
                step += 1
                self.progress_bar.setValue(step)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error joining attributes by location for LEG_NODURI: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error joining attributes by location for LEG_NODURI: {e}")
                return
            
            # 9. Join Attributes by Location - LEG_NRSTR
            try:
                self.join_attributes_by_location(self.layers['NOD_NRSTR'], self.layers['Numar_Postal'], 'LEG_NRSTR', 'One-to-One')
                self.update_step(8)  # Mark step 9 as done
                step += 1
                self.progress_bar.setValue(step)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error joining attributes by location for LEG_NRSTR: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error joining attributes by location for LEG_NRSTR: {e}")
                return

            # 10. Merge layers for NODURI_AUX_VRTX
            try:
                self.merge_layers([self.layers['InceputLinie'], self.layers['Cutii'], self.layers['Stalpi'], self.layers['BMPnou'], self.layers['AUXILIAR'], self.layers['pct_vrtx']], 'NODURI_AUX_VRTX')
                self.update_step(9)  # Mark step 10 as done
                step += 1
                self.progress_bar.setValue(step)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error merging layers for NODURI_AUX_VRTX: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error merging layers for NODURI_AUX_VRTX: {e}")
                return

            # 11. Join Attributes by Location - RAMURI_AUX_VRTX
            try:
                self.join_attributes_by_location(self.layers['RAMURI'], self.layers['NODURI_AUX_VRTX'], 'RAMURI_AUX_VRTX', 'One-to-Many')
                self.update_step(10)  # Mark step 11 as done
                step += 1
                self.progress_bar.setValue(step)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error joining attributes by location for RAMURI_AUX_VRTX: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error joining attributes by location for RAMURI_AUX_VRTX: {e}")
                return

            # 12. Add 'SEI' column with conditional values
            try:
                self.add_sei_column(self.layers['RAMURI_AUX_VRTX'].name())
                self.update_step(11)  # Mark step 12 as done
                step += 1
                self.progress_bar.setValue(step)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error adding 'SEI' column: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error adding 'SEI' column: {e}")
                return

            # 13. Add 'Join_Count' column for all joins with value '1'
            try:
                self.add_join_count_column(self.layers['RAMURI_NODURI'].name())
                self.add_join_count_column(self.layers['LEG_NODURI'].name())
                self.add_join_count_column(self.layers['LEG_NRSTR'].name())
                self.update_step(12)  # Mark step 13 as done
                step += 1
                QgsMessageLog.logMessage(f"Steps completed: {step}", "EnelAssist", level=Qgis.Info)
                self.progress_bar.setValue(step)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error adding 'Join_Count' column: {e}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Error adding 'Join_Count' column: {e}")
                return

            # Done
            self.progress_bar.setValue(total_steps)
            QgsMessageLog.logMessage("Data preprocessing completed successfully.", "EnelAssist", level=Qgis.Info)
            logging.info("Data preprocessing completed successfully.")
        except Exception as e:
            QgsMessageLog.logMessage(f"An error occurred during processing: {e}", "EnelAssist", level=Qgis.Critical)
            logging.error(f"An error occurred during processing: {e}")


    def update_step(self, index):
        """Marks a step as done by updating the list item."""
        try:
            item = self.steps_list.item(index)
            QgsMessageLog.logMessage(f"Updating step {index}: {item.text()}", "EnelAssist", level=Qgis.Info)
            QgsMessageLog.logMessage(f"Item flags: {item.flags()}", "EnelAssist", level=Qgis.Info)
            QgsMessageLog.logMessage(f"Steps list - {self.steps_list}", "EnelAssist", level=Qgis.Info)
            item.setText("✓ " + item.text())  # Add a checkmark
            item.setForeground(QColor("green"))  # Change text color to green to indicate completion
            item.setFont(QFont("Arial", 10, QFont.Bold))  # Make the completed step bold
            QApplication.processEvents()  # Force UI update after each step
        except Exception as e:
            QgsMessageLog.logMessage(f"Error updating step {index}: {e}", "EnelAssist", level=Qgis.Critical)
            logging.error(f"Error updating step {index}: {e}")
            pass

    # Retrieve layers by name from the QGIS project
    def get_layers(self):
        '''
        Get layers by name from the QGIS project and add them to self.layers
        '''
        layers = {}
        layer_names = ['InceputLinie', 'Cutii', 'Stalpi', 'BMPnou', 'ReteaJT', 'NOD_NRSTR', 'AUXILIAR', 'pct_vrtx', "Numar_Postal", "NODURI", "RAMURI", "RAMURI_NODURI", "LEG_NODURI", "NODURI_AUX_VRTX", "RAMURI_AUX_VRTX", "LEG_NRSTR"]

        # Get all layers in the current QGIS project (keep the layer objects)
        qgis_layers = QgsProject.instance().mapLayers().values()
        QgsMessageLog.logMessage(f"----------- QGIS LAYERS: {qgis_layers}", "EnelAssist", level=Qgis.Info)

        # Log all available layers in the project for debugging
        available_layer_names = [layer.name() for layer in qgis_layers]
        QgsMessageLog.logMessage(f"Available layers in QGIS: {available_layer_names}", "EnelAssist", level=Qgis.Info)

        # Iterate through the actual layer objects
        for layer in qgis_layers:
            # If the layer name matches one in the predefined list, add it to the dictionary
            if layer.name() in layer_names:
                layers[layer.name()] = layer

        QgsMessageLog.logMessage(f"Layers found with IDs: {layers}", "EnelAssist", level=Qgis.Info)

        return layers


    def add_layer_to_project(self, layer_path):
        try:
            # Get the name of the layer without the file extension and the full path
            layer_name = os.path.splitext(os.path.basename(layer_path))[0]
            
            # Load the merged layer from the output path
            merged_layer = QgsVectorLayer(layer_path, layer_name, 'ogr')
            
            # Check if the layer is valid
            if not merged_layer.isValid():
                QgsMessageLog.logMessage(f"Invalid layer: {layer_path}", "EnelAssist", level=Qgis.Critical)
                logging.error(f"Invalid layer: {layer_path}")
                return
            
            # Add the layer to the project with the proper name
            QgsProject.instance().addMapLayer(merged_layer)
            QgsMessageLog.logMessage(f"Layer added to project with name '{layer_name}': {layer_path}", "EnelAssist", level=Qgis.Info)
            logging.info(f"Layer added to project with name '{layer_name}': {layer_path}")
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Error adding layer to project: {e}", "EnelAssist", level=Qgis.Critical)
            logging.error(f"Error adding layer to project: {e}")


    # Geometry Calculation for X, Y, Z, and M coords
    def calculate_geometry(self, layer, x=None, y=None, z=None, m=None, start_x=None, start_y=None, end_x=None, end_y=None):
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
                'x': QgsExpression('x($geometry)') if x else None,
                'y': QgsExpression('y($geometry)') if y else None,
                'z': QgsExpression('z($geometry)') if z else None,
                'm': QgsExpression("round(coalesce(m($geometry), 1))") if m else None,
                'start_x': QgsExpression('x(start_point($geometry))') if start_x else None,
                'start_y': QgsExpression('y(start_point($geometry))') if start_y else None,
                'end_x': QgsExpression('x(end_point($geometry))') if end_x else None,
                'end_y': QgsExpression('y(end_point($geometry))') if end_y else None
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
            QgsMessageLog.logMessage("Geometry calculation and updates completed successfully.", "GeometryCalc", level=Qgis.Info)

        except Exception as e:
            QgsMessageLog.logMessage(f"Error in calculate_geometry: {str(e)}", "GeometryCalc", level=Qgis.Critical)
            layer.rollBack()



    # Add 'lungime' and 'id' fields
    def add_length_and_id(self, layer, length_field, id_field):
        QgsMessageLog.logMessage(f"Entered add_length_and_id with layer: {layer.name()} and fields: {length_field}, {id_field}", "EnelAssist", level=Qgis.Info)
        try:
            QgsMessageLog.logMessage(f"Adding length and ID fields for layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
            logging.info(f"Adding length and ID fields for layer: {layer.name()}")

            # Check if the fields already exist
            existing_fields = [field.name() for field in layer.fields()]
            if all(field in existing_fields for field in [length_field, id_field]):
                QgsMessageLog.logMessage(f"Fields already exist. Skipping adding length and ID fields for layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
                logging.info(f"Fields already exist. Skipping adding length and ID fields for layer: {layer.name()}")
                return

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
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_length_and_id: {e}", "EnelAssist", level=Qgis.Critical)
            logging.error(f"Error in add_length_and_id: {e}")

    # Modify 'NOD_NRSTR'
    def modify_nod_nrstr(self, layer):
        QgsMessageLog.logMessage(f"Entered modify_nod_nrstr with layer: {layer.name()}, {layer}", "EnelAssist", level=Qgis.Info)
        try:
            QgsMessageLog.logMessage(f"Modifying layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
            logging.info(f"Modifying layer: {layer.name()}")

            layer.startEditing()

            # Step 1: Remove 'GlobalId' if it exists
            if 'GlobalId' in [field.name() for field in layer.fields()]:
                layer.dataProvider().deleteAttributes([layer.fields().indexOf('GlobalId')])
                layer.updateFields()
                QgsMessageLog.logMessage(f"Removed 'GlobalId' from layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
                logging.info(f"Removed 'GlobalId' from layer: {layer.name()}")
            
            # Step 2: Add 'id' field if it doesn't exist
            if 'id' not in [field.name() for field in layer.fields()]:
                layer.dataProvider().addAttributes([QgsField('id', QVariant.Double)])
                layer.updateFields()
                QgsMessageLog.logMessage(f"Added 'id' field to layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
                logging.info(f"Added 'id' field to layer: {layer.name()}")
            
            # Step 3: Populate 'id' field with 'FID' values
            for feature in layer.getFeatures():
                feature['id'] = feature.id()  # Using feature.id() to get FID
                layer.updateFeature(feature)
            
            layer.commitChanges()
            QgsMessageLog.logMessage(f"Successfully modified layer: {layer.name()}", "EnelAssist", level=Qgis.Info)
            logging.info(f"Successfully modified layer: {layer.name()}")
            
        except Exception as e:
            layer.rollBack()  # Rollback any changes if there's an error
            QgsMessageLog.logMessage(f"Error in modify_nod_nrstr: {e}", "EnelAssist", level=Qgis.Critical)
            logging.error(f"Error in modify_nod_nrstr: {e}")

    # Merge Vector Layers
    def merge_layers(self, layer_list, folder):
        QgsMessageLog.logMessage(f"Entered merge_layers with layer_list: {layer_list} and folder: {folder}", "EnelAssist", level=Qgis.Info)
        try:
            # Populating input_layers
            QgsMessageLog.logMessage(f"Input layers are: {layer_list}", "EnelAssist", level=Qgis.Info)
            if not layer_list:
                QgsMessageLog.logMessage(f"No valid layers found for merging in layer_list: {layer_list}", "EnelAssist", level=Qgis.Warning)
                logging.warning(f"No valid layers found for merging in layer_list: {layer_list}")
                return
            
            QgsMessageLog.logMessage(f"Merging layers: {layer_list}", "EnelAssist", level=Qgis.Info)
            logging.info(f"Merging layers: {layer_list}")
            output = os.path.join(self.base_dir, f"{folder}.gpkg")
            if output and not QgsVectorLayer(output, '', 'ogr').isValid():
                processing.run("qgis:mergevectorlayers", {
                    'LAYERS': layer_list, 
                    'CRS': 'EPSG:3844', 
                    'OUTPUT': output
                })
                self.add_layer_to_project(output)
                self.layers = self.get_layers()
            else:
                QgsMessageLog.logMessage(f"Merge output already exists and is valid: {output}", "EnelAssist", level=Qgis.Info)
                logging.info(f"Merge output already exists and is valid: {output}")
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in merge_layers: {e}", "EnelAssist", level=Qgis.Critical)
            logging.error(f"Error in merge_layers: {e}")


    # Join Attributes by Location
    def join_attributes_by_location(self, input_file, join_file, output_name, method):
        QgsMessageLog.logMessage(f"Entered join_attributes_by_location with input_file: {input_file}, join_file: {join_file}, output_name: {output_name}, method: {method}", "EnelAssist", level=Qgis.Info)
        try:
            # Check if the layer already exists
            existing_layer = QgsProject.instance().mapLayersByName(output_name)
            if existing_layer:
                QgsMessageLog.logMessage(f"Layer '{output_name}' already exists. Skipping join.", "EnelAssist", level=Qgis.Info)
                logging.info(f"Layer '{output_name}' already exists. Skipping join.")
                return

            QgsMessageLog.logMessage(f"Joining attributes by location: {input_file} with {join_file}", "EnelAssist", level=Qgis.Info)
            logging.info(f"Joining attributes by location: {input_file} with {join_file}")
            output = os.path.join(self.base_dir, f"{output_name}.shp")
            if output:
                processing.run("qgis:joinattributesbylocation", {
                    'INPUT': input_file,
                    'JOIN': join_file,
                    'PREDICATE': [0],  # intersects
                    'JOIN_FIELDS': [],
                    'METHOD': 0 if method == 'One-to-Many' else 1,  # One-to-Many or One-to-One
                    'DISCARD_NONMATCHING': False,
                    'OUTPUT': output
                })
                self.add_layer_to_project(output)
                self.layers = self.get_layers()
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in join_attributes_by_location: {e}", "EnelAssist", level=Qgis.Critical)
            logging.error(f"Error in join_attributes_by_location: {e}")


    # Add 'SEI' column and calculate values
    def add_sei_column(self, layer_name):
        try:
            QgsMessageLog.logMessage(f"Adding SEI column for layer: {layer_name}", "EnelAssist", level=Qgis.Info)
            logging.info(f"Adding SEI column for layer: {layer_name}")
            layer = QgsProject.instance().mapLayersByName(layer_name)[0]
            if layer.fields().indexOf('SEI') != -1:
                QgsMessageLog.logMessage(f"SEI column already exists for layer: {layer_name}", "EnelAssist", level=Qgis.Info)
                logging.info(f"SEI column already exists for layer: {layer_name}")
                return
            
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
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_sei_column: {e}", "EnelAssist", level=Qgis.Critical)
            logging.error(f"Error in add_sei_column: {e}")

    # Add 'Join_Count' column
    def add_join_count_column(self, layer_name):
        try:
            QgsMessageLog.logMessage(f"Adding Join_Count column for layer: {layer_name}", "EnelAssist", level=Qgis.Info)
            logging.info(f"Adding Join_Count column for layer: {layer_name}")
            layer = QgsProject.instance().mapLayersByName(layer_name)[0]
            if layer.fields().indexOf('Join_Count') != -1:
                QgsMessageLog.logMessage(f"Join_Count column already exists for layer: {layer_name}", "EnelAssist", level=Qgis.Info)
                logging.info(f"Join_Count column already exists for layer: {layer_name}")
                return
            
            layer.startEditing()
            layer.dataProvider().addAttributes([QgsField('Join_Count', QVariant.Int)])
            layer.updateFields()

            for feature in layer.getFeatures():
                layer.changeAttributeValue(feature.id(), layer.fields().indexOf('Join_Count'), 1)

            layer.commitChanges()
        except Exception as e:
            QgsMessageLog.logMessage(f"Error in add_join_count_column: {e} for layer: {layer_name}", "EnelAssist", level=Qgis.Critical)
            logging.error(f"Error in add_join_count_column: {e}")


