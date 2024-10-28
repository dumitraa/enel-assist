import qgis
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis
from typing import Dict, Any, List
iface = qgis.utils.iface

from .base_parser import BaseParser

class LegNrstr:
    def __init__(self, internal_id, friendly_id, nr_strada, denumire_a, tip_artera, progresiv_, denumire_c, cod_strada, POINT_X, POINT_Y, POINT_Z, POINT_M, ignored=False):
        self.internal_id = internal_id
        self.friendly_id = friendly_id
        self.nr_strada = nr_strada
        self.denumire_a = denumire_a
        self.tip_artera = tip_artera
        self.progresiv_ = progresiv_
        self.denumire_c = denumire_c
        self.cod_strada = cod_strada
        self.POINT_X = POINT_X
        self.POINT_Y = POINT_Y
        self.POINT_Z = POINT_Z
        self.POINT_M = POINT_M
        self.ignored = ignored

    def to_dict(self):
        return {
            'internal_id': self.internal_id,
            'friendly_id': self.friendly_id,
            'nr_strada': self.nr_strada,
            'denumire_a': self.denumire_a,
            'tip_artera': self.tip_artera,
            'progresiv_': self.progresiv_,
            'denumire_c': self.denumire_c,
            'cod_strada': self.cod_strada,
            'POINT_X': self.POINT_X,
            'POINT_Y': self.POINT_Y,
            'POINT_Z': self.POINT_Z,
            'POINT_M': self.POINT_M,
            'ignored': self.ignored
        }

class LegNrstrParser(BaseParser):
    def __init__(self, layer: QgsVectorLayer):
        super().__init__(layer, "LEG_NRSTR")
        
        self.mapping = {
            'Join_Count': 'Join_Count',
            'ID': None,
            'nr_strada': 'NrStrada',
            'denumire_a': 'DenumireAr',
            'tip_artera': 'TipArtera',
            'progresiv_': 'ProgresivC',
            'denumire_c': 'DenumireCl',
            'cod_strada': 'cod_strada',
            'POINT_X': 'POINT_X',
            'POINT_Y': 'POINT_Y',
            'POINT_Z': 'POINT_Z',
            'POINT_M': 'POINT_M'
        }

        self.validation_rules: Dict[str, Any] = {
            'Join_Count': {
                'rule': ['1'],
                'required': True
            },
            'ID': {
                'rule': 'str',
                'required': True
            },
            'nr_strada': {
                'rule': 'str',
                'required': True
            },
            'denumire_a': {
                'rule': 'str',
                'required': True
            },
            'tip_artera': {
                'rule': 'str',
                'required': True
            },
            'cod_strada': {
                'rule': 'str',
                'required': False
            }
        }

        # Retrieve the layer named "leg_nrstr" from the current QGIS project
        self.layer = None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() == "LEG_NRSTR":
                self.layer = layer
                break

        if self.layer is None:
            raise ValueError("Layer named 'LEG_NRSTR' not found in the project.")

        self.leg_nrstr_data = []
        self.invalid_elements = []

    def parse(self):
        for feature in self.layer.getFeatures():
            leg_nrstr_data = LegNrstr(
                internal_id=feature.id(),
                friendly_id=feature.id() + 1,
                nr_strada=feature['NrStrada'] if feature['NrStrada'] not in [None, 'NULL', 'nan'] else None,
                denumire_a=feature['DenumireAr'] if feature['DenumireAr'] not in [None, 'NULL', 'nan'] else None,
                tip_artera=feature['TipArtera'] if feature['TipArtera'] not in [None, 'NULL', 'nan'] else None,
                progresiv_=feature['ProgresivC'] if feature['ProgresivC'] not in [None, 'NULL', 'nan'] else None,
                denumire_c=feature['DenumireCl'] if feature['DenumireCl'] not in [None, 'NULL', 'nan'] else None,
                cod_strada=feature['cod_strada'] if feature['cod_strada'] not in [None, 'NULL', 'nan'] else None,
                POINT_X=feature['POINT_X'] if feature['POINT_X'] not in [None, 'NULL', 'nan'] else None,
                POINT_Y=feature['POINT_Y'] if feature['POINT_Y'] not in [None, 'NULL', 'nan'] else None,
                POINT_Z=feature['POINT_Z'] if feature['POINT_Z'] not in [None, 'NULL', 'nan'] else None,
                POINT_M=feature['POINT_M'] if feature['POINT_M'] not in [None, 'NULL', 'nan'] else None
            )
            QgsMessageLog.logMessage(f"Feature {leg_nrstr_data.nr_strada} parsed successfully with data {leg_nrstr_data.to_dict()}", "EnelAssist", level=Qgis.Info)
            self.leg_nrstr_data.append(leg_nrstr_data)
            
        self.data = self.leg_nrstr_data

    def get_leg_nrstr_data(self) -> List[LegNrstr]:
        return self.leg_nrstr_data
