#!/bin/sh

INPUT_DIR="$(pwd)"

if [ -d "$INPUT_DIR" ]; then
    DOT_FILES=`find .  -name "*.dot"`
    for file in $DOT_FILES
    do
        dest=`sed s/.dot/.pdf/ <<< "$file"`
        dot -Tpdf $file > $dest
    done
else
    echo "Input directory $INPUT_DIR does not exist"
fi
