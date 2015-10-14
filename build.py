#!/usr/bin/env python

# This is the master combomb build script
# which is used to create releases.

import shutil, sys, os, platform, zipfile, tarfile, getopt, atexit
from subprocess import call
from subprocess import Popen, PIPE
sys.dont_write_bytecode = True
sys.path.append('../ComBomb/')
haveCreateVersion = True
try:
    import createVersion
except ImportError:
    haveCreateVersion = False

import makeutils
    
releaseNotes = "releasenotes.txt"

class Chdir:
    def __init__(self, newdir):
        self.origdir = os.getcwd()
        os.chdir(newdir)

    def __del__(self):
        os.chdir(self.origdir)

class uncrustify:
    def __init__(self, buildType):
        self.home = os.path.dirname(os.path.realpath(__file__))
        self.uncrust = self.home + "/call_Uncrustify.sh"
        self.buildType = buildType.lower()

    def callUncrustify(self, directory, ext):
        run(self.uncrust + " " + directory + " " + ext)

    def uncrustify(self, directory):
        if ((platform.system() == "Linux") and (self.buildType == "release") and (makeutils.which("uncrustify", fatal=False) != None)):
            self.callUncrustify(directory, "*.cpp")
            self.callUncrustify(directory, "*.h")
        gitVerStr = ""
        if (haveCreateVersion == True):
            c = Chdir(directory)
            CreateVer = createVersion.CreateVer()
            gitVerStr = CreateVer.getVerStr()
            if (gitVerStr.find("dirty") > 0) and (self.buildType == "release"):
                print("\033[31mBuilding on dirty codebase (" + gitVerStr + " - " + os.getcwd() + "):\033[0m"),
                sys.stdout.flush()
                sys.stdin.read(1)
        return gitVerStr

# if split == False, then cmd must be an array
def run(cmd, split=True):
    print(cmd)
    if (split == True):
        cmds = cmd.split(" ")
    else:
        cmds = cmd
    if (call(cmds)):
        sys.exit(1)

def cmakeBuildLinux(baseDir, buildType, buildVerbose, buildJobs):
    cmake = "cmake ../../../" + baseDir + " -DCMAKE_BUILD_TYPE=" + buildType
    make = "make -j " + buildJobs + " install"
    if (buildVerbose == True):
        make += " VERBOSE=1"
    run(cmake)
    run(make)

def cmakeBuildWindows(baseDir, buildType, buildVerbose, buildJobs):
    if ("VISUALSTUDIOVERSION" in os.environ):
        msvsVer = os.environ["VISUALSTUDIOVERSION"]
        msvsVer = msvsVer[:msvsVer.find('.')]
        if (msvsVer == "10"):
            gen = "Visual Studio 10 2010"
        elif (msvsVer == "11"):
            gen = "Visual Studio 11 2012"
        elif (msvsVer == "12"):
            gen = "Visual Studio 12 2013"
        elif (msvsVer == "14"):
            gen = "Visual Studio 14 2015"
        cmake = "cmake ../../../" + baseDir + " -G"
        make = "cmake --build . --target install --config " + buildType
        cmake = cmake.split(" ")
        cmake.append(gen)
        run(cmake, False)
        run(make)
    else:
        print("Unable to find VISUALSTUDIOVERSION in env, please run from MSVS command prompt")
        sys.exit(1)

def cmakeBuild(baseDir, buildType, buildClean, buildVerbose, buildJobs):
    buildTarget = "build/" + baseDir
    cleanTarget(buildTarget, buildClean)
    gitVerStr = uncrustify(buildType).uncrustify("../" + baseDir)
    c = Chdir(buildTarget)
    if (platform.system() == "Linux"):    
        cmakeBuildLinux(baseDir, buildType, buildVerbose, buildJobs)
    else:
        cmakeBuildWindows(baseDir, buildType, buildVerbose, buildJobs)

def cleanTarget(buildTarget, buildClean):
    if (buildClean == True):
        delBuildTree(buildTarget)
    if (os.path.exists(buildTarget) == False):
        os.makedirs(buildTarget)

def combombBuild(buildClean, buildType, buildJobs):
    buildType = buildType.lower()
    combombSrcDir = os.getcwd() + "/../ComBomb"
    buildTarget = os.getcwd() + "/build/ComBomb" 
    uncrustify(buildType).uncrustify(os.getcwd() + "/../include")
    gitVerStr = uncrustify(buildType).uncrustify(combombSrcDir)
    cleanTarget(buildTarget, buildClean)
    shutil.copy(combombSrcDir + "/ComBombGui/images/ComBomb64.png", buildTarget);
    c = Chdir(buildTarget)
    qmake = makeutils.which("qmake")
    run(qmake + " " + combombSrcDir + " CONFIG+=" + buildType)
    if (platform.system() == "Windows"):
        run(makeutils.which("jom") + " -j" + buildJobs + " " + buildType)
    else:
        run("make -j" + buildJobs)
    buildLog(combombSrcDir, buildTarget)
    if (buildType == "release"):
        zipIt(gitVerStr)

def delBuildTree(delDir):
    retries = 0
    while (os.path.exists(delDir) == True):
        shutil.rmtree(delDir, True)
        retries += 1
        if (retries > 10):
            break
    return not os.path.exists(delDir)

