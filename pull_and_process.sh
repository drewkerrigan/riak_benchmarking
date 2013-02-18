#! /bin/bash

s3cmd sync s3://basho-proserv-benchmarking/results . --exclude "*ip-*" --exclude "*preload*" --exclude "*perfmed* --exclude "*testing*""

python SummarizeResults.py results > summary.csv
