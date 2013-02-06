#! /bin/bash

s3cmd sync s3://basho-proserv-benchmarking/results . --exclude "*ip-*" --exclude "*preload*" --exclude "*perfmed*"

python SummarizeResults.py results > summary.csv