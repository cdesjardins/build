#!/usr/bin/env python
import urllib2, os, tarfile, platform, shutil

def download(fileUrl):
    print("Downloading: " + fileUrl)
    filename = fileUrl.split('/')[-1]
    u = urllib2.urlopen(fileUrl)
    f = open(filename, 'wb')
    meta = u.info()
    filesize = int(meta.getheaders("Content-Length")[0])

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / filesize)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()

def extractCompressedTar(compressedTar):
    print("Extracting " + compressedTar + "...")
    filename, fileExtension = os.path.splitext(compressedTar)
    file = tarfile.open(compressedTar, "r:" + fileExtension[1:])
    file.extractall()
    file.close()

def which(file, fatal = True, extraDirs = None):
    if (platform.system() == "Windows"):
        file += ".exe"
    if (extraDirs != None):
        for path in extraDirs:
            if os.path.exists(path + "/" + file):
                return path + "/" + file
    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.exists(path + "/" + file):
                return path + "/" + file
    print(file + " not found")
    os._exit(1)
    return None

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
        extractCompressedTar(filename)
    else:
        print("Skip extraction of qt archive because the " + srcdir + " directory already exists")
    installdir = externaldir + "/install"
    if (os.path.exists(installdir) == True):
        print("Deleting: " + installdir)
        shutil.rmtree(installdir)
    os.chdir(cwd)
    return installdir
