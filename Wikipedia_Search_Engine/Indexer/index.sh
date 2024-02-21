#!/bin/bash

mkdir $2
python nltk_download.py
python indexer.py "$1" "$2"
