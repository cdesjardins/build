#!/bin/bash

ret=0
if [ -n "$1" ] && [ -d "$1" ] && [ -n "$2" ]; then
    filesuffix=$2
    file_list=`find ${1} -name "${filesuffix}" -type f`
    DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
    for file2indent in $file_list; do
        uncrustify "$file2indent" -c "$DIR/uncrustify.cfg" --replace --no-backup
    done
else
    let ret=1
fi

if [ "$ret" -eq "1" ]; then
    echo "Syntax is: $0 dirname glob"
    echo "Example: $0 . *.cpp"
fi
exit $ret
