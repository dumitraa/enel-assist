from typing import Dict, Any, List
import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
iface = qgis.utils.iface

from .base_parser import BaseParser

class Cd:
    def __init__(self, internal_id, friendly_id, denumire, tip_aparat, stare_cone, cod_societ, cod_zona, serie_nod, nr_nod, observatii, POINT_X, POINT_Y, POINT_Z, POINT_M, ignored=False):
        self.internal_id = internal_id
        self.friendly_id = friendly_id
        self.denumire = denumire
        self.tip_aparat = tip_aparat
        self.stare_cone = stare_cone
        self.cod_societ = cod_societ
        self.cod_zona = cod_zona
        self.serie_nod = serie_nod
        self.nr_nod = nr_nod
        self.observatii = observatii
        self.POINT_X = POINT_X
        self.POINT_Y = POINT_Y
        self.POINT_M = POINT_M
        self.POINT_Z = POINT_Z
        self.ignored = ignored

    def to_dict(self):
        return {
            'internal_id': self.internal_id,
            'friendly_id': self.friendly_id,
            'denumire': self.denumire,
            'tip_aparat': self.tip_aparat,
            'stare_cone': self.stare_cone,
            'cod_societ': self.cod_societ,
            'cod_zona': self.cod_zona,
            'serie_nod': self.serie_nod,
            'nr_nod': self.nr_nod,
            'observatii': self.observatii,
            'POINT_X': self.POINT_X,
            'POINT_Y': self.POINT_Y,
            'POINT_Z': self.POINT_Z,
            'POINT_M': self.POINT_M,
            'ignored': self.ignored
        }

class CdParser(BaseParser):
    def __init__(self, layer: QgsVectorLayer):
        super().__init__(layer, "Cutii")
        
        self.column_names = ['denumire', 'tip_aparat', 'stare_cone', 'cod_societ', 'cod_zona', 'nr_nod', 'serie_nod', 'observatii', 'POINT_X', 'POINT_Y', 'POINT_Z', 'POINT_M']

        self.validation_rules: Dict[str, Any] = {
            "denumire": {
                'rule': 'str',
                'required': True
            }
        }

        # Retrieve the layer named "cd" from the current QGIS project
        self.layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == "Cutii":
                self.layer = layer
                break

        if self.layer is None:
            raise ValueError("Layer named 'Cutii' not found in the project.")

        self.cd_data = []
        self.invalid_elements = []

    def parse(self):
        for feature in self.layer.getFeatures():
            cd_data = Cd(
                internal_id=feature.id(),
                friendly_id=feature.id() + 1,
                denumire=feature['Denumire'] if feature['Denumire'] not in [None, 'NULL', 'nan'] else None,
                tip_aparat=feature['TipAparatu'] if feature['TipAparatu'] not in [None, 'NULL', 'nan'] else None,
                stare_cone=feature['StareConex'] if feature['StareConex'] not in [None, 'NULL', 'nan'] else None,
                cod_societ=feature['cod_societ'] if feature['cod_societ'] not in [None, 'NULL', 'nan'] else None,
                cod_zona=feature['cod_zona'] if feature['cod_zona'] not in [None, 'NULL', 'nan'] else None,
                nr_nod=feature['nr_nod'] if feature['nr_nod'] not in [None, 'NULL', 'nan'] else None,
                serie_nod=feature['serie_nod'] if feature['serie_nod'] not in [None, 'NULL', 'nan'] else None,
                observatii="",
                POINT_X=feature['POINT_X'] if feature['POINT_X'] not in [None, 'NULL', 'nan'] else None,
                POINT_Y=feature['POINT_Y'] if feature['POINT_Y'] not in [None, 'NULL', 'nan'] else None,
                POINT_Z=feature['POINT_Z'] if feature['POINT_Z'] not in [None, 'NULL', 'nan'] else None,
                POINT_M=feature['POINT_M'] if feature['POINT_M'] not in [None, 'NULL', 'nan'] else None
            )
            # QgsMessageLog.logMessage(f"Feature {cd_data.denumire} parsed successfully with data {cd_data.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.cd_data.append(cd_data)
            
        self.data = self.cd_data

    def get_cd_data(self):
        return self.cd_data
    
    def get_name(self):
        return "CD"
