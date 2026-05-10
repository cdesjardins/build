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

def isMultiConfigGenerator(generator):
    return (generator.startswith("Visual Studio")
            or generator == "Xcode"
            or "Multi-Config" in generator)

def cmakeBuild(baseDir, buildType, buildClean, buildVerbose, buildJobs, runUncrustify,
               extraArgs=None, target="install", generator="Ninja"):
    buildTarget = "build/" + baseDir
    cleanTarget(buildTarget, buildClean)
    uncrustify(buildType, runUncrustify).uncrustify("../" + baseDir)
    gitVerStr = gitVersionCheck(buildType, "../" + baseDir)
    c = Chdir(buildTarget)
    multiConfig = isMultiConfigGenerator(generator)
    # Ninja + cl.exe on Windows requires running from a Visual Studio
    # Developer Command Prompt (so cl/link/lib are on PATH and INCLUDE/LIB
    # are set). The architecture is whichever flavour of dev prompt is
    # active — x86 prompt → 32-bit, x64 prompt → 64-bit.
    cmake = ["cmake", "-G", generator, "../../../" + baseDir,
             # Static CRT (/MT, /MTd) on MSVC; ignored on other compilers. Keeps
             # the sibling static libs ABI-compatible with ComBomb, otherwise
             # MSVC raises LNK2038 ("RuntimeLibrary mismatch") at the final link.
             "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded$<$<CONFIG:Debug>:Debug>"]
    # Multi-config generators (Visual Studio, Xcode, Ninja Multi-Config) pick
    # the build type at build time via --config; they ignore CMAKE_BUILD_TYPE
    # at configure time and warn if you set it.
    if not multiConfig:
        cmake.append("-DCMAKE_BUILD_TYPE=" + buildType)
    if extraArgs:
        cmake.extend(extraArgs)
    run(cmake, split=False)
    build = ["cmake", "--build", ".", "-j", buildJobs]
    if multiConfig:
        build.extend(["--config", buildType])
    if target:
        build.extend(["--target", target])
    if buildVerbose:
        build.append("--verbose")
    run(build, split=False)
    return gitVerStr

def cleanTarget(buildTarget, buildClean):
    if (buildClean == True):
        delBuildTree(buildTarget)
    if (os.path.exists(buildTarget) == False):
        os.makedirs(buildTarget)

def combombBuild(buildClean, buildType, buildVerbose, buildJobs, runUncrustify, qtPath, generator):
    combombSrcDir = os.getcwd() + "/../ComBomb"
    buildTarget = os.getcwd() + "/build/ComBomb"
    uncrustify(buildType, runUncrustify).uncrustify(os.getcwd() + "/../include")
    extraArgs = ["-DCMAKE_PREFIX_PATH=" + qtPath] if qtPath else None
    gitVerStr = cmakeBuild(
        "ComBomb", buildType, buildClean, buildVerbose, buildJobs, runUncrustify,
        extraArgs=extraArgs, target=None, generator=generator,
    ).decode("utf-8")
    shutil.copy(combombSrcDir + "/ComBombGui/images/ComBomb64.png", buildTarget)
    buildLog(combombSrcDir, buildTarget)
    if (buildType.lower() == "release"):
        c = Chdir(buildTarget)
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
    # qt_standard_project_setup() forces RUNTIME_OUTPUT_DIRECTORY to the top
    # of the build tree on Windows, so the executable lives flat alongside
    # its (would-be) DLL dependencies — not under a per-subdir folder.
    files["ComBombGui.exe"] = "ComBomb/ComBombGui.exe"
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
    print(" -u --uncrustify")
    print(" -j#")
    print(" --qt=<path>     Path to a Qt6 install (sets CMAKE_PREFIX_PATH for ComBomb).")
    print("                 Defaults to $CMAKE_PREFIX_PATH if set.")
    print(" --generator=<g> CMake generator. Defaults to \"Ninja\".")
    print("                 Examples: \"Ninja\", \"Ninja Multi-Config\", \"Visual Studio 17 2022\",")
    print("                 \"Unix Makefiles\".")
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
    generator = "Ninja"
    builds = ["QueuePtr", "CDLogger", "cppssh", "ComBomb"]
    buildVals = {}
    for b in builds:
        buildVals[b] = True
    args = ["help", "debug", "release", "clean", "verbose", "uncrustify", "qt=", "generator="]
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
        if (opt == '--generator'):
            generator = arg
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
        cmakeBuild("CDLogger", buildType, buildClean, buildVerbose, buildJobs, runUncrustify, generator=generator)
    if (buildVals["cppssh"] == True):
        cmakeBuild("cppssh", buildType, buildClean, buildVerbose, buildJobs, runUncrustify, generator=generator)
    if (buildVals["QueuePtr"] == True):
        cmakeBuild("QueuePtr", buildType, buildClean, buildVerbose, buildJobs, runUncrustify, generator=generator)
    if (buildVals["ComBomb"] == True):
        combombBuild(buildClean, buildType, buildVerbose, buildJobs, runUncrustify, qtPath, generator)
    print("Done")

if __name__ == "__main__":
    main(sys.argv[1:])
