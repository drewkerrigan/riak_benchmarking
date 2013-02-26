#! /bin/bash
s3cmd sync s3://basho-proserv-benchmarking/results . --exclude "*ip-*" --exclude "*preload*" --exclude "*snapshot*" --exclude "*perfmed*" --exclude "*testing*" --exclude "*functionality_2i-1.2.1-eleveldb*" --exclude "*functionality_2i-1.3-eleveldb*" --exclude "*mdc-repl-1.3.0rc4_original*"
