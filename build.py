#!/usr/bin/env python

# This is the master combomb build script
# which is used to create releases.

import shutil, sys, os, platform, zipfile, tarfile, getopt, atexit
from subprocess import call
from subprocess import Popen, PIPE

sys.path.append('../ComBomb/')
import createVersion

releaseNotes = "releasenotes.txt"
gitVersions = {}

class Chdir:
    def __init__(self, newdir):
        self.origdir = os.getcwd()
        os.chdir(newdir)

    def __del__(self):
        os.chdir(self.origdir)

class uncrustify:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.uncrust = self.home + "/bin/call_Uncrustify.sh"
        self.config  = self.home + "/bin/uncrustify.cfg"

    def callUncrustify(self, directory, ext):
        process = Popen([self.uncrust, directory, ext])
        process.wait()

    def uncrustify(self, directory):
        if (platform.system() == "Linux"):
            if ((os.path.isfile(self.uncrust) == True) and (os.path.isfile(self.config) == True)):
                self.callUncrustify(directory, "cpp")
                self.callUncrustify(directory, "h")
        c = Chdir(directory)
        CreateVer = createVersion.CreateVer()
        gitVerStr = CreateVer.getVerStr()
        if (gitVerStr.find("dirty") > 0):
            raw_input("Building on dirty codebase (" + gitVerStr + " - " + os.getcwd() + "): ")
        return gitVerStr

def run(cmd):
    print(cmd)
    if (call(cmd.split(" "))):
        sys.exit(1)

def cmakeBuildLinux(baseDir, buildType, buildVerbose):
    cmake = "cmake ../../../" + baseDir + " -DCMAKE_BUILD_TYPE=" + buildType
    make = "make -j8 install VERBOSE=" + str(int(buildVerbose))
    run(cmake)
    run(make)

def cmakeBuildWindows(baseDir, buildType, buildVerbose):
    cmake = "cmake ../../../" + baseDir
    make = "cmake --build . --target install --config " + buildType
    run(cmake)
    run(make)

def cmakeBuild(baseDir, buildType, buildClean, buildVerbose):
    buildTarget = "build/" + baseDir
    cleanTarget(buildTarget, buildClean)
    gitVerStr = uncrustify().uncrustify("../" + baseDir)
    #gitVerStr = "v2015.257-2-g45287fa-dirty"
    gitVersions[baseDir] = gitVerStr
    c = Chdir(buildTarget)
    if (platform.system() == "Linux"):    
        cmakeBuildLinux(baseDir, buildType, buildVerbose)
    else:
        cmakeBuildWindows(baseDir, buildType, buildVerbose)

def cleanTarget(buildTarget, buildClean):
    if (buildClean == True):
        delBuildTree(buildTarget)
    if (os.path.exists(buildTarget) == False):
        os.makedirs(buildTarget)

def handleComBombDirty(gitVerStr, combombSrcDir):
    for k, v in gitVersions.iteritems():
        if (v != gitVerStr):
            c = Chdir(combombSrcDir)
            dirty = True
            index = gitVerStr.find("dirty")
            if (index == -1):
                gitVerStr += "-libs"
            else:
                gitVerStr = gitVerStr.replace("dirty", "libs")
            cmd = "git tag -a " + gitVerStr + " -m"
            cmdArray = cmd.split(' ')
            cmdArray.extend(["\"build script says you are dirty\""])
            call(cmdArray)
            gitVerStr += "-dirty"
            atexit.register(cleanupComBombDirty, gitVerStr=gitVerStr, combombSrcDir=combombSrcDir)
            break
    return gitVerStr 

def cleanupComBombDirty(gitVerStr, combombSrcDir):
    c = Chdir(combombSrcDir)
    gitVerStr = gitVerStr.replace("-dirty", "")
    cmd = "git tag -d " + gitVerStr
    run(cmd)

