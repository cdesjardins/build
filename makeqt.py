#!/usr/bin/env python
import sys, traceback, os, platform, getopt, shutil
from subprocess import call
sys.dont_write_bytecode = True
import makeutils

qtversion = "5.5"
qtname = "qt-everywhere-opensource-src-" + qtversion + ".0"
if (platform.system() == "Windows"):
    qtfile = qtname + ".zip"
else:
    qtfile = qtname + ".tar.gz"
qturl = "http://download.qt.io/official_releases/qt/" + qtversion + "/" + qtversion + ".0/single/" + qtfile
builddir = os.getcwd()
qtexternaldir = builddir +  "/../external/qt"
qtinstdir = qtexternaldir + "/Qt/"

def run(cmd):
    cmd = ' '.join(cmd.split())
    print("'" + cmd + "'")
    if (call(cmd.split(" "))):
        sys.exit(1)

def runMake(args, buildJobs):
    if (platform.system() == "Windows"):
        cmd = "jom"
    else:
        cmd = "make"
    cmd += " -j " + buildJobs + " " + args
    run(cmd)
    
def runBuild(buildJobs):
    cmd = "configure -opensource -nomake examples -nomake tests -prefix " + qtinstdir + " -confirm-license -static -no-openssl -nomake examples -nomake tests -no-compile-examples"
    if (platform.system() == "Windows"):
        cmd += " -opengl desktop -static-runtime"
    else:
        cmd = "./" + cmd + " -no-gtkstyle -qt-xcb"
    run(cmd)
    runMake("", buildJobs)
    runMake("install", buildJobs)

def buildQt(buildJobs, clean):
    if (os.path.exists(qtexternaldir) == False):
        os.makedirs(qtexternaldir)
    os.chdir(qtexternaldir)
    if (os.path.exists(qtfile) == False):
        makeutils.download(qturl)
    else:
        print("Skip download of qt archive because the " + qtfile + " already exists")

    if ((clean == True) and (os.path.exists(qtname) == True)):
        shutil.rmtree(qtname)

    if (os.path.exists(qtname) == False):
        makeutils.extractCompressedTar(qtfile)
        # fix build error in qt 5.5
        if (qtversion == "5.5"):
            makeutils.findReplace("#requires(qtHaveModule(opengl))", "requires(contains(QT_CONFIG, opengl))", qtname + "/qt3d/qt3d.pro")

    else:
        print("Skip extraction of qt archive because the " + qtname + " directory already exists")
        if (os.path.exists(qtinstdir) == True):
            print("Deleting: " + qtinstdir)
            shutil.rmtree(qtinstdir)
    os.chdir(qtname)
    runBuild(buildJobs)

def main(argv):
    buildJobs = "4"
    clean = False
    try:
        opts, args = getopt.getopt(argv, "cj:", [])
        for opt, arg in opts:
            if (opt in ('-j')):
                buildJobs = arg
            if (opt in ('-c')):
                clean = True
    
        buildQt(buildJobs, clean)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)

if __name__ == "__main__":
    main(sys.argv[1:])
