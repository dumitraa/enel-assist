from typing import Dict, Any

class RamuriNoduri:
    def __init__(self):
        self.mapping = {
            'Join_Count': 'Join_Count',
            'material': 'Material', # e.g. C513 // 3x16Al+25Al
            'CIR': 'CIR',
            'cod_materi': 'Material', # e.g. 513
            'Pozare': 'Material', # e.g. C
            'ID': None,
            'lungime': 'Lungime',
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
            'material': {
                'rule': 'str',
                'required': True
            },
            'CIR': {
                'rule': ['0'],
                'required': True
            },
            'cod_materi': {
                'rule': 'str', # has to be 2nd char to up until '//' of material
                'required': True
            },
            'Pozare': {
                'rule': 'str', # has to be 1st char of material
                'required': True
            },
            'ID': {
                'rule': 'str', # has to be in 2s, so it's 0 0 1 1 2 2 etc
                'required': True
            },
            'lungime': {
                'rule': 'str', # has to be a rounded number
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