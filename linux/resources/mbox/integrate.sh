#!/bin/bash

config="../../config"

for i in $(cat ls); do
	if [[ $i == "b.a.t.m"* ]]; then
		list="b.a.t.m.a.n"
		hoster="lists.open-mesh.org"
		shard="0"
	else
		list=$(echo $i | sed -e 's/\([^\.]*\)\..*/\1/')
		hoster=$(echo $i | sed -e 's/[^\.]*\.\(.*\)\../\1/')
		shard=$(echo $i | sed -e 's/.*\.\(.*\)/\1/')
	fi

	basedir="pubin/$hoster/$list"
	if [ -d $basedir ]; then
		echo "skipping $i"
		continue
	fi

	mkdir -p $basedir
	git submodule add https://github.com/linux-mailinglist-archives/$i $basedir/$shard

	echo "[mbox.pubin.\"$hoster\"]" >> $config
	echo -e "\t\"$list\"," >> $config
done
