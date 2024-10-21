import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from typing import Dict, Any, List
iface = qgis.utils.iface

from .base_parser import BaseParser

class Auxiliar:
    def __init__(self, id, friendly_id, denumire, observatii, POINT_X, POINT_Y, POINT_M, ignored=False):
        self.id = id
        self.friendly_id = friendly_id
        self.denumire = denumire
        self.observatii = observatii
        self.POINT_X = POINT_X
        self.POINT_Y = POINT_Y
        self.POINT_M = POINT_M
        self.ignored = ignored

    def to_dict(self):
        return {
            'id': self.id,
            'friendly_id': self.friendly_id,
            'denumire': self.denumire,
            'observatii': self.observatii,
            'POINT_X': self.POINT_X,
            'POINT_Y': self.POINT_Y,
            'POINT_M': self.POINT_M,
            'ignored': self.ignored
        }

class AuxiliarParser(BaseParser):
    def __init__(self, layer: QgsVectorLayer):
        super().__init__(layer, "auxiliar")
        
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
                friendly_id=feature.id() + 1,
                denumire=feature['Denumire'] if feature['Denumire'] not in [None, 'NULL', 'nan'] else None,
                observatii=feature['Observatii'] if feature['Observatii'] not in [None, 'NULL'] else None,
                POINT_X=feature['POINT_X'] if feature['POINT_X'] not in [None, 'NULL', 'nan'] else None,
                POINT_Y=feature['POINT_Y'] if feature['POINT_Y'] not in [None, 'NULL', 'nan'] else None,
                POINT_M=feature['POINT_M'] if feature['POINT_M'] not in [None, 'NULL', 'nan'] else None
            )
            QgsMessageLog.logMessage(f"Feature {auxiliar_data.denumire} parsed successfully with data {auxiliar_data.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.auxiliare_data.append(auxiliar_data)
            
        self.data = self.auxiliare_data

    def get_auxiliare_data(self):
        return self.auxiliare_data


