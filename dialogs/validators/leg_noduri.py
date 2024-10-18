from typing import Dict, Any

class LegNoduri:
    def __init__(self):
        self. mapping = {
            'Join_Count': 'Join_Count',
            'ID': None,
            'denumire': 'Denumire',
            'stare_cone': 'SerieConex',
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