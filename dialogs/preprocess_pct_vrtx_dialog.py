'''
LAYERS NEEDED = ['InceputLinie', 'Cutii', 'Stalpi', 'BMPnou', 'ReteaJT', 'NOD_NRSTR', 'AUXILIAR', 'pct_vrtx', "Numar_Postal"]

STEP 1. Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou > NODURI
> merge from process_dialog.py
STEP 2. Snap geometries to layer - ReteaJT, NODURI // Tolerance - 1, Behavior - End points to end points only > ReteaJT (overwrite)
STEP 3. Merge Vector Layers - BMPnou, Numar_Postal > LEG_NODURI
> merge from process_dialog.py
STEP 4. Snap geometries to layer - NOD_NRSTR, LEG_NODURI // Tolerance - 1, Behavior - End points to end points only > NOD_NRSTR (overwrite)
STEP 5. Snap geometries to layer - AUXILIAR, ReteaJT // Tolerance - 1, Behavior - Prefer alignment nodes, don't insert new vertices > AUXILIAR (overwrite)

'''

import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QPushButton, QFileDialog, QLabel, QListWidget, QListWidgetItem, QApplication, QMessageBox
from qgis.core import (QgsExpression, QgsExpressionContext, QgsExpressionContextUtils,  # type: ignore
                          QgsField, QgsProject, QgsMessageLog, Qgis, QgsVectorLayer)

class PreProcessPctVrtxDialog(QDialog):
    pass