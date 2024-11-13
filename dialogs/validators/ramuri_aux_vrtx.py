import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from typing import Dict, Any, List
import re
iface = qgis.utils.iface

from .base_parser import BaseParser

class RamuriAuxVrtx:
    def __init__(self, internal_id, FID, TARGET_FID, START_X, START_Y, END_X, END_Y, nr_nod,
                 POINT_X, POINT_Y, POINT_Z, POINT_M, SEI):
        self.internal_id = internal_id
        self.FID = FID
        self.TARGET_FID = TARGET_FID
        self.START_X = START_X
        self.START_Y = START_Y
        self.END_X = END_X
        self.END_Y = END_Y
        self.nr_nod = nr_nod
        self.POINT_X = POINT_X
        self.POINT_Y = POINT_Y
        self.POINT_Z = POINT_Z
        self.POINT_M = POINT_M
        self.SEI = SEI

    def to_dict(self):
        return {
            'internal_id': self.internal_id,
            'FID': self.FID,
            'TARGET_FID': self.TARGET_FID,
            'START_X': self.START_X,
            'START_Y': self.START_Y,
            'END_X': self.END_X,
            'END_Y': self.END_Y,
            'nr_nod': self.nr_nod,
            'POINT_X': self.POINT_X,
            'POINT_Y': self.POINT_Y,
            'POINT_Z': self.POINT_Z,
            'POINT_M': self.POINT_M,
        }

class RamuriAuxVrtxParser(BaseParser):
    def __init__(self, layer: QgsVectorLayer):
        super().__init__(layer, "RAMURI_NODURI")
        
        self.column_names = ['FID', 'TARGET_FID', 'START_X', 'START_Y', 'END_X', 'END_Y', 'nr_nod', 'POINT_X', 'POINT_Y', 'POINT_Z', 'POINT_M', 'SEI']

        self.validation_rules: Dict[str, Any] = {
            'internal_id': {
                'rule': 'int',
                'required': True
            },
        }

        # Retrieve the layer named "ramuri_noduri" from the current QGIS project
        self.layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == "RAMURI_AUX_VRTX":
                self.layer = layer
                break

        if self.layer is None:
            raise ValueError("Layer named 'RAMURI_AUX_VRTX' not found in the project.")

        self.ramuri_aux = []
        self.invalid_elements = []

    def parse(self):
        for feature in self.layer.getFeatures():
            # if feature['Material']:
            #     cod_material = re.search(r'[A-Z](\d+)', feature['Material']).group(1)
            # else:
            #     cod_material = None
            ramura_aux = RamuriAuxVrtx(
                internal_id=feature.id(),
                FID=feature.id(),
                TARGET_FID=feature['id_'] if feature['id_'] not in [None, 'NULL', 'nan'] else None,
                START_X=feature['START_X'] if feature['START_X'] not in [None, 'NULL', 'nan'] else None,
                START_Y=feature['START_Y'] if feature['START_Y'] not in [None, 'NULL', 'nan'] else None,
                END_X=feature['END_X'] if feature['END_X'] not in [None, 'NULL', 'nan'] else None,
                END_Y=feature['END_Y'] if feature['END_Y'] not in [None, 'NULL', 'nan'] else None,
                nr_nod=feature['nr_nod'] if feature['nr_nod'] not in [None, 'NULL', 'nan'] else None,
                POINT_X=feature['POINT_X'] if feature['POINT_X'] not in [None, 'NULL', 'nan'] else None,
                POINT_Y=feature['POINT_Y'] if feature['POINT_Y'] not in [None, 'NULL', 'nan'] else None,
                POINT_Z=feature['POINT_Z'] if feature['POINT_Z'] not in [None, 'NULL', 'nan'] else 0,
                POINT_M=feature['POINT_M'] if feature['POINT_M'] not in [None, 'NULL', 'nan'] else 0,
                SEI=feature['SEI'] if feature['SEI'] not in [None, 'NULL', 'nan'] else None
            )
            # QgsMessageLog.logMessage(f"Feature {ramura_aux.denumire} parsed successfully with data {ramura_aux.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.ramuri_aux.append(ramura_aux)
        
        self.data = self.ramuri_aux

    def get_ramuri_data(self):
        return self.ramuri_aux
    
    def get_name(self):
        return "RAMURI_AUX_VRTX"
