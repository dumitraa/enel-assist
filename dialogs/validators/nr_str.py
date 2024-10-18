from typing import Dict, Any

class NrStr:
    def __init__(self):
        self.mapping = {
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
            },
        }