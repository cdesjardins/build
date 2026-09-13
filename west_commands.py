# west extension commands for the scripts in this directory.
#
# Each command is a thin wrapper: it runs one script from the build project
# with the build directory as the working directory, and forwards every
# argument through untouched. So
#
#     west cb-build -d -j8 --qt=~/Qt/6
#
# does the same thing as
#
#     cd build && ./build.py -d -j8 --qt=~/Qt/6
#
# with the advantage that it works from anywhere in the workspace. The scripts
# stay usable on their own; nothing here is required in order to build.

import sys
from pathlib import Path

from west.commands import WestCommand

# This file sits at the root of the build project.
buildDir = Path(__file__).resolve().parent

class _ScriptCommand(WestCommand):
    # Set by each subclass below.
    script = None
    scriptArgs = []
    cmdName = None
    cmdHelp = None

    def __init__(self):
        super().__init__(self.cmdName, self.cmdHelp, self.describe(),
                         accepts_unknown_args=True)

    def describe(self):
        return ("Runs " + self.script + " from the build project, with the build\n"
                "directory as the working directory. Every argument is passed to\n"
                "the script unchanged, so \"west " + self.cmdName + " -h\" prints\n"
                "the script's own help.")

    def launcher(self):
        # The scripts carry a "#!/usr/bin/env python" shebang, but plenty of
        # distributions ship only python3. Run them under the interpreter west
        # itself is running, which sidesteps that and the exec bit both.
        return [sys.executable]

    def do_add_parser(self, parser_adder):
        # add_help is off so that -h reaches the script rather than being
        # answered by this wrapper.
        return parser_adder.add_parser(self.cmdName,
                                       help=self.cmdHelp,
                                       description=self.description,
                                       add_help=False)

    def do_run(self, args, unknown):
        cmd = self.launcher() + [str(buildDir / self.script)] + self.scriptArgs + unknown
        self.check_call(cmd, cwd=buildDir)

class CbBuild(_ScriptCommand):
    script = "build.py"
    cmdName = "cb-build"
    cmdHelp = "build the ComBomb modules"

class CbShell(_ScriptCommand):
    script = "docker-2204/run.sh"
    scriptArgs = ["shell"]
    cmdName = "cb-shell"
    cmdHelp = "open a shell in the Ubuntu 22.04 build container"

    def describe(self):
        return ("Builds the ubuntu:22.04 image if needed and drops you into a\n"
                "shell in it, sitting in the build directory with the workspace\n"
                "bind-mounted and CMAKE_PREFIX_PATH pointing at the 22.04 Qt.\n"
                "Run ./build.py in there exactly as you would on the host.")

    def launcher(self):
        return ["bash"]

class CbBoost(_ScriptCommand):
    script = "makeboost.py"
    cmdName = "cb-boost"
    cmdHelp = "build the vendored Boost"

class CbBotan(_ScriptCommand):
    script = "makebotan.py"
    cmdName = "cb-botan"
    cmdHelp = "build Botan"

class CbTag(_ScriptCommand):
    script = "tagrepo.sh"
    cmdName = "cb-tag"
    cmdHelp = "tag a release across every project in the workspace"

    def launcher(self):
        return ["bash"]
