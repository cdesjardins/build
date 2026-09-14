# ComBomb build scripts

The scripts that build ComBomb and its dependencies. This project is checked out
as `build/` in the ComBomb workspace and in a standalone cppssh workspace, and it
contributes the `west cb-*` commands below to both.

All python scripts work with python 2.6 or higher, including python 3.x.

## west commands

| command | runs | what it does |
|---|---|---|
| `west cb-build` | `build.py` | builds CDLogger → cppssh → QueuePtr → ComBomb |
| `west cb-shell` | `docker-2204/run.sh shell` | opens a shell in the Ubuntu 22.04 build container |
| `west cb-boost` | `makeboost.py` | downloads and builds Boost into `external/boost` |
| `west cb-botan` | `makebotan.py` | builds Botan into `external/botan/install` |
| `west cb-tag` | `tagrepo.sh` | tags a release across every project in the workspace |
| `west cb-release` | `release.py` | builds the tagged sources and publishes them to GitHub |

They run from anywhere inside the workspace, with `build/` as the working
directory, and pass every argument through untouched — so `west cb-build -h`
prints `build.py`'s own help, and

```bash
west cb-build -d -j8 --qt=~/Qt/6
```

is the same as `cd build && ./build.py -d -j8 --qt=~/Qt/6`.

`west-commands.yml` and `west_commands.py` are the whole implementation. They are
a convenience only: every script stays usable on its own, and nothing in the
build depends on west being installed.

## Host build or container build

None of these scripts know what docker is. They build wherever they are run, so
where you run them is the whole decision:

- **Natively** — `./build.py`, against the host's glibc and Qt. The fast loop.
- **In the 22.04 container** — `west cb-shell`, then the same `./build.py`. The
  binary gets a glibc 2.35 floor and runs on Ubuntu 22.04 and newer, which is
  what you want for anything you intend to ship.

The shell starts in the build directory with `~/sw` bind-mounted at the same
absolute path it has on the host, the gcc-12 toolchain preset by the image, and
`CMAKE_PREFIX_PATH` pointing at the 22.04 Qt — so a bare `./build.py` there picks
up the right Qt without `--qt`.

`docker-2204/run.sh` with no arguments is the unattended version of the same
thing: Qt (first run only) → Boost → Botan → ComBomb, no shell. It takes
environment variables rather than flags:

```bash
./docker-2204/run.sh                        # one-shot build
FORCE_QT=1 ./docker-2204/run.sh             # force a fresh Qt rebuild
DOCKER="sudo docker" ./docker-2204/run.sh   # not in the docker group yet
```

See `docker-2204/README.md` for the full story on why the container exists.

## First build

Boost and Botan are built once, then only when they change:

```bash
west cb-boost
west cb-botan
west cb-build
```

## The scripts

- **`build.py`** — builds the four modules in dependency order. Release by
  default; a dirty tree on a release build prints a warning.

  ```
  -d --debug        -r --release      -v --verbose
  -c --clean        -u --uncrustify   -j#
  --qt=<path>       Qt6 install dir → CMAKE_PREFIX_PATH for ComBomb.
                    Defaults to $CMAKE_PREFIX_PATH if set.
  --generator=<g>   CMake generator, default "Ninja". Also "Ninja Multi-Config",
                    "Visual Studio 17 2022", "Unix Makefiles".
  --arch=<a>        cmake -A <arch> for VS generators: Win32, x64, ARM64.
                    Ignored for Ninja.
  --QueuePtr --CDLogger --cppssh --ComBomb
                    Build only the listed modules; repeatable.
  ```

- **`makeboost.py`** — downloads the Boost tarball, bootstraps it and installs a
  static build under `external/boost`. Takes `-c` to re-extract from scratch and
  `-j#` for parallel jobs. Boost is not a git project, so west does not manage it.

- **`makebotan.py`** — wipes `external/botan/install`, then configures and builds
  Botan twice, debug and release. Takes no options.

- **`tagrepo.sh`** — release tagging. Requires a description:

  ```bash
  west cb-tag "what changed in this release"
  ```

  Tags every project with `v<year>.<dayofyear>.<hour>` and pushes the tags, then
  freezes the manifest to SHAs, commits it to the manifest repository and tags
  that commit. `west init -m <manifest repo url> --mr <tag>` reproduces the
  release exactly.

- **`release.py`** — publishes a release. Takes the version from
  `createVersion`, the same module the build uses to stamp the binary and name
  the archive, and refuses to run unless that version is an exact tag — so it
  can never create one. Builds (container on Linux, native on Windows), then
  creates the GitHub release if it is missing and uploads this platform's
  artifact to it.

  ```
  -n --dry-run    Build and check, but neither create the release nor upload
     --no-build   Publish the artifact already in the build tree
     --qt=<path>  Path to a Qt6 install, passed to build.py on Windows
  -j#             Parallel build jobs
  ```

- **`makeutils.py`** — shared helpers for the scripts above, not an entry point.

- **`call_Uncrustify.sh`, `uncrustify.cfg`** — style pass, run by `build.py -u`
  on Linux release builds when uncrustify is installed.

- **`docker-2204/`** — the Ubuntu 22.04 builder image and its driver scripts.

## Cutting a release

Tagging happens once, on one machine. Publishing happens on each platform you
ship from, and never tags anything:

```bash
# once, wherever you like
west cb-tag "what changed in this release"    # tags every project, freezes the
                                              # manifest, leaves ComBomb on the tag
west cb-release                               # container build, creates the
                                              # GitHub release, uploads the tarball

# later, on the other platform
git -C ComBomb fetch --tags
git -C ComBomb checkout v2026.257.14
west update                                   # frozen manifest pins every project
west cb-release                               # native build, adds the zip to the
                                              # release that is already there
```

The second `west update` is what makes both platforms build the same sources:
the manifest committed at the tag pins every project to a SHA.

`release.py` never creates a tag. It takes the version from `createVersion` —
so the artifact it publishes is the one the build just named — and refuses to
run unless that version names an existing tag. It also passes `--verify-tag` to
`gh release create`, which aborts rather than pushing a tag that is not on the
remote yet. The second platform finds the release already present and only
uploads.

Requires the GitHub CLI (`gh`) authenticated for the ComBomb repository
(`gh auth login`); the release attaches to whatever ComBomb's origin points at.

## Requirements

- cmake, ninja, a C++20 compiler, and git on PATH (git is used to generate the
  version string).
- A Qt6 install reachable through `--qt=<path>` or `$CMAKE_PREFIX_PATH`, for the
  ComBomb GUI module.
- west, for the `cb-*` commands only (`pip install west`).
- Docker, for `cb-shell` and `docker-2204/run.sh` only.
- The GitHub CLI (`gh`), authenticated, for `cb-release` only.
