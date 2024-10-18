"""
- Calculate geometry for all shp files - X, Y coord line start and end
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

- ReteaJT - Add 'lungime', 'id' columns - double
    > calculate length in "lungime" - length($geometry)
    > id - field calculator - FID - OK
    > example:
        >   layer.dataProvider().addAttributes([QgsField('lungime', QVariant.Double)])
            layer.updateFields()
            # calc length with length($geometry)

- layer_nod_nrstr - Add 'id' - double, Delete GlobalId (raman doar ID si FID)
    > id - field calculator - FID - OK
    
- Merge Vector Layers - inc_linii / cutii / stalpi / bmpnou > folder - NODURI
- Merge Vector Layers - layer_reteajt > folder - RAMURI
    > Use qgis:mergevectorlayers from the QGIS Processing Toolbox.
    > example:
        >   processing.run("qgis:mergevectorlayers", {
                'LAYERS': [layer1, layer2, layer3],  # list of layers to merge
                'CRS': 'EPSG:3844',  # Optional CRS
                'OUTPUT': '/path/to/output/layer.gpkg'
            })

- Join Attributes by Location - ramuri > noduri - ONE TO MANY > RAMURI_NODURI
- Join Attributes by Location - layer_nod_nrstr > noduri - ONE TO ONE > LEG_NODURI
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

- Merge Vector Layers - inc_linii, cutii, stalpi, bpmnou, auxiliar, pct_vrtx > folder - NODURI_AUX_VRTX

- Join Attributes by Location - ramuri > noduri_aux - ONE TO MANY > RAMURI_AUX_VRTX

- ramuri_aux_vrtx - Add 'SEI' column - text
    > CASE 
        WHEN "Noduri" THEN 3
        ELSE 1
      END

- for each Join Attributes by Location - add Join_Count column with all values '1'
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QPushButton, QFileDialog
from qgis.core import (QgsExpression, QgsExpressionContext, QgsExpressionContextUtils, 
                       QgsField, QgsProject, QgsProcessing, QgsProcessingFeatureSourceDefinition)
from qgis.PyQt.QtCore import QVariant
import processing

class PreProcessDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preprocess Data")
        self.layout = QVBoxLayout()

        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)

        self.run_button = QPushButton("Run", self)
        self.run_button.clicked.connect(self.__exec__)
        self.layout.addWidget(self.run_button)

        self.setLayout(self.layout)

    def __exec__(self):
        # Update progress bar
        total_steps = 12
        self.progress_bar.setMaximum(total_steps)
        step = 0
        
        # Get the active layer (assuming user will select the layer)
        layer = iface.activeLayer()

        # 1. Calculate start and end points for each geometry
        self.calculate_geometry(layer, 'START_X', 'START_Y', 'END_X', 'END_Y')
        step += 1
        self.progress_bar.setValue(step)

        # 2. Add 'lungime' and 'id' columns and calculate geometry length
        self.add_length_and_id(layer, 'lungime', 'id')
        step += 1
        self.progress_bar.setValue(step)

        # 3. Manage layer_nod_nrstr columns
        self.modify_nod_nrstr(layer)
        step += 1
        self.progress_bar.setValue(step)

        # 4. Merge layers for NODURI
        self.merge_layers(['inc_linii', 'cutii', 'stalpi', 'bmpnou'], 'NODURI')
        step += 1
        self.progress_bar.setValue(step)

        # 5. Merge layers for RAMURI
        self.merge_layers(['layer_reteajt'], 'RAMURI')
        step += 1
        self.progress_bar.setValue(step)

        # 6. Join Attributes by Location - RAMURI_NODURI
        self.join_attributes_by_location('ramuri.shp', 'noduri.shp', 'RAMURI_NODURI', 'intersects', 'One-to-Many')
        step += 1
        self.progress_bar.setValue(step)

        # 7. Join Attributes by Location - LEG_NODURI
        self.join_attributes_by_location('layer_nod_nrstr.shp', 'noduri.shp', 'LEG_NODURI', 'intersects', 'One-to-One')
        step += 1
        self.progress_bar.setValue(step)

        # 8. Merge layers for NODURI_AUX_VRTX
        self.merge_layers(['inc_linii', 'cutii', 'stalpi', 'bpmnou', 'auxiliar', 'pct_vrtx'], 'NODURI_AUX_VRTX')
        step += 1
        self.progress_bar.setValue(step)

        # 9. Join Attributes by Location - RAMURI_AUX_VRTX
        self.join_attributes_by_location('ramuri.shp', 'noduri_aux.shp', 'RAMURI_AUX_VRTX', 'intersects', 'One-to-Many')
        step += 1
        self.progress_bar.setValue(step)

        # 10. Add 'SEI' column with conditional values
        self.add_sei_column('ramuri_aux_vrtx', 'SEI')
        step += 1
        self.progress_bar.setValue(step)

        # 11. Add 'Join_Count' column for all joins with value '1'
        self.add_join_count_column('RAMURI_NODURI')
        self.add_join_count_column('LEG_NODURI')
        self.add_join_count_column('RAMURI_AUX_VRTX')
        step += 1
        self.progress_bar.setValue(step)

        # 12. Done
        self.progress_bar.setValue(total_steps)

    # Geometry Calculation for X, Y coords
    def calculate_geometry(self, layer, start_x, start_y, end_x, end_y):
        layer.startEditing()
        
        # Expression for Start and End points
        start_x_expr = QgsExpression('x(start_point($geometry))')
        start_y_expr = QgsExpression('y(start_point($geometry))')
        end_x_expr = QgsExpression('x(end_point($geometry))')
        end_y_expr = QgsExpression('y(end_point($geometry))')
        
        context = QgsExpressionContext()
        context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))

        # Adding new fields for coordinates
        layer.dataProvider().addAttributes([QgsField(start_x, QVariant.Double), QgsField(start_y, QVariant.Double), 
                                            QgsField(end_x, QVariant.Double), QgsField(end_y, QVariant.Double)])
        layer.updateFields()

        for feature in layer.getFeatures():
            context.setFeature(feature)
            layer.changeAttributeValue(feature.id(), layer.fields().indexOf(start_x), start_x_expr.evaluate(context))
            layer.changeAttributeValue(feature.id(), layer.fields().indexOf(start_y), start_y_expr.evaluate(context))
            layer.changeAttributeValue(feature.id(), layer.fields().indexOf(end_x), end_x_expr.evaluate(context))
            layer.changeAttributeValue(feature.id(), layer.fields().indexOf(end_y), end_y_expr.evaluate(context))

        layer.commitChanges()

    # Add 'lungime' and 'id' fields
    def add_length_and_id(self, layer, length_field, id_field):
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

    # Modify 'layer_nod_nrstr'
    def modify_nod_nrstr(self, layer):
        layer.startEditing()
        # Remove 'GlobalId', keep 'ID' and 'FID'
        if 'GlobalId' in [field.name() for field in layer.fields()]:
            layer.dataProvider().deleteAttributes([layer.fields().indexOf('GlobalId')])
        layer.updateFields()
        layer.commitChanges()

    # Merge Vector Layers
    def merge_layers(self, layer_list, folder):
        input_layers = [QgsProject.instance().mapLayersByName(name)[0] for name in layer_list]
        output = QFileDialog.getSaveFileName(self, f'Save {folder} Layer', '', 'Geopackage (*.gpkg)')[0]
        if output:
            processing.run("qgis:mergevectorlayers", {'LAYERS': input_layers, 'CRS': 'EPSG:3844', 'OUTPUT': output})

    # Join Attributes by Location
    def join_attributes_by_location(self, input_file, join_file, output_name, predicate, method):
        output = QFileDialog.getSaveFileName(self, f'Save {output_name}', '', 'Shapefiles (*.shp)')[0]
        if output:
            processing.run("qgis:joinattributesbylocation", {
                'INPUT': input_file,
                'JOIN': join_file,
                'PREDICATE': [0],  # intersects
                'JOIN_FIELDS': [],
                'METHOD': 1 if method == 'One-to-Many' else 0,  # One-to-Many or One-to-One
                'DISCARD_NONMATCHING': False,
                'OUTPUT': output
            })

    # Add 'SEI' column and calculate values
    def add_sei_column(self, layer_name, column_name):
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        layer.startEditing()
        # Add 'SEI' column as text
        layer.dataProvider().addAttributes([QgsField(column_name, QVariant.String)])
        layer.updateFields()

        # Expression to add the conditional values
        sei_expr = QgsExpression('CASE WHEN "Noduri" THEN 3 ELSE 1 END')
        context = QgsExpressionContext()
        context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))

        for feature in layer.getFeatures():
            context.setFeature(feature)
            sei_value = sei_expr.evaluate(context)
            layer.changeAttributeValue(feature.id(), layer.fields().indexOf(column_name), sei_value)

        layer.commitChanges()

    # Add 'Join_Count' column
    def add_join_count_column(self, layer_name):
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        layer.startEditing()
        layer.dataProvider().addAttributes([QgsField('Join_Count', QVariant.Int)])
        layer.updateFields()

        for feature in layer.getFeatures():
            layer.changeAttributeValue(feature.id(), layer.fields().indexOf('Join_Count'), 1)

        layer.commitChanges()

