# ADN
GUI-tool for retrieving the latest bathymetric data in the Netherlands, and converting it for use in e.g. OpenCPN.

NB: This tool is still experimental, don't use it as your primary navigational source.

## Building the applet

The tool is built with Python 2.7 and GUI is done with PyQt4. Before you can use the tool, you should have Python together with its dependencies installed. I'm working towards a solution in which you won't need to install Python yourself - please be patient! In the meanwhile, just Google for a Python27 installation. Also Google the possibilities to install the so-called site-packages. I recommend using 'pip' because it is just dead simple. After installing Python27 itself, make sure to install all site-packages listed below, otherwise the applet won't work.

## Settings

''' 
WMSADD;inspire.caris.nl/service
WMSCAP;&thisandthis
WFSADD;inspire.caris.nl/service
WFSCAP;hdjdk
'''
