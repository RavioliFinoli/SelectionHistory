import sys
import os

import pymel.core as pm
import maya.OpenMayaUI as omui
import maya.OpenMaya as OpenMaya
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtUiTools
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile
from shiboken2 import wrapInstance

def shorten_string(string, max_length_including_dots=20):
    newString = string
    if (len(string) > max_length_including_dots):
        newString = newString[:max_length_including_dots-3]
        newString+= "..."
    return newString

def get_selection_as_string(selection):
    string = ", ".join([str(s) for s in selection])
    return string


class SelectionItem(QtWidgets.QListWidgetItem):
    def __init(self, *args, **kwargs):
        super(SelectionItem, self).__init__(*args, **kwargs)
        self.key = ""
        self.selection = []
        
    def setKey(self, string):
        self.key = string
        
    def setSel(self, sel):
        self.selection = sel
        
    def getSelection(self):
        return self.selection

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

class CreateSelectionHistoryUI(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(CreateSelectionHistoryUI, self).__init__(*args, **kwargs)
        self.setWindowTitle("Selection History v1.0")
        self.initUI()
        self.callback_id = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.cb_selection_changed)
        self.setParent(maya_main_window())
        self.setWindowFlags(QtCore.Qt.Window)
        
        self.selected = ""
        self.selected_saved = ""
        self.save_names = []
        self.last_selection = []
        self.ignore_next_selection = False
        
    def cb_selection_changed(self, *args, **kwargs):
        if not self.ignore_next_selection:
            current_selection = pm.ls(sl=True, flatten=True)
            min_elements_required = self.ui.include_single_checkbox.isChecked() and 1 or 2
            
            if (len(current_selection) >= min_elements_required):
                current_selection = pm.ls(sl=True, flatten=False)
                if not (set(self.last_selection) == set(current_selection)):
                    self.last_selection = current_selection
                    selection_string = get_selection_as_string(current_selection)
                    count = self.ui.selection_history_list.count()
                    
                    item = SelectionItem(selection_string)
                    if (count >= self.ui.max_history.value()):
                        item = self.ui.selection_history_list.takeItem(count-1)
                        item.setText(selection_string)            

                    item.setKey(selection_string)
                    item.setSel(current_selection)
                    
                    self.ui.selection_history_list.insertItem(0, item)
                    self.layout().update()
                    
        else: self.ignore_next_selection = False
    
    def initUI(self):     
        loader = QUiLoader()   
        
        splitPath = os.path.realpath(__file__).split("\\")
        uiPath = "/".join(splitPath[:-1]) + "/selection_history.ui"
        
        file = QFile(uiPath)      
        file.open(QFile.ReadOnly)        
        self.ui = loader.load(file)     
        file.close()
        
        #Init ui 
        self.ui.closeEvent = self.closeEvent
        self.ui.setParent(maya_main_window())
        self.ui.setWindowFlags(QtCore.Qt.Window)
        self.ui.show()
        self.setCentralWidget(self.ui)
        
        #Init signals
        self.ui.selection_history_list.currentItemChanged.connect(self.on_item_changed)
        self.ui.selection_history_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.ui.saved_selections_list.currentItemChanged.connect(self.on_item_changed_saved)
        self.ui.saved_selections_list.itemDoubleClicked.connect(self.on_item_double_clicked_saved)
        self.ui.export_button.clicked.connect(self.on_export)
        self.ui.import_button.clicked.connect(self.on_import)
        self.ui.save_button.clicked.connect(self.on_save)
        self.ui.clear_history_button.clicked.connect(self.on_clear)
        self.ui.clear_saved_button.clicked.connect(self.on_clear_saved)

    def dockCloseEventTriggered(self):
        OpenMaya.MMessage.removeCallback(self.callback_id)
        print("Closed")

    def closeEvent(self, event):
        #remove callback and close window
        print("Closed.")
        OpenMaya.MMessage.removeCallback(self.callback_id)
        event.accept()
    
    def on_export(self):
        count = self.ui.saved_selections_list.count()
        if count == 0:
            print("There is nothing to export.")
        else:        
            fileName = QtWidgets.QFileDialog.getSaveFileName(self, ("Export Selection"), self.file_dir, ("Text Files (*.txt)"))
            if (fileName[0]):
                export_file = open(fileName[0], "w+")
                reversed_names = self.save_names[::-1]

                for i in range(count):
                    name = reversed_names[i]
                    item = self.ui.saved_selections_list.item(i)
                    selection_string = "|".join(str(s) for s in item.getSelection())
                    export_file.write(name + "|")
                    export_file.write(selection_string + "\n")
                export_file.close()
        
    def on_import(self):   
        fileName = QtWidgets.QFileDialog.getOpenFileName(self, ("Import Selection"), self.file_dir, ("Text Files (*.txt)"))
        
        if (fileName[0]):
            import_file = open(fileName[0], "r")
                
            selections = import_file.readlines()
            for selection in selections[::-1]:
                split_selection = selection.split('|')
                name = split_selection[0]
                selection_string = get_selection_as_string(split_selection[1:])
                
                item = SelectionItem(name)
                item.setKey(selection_string)
                item.setSel(split_selection[1:])
                self.ui.saved_selections_list.insertItem(0, item)

            import_file.close()
    
    def on_save(self):
        name = self.ui.lineEdit.text()
        selection = pm.ls(sl=True, flatten=False)
        print(selection)
        if selection:
            selection_string = get_selection_as_string(selection)
            
            if not name:
                name = get_selection_as_string(selection)
            
            proper_name = self.get_proper_name(name)
            

            item = SelectionItem(proper_name)
            item.setKey(selection_string)
            item.setSel(selection)
            self.ui.saved_selections_list.insertItem(0, item)
            self.save_names.append(proper_name)
        
    def on_load(self):
        #self.ui.selection_history_list.takeItem(self.ui.selection_history_list.currentRow())
        pm.select(self.selected.getSelection())
        
    def on_load_saved(self):
        #self.ui.selection_history_list.takeItem(self.ui.selection_history_list.currentRow())
        pm.select(self.selected_saved.getSelection())
    
    def on_clear(self):
        self.ui.selection_history_list.clear()
        self.last_selection = []
    
    def on_clear_saved(self):
        self.ui.saved_selections_list.clear()
        
    def on_item_changed(self):            
        self.selected = self.ui.selection_history_list.currentItem()
        if (not self.ui.double_click_checkbox.isChecked()):
            self.on_load()
            
    def on_item_changed_saved(self):            
        self.selected_saved = self.ui.saved_selections_list.currentItem()
        if (not self.ui.double_click_checkbox.isChecked()):
            self.on_load_saved()
        
    def on_item_double_clicked(self):
        if (self.ui.double_click_checkbox.isChecked()):
            self.ignore_next_selection = True
            self.on_load()
            
    def on_item_double_clicked_saved(self):
        if (self.ui.double_click_checkbox.isChecked()):
            self.on_load_saved()
        
    def get_proper_name(self, name):
        """ Returns a new name if the history already contains 
        the name. A number in parentheses is added and incremented
        until we have a unique name.
        """
        if not name:
            return ""
        
        new_name = name
        while (new_name in self.save_names):
            if new_name[len(new_name)-1] == ')':
                open_brace = new_name.find('(')
                if open_brace != -1:
                    brace_contents = str(new_name[open_brace+1:len(new_name)-1])
                    if brace_contents.isdigit():
                        number = int(brace_contents)
                        new_name = new_name[:open_brace]+'('+str(number+1)+')'
            else:
                new_name += ("(1)")
        return new_name

import sys
import os


def run():
    app = QApplication.instance() 
    win = CreateSelectionHistoryUI()
    win.show(dockable=True)
    app.exec_()