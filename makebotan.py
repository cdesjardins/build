#!/usr/bin/env python
import os, shutil, sys, platform, glob
from subprocess import call
sys.dont_write_bytecode = True
import makeutils

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
        botanDir + "/botan-test*",
        botanDir + "/botan_all*",
        botanDir + "/libbotan*",
        botanDir + "/botan*.lib",
        botanDir + "/botan*.exe",
        botanDir + "/*.dll",
        botanDir + "/*.pdb",
        botanDir + "/Makefile",
    ]
    for p in botanObjs:
        for f in glob.glob(p):
            print "delete: " + f
            if (os.path.exists(f) == True):
                os.remove(f)

def runConfigure(debug):
    debugFlags = ""
    if (debug == True):
        buildMode = "debug"
        debugFlags = " --with-debug-info --no-optimizations"
    else:
        buildMode = "release"
        
    cmd = "./configure.py" + \
        " --disable-shared" + \
        " --disable-modules=tls,ffi,mce" + \
        " --prefix=" + botanDir + "/install" + \
        " --libdir=" + botanDir + "/install/lib/botan/" + buildMode + \
        debugFlags + \
        " --disable-avx2"
    if (platform.system() == "Windows"):
        cmd = "python " + cmd + " --cpu=i386 --msvc-runtime=MT"
        if (debug == True):
            cmd += "d"
    run(cmd)
    
def runMakePosix():
    cmd = "make -j4 install"
    run(cmd)

def runMakeWin():
    jom = makeutils.which("jom", fatal=False)
    if (jom == None):
        cmd = "nmake install"
    else:
        cmd = "jom install -j5"
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
    shutil.rmtree(botanDir + "/install", True)
    runBuild(False)
    runBuild(True)

if __name__ == "__main__":
    main(sys.argv[1:])
