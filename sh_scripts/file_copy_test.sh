#!/bin/sh
a="$1"
if [ -z "$a" ]; then
    a="10000"
fi

files=(jsons/*)
`mkdir -p generated_jsons`
for i in `seq 1 $a`
do
    rand_name=`head -c 30 /dev/urandom | md5`
    rand_file="${files[RANDOM % ${#files[@]}]}"
    `cp $rand_file "../jsons/$rand_name.json"`
done
