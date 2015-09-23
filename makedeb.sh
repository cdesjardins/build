#!/bin/bash -e

VERSION=`(cd ../ComBomb && git describe) | sed s/v//`
PACKAGE=ComBomb-$VERSION
INSTDIR=usr
rm -rf build/ComBomb/ComBomb build/ComBomb/$PACKAGE *.deb
tar jxvf build/ComBomb/ComBomb-*.tar.bz2 -C build/ComBomb/
INSTSIZE=`du --block-size 1024 -c build/ComBomb/ComBomb | grep "	total" | cut -d "	" -f 1`

mkdir -p build/ComBomb/$PACKAGE/$INSTDIR/share/applications
mkdir -p build/ComBomb/$PACKAGE/$INSTDIR/share/pixmaps
mkdir -p build/ComBomb/$PACKAGE/DEBIAN


echo "Package: combomb" > build/ComBomb/$PACKAGE/DEBIAN/control
echo "Version: $VERSION" >> build/ComBomb/$PACKAGE/DEBIAN/control
echo "Section: base" >> build/ComBomb/$PACKAGE/DEBIAN/control
echo "Priority: optional" >> build/ComBomb/$PACKAGE/DEBIAN/control
echo "Architecture: amd64" >> build/ComBomb/$PACKAGE/DEBIAN/control
#echo "Depends: libsomethingorrather (>= 1.2.13), anotherDependency (>= 1.2.6)" >> build/ComBomb/DEBIAN/control
echo "Maintainer: Chris Desjardins <cjd@chrisd.info>" >> build/ComBomb/$PACKAGE/DEBIAN/control
echo "Installed-Size: $INSTSIZE" >> build/ComBomb/$PACKAGE/DEBIAN/control
echo "Description: ComBomb" >> build/ComBomb/$PACKAGE/DEBIAN/control
echo " The turbo encabulator of terminal emulators" >> build/ComBomb/$PACKAGE/DEBIAN/control


cp debian/menu build/ComBomb/$PACKAGE/DEBIAN
cp -a build/ComBomb/ComBomb/bin build/ComBomb/ComBomb/lib build/ComBomb/$PACKAGE/$INSTDIR
cp debian/combomb.desktop build/ComBomb/$PACKAGE/$INSTDIR/share/applications
cp ../ComBomb/ComBombGui/images/ComBomb128.png build/ComBomb/$PACKAGE/$INSTDIR/share/pixmaps/ComBomb.png
dpkg-deb --build build/ComBomb/$PACKAGE
