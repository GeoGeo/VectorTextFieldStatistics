# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VectorTextFieldStatistics
                                 A QGIS plugin
 VectorTextFieldStatistics
                              -------------------
        begin                : 2015-02-11
        git sha              : $Format:%H$
        copyright            : (C) 2015 by steven kay/geogeo
        email                : steven@geogeoglobal.com
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
# Initialize Qt resources from file resources.py
import resources_rc
from PyQt4 import QtCore, QtGui
from qgis.core import *
import time
# Import the code for the dialog
from VectorTextFieldStatistics_dialog import VectorTextFieldStatisticsDialog
import os.path
import os
    
class VectorTextFieldStatistics:
    """
    QGIS Plugin Implementation.
    """

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
            'VectorTextFieldStatistics_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = VectorTextFieldStatisticsDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Vector Text Field Statistics')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'VectorTextFieldStatistics')
        self.toolbar.setObjectName(u'VectorTextFieldStatistics')

        self.resultcache = {}
        self.hidenullfields = True
        self.hidenullvalues = False

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
        return QCoreApplication.translate('VectorTextFieldStatistics', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
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
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

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

        # fix to stop showing the default plugin icon
        
        # icon_path = ':/plugins/VectorTextFieldStatistics/icon.png'
        icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"icon.png")
        
        self.add_action(
            icon_path,
            text=self.tr(u'Vector Text Field Statistics'),
            callback=self.run,
            parent=self.iface.mainWindow())

        
        self.actionRun = QAction(QCoreApplication.translate("VectorTextStatistics", "Vector Text Statistics"), self.iface.mainWindow())
        self.iface.addPluginToVectorMenu(QCoreApplication.translate("VectorTextStatistics", "Vector Text Statistics"), self.actionRun)
        self.actionRun.triggered.connect(self.run)
            
    def sortlist(self, kvlist, sorttype=1):
        # sort a list in form [(value1, count1), (value2,count2)...]
        if sorttype==0:
            # sort by name of value (case insensitive)
            return sorted(kvlist, key=lambda tup: tup[0].lower())

        if sorttype==1:
        # sort by name of value (case sensitive)
            return sorted(kvlist, key=lambda tup: tup[0])

        if sorttype==2:
            # sort by count, descending
            return sorted(kvlist, key=lambda tup: tup[1], reverse=True)
    
    def getLayerDict(self, alayer, fieldnamelist, fieldtypes):
        
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.dlg.lbProgress.setText( "Reading features.." )
        dix = {}
        res = {}
        provider = alayer.dataProvider()
        iter = alayer.getFeatures()
        fix = 0
        tick = time.time()
        ignorenull = True
        for feature in iter:
            z = []
            ix = 0
            for fname in fieldnamelist:
                z.append((fname, feature.attribute(fname)))
            
            for kv in z:
                fname, val = kv
                #print "%s = %s" % (fname, val)
                if not val:
                    # we do this to avoid storing NULL elements 
                    # over and over and over (each NULL seems to hash to something
                    # different, so ('foo', NULL) will keep on being added) 
                    val = 'NULL'
                    kv = (fname, val)
                if not kv in dix:
                    dix[kv] = 1
                else:
                    dix[kv] = dix[kv]+1
            fix += 1
            if fix%1000 == 0:
                print "Read %d features" % fix
                
        for kv in dix:
            fname,fval = kv
            cnt = dix[kv]
            if not fname in res:
                res[fname]=[(fval,cnt)]
            else:
                res[fname].append((fval,cnt))
        
        sortby = self.dlg.cbSortType.currentIndex()
        
        for f in fieldnamelist:
            try:
                res[f] = self.sortlist(res[f], sorttype=sortby)
            except:
                # seems to be a problem with fieldnames beginning with @
                self.alert("Unable to access field called [%s]" % f)
        
        self.resultcache = res
        
        tock = time.time() - tick 
        msg =  "Read %d features in %2.2fs. " % (fix, tock)
        if len(fieldnamelist)==0:
            msg += "No text fields found." 
        else:
            msg += "Found %d text fields" % len(fieldnamelist)
            if len(res)<len(fieldnamelist):
                msg += ", showing %d fields" % len(res)
        self.dlg.lbProgress.setText(msg)
        QApplication.restoreOverrideCursor()
        return res

    def gettextline(self, value, count):
        return "%9d | %s" % (count, value)

    def getfieldcolor(self, kvlist):
        '''
        get colour for list of kv pairs [(value, count), ...]
        Fields are colourised as follows:-
        RED - no duplicate values, no NULLs. Likely to be a unique identifier
        ORANGE - no duplicate values, but one or more NULLs appear.
        GREY - all values are NULL (won't appear if checkbox is enabled to hide these)
        BLACK - duplicate values, some NULLs
        BLUE - duplicate values, no NULLs
        '''
        # show fields with only NULL values in 50% grey
        if len(kvlist)==1:
            k,v = kvlist[0]
            if k=='NULL':
                return QColor(127,127,127) # field with only NULL values
        
        # if any duplicates found, return black
        gotnull = False
        gotdupe = False
        for k,v in kvlist:
            if v>1 and k!= "NULL":
                gotdupe=True
                break
        for k,v in kvlist:
            if k=='NULL':
                gotnull=True
                break
        
        if gotnull:
            if not gotdupe:
                return QColor(255,127,60)
            else:
                return QColor(0,0,0)
        else:
            if not gotdupe:
                return QColor(255,0,0)
            else:
                return QColor(0,0,255)
        
    def alert(self, mess):
        self.iface.messageBar().pushMessage(QCoreApplication.translate("VectorTextStatistics", mess))
        
    def getItemsForTreeWidget(self, mylayer, fields):
        '''
        gets a series of top-level tree items, one per text field, with
        attached second-level tree items, one per value. Lists are truncated at 1000 elements in case of
        low RAM.
        '''
 
        items = []
        fieldnames = []
        fieldtypes = []
        ix = 0
        
        for f in fields:
            fieldtypes.append(f.type())
            if f.type()==10:
                fieldnames.append(f.name())

        if len(fieldnames)==0:
            # no text fields, don't bother to scan features
            return []
    
        # when you change sort mode, don't reload features
        if len(self.resultcache)==0:
            res = self.getLayerDict(mylayer, fieldnames, fieldtypes)
        else:
            res = self.resultcache

        sortby = self.dlg.cbSortType.currentIndex()
        
        for f in fieldnames:
            try:
                res[f] = self.sortlist(res[f], sorttype=sortby)
            except:
                self.alert("Unable to access field called [%s]" % f)

        provider = mylayer.dataProvider()
        fields = provider.fields() 
        ix = 0
        trunc = False
        dropped = 0
        for f in fields:
            
            if f.type()==10: # string only
                fieldname = f.name()
                skip = False
                
                widg = QTreeWidgetItem([fieldname])
                        
                # only add children if field has non-null values
                if fieldname in res:
                    
                    if len(res[fieldname])==1:
                        k,v = res[fieldname][0]
                        if k=="NULL" or not v:
                            # only got NULLs
                            skip = True
                            dropped += 1
                        else:
                            for val,cnt in res[fieldname]:
                                msg = self.gettextline(val,cnt)
                                QTreeWidgetItem(widg, ['',val,str(cnt)])
                    else:
                        ix = 0
                        for val,cnt in res[fieldname]:
                            if val=="NULL" and self.hidenullvalues:
                                pass
                            else:
                                msg = self.gettextline(val,cnt)
                                if ix<1000:
                                    QTreeWidgetItem(widg, ['',val,str(cnt)])
                            ix += 1
                        if ix>=1000:
                            QTreeWidgetItem(widg, ['','Truncated list at 1000',''])
                            trunc = True
                            
                    widg.setTextColor(0,self.getfieldcolor(res[fieldname]))
                    
                    if not self.hidenullfields:           
                        items.append(widg)
                    else:
                        if not skip:
                            items.append(widg)

                ix += 1
        return items

    def changedSortType(self, widget):
        ''' 
        
        changed sort type (also called if one of the checkboxes is changed)
        if we have results (in resultcache) we can reuse that, and avoid having to iterate over the features again.
         
        '''
        self.dlg.lbProgress.setText("Option has been changed")
        if len(self.resultcache)==0:
            return
        res = self.resultcache
        self.dlg.twInfo.clear()
        items = []
        newlayername = self.dlg.cbLayers.itemText(self.dlg.cbLayers.currentIndex())
        if newlayername == '':
            return
        
        mylayerid = self.layername2id[newlayername]
        mylayer = QgsMapLayerRegistry.instance().mapLayer(mylayerid)      
        
        provider = mylayer.dataProvider()

        fields = provider.fields() 
        
        items = self.getItemsForTreeWidget(mylayer, fields)
    
        if len(items)==0:
            self.dlg.lbProgress.setText("No text fields in this layer [%s]" % mylayer.name())
            
        self.dlg.twInfo.addTopLevelItems(items)
        self.dlg.twInfo.reexpand()
        
    def changedLayerSelection(self, widget):
        
        ''' 
        user selected new layer in combo 
        '''
        
        newlayername = self.dlg.cbLayers.itemText(self.dlg.cbLayers.currentIndex())
                
        if newlayername=='':
            return
        
        mylayerid = self.layername2id[newlayername]
        
        # use QgsMapLayerRegistry, unlike Canvas this also includes layers which are not shown on the map
        
        mylayer = QgsMapLayerRegistry.instance().mapLayer(mylayerid)
        
        self.dlg.twInfo.clear()
        self.resultcache = {}        
        
        provider = mylayer.dataProvider()

        fields = provider.fields() 
        
        items = self.getItemsForTreeWidget(mylayer, fields)
        
        if len(items)==0:
            self.dlg.lbProgress.setText("No text fields in this layer [%s]" % mylayer.name())
             
        self.dlg.twInfo.addTopLevelItems(items)
        
        
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Vector Text Field Statistics'),
                action)
            self.iface.removeToolBarIcon(action)


    def changedHideNulls(self, widget):
        self.hidenullfields = self.dlg.chHideNulls.checkState()
        self.changedSortType(widget)
        
        
    def changedIgnoreNulls(self, widget):
        self.hidenullvalues = self.dlg.chIgnoreNulls.checkState()
        self.changedSortType(widget)
        
        

    def run(self):
        """Run method that performs all the real work"""
        
        # get list of layers
        self.layername2id = {}
        self.dlg.twInfo.clear()
        self.dlg.lbProgress.setText("")
        
        self.dlg.twInfo.setColumnWidth(0, 150);
        self.dlg.twInfo.setColumnWidth(1, 200);
        self.dlg.twInfo.setColumnWidth(2, 50);
        
        # add logo
        pic = self.dlg.labLogo
        pic.setGeometry(20, 440, 218, 63)
        logofile = os.path.join(os.path.dirname(os.path.realpath(__file__)),"logo.png")
        pic.setPixmap(QtGui.QPixmap(logofile))
        
        self.dlg.cbLayers.clear()
        self.dlg.cbLayers.addItem("")
        
        # get layer name -> id mappings
        
        ct = 0
        ix = 0
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for layername in layerMap:
            layer = layerMap[layername]
            if layer.type() == QgsMapLayer.VectorLayer:
                self.dlg.cbLayers.addItem(layer.name())
                self.layername2id[layer.name()] = layer.id()
                ct += 1
            ix += 1
        if (ct==0):
            self.alert("No layers!")
                
        # show the dialog
        
        self.dlg.show()
        
        # bind events
        self.dlg.cbLayers.currentIndexChanged.connect(self.changedLayerSelection)
        self.dlg.cbSortType.currentIndexChanged.connect(self.changedSortType)
        self.dlg.chHideNulls.stateChanged.connect(self.changedHideNulls)
        self.dlg.chIgnoreNulls.stateChanged.connect(self.changedIgnoreNulls)
        
        # Run the dialog event loop
        
        result = self.dlg.exec_()
        
        # See if OK was pressed
        
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
