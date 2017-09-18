import requests
import json
from pyproj import Proj, transform

def toPseudo(coord):
    inProj = Proj(init='epsg:4326')
    outProj = Proj(init='epsg:3857')
    (xOut, yOut) = transform(inProj, outProj, coord[0], coord[1])
    return (xOut, yOut)
    
def toMercator(coord):
    inProj = Proj(init='epsg:3857')
    outProj = Proj(init='epsg:3395')
    (xOut, yOut) = transform(inProj, outProj, coord[0], coord[1])
    return (xOut, yOut)

def requesting(lowerCorner, upperCorner, url, counterList, recCount = 0):
    
    lowerPseudo = toPseudo(lowerCorner)
    upperPseudo = toPseudo(upperCorner)
                             
    extUrl = "&BBOX={0},{1},{2},{3}".format(lowerPseudo[0], lowerPseudo[1], upperPseudo[0], upperPseudo[1])
    
    #print extUrl
    response = requests.get(url + extUrl)
    json_data = json.loads(response.text)

    counter = 0
    for item in json_data['features']:
        hX = str(item['properties']['X'][0])
        hY = str(item['properties']['Y'][0])
        (hX,hY) = toMercator((float(hX),float(hY)))
        hH = str(item['properties']['Hoogte'][0])
        counterList.append(str(hX) + ";" + str(hY) + ";" + hH)
        counter += 1
    print recCount, counter
    #print counterList

    if counter == 100:
        if recCount == 18:
            print "MAX REC_DEPTH REACHED"
            return counterList
    
        lc = (lowerCorner[0], (lowerCorner[1]+upperCorner[1])/2.0)
        uc = ((lowerCorner[0]+upperCorner[0])/2.0, upperCorner[1])
        requesting(lc, uc, url, counterList, recCount = recCount + 1)
        
        lc = ((lowerCorner[0]+upperCorner[0])/2.0, (lowerCorner[1]+upperCorner[1])/2.0)
        uc = upperCorner
        requesting(lc, uc, url, counterList, recCount = recCount + 1)

        lc = lowerCorner
        uc = ((lowerCorner[0]+upperCorner[0])/2.0, (lowerCorner[1]+upperCorner[1])/2.0)
        requesting(lc, uc, url, counterList, recCount = recCount + 1)

        lc = ((lowerCorner[0]+upperCorner[0])/2.0, lowerCorner[1])
        uc = (upperCorner[0], (lowerCorner[1]+upperCorner[1])/2.0)
        requesting(lc, uc, url, counterList, recCount = recCount + 1)

    return counterList