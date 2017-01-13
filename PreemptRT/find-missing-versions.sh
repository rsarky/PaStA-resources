#!/bin/bash

stacks=$(find rt-ftp-mirror -name "patches*.gz" -print0 | \
	 xargs -0 -n 1 basename | sed -e "s/patches-\(.*\)\.tar\.gz/\1/g" | \
	 sort | uniq)

declare -a corrupt_stacks=(
# does not apply
3.0.14-rt31
# skip patches containing -feat*
3.2.43-rt63-feat1
3.2.43-rt63-feat2
3.4.41-rt55-feat1
3.4.41-rt55-feat2
3.4.41-rt55-feat3
# skip such things
3.2-rc1-52e4c2a05-rt1
3.2-rc1-52e4c2a05-rt2
# skip x.y.z.w versions
3.6.11.1-rt32
3.6.11.2-rt33
3.6.11.2-rt34
3.6.11.3-rt35
3.6.11.4-rt36
3.6.11.5-rt37
3.6.11.6-rt38
3.6.11.7-rt39
3.6.11.8-rt40
3.6.11.8-rt41
3.6.11.9-rt42
3.8.13.13-rt24
3.8.13.13-rt25
3.8.13.13-rt26
3.8.13.14-rt27
3.8.13.14-rt28
3.8.13.14-rt29
3.8.13.14-rt30
3.8.13.14-rt31
3.8.13.7-rt18
3.8.13.9-rt20
)

for stack in $stacks
do
	for corrupt in "${corrupt_stacks[@]}"
	do
		if [[ $stack == $corrupt ]]
		then
			corrupt=true
			break
		fi
	done
	if [[ $corrupt == true ]]
	then
		continue
	fi

	if [ ! -f resources/stack-hashes/${stack} ]
	then
		echo missing $stack
	fi
done
