#!/usr/bin/env python
import os, tarfile, platform, shutil, zipfile, sys

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

def download(fileUrl):
    print("Downloading: " + fileUrl)
    filename = fileUrl.split('/')[-1]
    u = urlopen(fileUrl)
    f = open(filename, 'wb')

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d" % (file_size_dl)
        status = status + chr(8)*(len(status)+1)
        sys.stdout.write(status)

    f.close()

def extractCompressedFile(compressedFile):
    print("Extracting " + compressedFile + "...")
    filename, fileExtension = os.path.splitext(compressedFile)
    if (fileExtension == ".zip"):
        with zipfile.ZipFile(compressedFile) as zf:
            zf.extractall(path=".")
    else:
        file = tarfile.open(compressedFile, "r:" + fileExtension[1:])
        file.extractall()
        file.close()

def _which(file, pathList):
    for path in pathList:
        targetFile = os.path.join(path, file)
        if os.path.exists(targetFile):
            return targetFile
    return None

def which(file, fatal = True, extraDirs = None):
    if (platform.system() == "Windows"):
        file += ".exe"
    ret = None
    if (extraDirs != None):
        ret = _which(file, extraDirs)
    if (ret == None):
        ret = _which(file, os.environ["PATH"].split(os.pathsep))
    if (ret == None):
        print(file + " not found")
        if (fatal == True):
            os._exit(1)
    return ret

def findReplace(find, replace, filename):
    filedata = ""
    with open(filename, 'r') as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace(find, replace)

    # Write the file out again
    with open(filename, 'w') as file:
        file.write(filedata)

def downloadAndExtract(externaldir, url, srcdir, clean):
    if (os.path.exists(externaldir) == False):
        os.makedirs(externaldir)
    cwd = os.getcwd()
    os.chdir(externaldir)
    filename = os.path.basename(url)
    if (os.path.exists(filename) == False):
        download(url)
    else:
        print("Skip download of archive because the " + filename + " already exists")

    if ((clean == True) and (os.path.exists(srcdir) == True)):
        shutil.rmtree(srcdir)

    if (os.path.exists(srcdir) == False):
        extractCompressedFile(filename)
    else:
        print("Skip extraction of qt archive because the " + srcdir + " directory already exists")
    installdir = os.path.join(externaldir, "install")
    if (os.path.exists(installdir) == True):
        print("Deleting: " + installdir)
        shutil.rmtree(installdir)
    os.chdir(cwd)
    return installdir
