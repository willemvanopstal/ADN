import numpy as np
from scipy.interpolate import griddata
import scipy
import scipy.misc
from PIL import Image
from pyproj import Proj, transform

def toWGS(coord):
    outProj = Proj(init='epsg:4326')
    inProj = Proj(init='epsg:3395')
    (xOut, yOut) = transform(inProj, outProj, coord[0], coord[1])
    return (xOut, yOut)

def saveImage(pointfile,xCells,yCells,arraying,xMin,xMax,yMin,yMax,NESW):
    
    # create color-image
    im_new = Image.new("RGB", (xCells,yCells), 'white')
    pix_new = im_new.load()
    sizing = (xCells,yCells)
    for i in range(xCells):
        for j in range(yCells):
            i = int(i)
            j = int(j)
            # assign colours by function
            oug = makeDepth(arraying[j,i])
            pix_new[int(i),int(j)] = (oug[0],oug[1],oug[2])            
    im_new.save('grids/{0}.png'.format(pointfile))
    
    # calculate characteristics
    (xMin,yMin) = toWGS((xMin,yMin))
    (xMax, yMax) = toWGS((xMax,yMax)) 
    dX = ((float(xMax)-float(xMin))*111120.0)/xCells
    dY = ((float(yMax)-float(yMin))*111120.0)/yCells
    
    # write chartcal
    chartcal = '[{0}.PNG]\nNA={0}\nFN={0}.PNG\n'.format(pointfile)
    chartcal = chartcal + 'GR=0\nPY=1\nQU=0\nSC={0}\nBC=4\n'.format(int(dX*dY)*2000) #resolution
    chartcal = chartcal + 'B1={0},{1}\nB2={2},{1}\n'.format(yMax,xMin,yMin)
    chartcal = chartcal + 'B3={0},{1}\nB4={2},{1}\n'.format(yMin,xMax,yMax)
    chartcal = chartcal + 'CC=4\nC1=0,0,{0},{1}\nC2={2},{3},{4},{5}\n'.format(yMax,xMin,xCells,yCells,yMin,xMax)
    chartcal = chartcal + 'C3={0},0,{1},{2}\nC4=0,{3},{4},{5}\n'.format(xCells,yMax,xMax,yCells,yMin,xMin)
    chartcal = chartcal + 'GD=WGS84\nNU=\nPR=1\nDS=0,0\n'
    chartcal = chartcal + 'WI={0}\nHE={1}\nDX={2}\nDY={3}\n'.format(xCells,yCells,dX,dY)
    chartcal = chartcal + 'LAT0=0\nLON0=0\nDT=0\nLATS=0\nLATN=0\nDU=0\nPC=0\n'
    with open('grids/{0}.dir'.format(pointfile),'w') as cf:
        cf.write(chartcal)

def interpolateToAsc(pointfile,NESW):
    outputfile = pointfile[:-4]
    pointfile = 'points/' + str(pointfile)
    pointfile_delimiter = ";"
    detail = 5 # INVERSE!
    nodata_value = 99999
    intmethod = 'cubic' #or linear, no extra options yet TODO
    outputascii = "grids/{0}.asc".format(outputfile) #optional

    # load the points in a numpy array
    points = np.loadtxt(pointfile,delimiter=pointfile_delimiter)
    xA, yA, zA = points[:,0], points[:,1], points[:,2]
    xMin, yMin = xA.min(), yA.min()
    xMax, yMax = xA.max(), yA.max()
    zA = np.around(zA*1000) # convert to millimeters and round

    # calculate cellsize
    xCells = int((xMax-xMin)/detail)
    yCells = int((yMax-yMin)/detail)

    # generate regular grid with spacing set
    xi = np.linspace(xMin,xMax,xCells)
    yi = np.linspace(yMin,yMax,yCells)

    # interpolation
    zi = griddata((xA,yA), zA, (xi[None,:], yi[:,None]), method=intmethod, fill_value=nodata_value)
    zi = np.flip(zi,0)
    
    # black and white image (optional, uncomment following line)
    #scipy.misc.imsave('grids/{0}.png'.format(outputfile), zi)
    # colour imaging, needed for chart
    saveImage(outputfile,xCells,yCells,zi,xMin,xMax,yMin,yMax,NESW)
    
    # ASCII (optional, good use in QGIS)        !! OUT OF DATE !!
    '''
    header = "NCOLS {0}\nNROWS {1}\nXLLCENTER {2}\nYLLCENTER {3}\nCELLSIZE {4}\nNODATA_VALUE {5}\n".format(xCells, yCells, xMin, yMin, detail, nodata_value)
    with open(outputascii,'w') as oa:
        oa.write(header)
    of = file(outputascii,'a')
    np.savetxt(of, zi, fmt='%1.3f')
    of.close()
    '''
    
def makeDepth(depth):
    #default colourramp
    if depth <= -3000.0:
        rgb = (247,231,111)
    elif depth > -3000 and depth <= 0.0:
        rgb = (151,199,000)
    elif depth > 0.0 and depth <= 2000.0:
        rgb = (031,175,247)
    elif depth > 2000.0 and depth <= 4000.0:
        rgb = (071,191,247)
    elif depth > 4000.0 and depth <= 6000.0:
        rgb = (103,199,247)
    elif depth > 6000.0 and depth <= 8000.0:
        rgb = (127,207,247)
    elif depth > 8000.0 and depth <= 10000.0:
        rgb = (143,215,247)
    elif depth > 10000.0 and depth <= 12000.0:
        rgb = (159,215,247)
    elif depth > 12000.0 and depth <= 14000.0:
        rgb = (167,223,247)
    elif depth > 14000.0 and depth <= 16000.0:
        rgb = (175,223,247)
    elif depth > 16000.0 and depth <= 18000.0:
        rgb = (183,223,247)
    elif depth > 18000.0 and depth <= 20000.0:
        rgb = (188,228,244)
    elif depth > 20000.0:
        rgb = (254,254,254) 
    else:
        rgb = (254,254,254)
    '''    
    if depth == 99999.0: #NODATA
        rgb = (255,255,255)
    '''
    return rgb