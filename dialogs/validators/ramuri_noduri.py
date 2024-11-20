import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from typing import Dict, Any, List
import re
iface = qgis.utils.iface

from .base_parser import BaseParser

class RamuriNoduri:
    def __init__(self, Join_Count, internal_id, material, CIR, cod_materi, Pozare, ID, lungime, denumire, stare_cone, cod_societ, cod_zona, nr_nod, serie_nod, POINT_X, POINT_Y, POINT_Z, POINT_M):
        self.Join_Count = Join_Count
        self.internal_id = internal_id
        self.material = material
        self.CIR = CIR
        self.cod_materi = cod_materi
        self.Pozare = Pozare
        self.ID = ID
        self.lungime = lungime
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

    def to_dict(self):
        return {
            'Join_Count': self.Join_Count,
            'internal_id': self.internal_id,
            'material': self.material,
            'CIR': self.CIR,
            'cod_materi': self.cod_materi,
            'Pozare': self.Pozare,
            'ID': self.ID,
            'lungime_': self.lungime,
            'denumire': self.denumire,
            'stare_cone': self.stare_cone,
            'cod_societ': self.cod_societ,
            'cod_zona': self.cod_zona,
            'nr_nod': self.nr_nod,
            'serie_nod': self.serie_nod,
            'POINT_X': self.POINT_X,
            'POINT_Y': self.POINT_Y,
            'POINT_Z': self.POINT_Z,
            'POINT_M': self.POINT_M
        }

class RamuriNoduriParser(BaseParser):
    def __init__(self, layer: QgsVectorLayer):
        super().__init__(layer, "RAMURI_NODURI")
        
        self.column_names = ['Join_Count', 'material', 'CIR', 'cod_materi', 'Pozare', 'ID', 'lungime', 'denumire', 'stare_cone', 'cod_societ', 'cod_zona', 'nr_nod', 'serie_nod', 'POINT_X', 'POINT_Y', 'POINT_Z', 'POINT_M']

        self.validation_rules: Dict[str, Any] = {
            'material': {
                'rule': 'str',
                'required': True
            },
            'CIR': {
                'rule': ['0'],
                'required': True
            },
            'cod_materi': {
                'rule': 'str',
                'required': True
            },
            'Pozare': {
                'rule': 'str',
                'required': True
            },
            'TARGET_FID': {
                'rule': 'str',
                'required': True
            },
            'lungime_': {
                'rule': 'str',
                'required': True
            },
            'denumire': {
                'rule': 'str',
                'required': True
            },
            'stare_cone': {
                'rule': ['C - inchis', 'A - deschis'],
                'required': True
            },
            'cod_societ': {
                'rule': 'str',
                'required': True
            },
            'cod_zona': {
                'rule': 'str',
                'required': True
            },
            'nr_nod': {
                'rule': 'str',
                'required': True
            },
            'serie_nod': {
                'rule': 'str',
                'required': True
            }
        }

        # Retrieve the layer named "ramuri_noduri" from the current QGIS project
        self.layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == "RAMURI_NODURI":
                self.layer = layer
                break

        if self.layer is None:
            raise ValueError("Layer named 'RAMURI_NODURI' not found in the project.")

        self.ramuri_data = []
        self.invalid_elements = []

    def parse(self):
        for feature in self.layer.getFeatures():
            if feature['Material']:
                cod_material = re.search(r'[A-Z](\d+)', feature['Material']).group(1)
            else:
                cod_material = None
            
            ramura_nod = RamuriNoduri(
                Join_Count=1,
                internal_id=feature.id(),
                material=feature['Material'] if feature['Material'] not in [None, 'NULL', 'nan'] else None,
                CIR=feature['CIR'] if feature['CIR'] not in [None, 'NULL', 'nan'] else None,
                cod_materi = cod_material,
                Pozare=feature['Material'][0] if feature['Material'] not in [None, 'NULL', 'nan'] else None,
                ID=feature['TARGET_FID'],
                lungime=round(feature['lungime_']),
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
            # QgsMessageLog.logMessage(f"Feature {ramura_nod.denumire} parsed successfully with data {ramura_nod.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.ramuri_data.append(ramura_nod)
        
        self.data = self.ramuri_data

    def get_ramuri_data(self):
        return self.ramuri_data
    
    def get_name(self):
        return "RAMURI_NODURI"
