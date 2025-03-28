import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from typing import Dict, Any, List
iface = qgis.utils.iface

from .base_parser import BaseParser

class LegNod:
    def __init__(self, Join_Count, ID, internal_id, friendly_id, denumire, stare_cone, cod_societ, cod_zona, nr_nod, serie_nod, POINT_X, POINT_Y, POINT_Z, POINT_M, ignored=False):
        self.Join_Count = Join_Count
        self.ID = ID
        self.internal_id = internal_id
        self.friendly_id = friendly_id
        self.denumire = denumire
        self.stare_cone = stare_cone
        self.cod_societ = cod_societ
        self.cod_zona = cod_zona
        self.nr_nod = nr_nod
        self.serie_nod = serie_nod
        self.POINT_X = POINT_X
        self.POINT_Y = POINT_Y
        self.POINT_Z = POINT_Z
        self.POINT_M = POINT_M
        self.ignored = ignored

    def to_dict(self):
        return {
            'Join_Count': self.Join_Count,
            "ID": self.ID,
            'internal_id': self.internal_id,
            'friendly_id': self.friendly_id,
            'denumire': self.denumire,
            'stare_cone': self.stare_cone,
            'cod_societ': self.cod_societ,
            'cod_zona': self.cod_zona,
            'nr_nod': self.nr_nod,
            'serie_nod': self.serie_nod,
            'POINT_X': self.POINT_X,
            'POINT_Y': self.POINT_Y,
            'POINT_Z': self.POINT_Z,
            'POINT_M': self.POINT_M,
            'ignored': self.ignored
        }

class LegNoduriParser(BaseParser):
    def __init__(self, layer: QgsVectorLayer):
        super().__init__(layer, "LEG_NODURI")
        
        self.column_names = ['Join_Count', 'ID', 'denumire', 'stare_cone', 'cod_societ', 'cod_zona', 'nr_nod', 'serie_nod', 'POINT_X', 'POINT_Y', 'POINT_Z', 'POINT_M']

        self.validation_rules: Dict[str, Any] = {
            "denumire": {
                'rule': 'str',
                'required': True
            },
            "stare_cone": {
                'rule': ['C - inchis'],
                'required': True
            },
            "nr_nod": {
                'rule': 'str',
                'required': False
            },
            "serie_nod": {
                'rule': ['7'],
                'required': True
            }
        }

        # Retrieve the layer named "leg_noduri" from the current QGIS project
        self.layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == "LEG_NODURI":
                self.layer = layer
                break

        if self.layer is None:
            raise ValueError("Layer named 'LEG_NODURI' not found in the project.")

        self.leg_noduri_data = []
        self.invalid_elements = []

    def parse(self):
        for feature in self.layer.getFeatures():
            leg_nod_data = LegNod(
                Join_Count=1,
                internal_id=feature.id(),
                friendly_id=feature.id() + 1,
                ID=feature.id() + 2,
                denumire=feature['Denumire'] if feature['Denumire'] not in [None, 'NULL', 'nan'] else None,
                stare_cone=feature['StareConex'] if feature['StareConex'] not in [None, 'NULL', 'nan'] else None,
                cod_societ=feature['cod_societ'] if feature['cod_societ'] not in [None, 'NULL', 'nan'] else None,
                cod_zona=feature['cod_zona'] if feature['cod_zona'] not in [None, 'NULL', 'nan'] else None,
                nr_nod=feature['nr_nod'] if feature['nr_nod'] not in [None, 'NULL', 'nan'] else None,
                serie_nod=feature['serie_nod'] if feature['serie_nod'] not in [None, 'NULL', 'nan'] else None,
                POINT_X=feature['POINT_X'] if feature['POINT_X'] not in [None, 'NULL', 'nan'] else None,
                POINT_Y=feature['POINT_Y'] if feature['POINT_Y'] not in [None, 'NULL', 'nan'] else None,
                POINT_Z=feature['POINT_Z'] if feature['POINT_Z'] not in [None, 'NULL', 'nan'] else 0,
                POINT_M=feature['POINT_M'] if feature['POINT_M'] not in [None, 'NULL', 'nan'] else 0
            )
            # QgsMessageLog.logMessage(f"Feature {leg_nod_data.denumire} parsed successfully with data {leg_nod_data.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.leg_noduri_data.append(leg_nod_data)
            
        self.data = self.leg_noduri_data

    def get_leg_noduri_data(self) -> List[LegNod]:
        return self.leg_noduri_data
    
    def get_name(self) -> str:
        return "LEG_NODURI"