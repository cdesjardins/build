#!/usr/bin/env python

# This is the master combomb build script
# which is used to create releases.

import shutil, sys, os, platform, zipfile, tarfile, getopt, atexit
from subprocess import call
from subprocess import Popen, PIPE
import multiprocessing

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
    def __init__(self, buildType, runUncrustify):
        self.home = os.path.dirname(os.path.realpath(__file__))
        self.uncrust = self.home + "/call_Uncrustify.sh"
        self.buildType = buildType.lower()
        self.runUncrustify = runUncrustify

    def callUncrustify(self, directory, ext):
        run(self.uncrust + " " + directory + " " + ext)

    def uncrustify(self, directory):
        if (self.runUncrustify and (platform.system() == "Linux") and (self.buildType == "release") and (makeutils.which("uncrustify", fatal=False) != None)):
            self.callUncrustify(directory, "*.cpp")
            self.callUncrustify(directory, "*.h")

def gitVersionCheck(buildType, directory):
    gitVerStr = ""
    if (haveCreateVersion == True):
        c = Chdir(directory)
        CreateVer = createVersion.CreateVer()
        gitVerStr = CreateVer.getVerStr()
        if (gitVerStr.find(b"dirty") > 0) and (buildType.lower() == "release"):
            print("\033[31mBuilding on dirty codebase (" + str(gitVerStr) + " - " + os.getcwd() + "):\033[0m"),
            sys.stdout.flush()
            sys.stdin.read(1)
    return gitVerStr

# if split == False, then cmd must be an array
def run(cmd, split=True):
    if (split == True):
        cmds = cmd.split(" ")
        print(cmd)
    else:
        cmds = cmd
        print(" ".join(cmd))
    if (call(cmds)):
        sys.exit(1)

def cmakeBuildLinux(baseDir, buildType, buildVerbose, buildJobs, extraArgs, target):
    cmake = ["cmake", "../../../" + baseDir, "-DCMAKE_BUILD_TYPE=" + buildType]
    if extraArgs:
        cmake.extend(extraArgs)
    run(cmake, split=False)
    build = ["cmake", "--build", ".", "-j", buildJobs]
    if target:
        build.extend(["--target", target])
    if buildVerbose:
        build.append("--verbose")
    run(build, split=False)

def cmakeBuildWindows(baseDir, buildType, buildVerbose, buildJobs, extraArgs, target):
    if "VISUALSTUDIOVERSION" not in os.environ:
        print("Unable to find VISUALSTUDIOVERSION in env, please run from MSVS command prompt")
        sys.exit(1)
    msvsVer = os.environ["VISUALSTUDIOVERSION"]
    msvsVer = msvsVer[:msvsVer.find('.')]
    msvsGenerators = {
        "10": "Visual Studio 10 2010",
        "11": "Visual Studio 11 2012",
        "12": "Visual Studio 12 2013",
        "14": "Visual Studio 14 2015",
        "15": "Visual Studio 15 2017",
        "16": "Visual Studio 16 2019",
        "17": "Visual Studio 17 2022",
    }
    gen = msvsGenerators.get(msvsVer)
    if gen is None:
        print("Unsupported Visual Studio version: " + msvsVer)
        sys.exit(1)
    cmake = [
        "cmake", "../../../" + baseDir, "-A", "Win32", "-G", gen,
        # Match the static CRT (/MT, /MTd) used by ComBomb so the sibling
        # static libs link without LNK2038 RuntimeLibrary mismatches.
        "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded$<$<CONFIG:Debug>:Debug>",
    ]
    if extraArgs:
        cmake.extend(extraArgs)
    run(cmake, split=False)
    build = ["cmake", "--build", ".", "--config", buildType, "-j", buildJobs]
    if target:
        build.extend(["--target", target])
    if buildVerbose:
        build.append("--verbose")
    run(build, split=False)

def cmakeBuild(baseDir, buildType, buildClean, buildVerbose, buildJobs, runUncrustify,
               extraArgs=None, target="install"):
    buildTarget = "build/" + baseDir
    cleanTarget(buildTarget, buildClean)
    uncrustify(buildType, runUncrustify).uncrustify("../" + baseDir)
    gitVerStr = gitVersionCheck(buildType, "../" + baseDir)
    c = Chdir(buildTarget)
    if (platform.system() == "Linux"):
        cmakeBuildLinux(baseDir, buildType, buildVerbose, buildJobs, extraArgs, target)
    else:
        cmakeBuildWindows(baseDir, buildType, buildVerbose, buildJobs, extraArgs, target)
    return gitVerStr

