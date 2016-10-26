#!/bin/sh
arg1="$1"
if [ -z "$arg1" ]; then
    arg1="100"
fi

arg2="$2"
if [ -z "$arg2" ]; then
    arg2="5"
fi

for i in `seq 1 $arg2`
do
  `./file_copy_test.sh $arg1 &`
done
