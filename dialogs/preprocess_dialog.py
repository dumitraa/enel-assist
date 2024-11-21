'''
LAYERS NEEDED = ['InceputLinie', 'Cutii', 'Stalpi', 'BMPnou', 'ReteaJT', 'NOD_NRSTR', 'AUXILIAR', 'pct_vrtx', "Numar_Postal"]

STEP 1. Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou > NODURI
> merge from process_dialog.py
STEP 2. Extract Vertices - ReteaJT > VERTICES
STEP 3. Difference - VERTICES, NODURI > DIFFERENCE
STEP 4. Add Geometry Attributes - DIFFERENCE > pct_vrtx
STEP 5. Delete rows without coordinates (point_x, point_y)

'''

import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem, QApplication, QMessageBox
from qgis.core import (QgsExpression, QgsExpressionContext, QgsExpressionContextUtils,  # type: ignore
                       QgsField, QgsProject, QgsMessageLog, Qgis, QgsVectorLayer)

class PreProcessDialog(QDialog):
    pass