import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from typing import Dict, Any, List
iface = qgis.utils.iface

from .base_parser import BaseParser

class IncLini:
    def __init__(self, internal_id, friendly_id, denumire, stare_cone, cod_societ, cod_zona, nr_nod, serie_nod, observatii, POINT_X, POINT_Y, POINT_Z, POINT_M, ignored=False):
        self.internal_id = internal_id
        self.friendly_id = friendly_id
        self.denumire = denumire
        self.stare_cone = stare_cone
        self.cod_societ = cod_societ
        self.cod_zona = cod_zona
        self.nr_nod = nr_nod
        self.serie_nod = serie_nod
        self.observatii = observatii
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
            'stare_cone': self.stare_cone,
            'cod_societ': self.cod_societ,
            'cod_zona': self.cod_zona,
            'nr_nod': self.nr_nod,
            'serie_nod': self.serie_nod,
            'observatii': self.observatii,
            'POINT_X': self.POINT_X,
            'POINT_Y': self.POINT_Y,
            'POINT_Z': self.POINT_Z,
            'POINT_M': self.POINT_M,
            'ignored': self.ignored
        }

class IncLiniParser(BaseParser):
    def __init__(self, layer: QgsVectorLayer):
        super().__init__(layer, "InceputLinie")
        
        self.mapping = {  # Attribute table values to friendly names
            'denumire': 'Denumire',
            'stare_cone': 'StareConex',
            'cod_societ': 'cod_societ',
            'cod_zona': 'cod_zona',
            'nr_nod': 'nr_nod',
            'serie_nod': 'serie_nod',
            'observatii': None,
            'POINT_X': 'POINT_X',
            'POINT_Y': 'POINT_Y',
            'POINT_Z': 'POINT_Z',
            'POINT_M': 'POINT_M'
        }

        self.validation_rules: Dict[str, Any] = {
            "denumire": {
                'rule': 'str',
                'required': True
            },
            "stare_cone": {
                'rule': ['C - inchis'],
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
                'rule': ['8'],
                'required': True
            },
            "observatii": {
                'rule': 'str',
                'required': True
            }
        }

        # Retrieve the layer named "inclini" from the current QGIS project
        self.layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == "InceputLinie":
                self.layer = layer
                break

        if self.layer is None:
            raise ValueError("Layer named 'InceputLinie' not found in the project.")

        self.inclini_data = []
        self.invalid_elements = []

    def parse(self):
        for feature in self.layer.getFeatures():
            inclini_data = IncLini(
                internal_id=feature.id(),
                friendly_id=feature.id() + 1,
                denumire=feature['Denumire'] if feature['Denumire'] not in [None, 'NULL', 'nan'] else None,
                stare_cone=feature['StareConex'] if feature['StareConex'] not in [None, 'NULL'] else None,
                cod_societ=feature['cod_societ'] if feature['cod_societ'] not in [None, 'NULL', 'nan'] else None,
                cod_zona=feature['cod_zona'] if feature['cod_zona'] not in [None, 'NULL', 'nan'] else None,
                nr_nod=feature['nr_nod'] if feature['nr_nod'] not in [None, 'NULL'] else None,
                serie_nod=feature['serie_nod'] if feature['serie_nod'] not in [None, 'NULL', 'nan'] else None,
                observatii=feature['observatii'] if feature['observatii'] not in [None, 'NULL'] else None,
                POINT_X=feature['POINT_X'] if feature['POINT_X'] not in [None, 'NULL', 'nan'] else None,
                POINT_Y=feature['POINT_Y'] if feature['POINT_Y'] not in [None, 'NULL', 'nan'] else None,
                POINT_Z=feature['POINT_Z'] if feature['POINT_Z'] not in [None, 'NULL', 'nan'] else None,
                POINT_M=feature['POINT_M'] if feature['POINT_M'] not in [None, 'NULL', 'nan'] else None
            )
            # QgsMessageLog.logMessage(f"Feature {inclini_data.denumire} parsed successfully with data {inclini_data.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.inclini_data.append(inclini_data)
            
        self.data = self.inclini_data

    def get_inclini_data(self):
        return self.inclini_data
