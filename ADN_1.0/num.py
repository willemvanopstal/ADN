from pyproj import *

def WGStoPseudo(coords):
	inPrj = Proj('+init=epsg:4326')
	outPrj = Proj('+init=epsg:3857')
	(x,y) = transform(inPrj,outPrj,coords[0],coords[1])
	return (x,y)
	
def PseudoToMercator(coords):
	inPrj = Proj('+init=epsg:3857')
	outPrj = Proj('+init=epsg:3395')
	(x,y) = transform(inPrj,outPrj,coords[0],coords[1])
	return (x,y)
	
def MercatorToWGS(coords):
	inPrj = Proj('+init=epsg:3395')
	outPrj = Proj('+init=epsg:4326')
	(x,y) = transform(inPrj,outPrj,coords[0],coords[1])
	return (x,y)
	
	
coords = (4.39,51.68)
print coords, " -> ", WGStoPseudo(coords)
print WGStoPseudo(coords), " -> ", PseudoToMercator(WGStoPseudo(coords))
print PseudoToMercator(WGStoPseudo(coords)), " -> ", MercatorToWGS(PseudoToMercator(WGStoPseudo(coords)))