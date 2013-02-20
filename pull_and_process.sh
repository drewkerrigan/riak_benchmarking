#! /bin/bash

s3cmd sync s3://basho-proserv-benchmarking/results . --exclude "*ip-*" --exclude "*preload*" --exclude "*snapshot*" --exclude "*perfmed*" --exclude "*testing*" --exclude "*slriakservers/20130208*" --exclude "*slriakservers/20130209*"   --exclude "*slriakservers/20130207_214936*" --exclude "*functionality_2i-1.2.1-eleveldb*" --exclude "*functionality_2i-1.3-eleveldb*"

python SummarizeResults.py results > summary.csv
