#!/usr/bin/env bash

if [ -z "$1" ]
then
    echo "Run: sh scripts/common/similarities.sh 'Dataset'"
    exit 1
fi

cd src/main/python
python sos/analyze.py get_similarities $1 java_python
