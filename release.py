#!/usr/bin/env python

# Publishes a release to GitHub.
#
# The version comes from the tag the ComBomb checkout sits on, so this script
# never creates a tag - tagrepo.sh does that, once, on one machine. Run this on
# each platform you ship from: the first run creates the GitHub release, and
# every run after that adds its artifact to the release already there.
#
#   west cb-tag "what changed"                 # once, on one machine
#   git -C ComBomb checkout <tag>              # tagrepo.sh leaves you here
#   west cb-release                            # build and publish, per platform

import os, sys, platform, getopt, subprocess
import multiprocessing
sys.dont_write_bytecode = True
import makeutils

baseDir = os.path.dirname(os.path.realpath(__file__))
topDir = os.path.dirname(baseDir)
combombDir = os.path.join(topDir, "ComBomb")
artifactDir = os.path.join(baseDir, "build", "ComBomb")

sys.path.append(combombDir)
import createVersion

def die(msg):
    print("Error: " + msg)
    sys.stdout.flush()
    os._exit(1)

def run(cmd, cwd = None):
    print(" ".join(cmd))
    if (subprocess.call(cmd, cwd = cwd) != 0):
        die("command failed: " + " ".join(cmd))

def releaseVersion():
    # The same string the build stamps into the binary and into the archive
    # name, so the artifact looked for below is the one the build just wrote.
    # getVerStr runs git in the working directory, hence the chdir.
    cwd = os.getcwd()
    os.chdir(combombDir)
    version = createVersion.CreateVer().getVerStr().decode("utf-8")
    os.chdir(cwd)
    # "git describe --dirty --always" names a tag exactly when HEAD is on one.
    # Otherwise it carries a -<n>-g<sha> or -dirty suffix, or falls back to a
    # bare abbreviated sha, and none of those name a release.
    # show-ref rather than rev-parse: rev-parse parses its argument as a
    # revision, and "v1.2.3-4-gabc1234" is valid describe syntax that resolves
    # to a commit, so it would accept a version that is four commits past a tag.
    devnull = open(os.devnull, 'w')
    isTag = subprocess.call(["git", "show-ref", "--verify", "--quiet",
                             "refs/tags/" + version], cwd = combombDir,
                            stdout = devnull, stderr = devnull)
    devnull.close()
    if (isTag != 0):
        die("ComBomb is at '" + version + "', which is not a release tag.\n"
            "       Tag with 'west cb-tag \"description\"', or check out an\n"
            "       existing tag: git -C ComBomb checkout <tag> && west update")
    return version

def buildRelease(qtPath, buildJobs):
    if (platform.system() == "Windows"):
        cmd = [sys.executable, os.path.join(baseDir, "build.py"), "-c", "-j" + buildJobs]
        if (qtPath != ""):
            cmd.append("--qt=" + qtPath)
        run(cmd, cwd = baseDir)
    else:
        # Linux ships from the container so the binary keeps its glibc 2.35 floor.
        run(["bash", os.path.join(baseDir, "docker-2204", "run.sh")], cwd = baseDir)

def findArtifact(version):
    if (platform.system() == "Windows"):
        artifact = os.path.join(artifactDir, "ComBomb-" + version + ".zip")
    else:
        artifact = os.path.join(artifactDir, "ComBomb-" + version + ".tar.bz2")
    if (os.path.exists(artifact) == False):
        die("no artifact at " + artifact + "\n"
            "       A release build names its archive after the tag, so this\n"
            "       usually means the build ran against untagged sources.")
    return artifact

def releaseExists(gh, version):
    devnull = open(os.devnull, 'w')
    ret = subprocess.call([gh, "release", "view", version], cwd = combombDir,
                          stdout = devnull, stderr = devnull)
    devnull.close()
    return (ret == 0)

def publish(version, artifact, dryRun):
    # gh reads the target repository from ComBomb's origin remote.
    gh = makeutils.which("gh")
    if (releaseExists(gh, version) == True):
        print("Release " + version + " already exists, adding this platform's artifact")
    else:
        # --verify-tag makes gh refuse to invent a tag that is not on the remote
        # yet, and --notes-from-tag takes the notes from the annotated tag that
        # tagrepo.sh wrote.
        print("Creating release " + version)
        if (dryRun == False):
            run([gh, "release", "create", version, "--verify-tag",
                 "--notes-from-tag", "--title", version], cwd = combombDir)
    if (dryRun == False):
        run([gh, "release", "upload", version, artifact, "--clobber"], cwd = combombDir)
    else:
        print("Dry run: would upload " + artifact + " to release " + version)

def usage():
    print("Publish a ComBomb release to GitHub")
    print(" -h --help")
    print(" -n --dry-run    Build and check, but neither create the release nor upload")
    print("    --no-build   Publish the artifact already in the build tree")
    print("    --qt=<path>  Path to a Qt6 install, passed to build.py on Windows.")
    print("                 Defaults to $CMAKE_PREFIX_PATH if set.")
    print(" -j#             Parallel build jobs")
    sys.stdout.flush()
    os._exit(1)

def main(argv):
    qtPath = os.environ.get("CMAKE_PREFIX_PATH", "")
    buildJobs = str(multiprocessing.cpu_count())
    dryRun = False
    doBuild = True
    try:
        opts, args = getopt.getopt(argv, "hnj:", ["help", "dry-run", "no-build", "qt="])
    except getopt.GetoptError as e:
        print("Error: " + str(e))
        usage()
    for opt, arg in opts:
        if (opt in ('-h', '--help')):
            usage()
        if (opt in ('-n', '--dry-run')):
            dryRun = True
        if (opt == '--no-build'):
            doBuild = False
        if (opt == '--qt'):
            qtPath = arg
        if (opt in ('-j')):
            buildJobs = arg

    version = releaseVersion()
    print("Release " + version + " from " + platform.system())
    if (doBuild == True):
        buildRelease(qtPath, buildJobs)
    publish(version, findArtifact(version), dryRun)
    print("Done")

if __name__ == "__main__":
    main(sys.argv[1:])