def cleanTarget(buildTarget, buildClean):
    if (buildClean == True):
        delBuildTree(buildTarget)
    if (os.path.exists(buildTarget) == False):
        os.makedirs(buildTarget)

def combombBuild(buildClean, buildType, buildVerbose, buildJobs, runUncrustify, qtPath):
    combombSrcDir = os.getcwd() + "/../ComBomb"
    buildTarget = os.getcwd() + "/build/ComBomb"
    uncrustify(buildType, runUncrustify).uncrustify(os.getcwd() + "/../include")
    extraArgs = ["-DCMAKE_PREFIX_PATH=" + qtPath] if qtPath else None
    gitVerStr = cmakeBuild(
        "ComBomb", buildType, buildClean, buildVerbose, buildJobs, runUncrustify,
        extraArgs=extraArgs, target=None,
    ).decode("utf-8")
    shutil.copy(combombSrcDir + "/ComBombGui/images/ComBomb64.png", buildTarget)
    buildLog(combombSrcDir, buildTarget)
    if (buildType.lower() == "release"):
        c = Chdir(buildTarget)
        zipIt(gitVerStr, buildType)

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

def zipItWindows(filename, buildType):
    files["ComBombGui/" + buildType + "/ComBombGui.exe"] = "ComBomb/ComBombGui.exe"
    filename += ".zip"
    combombZip = zipfile.ZipFile(filename, "w")
    for k, v in files.items():
        combombZip.write(k, v, zipfile.ZIP_DEFLATED)
    
def zipItPosix(filename):
    files["../../../ComBomb/scripts/ComBomb.sh"]                   = "ComBomb/bin/ComBomb.sh"
    files["ComBombGui/ComBombGui"]                              = "ComBomb/bin/ComBombGui"
    filename += ".tar.bz2"
    file = tarfile.open(filename, "w:bz2")
    for k, v in files.items():
        print(os.path.realpath(k))
        file.add(os.path.realpath(k), v)

def zipIt(gitVerStr, buildType):
    vers = gitVerStr.split("-")

    #filename = "ComBomb-" + vers[0]
    #if (len(vers) > 1):
    #    filename = filename + "-" + vers[1]

    filename = "ComBomb-" + gitVerStr
    if (platform.system() == "Windows"):
        zipItWindows(filename, buildType)
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
    print(" -u --uncrustify")
    print(" -j#")
    print(" --qt=<path>     Path to a Qt6 install (sets CMAKE_PREFIX_PATH for ComBomb).")
    print("                 Defaults to $CMAKE_PREFIX_PATH if set.")
    print("The following modules can be individually built")
    for b in builds:
        print("    --" + b)
    os._exit(1)

def main(argv):
    buildJobs = str(multiprocessing.cpu_count())
    buildClean = False
    buildVerbose = False
    runUncrustify = False
    buildType = "Release"
    qtPath = os.environ.get("CMAKE_PREFIX_PATH", "")
    builds = ["QueuePtr", "CDLogger", "cppssh", "ComBomb"]
    buildVals = {}
    for b in builds:
        buildVals[b] = True
    args = ["help", "debug", "release", "clean", "verbose", "uncrustify", "qt="]
    args.extend(builds)
    buildsToRun = []
    try:
        opts, args = getopt.getopt(argv, "hdrcvuj:", args)
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
        if (opt in ('-u', '--uncrustify')):
            runUncrustify = True
        if (opt in ('-j')):
            buildJobs = arg
        if (opt == '--qt'):
            qtPath = arg
        if opt[2:] in list(buildVals.keys()):
            buildsToRun.append(opt[2:])

    if (len(buildsToRun) > 0):
        for b in builds:
            buildVals[b] = False
        for b in buildsToRun:
            buildVals[b] = True
    elif (buildClean == True):
        delBuildTree("../install")
    if (buildVals["CDLogger"] == True):
        cmakeBuild("CDLogger", buildType, buildClean, buildVerbose, buildJobs, runUncrustify)
    if (buildVals["cppssh"] == True):
        cmakeBuild("cppssh", buildType, buildClean, buildVerbose, buildJobs, runUncrustify)
    if (buildVals["QueuePtr"] == True):
        cmakeBuild("QueuePtr", buildType, buildClean, buildVerbose, buildJobs, runUncrustify)
    if (buildVals["ComBomb"] == True):
        combombBuild(buildClean, buildType, buildVerbose, buildJobs, runUncrustify, qtPath)
    print("Done")

if __name__ == "__main__":
    main(sys.argv[1:])
