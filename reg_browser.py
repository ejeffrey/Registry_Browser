#!/usr/bin/python
import labrad
from PyQt4 import QtCore, QtGui, uic
import sys
cxn = None
import labrad_xml
import xml.etree.ElementTree as ET


def labrad_prettyprint(data):
    '''
    This is to solve a really simple/stupid problem.  Calling str() on a container
    calls repr on the items.  This is fine for most cases, but for LabRAD values
    results in the unappealing Value(3.2, 'ns') format
    '''
    if type(data) == list:
        return "[ " + ", ".join([labrad_prettyprint(x) for x in data]) + " ]"
    elif type(data) == tuple:
        return "( " + ", ".join([labrad_prettyprint(x) for x in data]) + " )"
    elif type(data) == labrad.types.Value or type(data)==labrad.types.Complex:
        return str(data)
    else: # Strings, bare nunbers, etc."
        return repr(data)
class LABRADRegistryTree(QtGui.QTreeWidget):
    '''
    We only need to override the drag-and-drop events because they aren't
    signals in Qt.
    '''
    def startDrag(self, event):
        pass
    def dragEnterEvent(self, event):
        event.accept()
    def dragMoveEvent(self, event):
        event.accept()        
    def dropEvent(self, event):
        print "received drop event"
        mime_data = event.mimeData()
        for fmt in mime_data.formats():
            print "MIME type: %s" % fmt
        if mime_data.hasUrls():
            print "Drop URLs:"
            for url in event.mimeData().urls():
                print url

class LabRadTable(QtGui.QTableWidget):
    '''
    We only need to override the drag-and-drop events because they aren't
    signals in Qt.
    '''
    def dragEnterEvent(self, event):
        event.accept()
    def dragMoveEvent(self, event):
        event.accept()        
    def dropEvent(self, event):
        mime_data = event.mimeData()
        for fmt in mime_data.formats():
            print "MIME type: %s" % fmt
        if mime_data.hasUrls():
            print "Drop URLs:"
            for url in event.mimeData().urls():
                print url
    def startDrag(self, event):
        row = self.currentRow()
        key = str(self.item(row,0).text())
        value = str(self.item(row,1).text())
        top_widget = self.parent().parent() # This is a total hack I don't know how to fix... 
        item = top_widget.dirBrowser.currentItem()
        regpath = top_widget.get_path(item)
        print "startDrag: key= ", key
        print "startDrag: value= ", value
        print "startDrag: path= ", regpath
        data = labrad_xml.lr_to_element(self.item(row,1).LRdata)
        print "data: ", data
        mimeData = QtCore.QMimeData()
        mimeData.setData("text/xml", key)
        path = QtCore.QDir.tempPath() + "/" + key + ".xml"
        with open(path, "w") as f:
            ET.ElementTree(data).write(f)
        mimeData.setUrls([QtCore.QUrl.fromLocalFile(path)])
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        result = drag.start(QtCore.Qt.MoveAction)


class RegistryEditorMainWindow(QtGui.QMainWindow):
    def __init__(self, cxn):
        super(RegistryEditorMainWindow, self).__init__()
        uic.loadUi('registry_editor.ui', self)
        print self.editor
        print self.dirBrowser
        print self.reg_items
        self.editor.set_cxn(cxn)
        self.show()
        
class RegistryEditor(QtGui.QWidget):
    '''
    This widget provieds a two-pane tree + list browser for a LABRad registry
    '''
    def set_cxn(self, cxn):
        '''
        This should be called by the parent frame 
        '''
        self.cxn = cxn
        self.reg = cxn.registry
        root_item = QtGui.QTreeWidgetItem(self.dirBrowser.invisibleRootItem(), [""])
        root_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
        #self.dirBrowser.addTopLevelItem(root_item)
        self.dirBrowser.itemExpanded.connect(self.on_expand)
        self.dirBrowser.currentItemChanged.connect(self.on_dir_select)
        
        create_action = QtGui.QAction("Create Directory", self)
        create_action.triggered.connect(self.on_create_dir)
        self.dirBrowser.addAction(create_action)
        
        delete_action = QtGui.QAction("Delete Directory", self)
        delete_action.triggered.connect(self.on_delete_dir)
        self.dirBrowser.addAction(delete_action)

        duplicate_action = QtGui.QAction("Create Duplicate", self)
        duplicate_action.triggered.connect(self.on_duplicate_dir)
        self.dirBrowser.addAction(duplicate_action)

        key_edit_action = QtGui.QAction("Edit Key", self)
        key_edit_action.triggered.connect(self.on_key_edit)
        self.reg_items.addAction(key_edit_action)

        self.dirBrowser.setAcceptDrops(True)
        self.reg_items.setAcceptDrops(True)
        root_item.setExpanded(True)

#  These are signal handlers for the various signals connected above.
#  The goal is to put handlers for both the tree widget and the table
#  widget in the top-level widget.  The only thing that can't go here
#  are the drag-and-drop events since they are events not signals

#  Currently, only read-only events are actually implemented for safety

    def on_key_edit(self):
        row = self.reg_items.currentRow()
        print "editing item: ", self.reg_items.item(row, 0).text()
    def on_create_dir(self):
        item = self.dirBrowser.currentItem()
        path = self.get_path(item)
        print "creating a subdirectory of: ", path

    def on_delete_dir(self):
        item = self.dirBrowser.currentItem()
        path = self.get_path(item)
        print "pretending to delete: ", path
    def on_duplicate_dir(self):
        pass

    def on_edit_key(self):
        pass
    def on_new_key(self):
        pass
    def on_rename_key(self, key): # Tricky, not suppored by registry
        pass
    def on_del_key(self):
        pass
    def get_path(self, item):
        path = []
        walk = item
        while walk:
            path.append(str(walk.text(0)))
            walk = walk.parent()
        path.reverse()
        return path

    def on_expand(self, item):
        if item.childCount() == 0:
            path = self.get_path(item)
            self.reg.cd(path)
            (subdirs, keys_) = self.reg.dir()
            subdirs.sort()
            self.reg.cd([''])
            for d in subdirs:
                new_item = QtGui.QTreeWidgetItem(item, [d])
                new_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)

    def on_dir_select(self, item, olditem):
        path = self.get_path(item)
        self.reg.cd(path)
        (subdirs, keys_) = self.reg.dir()
        keys_.sort()
        for k in range(self.reg_items.rowCount()):
            self.reg_items.removeRow(k)
        self.reg_items.setRowCount(len(keys_))
        for idx,key in enumerate(keys_):
            val = self.reg.get(key)
            self.reg_items.setItem(idx, 0, QtGui.QTableWidgetItem(key))
            value_item = QtGui.QTableWidgetItem(labrad_prettyprint(val))
            value_item.LRdata = val
            self.reg_items.setItem(idx, 1, value_item)

def main():
    cxn = labrad.connect()
    app = QtGui.QApplication(sys.argv)
    w = RegistryEditorMainWindow(cxn)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
    
