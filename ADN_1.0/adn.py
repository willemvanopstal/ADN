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
        self.treeWidget.itemChanged.connect(self.getSelAreas)
        self.webView.load(QtCore.QUrl('leaflet/index.html'))
        self.hisAreaCombo.currentIndexChanged.connect(self.loadHisTime)
        self.populateDatasets()
        self.populateKaps()

        ## Btn.clicked connections
        self.initConnectBtn.clicked.connect(self.connectInit)
        self.dataConnectBtn.clicked.connect(self.connectData)
        self.compBtn.clicked.connect(self.compareHis)
        self.downAreaBtn.clicked.connect(self.downloadAreaPoints)
        self.interpolateBtn.clicked.connect(self.interpolateDataset)
        self.toKapBtn.clicked.connect(self.createKap)

    ############################################
    ##  General Functions                     ##
    ############################################
    
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
        timing = str(datetime.now().strftime('%H:%M:%S >\t'))
        self.createLogBox.append(timing + str(msg))
        return
    
    def clearCreateLog(self):
        self.createLogBox.clear()
        self.createLogBox('log cleared')
    
    def populateDatasets(self):
        self.datasetCombo.clear()
        dirname = os.getcwd() + '\\points\\'
        mylist = os.listdir(dirname)
        self.datasetCombo.addItems(mylist)
        
    def populateKaps(self):
        self.kapCombo.clear()
        dirname = os.getcwd() + '\\grids\\'
        mylist = os.listdir(dirname)
        newlist = []
        for item in mylist:
            print item, item[:-4]
            if item[-4:] == '.dir':
                newlist.append(item[:-4])
        self.kapCombo.addItems(newlist)

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
        try:
            response = requests.get(initUrl)
            if response.status_code == 200:
                self.initOutBox.append("\nINITIAL CONNECTION SUCCESSFULL\n")
                self.initOutBox.append(response.content)
                self.log('initial connection successfull')
                self.dataBox.setEnabled(True)
                
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
        self.dataOutBox.clear()
        initDict = self.getInit()
        wmsCapUrl = initDict['WMSADDRESS'] + initDict['WMSCAP']
        wfsCapUrl = initDict['WFSADDRESS'] + initDict['WFSCAP']
        hisAddress = initDict['HISADDRESS'] + '/history.adn'
        
        #wms capabilities and layer
        try:      
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
        except:
            self.dataOutBox.append('\nWMS CONNECTION FAILED\nCheck your internet connection and the url')
            self.log('initial connection failed')
			
        #wfs capabilities and layer 
        try:
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
        except:
            self.dataOutBox.append('\nWFS CONNECTION FAILED\nCheck your internet connection and the url')
            self.log('initial connection failed')
        
        self.dataOutBox.append('\nLast revision of data:')
        self.dataOutBox.append(lastRevision)        
        self.datingLine.setText(lastRevision)
        self.layBox.setEnabled(True)
        self.wmsLayCombo.setEnabled(True)
        self.wfsLayCombo.setEnabled(True)
        
        #history connection
        try:
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
        except:
            self.dataOutBox.append('\nHISTORY CONNECTION FAILED\nCheck your internet connection and the url')
            self.log('initial connection failed')
        

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

        print checked
        
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
                print coords
                North,East,South,West = coords[3],coords[2],coords[1],coords[0]
                polyBase = 'L.polygon([[{0},{3}],[{2},{3}],[{2},{1}],[{0},{1}]]).addTo(mymap);'.format(North,East,South,West)
                self.js(polyBase)
                
                selAreaList.append('{0} -> {1}'.format(pol,kor))
        self.downAreaCombo.addItems(selAreaList)
        self.downGroupCombo.addItems(selGroupList)
                
    ############################################
    ##  Download Functions                     ##
    ############################################
    
    def downloadAreaPoints(self):
        selAreaCombo = str(self.downAreaCombo.currentText())
        selArea = selAreaCombo.split(' -> ')
        
        coords = self.buildCatalog()[selArea[0]][selArea[1]]
        baseUrl = self.getInit()['WFSADDRESS']
        basicExtension = "?service=WFS&request=GetFeature&version=2.0.0" 
        outputFormat = "application/json"
        typeNames = str(self.wfsLayCombo.currentText()) #"Bathy2017_2_raster:EL.GridCoverage"
        crs = "EPSG:3857"
        requestUrl = baseUrl + basicExtension + "&outputFormat=" + outputFormat + "&typeNames=" + typeNames + "&crs=" + crs

        ## GIVE IN YOUR COORDINATES
        '''lowerCorner = (5.0, 52.0)
        upperCorner = (5.5, 53.0)
        lowerCorner = (3.2, 51.15)
        upperCorner = (4.95, 52.0)'''
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
           
    ############################################
    ##  Crreate Functions                     ##
    ############################################
    
    def interpolateDataset(self):
        fullname = str(self.datasetCombo.currentText())
        parts = fullname.split('_')[0].split('-')
        coords= self.buildCatalog()[parts[0]][parts[1]]
        print coords
        North,East,South,West = coords[3],coords[2],coords[1],coords[0]
        NESW = [North,East,South,West]
        
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
        
    def createKap(self):
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
        
        imgkap = 'imgkap {0} {1} {2}'.format(infile_png, header_out, kap_out)
        process = os.popen(imgkap)
        process.close()
        print 'imgkap ok'
        self.log('imgkap ok')
        self.createLog('.kap CHART created!\n You can find your .kap charts in /charts/.')
        
         
    ############################################
    ##  Compare Functions                     ##
    ############################################
   
    def loadHisTime(self):
        with open('history.adn') as haf:
            for line in haf.readlines():
                if line.split(',')[0] == self.hisAreaCombo.currentText():
                    self.hisTimeCombo.clear()
                    self.hisTimeCombo.addItems(line.split(',')[2:-1])
                    lastItem = [line.split(',')[-1:][0][:-2]]
                    print lastItem
                    self.hisTimeCombo.addItems(lastItem)
    
    def compareHis(self):
        self.testLbl.clear()

        # History being downloaded from github
        selArea = self.hisAreaCombo.currentText()
        selTime = self.hisTimeCombo.currentText()
        hisImagePath = '/history/'
        hisImageName = '{0}_{1}.png'.format(selArea,selTime)
        hisImageUrl = self.getInit()['HISADDRESS'] + hisImagePath + hisImageName
        print hisImageUrl

        r = requests.get(hisImageUrl, stream=True)
        print r.status_code
        if r.status_code == 200:
            with open(hisImagePath[1:] + hisImageName, 'wb') as f:
                f.write(r.content)
                print "writing"
        
        # current dataset using WMS
        #localBBox = "51.25,2,53.7,7.3"
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
        print WMS
        
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
                print curImageName
                with open(curImagePath + curImageName, 'wb') as fp:
                    fp.write(rs.content)
        
        # Comparing the two images
        im_one = Image.open(str(curImagePath)+ str(hisImageName))
        #im_two = Image.open(str(curImagePath) + 'IJsselmeer_2017-09-04.png')
        im_two = Image.open(str(curImagePath) + curImageName)
        im_new = Image.new("RGB", im_one.size, 'white')

        pix_one = im_one.load()
        pix_two = im_two.load()
        pix_new = im_new.load()

        sizing = im_one.size
        print sizing, type(sizing)

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

        #im_new.save(str(curImagePath) + "testcompare_changes.png")
        im_new.save(str(curImagePath) + "changes_{0}_{1}_{2}.png".format(selArea,dating,selTime))
        print "ready"

        pixmap = QtGui.QPixmap(str(curImagePath) + "changes_{0}_{1}_{2}.png".format(selArea,dating,selTime))
        pixmap = pixmap.scaledToWidth(1000)
        self.testLbl.setPixmap(pixmap)
             
    ############################################
    ##  Download Service Functions            ##
    ############################################
    
    def getInit(self):
        initDict = {}
        with open('init.adn') as file:
            for line in file.readlines():
                initDict[line.split(';')[0]] = line.split(';')[1][:-1]
        return initDict 

    def downloadCatalog(self):
        baseUrl = self.initAddressLine.text()
        initDict = self.getInit()
        areaUrl = baseUrl + initDict['catalog']
        try:
            response = requests.get(areaUrl)
            if response.status_code == 200:     
                with open('catalog.adn','w') as of:
                    of.write(response.content)    
            else:
                self.log('catalog connection failed')
        except:
            self.log('catalog connection failed')

    def buildCatalog(self):

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
        return catDict
            
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
