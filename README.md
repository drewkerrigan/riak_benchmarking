riak_benchmarking
=================

# Usage
## Pull New Results:
```
s3cmd sync s3://basho-proserv-benchmarking/results . --exclude "*ip-*" --exclude "*preload*"
```
(Note: you must configure s3cmd beforehand)

## Generate New Results CSV:
```
python SummarizeResults.py results > summary.csv
```

## Do All of the Above:
```
./pull_and_process.sh 
```
Check summary.csv for results
