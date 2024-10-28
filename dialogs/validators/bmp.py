from typing import Dict, Any, List
import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
iface = qgis.utils.iface

from .base_parser import BaseParser

class BMP:
    def __init__(self, internal_id, friendly_id, denumire, serie_cont, stare_cone, serie_con2, serie_con3, serie_con4, serie_con5, cod_societ, cod_zona, nr_nod, serie_nod, POINT_X, POINT_Y, POINT_M, ignored=False):
        self.internal_id = internal_id
        self.friendly_id = friendly_id
        self.denumire = denumire
        self.serie_cont = serie_cont
        self.stare_cone = stare_cone
        self.serie_con2 = serie_con2
        self.serie_con3 = serie_con3
        self.serie_con4 = serie_con4
        self.serie_con5 = serie_con5
        self.cod_societ = cod_societ
        self.cod_zona = cod_zona
        self.nr_nod = nr_nod
        self.serie_nod = serie_nod
        self.POINT_X = POINT_X
        self.POINT_Y = POINT_Y
        self.POINT_M = POINT_M
        self.ignored = ignored

    def to_dict(self):
        return {
            'internal_id': self.internal_id,
            'friendly_id': self.friendly_id,
            'denumire': self.denumire,
            'serie_cont': self.serie_cont,
            'stare_cone': self.stare_cone,
            'serie_con2': self.serie_con2,
            'serie_con3': self.serie_con3,
            'serie_con4': self.serie_con4,
            'serie_con5': self.serie_con5,
            'cod_societ': self.cod_societ,
            'cod_zona': self.cod_zona,
            'nr_nod': self.nr_nod,
            'serie_nod': self.serie_nod,
            'POINT_X': self.POINT_X,
            'POINT_Y': self.POINT_Y,
            'POINT_M': self.POINT_M,
            'ignored': self.ignored
        }

class BMPParser(BaseParser):
    def __init__(self, layer: QgsVectorLayer):
        super().__init__(layer, "BMPnou")
        
        self.mapping = {  # Attribute table values to friendly names
            'denumire': 'Denumire',
            'serie_cont': 'SerieConto',
            'stare_cone': 'StareConex',
            'serie_con2': 'SerieCon_1',
            'serie_con3': 'SerieCon_2',
            'serie_con4': 'SerieCon_3',
            'serie_con5': 'serie_con5',
            'cod_societ': 'cod_societ',
            'cod_zona': 'cod_zona',
            'nr_nod': 'nr_nod',
            'serie_nod': 'serie_nod',
            'POINT_X': 'POINT_X',
            'POINT_Y': 'POINT_Y',
            'POINT_M': 'POINT_M'
        }

        self.validation_rules: Dict[str, Any] = {
            "denumire": {
                'rule': 'str',
                'required': True
            },
            "serie_cone": {
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

        # Retrieve the layer named "bmp" from the current QGIS project
        self.layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == "BMPnou":
                self.layer = layer
                break

        if self.layer is None:
            raise ValueError("Layer named 'BMPnou' not found in the project.")

        self.bmp_data = []
        self.invalid_elements = []

    def parse(self):
        for feature in self.layer.getFeatures():
            bmp_data = BMP(
                internal_id=feature.id(),
                friendly_id=feature.id() + 1,
                denumire=feature['Denumire'] if feature['Denumire'] not in [None, 'NULL', 'nan'] else None,
                serie_cont=feature['SerieConto'] if feature['SerieConto'] not in [None, 'NULL', 'nan'] else None,
                stare_cone=feature['StareConex'] if feature['StareConex'] not in [None, 'NULL', 'nan'] else None,
                serie_con2=feature['SerieCon_1'] if feature['SerieCon_1'] not in [None, 'NULL', 'nan'] else None,
                serie_con3=feature['SerieCon_2'] if feature['SerieCon_2'] not in [None, 'NULL', 'nan'] else None,
                serie_con4=feature['SerieCon_3'] if feature['SerieCon_3'] not in [None, 'NULL', 'nan'] else None,
                serie_con5=feature['serie_con5'] if feature['serie_con5'] not in [None, 'NULL', 'nan'] else None,
                cod_societ=feature['cod_societ'] if feature['cod_societ'] not in [None, 'NULL', 'nan'] else None,
                cod_zona=feature['cod_zona'] if feature['cod_zona'] not in [None, 'NULL', 'nan'] else None,
                nr_nod=feature['nr_nod'] if feature['nr_nod'] not in [None, 'NULL', 'nan'] else None,
                serie_nod=feature['serie_nod'] if feature['serie_nod'] not in [None, 'NULL', 'nan'] else None,
                POINT_X=feature['POINT_X'] if feature['POINT_X'] not in [None, 'NULL', 'nan'] else None,
                POINT_Y=feature['POINT_Y'] if feature['POINT_Y'] not in [None, 'NULL', 'nan'] else None,
                POINT_M=feature['POINT_M'] if feature['POINT_M'] not in [None, 'NULL', 'nan'] else None
            )
            QgsMessageLog.logMessage(f"Feature {bmp_data.denumire} parsed successfully with data {bmp_data.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.bmp_data.append(bmp_data)
            
        self.data = self.bmp_data

    def get_bmp_data(self):
        return self.bmp_data
