#!/usr/bin/env python
import sys, traceback, os, platform, tempfile, getopt
from subprocess import call
sys.dont_write_bytecode = True
import makeutils

boostname = "boost_1_59_0"
boostfile = boostname + ".tar.bz2"
boosturl = "http://downloads.sourceforge.net/project/boost/boost/1.59.0/" + boostfile
boostdir = boostname + "/boost"

builddir = os.getcwd()
boostexternaldir = builddir +  "/../external/boost"
boostsrcdir = boostexternaldir + "/" + boostname

def runBootstrap():
    bootstrap = []
    # bootstrap on windows is done as part of runB2Windows becuase it needs the vcvars also
    if (platform.system() != "Windows"):
        bootstrap = ["./bootstrap.sh"]
        call(bootstrap)

def runB2Linux(extraArgs, buildJobs, installdir):
    cmd = ["./b2", "link=static", "-j", str(buildJobs), "install", "-a", "toolset=gcc", "--prefix=" + installdir]
    cmd.extend(extraArgs)
    call(cmd)

def runB2Windows(extraArgs, buildJobs, installdir):
    batfilefd, batfilename = tempfile.mkstemp(suffix=".bat", text=True)
    file = os.fdopen(batfilefd, 'w')
    msvsfound = False
    msvsvars = []
    for ver in range (14, 8, -1):
        envvar = "VS" + str(ver) + "0COMNTOOLS"
        msvsvars.append(envvar)
        if (envvar in os.environ):
            visualStudioInstallDir = os.environ[envvar];
            file.write("call \"" + visualStudioInstallDir + "..\\..\\VC\\vcvarsall.bat\" x86\n")
            file.write("call bootstrap.bat msvc\n")
            cmd = "b2 --toolset=msvc-" + str(ver) + ".0 " + " ".join(extraArgs) + " link=static runtime-link=static -j " + str(buildJobs) + " install --layout=system --includedir=" + installdir + " -a variant="
            file.write(cmd + "release --libdir=" + installdir + "/lib/release\n")
            file.write(cmd + "debug --libdir=" + installdir + "/lib/debug\n")
            file.close()
            print batfilename
            call([batfilename])
            msvsfound = True
            break
    if (msvsfound == False):
        print("Unable to find env var for MSVS, tried: ", msvsvars)

def runB2(extraArgs, buildJobs, installdir):
    if (platform.system() == "Windows"):
        runB2Windows(extraArgs, buildJobs, installdir)
    else:
        extraArgs.extend(["cxxflags=-fPIC"]);
        runB2Linux(extraArgs, buildJobs, installdir)
    
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

        installdir = makeutils.downloadAndExtract(boostexternaldir, boosturl, boostsrcdir, clean)
        os.chdir(boostsrcdir)
        runBootstrap()
        extraArgs = [
            "--with-system",
            ]
        runB2(extraArgs, buildJobs, installdir)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
if __name__ == "__main__":
    main(sys.argv[1:])

