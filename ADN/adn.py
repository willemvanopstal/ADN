import sys
import os
from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import *
from datetime import datetime
import requests
from xml.etree import ElementTree
from PIL import Image
import json
from pyproj import Proj, transform

from pointdownloader import requesting
from inter import interpolateToAsc

qtCreatorFile = "adn_ui.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
 
class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.log('application successfully initialized')
        
        ## stand-alone connections & initialization
        self.setWindowIcon(QtGui.QIcon('icon/icon64.gif'))
        self.treeWidget.itemChanged.connect(self.getSelAreas)
        self.webView.load(QtCore.QUrl('leaflet/index.html'))
        self.log('webview loaded')
        self.hisAreaCombo.currentIndexChanged.connect(self.loadHisTime)
        self.populateDatasets()
        self.populateKaps()
        self.initTabs()
        
        self.colorUp_1.setStyleSheet("background-color: rgb(247,231,111)");
        self.colorUp_2.setStyleSheet("background-color: rgb(151,199,0)");
        self.colorUp_3.setStyleSheet("background-color: rgb(31,175,247)");
        self.colorUp_4.setStyleSheet("background-color: rgb(71,191,247)");
        self.colorUp_5.setStyleSheet("background-color: rgb(103,199,247)");
        self.colorUp_6.setStyleSheet("background-color: rgb(127,207,247)");
        self.colorUp_7.setStyleSheet("background-color: rgb(143,215,247)");
        self.colorUp_8.setStyleSheet("background-color: rgb(159,215,247)");
        self.colorUp_9.setStyleSheet("background-color: rgb(167,223,247)");
        self.colorUp_10.setStyleSheet("background-color: rgb(175,223,247)");
        self.colorUp_11.setStyleSheet("background-color: rgb(183,223,247)");
        self.colorUp_12.setStyleSheet("background-color: rgb(188,228,244)");
        

        ## Btn.clicked connections
        self.initConnectBtn.clicked.connect(self.connectInit)
        self.dataConnectBtn.clicked.connect(self.connectData)
        self.compBtn.clicked.connect(self.compareHis)
        self.downAreaBtn.clicked.connect(self.downloadAreaPoints)
        self.interpolateBtn.clicked.connect(self.interpolateDataset)
        self.toKapBtn.clicked.connect(self.createKap)
        self.clearLogBtn.clicked.connect(self.clearLog)

    ############################################
    ##  General Functions                     ##
    ############################################
    def initTabs(self):
        self.tabs(0,0,0)
        
    def tabs(self, compare, areasel, download):
        self.mainTabs.setTabEnabled(1, compare)
        self.mainTabs.setTabEnabled(2, areasel)
        self.mainTabs.setTabEnabled(3, download)
    
    def js(self,command):
        self.webView.page().mainFrame().evaluateJavaScript(command)
        
    def log(self, msg):
        timing = str(datetime.now().strftime('%H:%M:%S >\t'))
        self.logBox.append(timing + str(msg))
        return
    
    def clearLog(self):
        self.logBox.clear()
        self.log('log cleared')
        
    def createLog(self, msg):
        self.log(msg)
        timing = str(datetime.now().strftime('%H:%M:%S >\t'))
        self.createLogBox.append(timing + str(msg))
        return
    
    def clearCreateLog(self):
        self.log('createlog cleared')
        self.createLogBox.clear()
        self.createLogBox('log cleared')
    
    def populateDatasets(self):
        self.datasetCombo.clear()
        dirname = os.getcwd() + '\\points\\'
        mylist = os.listdir(dirname)
        self.datasetCombo.addItems(mylist)
        self.log('datasetCombo refreshed')
        
    def populateKaps(self):
        self.kapCombo.clear()
        dirname = os.getcwd() + '\\grids\\'
        mylist = os.listdir(dirname)
        newlist = []
        for item in mylist:
            if item[-4:] == '.dir':
                newlist.append(item[:-4])
        self.kapCombo.addItems(newlist)
        self.log('kapCombo refreshed')

    ############################################
    ##  Connect Functions                     ##
    ############################################
            
    def connectInit(self):
        self.initOutBox.clear()
        self.log('trying initial connection ...')
        self.dataBox.setEnabled(False)
        self.wmsLayCombo.setEnabled(False)
        self.wfsLayCombo.setEnabled(False)
        baseAddress = self.initAddressLine.text()
        initUrl = baseAddress + 'init.adn'
        self.log('address: ' + initUrl)
        try:
            response = requests.get(initUrl)
            if response.status_code == 200:
                self.initOutBox.append("\nINITIAL CONNECTION SUCCESSFULL\n")
                self.initOutBox.append(response.content)
                self.log('INITIAL CONNECTION SUCCESSFULL')
                self.dataBox.setEnabled(True)
                self.tabs(0,1,0)
                
                with open('init.adn','w') as of:
                    of.write(response.content)    
                
            else:
                self.initOutBox.append('\nCONNECTION FAILED\nCheck your internet connection and the url')
                self.log('initial connection failed')
        except:
            self.initOutBox.append('\nCONNECTION FAILED\nCheck your internet connection and the url')
            self.log('initial connection failed')

        self.treeWidget.clear()
        self.downloadCatalog()
        self.initAreaTree()
        
    def connectData(self):
        self.log('trying data connection ...')
        self.dataOutBox.clear()
        initDict = self.getInit()
        wmsCapUrl = initDict['WMSADDRESS'] + initDict['WMSCAP']
        wfsCapUrl = initDict['WFSADDRESS'] + initDict['WFSCAP']
        hisAddress = initDict['HISADDRESS'] + '/history.adn'
        
        #wms capabilities and layer
        try:
            self.log('wmscap: ' + wmsCapUrl)
            response = requests.get(wmsCapUrl)
            tree = ElementTree.fromstring(response.content)

            if tree is not None:
                self.dataOutBox.append("WMS connection successfull")
                lastRevision = tree[1][2][2][0].text
                #self.dataOutBox.append("Last revision of data:")
                #self.dataOutBox.append(tree[1][2][2][0].text)

                wmsLayers = []
                for item in tree[1][3]:
                    if item.tag == '{http://www.opengis.net/wms}Layer':
                        wmsLayers.append(item[0].text)

                self.wmsLayCombo.clear()
                self.wmsLayCombo.addItems(wmsLayers)
                self.log('WMS CONNECTION SUCCESSFULL')
                self.tabs(1,1,1)
        except:
            self.dataOutBox.append('\nWMS CONNECTION FAILED\nCheck your internet connection and the url')
            self.log('initial connection failed')
			
        #wfs capabilities and layer 
        try:
            self.log('wfscap: ' + wfsCapUrl)
            response = requests.get(wfsCapUrl)
            tree = ElementTree.fromstring(response.content)

            if tree is not None:
                self.dataOutBox.append("WFS connection successfull")

                wfsLayers = []
                for item in tree[3]:
                    if item.tag == '{http://www.opengis.net/wfs/2.0}FeatureType':
                        wfsLayers.append(item[0].text)

                self.wfsLayCombo.clear()
                self.wfsLayCombo.addItems(wfsLayers)
                self.log('WFS CONNECTION SUCCESSFULL')
        except:
            self.dataOutBox.append('\nWFS CONNECTION FAILED\nCheck your internet connection and the url')
            self.log('initial connection failed')
        
        self.dataOutBox.append('\nLast revision of data:')
        self.dataOutBox.append(lastRevision)        
        self.datingLine.setText(lastRevision)        
        self.datingLine_2.setText(lastRevision)
        self.layBox.setEnabled(True)
        self.wmsLayCombo.setEnabled(True)
        self.wfsLayCombo.setEnabled(True)
        
        #history connection
        try:
            self.log('hisaddress: ' + hisAddress)
            response = requests.get(hisAddress)
            self.dataOutBox.append("History connection successfull")
            with open('history.adn','w') as hf:
                hf.write(response.content)
            
            areaList = []
            with open('history.adn') as hhf:
                for line in hhf.readlines():
                    areaList.append(line.split(',')[0])
            
            self.hisAreaCombo.clear()
            self.hisAreaCombo.addItems(areaList)
            self.log('history connection successfull')
        except:
            self.dataOutBox.append('\nHISTORY CONNECTION FAILED\nCheck your internet connection and the url')
            self.log('initial connection failed')
        self.log('data connection completed')
        self.log('lastRevision: ' + lastRevision)

    ############################################
    ##  Area Functions                        ##
    ############################################
    
    def initAreaTree(self):
        tree = self.treeWidget
        headerItem = QtGui.QTreeWidgetItem()
        item = QtGui.QTreeWidgetItem
        
        predefAreas = self.buildCatalog()
        
        cf = open('catalog.adn')
        for i in predefAreas.keys():
            parent = QtGui.QTreeWidgetItem(tree)
            parent.setText(0, i)
            parent.setFlags(parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            for x in predefAreas[i].keys():
                child = QtGui.QTreeWidgetItem(parent)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setText(0, x)
                child.setCheckState(0, Qt.Unchecked)
        cf.close()
        self.log('areaselector-items are refreshed')
        
    def getSelAreas(self, item, column):
        checked = {}
        root = self.treeWidget.invisibleRootItem()
        area_count = root.childCount()

        for i in range(area_count):
            area = root.child(i)
            if area.checkState(0) == QtCore.Qt.Checked or area.checkState(0) == QtCore.Qt.PartiallyChecked:
            
                checked_sweeps = list()
                num_children = area.childCount()
    
                for n in range(num_children):
                    child = area.child(n)
                    if child.checkState(0) == QtCore.Qt.Checked:
                        checked_sweeps.append(str(child.text(0)))

                checked[str(area.text(0))] = checked_sweeps
                checked[str(area.text(0))] = checked_sweeps
        self.log('checked areas retrieved')
        
        # update leaflet/js
        self.js('clearMap()')
        self.downAreaCombo.clear()
        self.downGroupCombo.clear()
        selAreaList = []
        selGroupList = []
        for pol in checked.keys():
            selGroupList.append(pol)
            for kor in checked[pol]:
                coords= self.buildCatalog()[pol][kor]
                North,East,South,West = coords[3],coords[2],coords[1],coords[0]
                polyBase = 'L.polygon([[{0},{3}],[{2},{3}],[{2},{1}],[{0},{1}]]).addTo(mymap);'.format(North,East,South,West)
                self.js(polyBase)
                selAreaList.append('{0} -> {1}'.format(pol,kor))
        self.downAreaCombo.addItems(selAreaList)
        self.downGroupCombo.addItems(selGroupList)
        self.log('leaflet updated with selection')
        self.log('downAreaCombo, downGroupCombo updated with selection')
                
    ############################################
    ##  Download Functions                     ##
    ############################################
    
    def downloadAreaPoints(self):
        self.log('starting download')
        selAreaCombo = str(self.downAreaCombo.currentText())
        selArea = selAreaCombo.split(' -> ')
        
        coords = self.buildCatalog()[selArea[0]][selArea[1]]
        baseUrl = self.getInit()['WFSADDRESS']
        basicExtension = "?service=WFS&request=GetFeature&version=2.0.0" 
        outputFormat = "application/json"
        typeNames = str(self.wfsLayCombo.currentText()) #"Bathy2017_2_raster:EL.GridCoverage"
        crs = "EPSG:3857"
        requestUrl = baseUrl + basicExtension + "&outputFormat=" + outputFormat + "&typeNames=" + typeNames + "&crs=" + crs

        lowerCorner = (coords[0], coords[1])
        upperCorner = (coords[2], coords[3])

        filename = "points/{0}-{1}_{2}.csv".format(selArea[0],selArea[1],str(self.datingLine.text()))
        fh = open(filename,'w')
        #fh.write("lon;lat;depth\n")

        newlist = []
        for item in requesting(lowerCorner, upperCorner, requestUrl, []):
            if item not in newlist:
                newlist.append(item)
                fh.write(item + "\n") 
        fh.close()
        self.populateDatasets()
        self.log('download finished, .csv file saved')
           
    ############################################
    ##  Crreate Functions                     ##
    ############################################
    
    def interpolateDataset(self):
        self.createLogBox.clear()
        self.log('starting interpolation')
        fullname = str(self.datasetCombo.currentText())
        parts = fullname.split('_')[0].split('-')
        coords= self.buildCatalog()[parts[0]][parts[1]]
        print coords
        North,East,South,West = coords[3],coords[2],coords[1],coords[0]
        NESW = [North,East,South,West]
        self.log(str(NESW))
        
        self.createLog('Starting interpolation..\nwriting to grids')
        interpolateToAsc(str(self.datasetCombo.currentText()),NESW)
        filename = str(self.datasetCombo.currentText())[:-4]
        self.createLog('Image on the right is an uncalibrated version.')
        pixmap = QtGui.QPixmap('grids/{0}.png'.format(filename))
        #pixmap = pixmap.scaledToWidth(1000)
        self.chartLbl.setPixmap(pixmap)
        self.populateKaps()
        index = self.kapCombo.findText(filename, QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.kapCombo.setCurrentIndex(index)
        self.log('interpolation finished')
        
    def createKap(self):
        self.log('starting creating .kap')
        self.createLog('Creating .kap file\nwriting to charts..')
        filename = str(self.kapCombo.currentText())
        infile_dir = 'grids/{0}.dir'.format(filename)
        infile_png = 'grids/{0}.png'.format(filename)
        header_out = 'charts/{0}.txt'.format(filename)
        kap_out = 'charts/{0}.kap'.format(filename)
        
        mc2bsbh = 'mc2bsbh {0} -o {1}'.format(infile_dir, header_out)
        process = os.popen(mc2bsbh)
        process.close()
        print 'mc2bsbh ok'
        self.log('mc2bsbh ok')
        
        #attribution   
        with open(header_out,'rb') as old:
            contents = old.read()
        with open(header_out,'wb') as new:
            new.write('! Chart created by ADN (github.com/willemvanopstal/ADN)\r\n! Chart data from Netherlands Hydrographic Service\r\n')
            new.write(contents)
        
        imgkap = 'imgkap {0} {1} {2}'.format(infile_png, header_out, kap_out)
        process = os.popen(imgkap)
        process.close()
        print 'imgkap ok'
        self.log('imgkap ok')
        
        
        
        self.createLog('.kap CHART created!\n You can find your .kap charts in /charts/.')
        self.log('chart created')
        
         
    ############################################
    ##  Compare Functions                     ##
    ############################################
   
    def loadHisTime(self):
        self.log('retrieving saved history')
        with open('history.adn') as haf:
            for line in haf.readlines():
                if line.split(',')[0] == self.hisAreaCombo.currentText():
                    self.hisTimeCombo.clear()
                    self.hisTimeCombo.addItems(line.split(',')[2:-1])
                    lastItem = [line.split(',')[-1:][0][:-2]]
                    self.hisTimeCombo.addItems(lastItem)
        self.log('hisTimeCombo updated')
    
    def compareHis(self):
        self.testLbl.clear()
        self.log('starting comparing')

        # History being downloaded from github
        selArea = self.hisAreaCombo.currentText()
        selTime = self.hisTimeCombo.currentText()
        #hisImageName = '{0}_{1}.png'.format(selArea,'2017-09-13')
        hisImagePath = '/history/'
        hisImageName = '{0}_{1}.png'.format(selArea,selTime)
        hisImageUrl = self.getInit()['HISADDRESS'] + hisImagePath + hisImageName
        self.log('historyDB: ' + hisImageUrl)

        r = requests.get(hisImageUrl, stream=True)
        print r.status_code
        if r.status_code == 200:
            with open(hisImagePath[1:] + hisImageName, 'wb') as f:
                f.write(r.content)
                self.log('writing git history')
        
        # current dataset using WMS
        with open('history.adn') as hif:
            for line in hif.readlines():
                if line.split(',')[0] == self.hisAreaCombo.currentText():
                    localBBox = line.split(',')[1]
        splitBox = localBBox.split(';')
        localBBox = '{0},{1},{2},{3}'.format(splitBox[1],splitBox[0],splitBox[3],splitBox[2])
        calHeight = int((float(splitBox[3])-float(splitBox[1]))*1500)
        calWidth = int((float(splitBox[2])-float(splitBox[0]))*1500)
        lining = self.getInit()
        WMS = ("{0}{1}&layers={2}&styles=&format=image/png&transparent=false&version=1.3.0&info_format=application/json&tiled=true&height={3}&width={4}&crs=EPSG:4326&bbox={5}").format(lining['WMSADDRESS'],'?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap',self.wmsLayCombo.currentText(),calHeight,calWidth,localBBox)
        self.log('historyWMS: ' + WMS)   
        
        rs = requests.get(WMS, stream=True)
        print rs.status_code
        if rs.status_code == 200:
            curImagePath = 'history/'
            capabilityUrl = self.getInit()['WMSADDRESS'] + self.getInit()['WMSCAP']
            response = requests.get(capabilityUrl)
            tree = ElementTree.fromstring(response.content)
            if tree is not None:
                dating = tree[1][2][2][0].text
                curImageName = '{0}_{1}.png'.format(selArea,dating)
                #print curImageName
                with open(curImagePath + curImageName, 'wb') as fp:
                    fp.write(rs.content)
                self.log('writing current history')
        
        # Comparing the two images
        self.log('comparing the two images')
        im_one = Image.open(str(curImagePath)+ str(hisImageName))
        im_two = Image.open(str(curImagePath) + curImageName)
        im_new = Image.new("RGB", im_one.size, 'white')

        pix_one = im_one.load()
        pix_two = im_two.load()
        pix_new = im_new.load()
        sizing = im_one.size
        
        for i in range(im_one.size[0]):
            for j in range(im_one.size[1]):
                rd = pow(pix_two[i, j][0] - pix_one[i, j][0], 2)
                gd = pow(pix_two[i, j][1] - pix_one[i, j][1], 2)
                bd = pow(pix_two[i, j][2] - pix_one[i, j][2], 2)
                # print rd + gd + bd
                if (rd + gd + bd) == 0:
                    pix_new[i, j] = (255, 255, 255)
                else:
                    pix_new[i, j] = ((250 + rd), gd, bd)

        im_new.save(str(curImagePath) + "changes_{0}_{1}_{2}.png".format(selArea,dating,selTime))
        self.log('done comparing history, file written')

        pixmap = QtGui.QPixmap(str(curImagePath) + "changes_{0}_{1}_{2}.png".format(selArea,dating,selTime))
        pixmap = pixmap.scaledToWidth(1000)
        self.testLbl.setPixmap(pixmap)
        
    ############################################
    ##  Download Service Functions            ##
    ############################################
    
    def getInit(self):
        self.log('establishing initDict')
        initDict = {}
        with open('init.adn') as file:
            for line in file.readlines():
                initDict[line.split(';')[0]] = line.split(';')[1][:-1]
        self.log('initDict established')
        return initDict 

    def downloadCatalog(self):
        self.log('downloading catalog')
        baseUrl = self.initAddressLine.text()
        initDict = self.getInit()
        areaUrl = baseUrl + initDict['catalog']
        try:
            self.log('catalog url: ' + areaUrl)
            response = requests.get(areaUrl)
            if response.status_code == 200:     
                with open('catalog.adn','w') as of:
                    of.write(response.content)    
            else:
                self.log('catalog connection failed')
        except:
            self.log('catalog connection failed')
        self.log('catalog downloaded')

    def buildCatalog(self):
        self.log('establishing catalog')
        cf = open('catalog.adn')
        catDict = {}
        for line in cf.readlines():
            parDict = {}
            elem = line.split(',')
            for part in elem[1:]:
                spec = part.split(';')
                parDict[spec[0]] = (float(spec[1]),float(spec[2]),float(spec[3]),float(spec[4]))
            catDict[elem[0]] = parDict
        cf.close()
        self.log('catalog established')
        return catDict
            
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())