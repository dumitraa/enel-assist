from typing import Dict, Any

class BMP:
    def __init__(self):    
        self.mapping = {
            'denumire': 'Denumire',
            'serie_cont': 'SerieConto',
            'stare_cone': 'SerieConex',
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
                'rule': 'C - inchis',
                'required': True
            },
            "nr_nod": {
                'rule': 'str',
                'required': False
            },
            "serie_nod": {
                'rule': '7',
                'required': True
            }
        }