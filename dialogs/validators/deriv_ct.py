from typing import Dict, Any, List
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from .base_parser import BaseParser

class DerivCT:
    def __init__(self, internal_id, friendly_id, denumire, serie_cone, cod_societ, cod_zona, nr_nod, serie_nod, POINT_X, POINT_Y, POINT_Z, POINT_M, ignored=False):
        self.internal_id = internal_id
        self.friendly_id = friendly_id
        self.denumire = denumire
        self.serie_cone = serie_cone
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
            'internal_id': self.internal_id,
            'friendly_id': self.friendly_id,
            'denumire': self.denumire,
            'serie_cone': self.serie_cone,
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

class DerivCTParser(BaseParser):
    def __init__(self, layer: QgsVectorLayer):
        super().__init__(layer, "Stalpi")

        self.mapping = {
            'denumire': 'Denumire',
            'serie_cone': 'StareConex',
            'cod_societ': 'cod_societ',
            'cod_zona': 'cod_zona',
            'nr_nod': 'nr_nod',
            'serie_nod': 'serie_nod',
            'POINT_X': 'POINT_X',
            'POINT_Y': 'POINT_Y',
            'POINT_Z': 'POINT_Z',
            'POINT_M': 'POINT_M'
        }

        self.validation_rules: Dict[str, Any] = {
            "denumire": {
                'rule': ['SE10', 'SC10001', 'SE4', 'SC10002', 'SC10005', 'SE11', 'Stalp'],
                'required': True
            },
            "serie_cone": {
                'rule': ['C - inchis', 'A - deschis'],
                'required': True
            },
            "cod_societ": {
                'rule': 'str',
                'required': True
            },
            "cod_zona": {
                'rule': 'str',
                'required': True
            },
            "nr_nod": {
                'rule': 'str',
                'required': False
            },
            "serie_nod": {
                'rule': ['6'],
                'required': True
            }
        }

        # Retrieve the layer named "deriv_ct" from the current QGIS project
        self.layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == "Stalpi":
                self.layer = layer
                break

        if self.layer is None:
            raise ValueError("Layer named 'Stalpi' not found in the project.")

        self.deriv_ct_data = []
        self.invalid_elements = []

    def parse(self):
        for feature in self.layer.getFeatures():
            deriv_ct_data = DerivCT(
                internal_id=feature.id(),
                friendly_id=feature.id() + 1,
                denumire=feature['Denumire'] if feature['Denumire'] not in [None, 'NULL', 'nan'] else None,
                serie_cone=feature['StareConex'] if feature['StareConex'] not in [None, 'NULL'] else None,
                cod_societ=feature['cod_societ'] if feature['cod_societ'] not in [None, 'NULL'] else None,
                cod_zona=feature['cod_zona'] if feature['cod_zona'] not in [None, 'NULL'] else None,
                nr_nod=feature['nr_nod'] if feature['nr_nod'] not in [None, 'NULL'] else None,
                serie_nod=feature['serie_nod'] if feature['serie_nod'] not in [None, 'NULL'] else None,
                POINT_X=feature['POINT_X'] if feature['POINT_X'] not in [None, 'NULL', 'nan'] else None,
                POINT_Y=feature['POINT_Y'] if feature['POINT_Y'] not in [None, 'NULL', 'nan'] else None,
                POINT_Z=feature['POINT_Z'] if feature['POINT_Z'] not in [None, 'NULL', 'nan'] else None,
                POINT_M=feature['POINT_M'] if feature['POINT_M'] not in [None, 'NULL', 'nan'] else None
            )
            QgsMessageLog.logMessage(f"Feature {deriv_ct_data.denumire} parsed successfully with data {deriv_ct_data.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.deriv_ct_data.append(deriv_ct_data)

        self.data = self.deriv_ct_data

    def get_deriv_ct_data(self):
        return self.deriv_ct_data