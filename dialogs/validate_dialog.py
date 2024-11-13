import os

from qgis.core import QgsVectorLayer, QgsProject, QgsMessageLog # type: ignore
from PyQt5.QtWidgets import QComboBox, QLineEdit, QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QFrame
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtCore import Qt


from .validators.auxiliar import AuxiliarParser
from .validators.bmp import BMPParser
from .validators.cd import CdParser
from .validators.inc_lini import IncLiniParser
from .validators.deriv_ct import DerivCTParser
from .validators.leg_noduri import LegNoduriParser
from .validators.ramuri_noduri import RamuriNoduriParser
from .validators.ramuri_aux_vrtx import RamuriAuxVrtxParser
from .validators.nr_str import NrStrParser
from .validators.leg_nrstr import LegNrstrParser


class ShpProcessor:
    '''
    Class to process the shapefile (SHP) layers, validate them, and work with them in QGIS.
    '''
    def __init__(self, source_paths, validate=True):
        '''
        Constructor for the ShpProcessor class
        :param source_paths: List of paths to the source shapefile layers
        :return: None
        '''
        QgsMessageLog.logMessage("Initializing ShpProcessor with source paths", "EnelAssist", 0)
        self.source_paths = source_paths
        self.parsers = []
        self.invalid_elements = []
        self.load_shp_layers()
        if validate:
            self.validate_layers()
        QgsMessageLog.logMessage("ShpProcessor initialized", "EnelAssist", 0)
    
    def load_shp_layers(self, validate=False):
        '''
        Load the SHP layers from the QGIS project, parse them, and store the parsers in a list
        :return: None
        '''
        QgsMessageLog.logMessage("Loading SHP layers from QGIS project", "EnelAssist", 0)
        for layer in QgsProject.instance().mapLayers().values():
            QgsMessageLog.logMessage(f"Processing layer: {layer.name()}", "EnelAssist", 0)
            if not isinstance(layer, QgsVectorLayer):
                continue
            
            layer_name = layer.name()
            # parse layers accordinging - AUXILIAR, Cutii (CD), InceputLinie, LEG_NODURI, LEG_NRSTR, Numar_Postal, RAMURI_NODURI, BMPnou, Stalpi (DerivCt)
            
            if layer_name.endswith("AUXILIAR"):
                parser = AuxiliarParser(layer)
            elif layer_name.endswith("BMPnou"):
                parser = BMPParser(layer)
            elif layer_name.endswith("Cutii"):
                parser = CdParser(layer)
            elif layer_name.endswith("InceputLinie"):
                parser = IncLiniParser(layer)
            elif layer_name.endswith("Stalpi"):
                parser = DerivCTParser(layer)
            elif layer_name.endswith("LEG_NODURI"):
                parser = LegNoduriParser(layer)
            elif layer_name.endswith("RAMURI_NODURI"):
                parser = RamuriNoduriParser(layer)
            elif layer_name.endswith("RAMURI_AUX_VRTX"):
                parser = RamuriAuxVrtxParser(layer)
            elif layer_name.endswith("LEG_NRSTR"):
                parser = LegNrstrParser(layer)
            elif layer_name.endswith("Numar_Postal"):
                parser = NrStrParser(layer)
            else:
                parser = None
                QgsMessageLog.logMessage(f"Layer {layer_name} not recognized. Skipping...", "EnelAssist", 1)
                
            
            if parser:
                parser.parse()
                self.parsers.append(parser)
                QgsMessageLog.logMessage(f"Parser for {layer_name} added", "EnelAssist", 0)
    
        QgsMessageLog.logMessage("Finished loading SHP layers", "EnelAssist", 0)
    
    def validate_layers(self):
        '''
        Validate the SHP layers and store the invalid elements in a list
        :return: None
        '''
        QgsMessageLog.logMessage(f"Initial invalids - {self.invalid_elements}", "EnelAssist", 0)
        QgsMessageLog.logMessage("Validating SHP layers", "EnelAssist", 0)
        self.invalid_elements = []
        for parser in self.parsers:
            QgsMessageLog.logMessage(f"Validating parser", "EnelAssist", 0)
            invalids = parser.validate()
            self.invalid_elements.append(invalids)
            # QgsMessageLog.logMessage(f"Validation completed for parser. Found {len(invalids)} invalid elements, {invalids}", "EnelAssist", 0)
        QgsMessageLog.logMessage("Finished validating all SHP layers", "EnelAssist", 0)

