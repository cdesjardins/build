#!/usr/bin/env python
import os, shutil, sys, platform, glob, fileinput
from subprocess import call

baseDir = os.path.dirname(os.path.realpath(__file__))
botanDir = baseDir + "/../botan"

def run(cmd):
    print(cmd)
    if (call(cmd.split(" "))):
        sys.exit(1)

def runClean():
    shutil.rmtree(botanDir + "/build", True)
    botanObjs = [ 
        botanDir + "/botan",
        botanDir + "/botan-test",
        botanDir + "/botan_all*",
        botanDir + "/libbotan*",
        botanDir + "botan*.lib",
        botanDir + "botan*.exe",
        botanDir + "*.dll"
    ]
    for p in botanObjs:
        for f in glob.glob(p):
            print "delete: " + f
            if (os.path.exists(f) == True):
                os.remove(f)

def runConfigurePosix(buildMode):
    cmd = "./configure.py" + \
        " --disable-shared" + \
        " --disable-modules=tls" + \
        " --prefix=" + baseDir + "/../install" + \
        " --libdir=" + baseDir + "/../install/lib/botan/" + buildMode + \
        " --build-mode=" + buildMode + \
        " --via-amalgamation" + \
        " --disable-avx2" + \
        " --maintainer-mode"
    run(cmd)

def runConfigureWin(buildMode):
    cmd = "configure.py" + \
        " --disable-shared" + \
        " --disable-modules=tls" + \
        " --prefix=" + baseDir + "/../install" + \
        " --libdir=" + baseDir + "/../install/lib/botan/" + buildMode + \
        " --build-mode=" + buildMode + \
        " --via-amalgamation" + \
        " --maintainer-mode" + \
        " --cpu=i386"
    run(cmd)

def runConfigure(debug):
    if (debug == True):
        buildMode = "debug"
    else:
        buildMode = "release"
    
    if (platform.system() == "Windows"):
        runConfigureWin(buildMode)
    else:
        runConfigurePosix(buildMode)
    
def runMakePosix():
    cmd = "make -j4 install"
    run(cmd)

def runMakeWin():
    with open('Makefile', 'r') as file :
        makefile = file.read()

    makefile = makefile.replace('cl \/MD', 'cl \/MT')

    with open('file.txt', 'w') as file:
        file.write(makefile)
    
    cmd = "nmake install"
    run(cmd)

def runMake():
    if (platform.system() == "Windows"):
        runMakeWin()
    else:
        runMakePosix()

def runBuild(debug):
    runClean()
    os.chdir(botanDir)
    runConfigure(debug)
    runMake()
    os.chdir(baseDir)

def main(argv):
    runBuild(True)
    runBuild(False)

if __name__ == "__main__":
    main(sys.argv[1:])
