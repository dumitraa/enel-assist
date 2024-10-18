import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from typing import Dict, Any, List
iface = qgis.utils.iface

class Auxiliar:
    def __init__(self, id, denumire, observatii, POINT_X, POINT_Y, POINT_M, ignored=False):
        self.id = id
        self.denumire = denumire
        self.observatii = observatii
        self.POINT_X = POINT_X
        self.POINT_Y = POINT_Y
        self.POINT_M = POINT_M
        self.ignored = ignored

    def to_dict(self):
        return {
            'id': self.id,
            'denumire': self.denumire,
            'observatii': self.observatii,
            'POINT_X': self.POINT_X,
            'POINT_Y': self.POINT_Y,
            'POINT_M': self.POINT_M,
            'ignored': self.ignored
        }

class AuxiliarParser:
    def __init__(self, layer: QgsVectorLayer):
        self.layer = layer
        
        self.mapping = {  # Attribute table values to friendly names
            'denumire': 'Denumire',
            'observatii': 'Observatii',
            'POINT_X': 'POINT_X',
            'POINT_Y': 'POINT_Y',
            'POINT_M': 'POINT_M'
        }

        self.validation_rules: Dict[str, Any] = {
            "denumire": {
                'rule': 'str',
                'required': True
            },
        }

        # Retrieve the layer named "auxiliar" from the current QGIS project
        self.layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name().lower() == "auxiliar":
                self.layer = layer
                break

        if self.layer is None:
            raise ValueError("Layer named 'auxiliar' not found in the project.")

        self.auxiliare_data = []
        self.invalid_elements = []

    def parse(self):
        for feature in self.layer.getFeatures():
            auxiliar_data = Auxiliar(
                id=feature.id(),
                denumire=feature['Denumire'] if feature['Denumire'] not in [None, 'NULL', 'nan'] else None,
                observatii=feature['Observatii'] if feature['Observatii'] not in [None, 'NULL'] else None,
                POINT_X=feature['POINT_X'] if feature['POINT_X'] not in [None, 'NULL', 'nan'] else None,
                POINT_Y=feature['POINT_Y'] if feature['POINT_Y'] not in [None, 'NULL', 'nan'] else None,
                POINT_M=feature['POINT_M'] if feature['POINT_M'] not in [None, 'NULL', 'nan'] else None
            )
            QgsMessageLog.logMessage(f"Feature {auxiliar_data.denumire} parsed successfully with data {auxiliar_data.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.auxiliare_data.append(auxiliar_data)

    def validate(self) -> List[Dict[str, Any]]:
        print("~~~* Validating auxiliare *~~~")
        self.invalid_elements = []

        for aux in self.auxiliare_data:
            aux_dict = aux.to_dict()
            for field, rule_config in self.validation_rules.items():
                value = aux_dict.get(field, None)
                rule = rule_config.get('rule')
                required = rule_config.get('required', False)
                
                QgsMessageLog.logMessage(f"Validating field {field} with value {value} and rule {rule}", "EnelAssist", level=Qgis.Info)

                if value is None and required:
                    self.invalid_elements.append({
                        'layer_name': "Auxiliar",
                        'id': f"{aux.denumire if aux.denumire else f"ID {aux.id}"}",
                        'tag': field,
                        'friendly_name': f"{self.mapping.get(field)}",
                        'error': f"Câmpul trebuie să fie completat!",
                        'suggestions': rule
                    })
                    continue

                if value is not None:
                    if rule == "str":
                        if not isinstance(value, str):
                            self.invalid_elements.append({
                                'layer_name': "Auxiliar",
                                'id': f"{aux.denumire if aux.denumire else f"ID {aux.id}"}",
                                'tag': field,
                                'friendly_name': f"{self.mapping.get(field)}",
                                'error': f"Valoarea '{value}' nu este de tip text",
                                'suggestions': rule
                            })
                            
                            QgsMessageLog.logMessage(f"Field {field} with value {value} is not of type 'str'", "EnelAssist", level=Qgis.Warning)

        return self.invalid_elements if self.invalid_elements else [{'layer_name': self.layer.name()}]

    def get_auxiliare_data(self):
        return self.auxiliare_data

    def update_feature(self, feature_id, field, value):
        for aux in self.auxiliare_data:
            if aux.id == feature_id:
                setattr(aux, field, value)
                print(f"Value was changed for Feature {feature_id}: {field} - {value}")
                break

    def save_to_layer(self):
        """
        Save the updated data back to the layer.
        """
        if not self.layer:
            raise ValueError("Layer is not loaded.")

        # Start an editing session on the layer
        if not self.layer.isEditable():
            if not self.layer.startEditing():
                QgsMessageLog.logMessage("Failed to start editing the layer.", "EnelAssist", Qgis.Warning)
                return

        # Iterate over the auxiliar data and update the corresponding features
        for aux in self.auxiliare_data:
            if aux.ignored:
                continue
            feature = self.layer.getFeature(aux.id)
            if feature.isValid():
                # Update each attribute in the feature
                fields = self.layer.fields()

                success = True  # Track whether all attribute changes succeed
                
                for field_name, new_value in [
                    ('Denumire', aux.denumire),
                    ('Observatii', aux.observatii),
                    ('POINT_X', aux.POINT_X),
                    ('POINT_Y', aux.POINT_Y),
                    ('POINT_M', aux.POINT_M),
                ]:
                    # Get the field index
                    field_index = fields.indexFromName(field_name)
                    if field_index == -1:
                        QgsMessageLog.logMessage(f"Field '{field_name}' not found in layer.", "EnelAssist", Qgis.Warning)
                        continue

                    # Change the attribute value
                    if not self.layer.changeAttributeValue(feature.id(), field_index, new_value):
                        success = False
                        QgsMessageLog.logMessage(f"Failed to update field '{field_name}' for feature ID {aux.id}.", "EnelAssist", Qgis.Warning)
                    else:
                        QgsMessageLog.logMessage(f"Feature ID {aux.id}: Field '{field_name}' updated successfully.", "EnelAssist", Qgis.Info)

                if not success:
                    QgsMessageLog.logMessage(f"Some attributes could not be updated for feature ID {aux.id}. Rolling back changes.", "EnelAssist", Qgis.Warning)
                    self.layer.rollBack()
                    return

        # Commit changes to the layer
        if not self.layer.commitChanges():
            QgsMessageLog.logMessage("Failed to commit changes to the layer.", "EnelAssist", Qgis.Warning)
        else:
            QgsMessageLog.logMessage("Changes successfully committed to the layer.", "EnelAssist", Qgis.Info)