files = {
    "../../../ComBomb/ComBombGui/images/ComBomb128.png": "ComBomb/ComBomb128.png",
    releaseNotes : "ComBomb/" + releaseNotes,
    "../../../ComBomb/addons/savetofile.py" : "ComBomb/addons/savetofile.py",
    "../../../ComBomb/addons/example.py" : "ComBomb/addons/example.py",
}

def zipItWindows(filename):
    files["ComBombGui/release/ComBombGui.exe"] = "ComBomb/ComBombGui.exe"
    filename += ".zip"
    combombZip = zipfile.ZipFile(filename, "w")
    for k, v in files.items():
        combombZip.write(k, v, zipfile.ZIP_DEFLATED)
    
def zipItPosix(filename):
    files["../../../ComBomb/scripts/ComBomb.sh"]                   = "ComBomb/bin/ComBomb.sh"
    files["ComBombGui/ComBombGui"]                              = "ComBomb/bin/ComBombGui"
    files["/usr/lib/x86_64-linux-gnu/libX11-xcb.so.1"]          = "ComBomb/lib/libX11-xcb.so.1"
    files["/usr/lib/x86_64-linux-gnu/libxcb-render-util.so.0"]  = "ComBomb/lib/libxcb-render-util.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-render.so.0"]       = "ComBomb/lib/libxcb-render.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb.so.1"]              = "ComBomb/lib/libxcb.so.1"
    files["/usr/lib/x86_64-linux-gnu/libxcb-image.so.0"]        = "ComBomb/lib/libxcb-image.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-icccm.so.4"]        = "ComBomb/lib/libxcb-icccm.so.4"
    files["/usr/lib/x86_64-linux-gnu/libxcb-sync.so.0"]         = "ComBomb/lib/libxcb-sync.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-xfixes.so.0"]       = "ComBomb/lib/libxcb-xfixes.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-shm.so.0"]          = "ComBomb/lib/libxcb-shm.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-randr.so.0"]        = "ComBomb/lib/libxcb-randr.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-shape.so.0"]        = "ComBomb/lib/libxcb-shape.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-keysyms.so.1"]      = "ComBomb/lib/libxcb-keysyms.so.1"
    files["/usr/lib/x86_64-linux-gnu/libxcb-util.so.0"]         = "ComBomb/lib/libxcb-util.so.0"
    filename += ".tar.bz2"
    file = tarfile.open(filename, "w:bz2")
    for k, v in files.items():
        print(os.path.realpath(k))
        file.add(os.path.realpath(k), v)

def zipIt(gitVerStr):
    vers = gitVerStr.split("-")

    #filename = "ComBomb-" + vers[0]
    #if (len(vers) > 1):
    #    filename = filename + "-" + vers[1]

    filename = "ComBomb-" + gitVerStr
    if (platform.system() == "Windows"):
        zipItWindows(filename)
    else:
        zipItPosix(filename)
    latest = open("latest.txt", 'w')
    latest.write(vers[0])
    latest.close()
    
def buildLog(combombSrcDir, buildTarget):
    c = Chdir(combombSrcDir)
    logFile = open(buildTarget + "/" + releaseNotes, 'w')
    process = Popen(["git", "log", "--pretty=%an %ai %d %s"], stdout=logFile)
    process.wait()
    logFile.flush()
    logFile.close()

def usage(builds):
    print("Build the ComBomb software suite")
    print(" -d --debug")
    print(" -r --release")
    print(" -v --verbose")
    print(" -c --clean")
    print(" -j#")
    print("The following modules can be individually built")
    for b in builds:
        print("    --" + b)
    os._exit(1)

def main(argv):
    buildJobs = "4"
    buildClean = False
    buildVerbose = False
    buildType = "Release"
    builds = ["QueuePtr", "CDLogger", "cppssh", "ComBomb"]
    buildVals = {}
    for b in builds:
        buildVals[b] = True
    args = ["help", "debug", "release", "clean", "verbose"]
    args.extend(builds)
    buildsToRun = []
    try:
        opts, args = getopt.getopt(argv, "hdrcvj:", args)
    except getopt.GetoptError as e:
        print("Error: " + str(e))
        usage(builds)
    for opt, arg in opts:
        if (opt in ('-h', '--help')):
            usage(builds)
        if (opt in ('-d', '--debug')):
            buildType = "Debug"
        if (opt in ('-r', '--release')):
            pass
        if (opt in ('-c', '--clean')):
            buildClean = True
        if (opt in ('-v', '--verbose')):
            buildVerbose = True
        if (opt in ('-j')):
            buildJobs = arg
        if opt[2:] in list(buildVals.keys()):
            buildsToRun.append(opt[2:])

    if (len(buildsToRun) > 0):
        for b in builds:
            buildVals[b] = False
        for b in buildsToRun:
            buildVals[b] = True
    if (buildClean == True):
        delBuildTree("../install")
    if (buildVals["CDLogger"] == True):
        cmakeBuild("CDLogger", buildType, buildClean, buildVerbose, buildJobs)
    if (buildVals["cppssh"] == True):
        cmakeBuild("cppssh", buildType, buildClean, buildVerbose, buildJobs)
    if (buildVals["QueuePtr"] == True):
        cmakeBuild("QueuePtr", buildType, buildClean, buildVerbose, buildJobs)
    if (buildVals["ComBomb"] == True):
        combombBuild(buildClean, buildType, buildJobs)
    print("Done")

if __name__ == "__main__":
    main(sys.argv[1:])
