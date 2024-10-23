from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis

class BaseParser:
    def __init__(self, layer: QgsVectorLayer, layer_name: str):
        self.layer = None
        for l in QgsProject.instance().mapLayers().values():
            if l.name().lower() == layer_name.lower():
                self.layer = l
                break

        if self.layer is None:
            raise ValueError(f"Layer named '{layer_name}' not found in the project.")

        self.invalid_elements = []

    def validate(self):
        self.invalid_elements = []

        def append_error(obj, field, error_msg, rule):
            """Helper function to append validation errors."""
            friendly_name = getattr(obj, 'denumire', None) or getattr(obj, 'denumire_a', None) or f"ID {obj.friendly_id}"
            self.invalid_elements.append({
                'layer_name': self.layer.name(),
                'id': obj.id,
                'tag': field,
                'friendly_name': friendly_name,
                'error': error_msg,
                'suggestions': rule
            })

        for obj in self.data:
            obj_dict = obj.to_dict()
            for field, rule_config in self.validation_rules.items():
                value = obj_dict.get(field, None)
                rule = rule_config.get('rule')
                required = rule_config.get('required', False)

                QgsMessageLog.logMessage(f"Validating field {field} with value {value} and rule {rule}", "EnelAssist", level=Qgis.Info)

                # Check if the field is required but missing
                if value is None and required:
                    append_error(obj, field, f"Câmpul trebuie să fie completat!", rule)
                    continue

                # Type validation: Check if value is a string
                if rule == "str" and value is not None and not isinstance(value, str):
                    append_error(obj, field, f"Valoarea '{value}' nu este de tip text", rule)
                    QgsMessageLog.logMessage(f"Field {field} with value {value} is not of type 'str'", "EnelAssist", level=Qgis.Warning)

                # Type validation: Check if value is an integer
                if rule == "int" and value is not None and not isinstance(value, int):
                    append_error(obj, field, f"Valoarea '{value}' nu este de tip număr întreg", rule)
                    QgsMessageLog.logMessage(f"Field {field} with value {value} is not of type 'int'", "EnelAssist", level=Qgis.Warning)

                # List validation: Check if value is in a list of valid values
                if isinstance(rule, list) and value is not None and value not in rule:
                    append_error(obj, field, f"Valoarea '{value}' nu este în lista de valori posibile", rule)
                    QgsMessageLog.logMessage(f"Field {field} with value {value} is not in the list of valid values", "EnelAssist", level=Qgis.Warning)

        return self.invalid_elements if self.invalid_elements else []


    def update_feature(self, feature_id, field, value):
        for obj in self.data:
            QgsMessageLog.logMessage(f"Comparing obj.id with feature_id - {obj.id} == {feature_id}?", "EnelAssist", level=Qgis.Info)
            if obj.id == feature_id:
                QgsMessageLog.logMessage(f"Found feature {feature_id} in data. Updating field {field} with value {value}", "EnelAssist", level=Qgis.Info)
                setattr(obj, field, value)
                print(f"Value was changed for Feature {feature_id}: {field} - {value}")
                break
            else:
                QgsMessageLog.logMessage(f"Feature {feature_id} not found in data.", "EnelAssist", level=Qgis.Warning)

    def save_to_layer(self):
        if not self.layer:
            raise ValueError("Layer is not loaded.")

        if not self.layer.isEditable():
            if not self.layer.startEditing():
                QgsMessageLog.logMessage("Failed to start editing the layer.", "EnelAssist", Qgis.Warning)
                return

        for obj in self.data:
            if obj.ignored:
                continue
            feature = self.layer.getFeature(obj.id)
            if feature.isValid():
                fields = self.layer.fields()
                QgsMessageLog.logMessage(f"Feature ID {obj.id} found in layer. - {fields}", "EnelAssist", Qgis.Info)

                success = True
                
                for internal_field, layer_field in self.mapping.items():
                    new_value = getattr(obj, internal_field, None)

                    QgsMessageLog.logMessage(f"Updating field '{layer_field}' with value '{new_value}'", "EnelAssist", Qgis.Info)
                    
                    field_index = fields.indexFromName(layer_field)
                    if field_index == -1:
                        QgsMessageLog.logMessage(f"Field '{layer_field}' not found in layer.", "EnelAssist", Qgis.Warning)
                        continue

                    if not self.layer.changeAttributeValue(feature.id(), field_index, new_value):
                        success = False
                        QgsMessageLog.logMessage(f"Failed to update field '{layer_field}' for feature ID {obj.id}.", "EnelAssist", Qgis.Warning)
                    else:
                        QgsMessageLog.logMessage(f"Feature ID {obj.id}: Field '{layer_field}' updated successfully.", "EnelAssist", Qgis.Info)


                if not success:
                    QgsMessageLog.logMessage(f"Some attributes could not be updated for feature ID {obj.id}. Rolling back changes.", "EnelAssist", Qgis.Warning)
                    self.layer.rollBack()
                    return

        if not self.layer.commitChanges():
            QgsMessageLog.logMessage("Failed to commit changes to the layer.", "EnelAssist", Qgis.Warning)
        else:
            QgsMessageLog.logMessage("Changes successfully committed to the layer.", "EnelAssist", Qgis.Info)
