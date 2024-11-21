# -*- coding: utf-8 -*-
"""
/***************************************************************************
 EnelAssist
                                 A QGIS plugin
 Helps in assisting for Enel
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-10-08
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Ionela
        email                : ioneladumitra@yahoo.ro
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from pathlib import Path

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsMessageLog, Qgis

import os

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .dialogs.process_dialog import ProcessDialog
from .dialogs.validate_dialog import ValidateDialog
from .dialogs.generate_dialog import GenerateExcelDialog
from .dialogs.preprocess_dialog import PreProcessDialog
from .dialogs.preverify_dialog import PreVerifyDialog
from .dialogs.preprocess_pct_vrtx_dialog import PreProcessPctVrtxDialog
import os.path


class EnelAssist:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'EnelAssist_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&EnelAssist')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None


    @staticmethod
    def plugin_path(*args) -> Path:
        """ Return the path to the plugin root folder or file. """
        path = Path(__file__).resolve().parent
        for item in args:
            path = path.joinpath(item)
        return path


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('EnelAssist', message)


    def add_action(
        self,
        name,
        text,
        callback=None,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
        icon_path=None,
        shortcut=None,):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.setEnabled(enabled_flag)

        if callback is not None:
            action.triggered.connect(callback)
            action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
            
        if shortcut is not None:
            action.setShortcut(shortcut)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.toolbar = self.iface.addToolBar('EnelAssist')
        self.toolbar.setObjectName('EnelAssist')
        self.toolbar.setMovable(True)
        
        self.add_action(
            "Pre-Process",
            text=self.tr(u'Pre-Process'),
            callback=self.pre_process,
            parent=self.iface.mainWindow(),
            icon_path= str(self.plugin_path('icons/preprocess.png'))
            )
        
        self.add_action(
            "Pre-verify",
            text=self.tr(u'Pre-verify'),
            callback=self.pre_verify,
            parent=self.iface.mainWindow(),
            icon_path= str(self.plugin_path('icons/verify.png'))
        )
        
        self.add_action(
            "Pre-process pct_vrtx",
            text=self.tr(u'Pre-process pct_vrtx'),
            callback=self.pre_process_pct_vrtx,
            parent=self.iface.mainWindow(),
            icon_path= str(self.plugin_path('icons/vertex.png'))
        )

        self.add_action(
            "Process",
            text=self.tr(u'Process'),
            callback=self.process,
            parent=self.iface.mainWindow(),
            icon_path= str(self.plugin_path('icons/process.png'))
            )
        
        self.add_action(
            "Validate",
            text=self.tr(u'Validate'),
            callback=self.validate,
            parent=self.iface.mainWindow(),
            icon_path= str(self.plugin_path('icons/validate.png'))
        )
        
        self.add_action(
            "Generate Excel",
            text=self.tr(u'Generate Excel'),
            callback=self.generate_excel,
            parent=self.iface.mainWindow(),
            icon_path= str(self.plugin_path('icons/excel.png'))
        )
        
        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&Enel Assist'), action)
            self.toolbar.removeAction(action)
        del self.toolbar
        
    def pre_process(self):
        """
        - Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou > NODURI
        - Extract Vertices - ReteaJT > VERTICES
        - Difference - VERTICES, NODURI > DIFFERENCE
        - Add Geometry Attributes - DIFFERENCE > pct_vrtx
        - Delete rows without coordinates (point_x, point_y)
        """
        QgsMessageLog.logMessage("Entering pre-process...", "EnelAssist", level=Qgis.Info)
        PreProcessDialog().exec_()
        
    def pre_verify(self):
        """
        - Automated layer retrieval
        - Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou > NODURI
        - Merge Vector Layers - RAMURI
        - Join Attributes by Location - RAMURI_NODURI
        - Adauga coloana Count_ID - RAMURI_NODURI
        - Rename layers without the numbers
        """
        QgsMessageLog.logMessage("Entering pre-verify...", "EnelAssist", level=Qgis.Info)
        PreVerifyDialog().exec_()
        
    def pre_process_pct_vrtx(self):
        """
        - Merge Vector Layers - InceputLinie, Cutii, Stalpi, BMPnou > NODURI
        - Snap geometries to layer - ReteaJT, NODURI // Tolerance - 1, Behavior - End points to end points only > ReteaJT (overwrite)
        - Merge Vector Layers - BMPnou, Numar_Postal > LEG_NODURI
        - Snap geometries to layer - NOD_NRSTR, LEG_NODURI // Tolerance - 1, Behavior - End points to end points only > NOD_NRSTR (overwrite)
        - Snap geometries to layer - AUXILIAR, ReteaJT // Tolerance - 1, Behavior - Prefer alignment nodes, don't insert new vertices > AUXILIAR (overwrite)
        """
        QgsMessageLog.logMessage("Entering pre-process pct_vrtx...", "EnelAssist", level=Qgis.Info)
        PreProcessPctVrtxDialog().exec_()
        
    def process(self):
        """
        - Calculate geometry for all - X, Y coord line start and end >> field calculator - x(start_point($geometry)) etc.
        - ReteaJT - Add 'lungime', 'id' columns - double
            > lungime - field calculator - $length
            > id - field calculator - FID - OK
        - layer_nod_nrstr - Add 'id' - double, Delete GlobalId (raman doar ID si FID)
            > id - field calculator - FID - OK
        - Merge Vector Layers - inc_linii / cutii / stalpi / bmpnou > folder - NODURI
        - Merge Vector Layers - layer_reteajt > folder - RAMURI
        - Join Attributes by Location - ramuri > noduri - ONE TO MANY > RAMURI_NODURI
        - Join Attributes by Location - layer_nod_nrstr > noduri - ONE TO ONE > LEG_NODURI
        - Merge Vector Layers - inc_linii, cutii, stalpi, bpmnou, auxiliar, pct_vrtx > folder - NODURI_AUX_...
        - Join Attributes by Location - ramuri > noduri_aux - ONE TO MANY > RAMURI_AUX
        - ramuri_aux - Add 'SEI' column - text
            > Noduri ? 3 : 1

        - for each Join Attributes by Location - add Join_Count column with all values '1'
        """
        QgsMessageLog.logMessage("Entering preprocess...", "EnelAssist", level=Qgis.Info)
        ProcessDialog().exec_()
    
    
    def validate(self):
        """
        - Validate the attribute tables columns with the corresponding rules:
            > correct num of columns and names
            > correct data
        """
        QgsMessageLog.logMessage("Entering validate...", "EnelAssist", level=Qgis.Info)
        ValidateDialog().exec_()
    
    
    def generate_excel(self):
        """
        - auxiliar > AUXILIAR
        - bmpnou > BMP
        - cutii > CD
        - stalpi > DERIV_CT
        - inc_linii > INC_LINI
        - leg_noduri > LEG_NODURI
        - leg_nrstr > LEG_NRSTR
        - numar_postal > NR_STR
        - ramuri_noduri > RAMURI_NODURI
        """
        QgsMessageLog.logMessage("Entering generate excel...", "EnelAssist", level=Qgis.Info)
        GenerateExcelDialog().exec_()
        pass
    