def combombBuild(buildClean, buildType):
    buildType = buildType.lower()
    combombSrcDir = os.getcwd() + "/../ComBomb"
    buildTarget = os.getcwd() + "/build/ComBomb" 
    gitVerStr = uncrustify().uncrustify(combombSrcDir)
    newGitVerStr = handleComBombDirty(gitVerStr, combombSrcDir)
    cleanTarget(buildTarget, buildClean)
    shutil.copy(combombSrcDir + "/ComBombGui/images/ComBomb64.png", buildTarget);
    c = Chdir(buildTarget)
    qmake = which("qmake")
    run(qmake + " " + combombSrcDir + " CONFIG+=" + buildType)
    if (platform.system() == "Windows"):
        run(which("jom") + " -j5 " + buildType)
    else:
        run("make -j5")
    buildLog(combombSrcDir, buildTarget)
    zipIt(newGitVerStr)

def delBuildTree(delDir):
    retries = 0
    while (os.path.exists(delDir) == True):
        shutil.rmtree(delDir, True)
        retries += 1
        if (retries > 10):
            break
    return not os.path.exists(delDir)

def which(file):
    if (platform.system() == "Windows"):
        file += ".exe"
    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.exists(path + "/" + file):
                return path + "/" + file
    print(file + " not found")
    os._exit(1)
    return None

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
    for k, v in files.iteritems():
        combombZip.write(k, v, zipfile.ZIP_DEFLATED)
    
def zipItPosix(filename):
    files["../../../ComBomb/scripts/ComBomb.sh"]                   = "ComBomb/ComBomb.sh"
    files["ComBombGui/ComBombGui"]                              = "ComBomb/ComBombGui"
    files["/usr/lib/x86_64-linux-gnu/libX11-xcb.so.1"]          = "ComBomb/platforms/libX11-xcb.so.1"
    files["/usr/lib/x86_64-linux-gnu/libxcb-render-util.so.0"]  = "ComBomb/platforms/libxcb-render-util.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-render.so.0"]       = "ComBomb/platforms/libxcb-render.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb.so.1"]              = "ComBomb/platforms/libxcb.so.1"
    files["/usr/lib/x86_64-linux-gnu/libxcb-image.so.0"]        = "ComBomb/platforms/libxcb-image.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-icccm.so.4"]        = "ComBomb/platforms/libxcb-icccm.so.4"
    files["/usr/lib/x86_64-linux-gnu/libxcb-sync.so.0"]         = "ComBomb/platforms/libxcb-sync.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-xfixes.so.0"]       = "ComBomb/platforms/libxcb-xfixes.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-shm.so.0"]          = "ComBomb/platforms/libxcb-shm.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-randr.so.0"]        = "ComBomb/platforms/libxcb-randr.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-shape.so.0"]        = "ComBomb/platforms/libxcb-shape.so.0"
    files["/usr/lib/x86_64-linux-gnu/libxcb-keysyms.so.1"]      = "ComBomb/platforms/libxcb-keysyms.so.1"
    files["/usr/lib/x86_64-linux-gnu/libxcb-util.so.0"]         = "ComBomb/platforms/libxcb-util.so.0"
    filename += ".tar.bz2"
    file = tarfile.open(filename, "w:bz2")
    for k, v in files.iteritems():
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
    print("The following modules can be individually built")
    for b in builds:
        print ("    --" + b)
    os._exit(1)

def main(argv):
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
        opts, args = getopt.getopt(argv, "hdrcv", args)
    except getopt.GetoptError as e:
        print "Error: " + str(e)
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
        if opt[2:] in buildVals.keys():
            buildsToRun.append(opt[2:])

    if (len(buildsToRun) > 0):
        for b in builds:
            buildVals[b] = False
        for b in buildsToRun:
            buildVals[b] = True
    else:
        delBuildTree("../install")
    if (buildVals["CDLogger"] == True):
        cmakeBuild("CDLogger", buildType, buildClean, buildVerbose)
    if (buildVals["cppssh"] == True):
        cmakeBuild("cppssh", buildType, buildClean, buildVerbose)
    if (buildVals["QueuePtr"] == True):
        cmakeBuild("QueuePtr", buildType, buildClean, buildVerbose)
    if (buildVals["ComBomb"] == True):
        combombBuild(buildClean, buildType)
    print("Done")

if __name__ == "__main__":
    main(sys.argv[1:])
