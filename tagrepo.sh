#!/bin/bash

VERSION=v`date +%Y.%j.%H`
DESC=$@

if [ -z "$DESC" ] ; then
    echo "Description required"
elif ! TOPDIR=`west topdir 2>/dev/null` ; then
    echo "Not in a west workspace"
else
    cd "$TOPDIR"
    MANIFEST=`west manifest --path`
    TMPBRANCH=tagrepo-$VERSION
    # west forall includes the manifest repository by default. Leave it out
    # here; it is tagged below, once the frozen manifest has been committed to
    # it, so that its tag names the commit that reproduces this release.
    PROJECTS=`west list -f '{name}' | grep -v '^manifest$'`

    # forall runs the command through a shell that inherits this environment,
    # so the tag text survives regardless of what is in the description.
    export VERSION DESC
    west forall -c 'git tag -a "$VERSION" -m "$DESC"' $PROJECTS
    west forall -c 'git push --tags' $PROJECTS

    west manifest --freeze -o west.yml.tmp
    mv west.yml.tmp "$MANIFEST"
    MANIFESTDIR=`dirname "$MANIFEST"`
    pushd .
    cd "$MANIFESTDIR"
    ORIG=`git symbolic-ref -q --short HEAD || git rev-parse HEAD`
    git checkout -b "$TMPBRANCH"
    git commit -a -m "$DESC"
    git tag -a "$VERSION" -m "$DESC"
    git push origin "refs/tags/$VERSION"
    # Leave the manifest repository on the tag: that is the state release.py
    # publishes from, and the state anyone reproducing the release checks out.
    git checkout "$VERSION"
    git branch -D "$TMPBRANCH"
    popd
    echo "### $VERSION tagged and pushed; $MANIFESTDIR is at that tag"
    echo "### publish it with 'west cb-release', or go back with 'git -C $MANIFESTDIR checkout $ORIG'"
fi
