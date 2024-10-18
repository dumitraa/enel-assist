from typing import Dict, Any

class IncLini:
    def __init__(self):
        self.mapping = {
            'denumire': 'Denumire',
            'stare_cone': 'SerieConex',
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
                'rule': ['0'],
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
            "Observatii": {
                'rule': 'str',
                'required': True
            }
        }