class ValidateDialog(QDialog):
    '''
    The main class for the GUI
    '''
    def __init__(self, parent=None):
        '''
        Constructor for the ValidateDialog class
        '''
        QgsMessageLog.logMessage("Initializing ValidateDialog", "EnelAssist", 0)
        super().__init__(parent if isinstance(parent, QtWidgets.QWidget) else None)
        self.setWindowTitle("Validare SHP")

        # Collecting SHP layers from the QGIS project
        source_paths = [layer.source() for layer in QgsProject.instance().mapLayers().values() if isinstance(layer, QgsVectorLayer)]
        if not source_paths:
            QgsMessageLog.logMessage("No SHP layers found in the project.", "EnelAssist", 2)

        # Initialize ShpProcessor with the collected source paths
        self.processor = ShpProcessor(source_paths)
        
        self.current_shp_index = 0
        self.current_element_page = 0
        self.global_updated_elements = []
        self.EL = 4
        self.visited_pages = set()
        self.total_pages = 0
        self.setup_styles()
        QgsMessageLog.logMessage("ValidateDialog initialized", "EnelAssist", 0)
    
    def calculate_total_pages(self):
        '''
        Calculate the total number of pages
        '''
        QgsMessageLog.logMessage("~~~~~~~~~~~~~~~~~~~~~~~ ENTERED Calculating total pages", "EnelAssist", 0)
        self.total_pages = 0
        for idx, parser in enumerate(self.processor.parsers):
            # find how many elements are invalid - invalidelements[idx]["layer_name"]
            total_elements = set()
            for element in self.processor.invalid_elements[idx]:
                total_elements.add(element.get('internal_id', ""))
            
            total_element_pages = len(total_elements) // self.EL
            QgsMessageLog.logMessage(f"********************** CALCULATED TOTAL ELEMENT PAGES: {total_element_pages} //// FROM {len(total_elements)} // EL {self.EL}", "EnelAssist", 0)
            total_element_pages += 1 if len(total_elements) % self.EL else 0
            self.total_pages += total_element_pages
            QgsMessageLog.logMessage(f"SHP {idx} has {total_element_pages} pages with {len(total_elements)} elements, which makes the number of elements per page {self.EL}", "EnelAssist", 0)
    
    def setup_styles(self):
        QgsMessageLog.logMessage("Setting up enhanced styles for ValidateDialog", "EnelAssist", 0)
        style_sheet = """
            QWidget {
                background-color: #ecf0f1;
                color: #2c3e50;
                font-family: Helvetica;
                font-size: 12pt;
            }
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                border: none;
                padding: 10px 15px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QLineEdit, QComboBox {
                font-size: 12pt;
                padding: 5px;
                border: 1px solid #2c3e50;
                border-radius: 4px;
            }
            QLabel {
                padding: 5px;
                font-size: 11pt;
                color: #34495e;
            }
            QCheckBox {
                font-size: 11pt;
            }
            QFrame {
                background-color: #bdc3c7;
                height: 2px;
            }
        """
        self.setStyleSheet(style_sheet)
        self.init_validator_gui()
    
    def init_validator_gui(self):
        self.layout = QVBoxLayout(self)

        # Invalid elements label at the top
        self.invalid_elements_var = QLabel(f"Elemente invalide pentru SHP [placeholder]")
        self.invalid_elements_var.setAlignment(Qt.AlignCenter)
        self.invalid_elements_var.setStyleSheet("font-size: 14pt; font-weight: bold; color: #e74c3c;")
        self.layout.addWidget(self.invalid_elements_var)

        # Fields frame for displaying invalid elements
        self.fields_frame = QVBoxLayout()
        fields_frame_container = QFrame()
        fields_frame_container.setLayout(self.fields_frame)
        fields_frame_container.setStyleSheet("background-color: #ffffff; border: 1px solid #bdc3c7; padding: 10px;")
        self.layout.addWidget(fields_frame_container)

        # Buttons frame for navigation and actions
        self.buttons_frame = QHBoxLayout()
        self.layout.addLayout(self.buttons_frame)

        # Previous SHP button
        self.prev_button = QPushButton("Anterior")
        self.prev_button.clicked.connect(self.prev_shp)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.buttons_frame.addWidget(self.prev_button)

        # Previous element page button
        self.prev_elem_button = QPushButton("<")
        self.prev_elem_button.clicked.connect(self.prev_element_page)
        self.prev_elem_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.buttons_frame.addWidget(self.prev_elem_button)

        # Save button
        done_button = QPushButton("Salvează")
        done_button.clicked.connect(self.done_action)
        done_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.buttons_frame.addWidget(done_button)
        self.done_button = done_button

        # Next element page button
        self.next_elem_button = QPushButton(">")
        self.next_elem_button.clicked.connect(self.next_element_page)
        self.next_elem_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.buttons_frame.addWidget(self.next_elem_button)

        # Next SHP button
        self.next_button = QPushButton("Următor")
        self.next_button.clicked.connect(self.next_shp)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.buttons_frame.addWidget(self.next_button)

        # Page indicator label at the bottom
        self.page_indicator_label = QLabel("1/1")
        self.page_indicator_label.setAlignment(Qt.AlignCenter)
        self.page_indicator_label.setStyleSheet("font-size: 12pt; font-weight: bold; margin-top: 15px; color: #2c3e50;")
        self.layout.addWidget(self.page_indicator_label)

        # Display invalid elements
        self.show_invalid_elements()

        QgsMessageLog.logMessage("Second GUI layout initialized with enhanced styling", "EnelAssist", 0)

    def show_invalid_elements(self):
        self.calculate_total_pages()
        
        QgsMessageLog.logMessage(f"Showing invalid elements for SHP index {self.current_shp_index}", "EnelAssist", 0)
        if not self.processor or not self.processor.parsers:
            QgsMessageLog.logMessage("No SHP processors found. Exiting show_invalid_elements.", "EnelAssist", 2)
            return

        if self.current_shp_index >= len(self.processor.invalid_elements):
            QgsMessageLog.logMessage("Current SHP index out of range. Exiting show_invalid_elements.", "EnelAssist", 2)
            return

        for i in reversed(range(self.fields_frame.count())):
            widget = self.fields_frame.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        
        self.widget_dict = {}
        
        QgsMessageLog.logMessage(f"Current SHP index: {self.current_shp_index}, Current element page: {self.current_element_page}", "EnelAssist", 0)
        invalid_elements = self.processor.invalid_elements[self.current_shp_index]
        
        if not invalid_elements:
            self.invalid_elements_var.setText(f"Felicitări! Toate elementele din SHP sunt valide!")
            self.visited_pages.add((self.current_shp_index, self.current_element_page))
            QgsMessageLog.logMessage("All elements in SHP are valid", "EnelAssist", 0)
            return
        else:
            self.invalid_elements_var.setText(f"Elemente invalide pentru SHP {invalid_elements[0].get('layer_name')}")
            # QgsMessageLog.logMessage(f"Invalid elements found for SHP - {invalid_elements}", "EnelAssist", 1)

        # Determine whether to show or hide next/prev buttons
        if len(invalid_elements) > self.EL:
            self.prev_elem_button.setVisible(True)
            self.next_elem_button.setVisible(True)
        else:
            self.prev_elem_button.setVisible(False)
            self.next_elem_button.setVisible(False)

        start_index = self.current_element_page * self.EL
        end_index = start_index + self.EL
        
        grouped_elements = []
        current_group = []
        last_element_id = None
        
        for element in invalid_elements:
            element_id = element.get('internal_id', "")
            if element_id != last_element_id:
                if current_group:
                    grouped_elements.append(current_group)
                current_group = [element]
                last_element_id = element_id
            else:
                current_group.append(element)
        if current_group:
            grouped_elements.append(current_group)
            
        total_pages = (len(grouped_elements) + self.EL - 1) // self.EL
        QgsMessageLog.logMessage(f"Total pages: {total_pages}", "EnelAssist", 0)
        self.page_indicator_label.setText(f"{self.current_element_page + 1}/{total_pages}")
        page_groups = grouped_elements[start_index:end_index]

        if self.current_element_page == 0:
            self.prev_elem_button.setDisabled(True)
        else:
            self.prev_elem_button.setDisabled(False)

        if end_index >= len(grouped_elements):
            self.next_elem_button.setDisabled(True)
        else:
            self.next_elem_button.setDisabled(False)
            
        if self.current_shp_index != 0:
            self.prev_button.setDisabled(False)
            
        if self.current_shp_index == len(self.processor.parsers) - 1:
            self.next_button.setDisabled(True)
        else:
            self.next_button.setDisabled(False)
            
        self.visited_pages.add((self.current_shp_index, self.current_element_page))
        self.check_all_pages_visited()

        for group in page_groups:
            for element in group:
                tag = element.get('tag')
                friendly_name = element.get('friendly_name')
                error = element.get('error')
                suggestions = element.get('suggestions', [])
                ignored = element.get('ignored', "")
                element_id = element.get('internal_id', "")
                current_value = element.get('current_value', "")

                # Horizontal Layout for each row
                row_layout = QHBoxLayout()

                # Checkbox for ignoring error
                checkbox = QCheckBox(f"Ignora eroarea")
                checkbox.setChecked(ignored == "ignored")
                row_layout.addWidget(checkbox)
                self.widget_dict[(element_id, tag, 'ignore')] = checkbox

                # Label with element details
                label = QLabel(f"{friendly_name}: {error} ")
                row_layout.addWidget(label)

                # Suggestions or entry field
                if isinstance(suggestions, list) and suggestions:
                    combobox = QComboBox()
                    combobox.addItems(suggestions)
                    if current_value in suggestions:
                        combobox.setCurrentText(current_value)
                    row_layout.addWidget(combobox)
                    self.widget_dict[(element_id, tag)] = combobox
                else:
                    entry = QLineEdit(current_value)
                    QgsMessageLog.logMessage(f"Setting current value for element {element_id} to {current_value}", "EnelAssist", 0)
                    row_layout.addWidget(entry)
                    self.widget_dict[(element_id, tag)] = entry

                # Adding the row to the fields frame
                self.fields_frame.addLayout(row_layout)

                # Separator between rows
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                self.fields_frame.addWidget(separator)

    def check_all_pages_visited(self):
        visited_page_count = len(self.visited_pages)
        QgsMessageLog.logMessage(f"Visited pages: {visited_page_count}, Total pages: {self.total_pages}", "EnelAssist", 0)

        if visited_page_count == self.total_pages:
            QgsMessageLog.logMessage("All pages have been visited!", "EnelAssist", 0)
            self.done_button.setEnabled(True)  # Enabling the button
        else:
            QgsMessageLog.logMessage(f"Not all pages have been visited yet. Pages visited: {visited_page_count} vs Total pages: {self.total_pages}", "EnelAssist", 0)
            self.done_button.setEnabled(False)  # Disabling the button

    def prev_element_page(self):
        self.save_current_shp_elements() 
        if self.current_element_page > 0:
            self.current_element_page -= 1
            self.show_invalid_elements()

    def next_element_page(self):
        self.save_current_shp_elements()
        self.total_pages = (len(self.processor.invalid_elements[self.current_shp_index]) + self.EL - 1) // self.EL
        if self.current_element_page < self.total_pages - 1:
            self.current_element_page += 1
            self.show_invalid_elements()

    def prev_shp(self):
        self.save_current_shp_elements()
        if self.current_shp_index > 0:
            self.current_shp_index -= 1
            self.current_element_page = 0
            self.show_invalid_elements()

    def next_shp(self):
        self.save_current_shp_elements()
        if self.current_shp_index < len(self.processor.parsers) - 1:
            self.current_shp_index += 1
            self.current_element_page = 0
            self.show_invalid_elements()

    def save_current_shp_elements(self):
        """Save the elements for the current shapefile only."""
        current_elements = self.processor.invalid_elements[self.current_shp_index]
        updated_elements = []

        for element in current_elements:
            tag = element.get('tag', "") 
            element_id = element.get('internal_id', "")

            # Handle 'ignore' checkbox
            if (element_id, tag, 'ignore') in self.widget_dict:
                ignore_checkbox = self.widget_dict[(element_id, tag, 'ignore')]
                if ignore_checkbox.isChecked():
                    element['ignored'] = "ignored"
                else:
                    element.pop('ignored', None)

            # Update the element based on widget values
            if (element_id, tag) in self.widget_dict:
                widget = self.widget_dict[(element_id, tag)]

                if isinstance(widget, QComboBox):
                    selected_value = widget.currentText()
                    if selected_value not in element.get('suggestions', []):
                        element['suggestions'].append(selected_value)
                    element['current_value'] = selected_value

                elif isinstance(widget, QLineEdit):
                    entered_value = widget.text()
                    element['current_value'] = entered_value

                updated_elements.append({
                    'element_id': element_id,
                    'tag': tag,
                    'current_value': element['current_value']
                })

        self.global_updated_elements = updated_elements

    def save_all_shp_elements(self):
        """Apply all the updates to all SHP files."""
        for parser, invalid_elements in zip(self.processor.parsers, self.processor.invalid_elements):
            for element in invalid_elements:
                    if element.get('ignored', "") == "ignored":
                        continue
                
                    element_id = element.get('internal_id', "")
                    tag = element.get('tag')
                    current_value = element.get('current_value', None)
                    
                    QgsMessageLog.logMessage(f"Updating parser with element {element_id}, tag {tag}, value {current_value}", "EnelAssist", 0)
                    
                    if element_id is not None and element_id != "" and tag:
                        parser.update_feature(element_id, tag.lower(), current_value)
                    else:
                        QgsMessageLog.logMessage(f"Element {element_id} has no tag -- {tag} which is true? {tag == None}.  what about element_id? {element_id == None}", "EnelAssist", 1)
                
            parser.save_to_layer()

    def done_action(self):
        if len(self.processor.parsers) == 1:
            self.save_current_shp_elements()
            self.accept()
        self.save_all_shp_elements()
        self.accept()
