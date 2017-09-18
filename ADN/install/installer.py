import pip

def install(package):
    try:
        pip.main(['install', package])
        print package, ' installed'
    except:
        print package, ' NOT installed'

# Example
if __name__ == '__main__':
    install('numpy')
    install('matplotlib')
    install('scipy')
    install('requests==2.5.3')
    install('Image')
    install('Pillow')
    install('pyproj')
    install('PyQt4-4.11.4-cp27-cp27m-win32.whl')