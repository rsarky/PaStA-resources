#!/bin/bash

mirror="https://www.kernel.org/pub/linux/kernel/projects/rt/"
repo="./repo"
git="git -C $repo"
prefix="preemptrt-"
psd="./psd"
mirror_dst="./mirror"
quilt_dst="./quilt-stacks"

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
4.1.46-rt52-rc1
4.4.148-rt166-rc1
4.4.162-rt176-rc1
4.9.115-rt94-rc1
# erroneous version numbering
4.9.61-rt61
)

function die {
  echo "$@" 1>&2;
  exit -1;
}

function require {
  if [ -z $1 ]
  then
    die "error calling require()"
  else
    hash $1 &> /dev/null || die "Please install $1"
  fi
}

function apply
{
	version=$1
	base=$(sed -e 's/-rt[0-9]\+\(\|-feat[0-9]\+\)$//' <<< $version)
	major=$(sed -e 's/\([0-9]*\.[0-9]*\).*/\1/' <<< $base)
	$git checkout -b ${prefix}${version} v${base} || exit 1
	$git quiltimport --patches $(realpath ${quilt_dst}/${version}/patches/) || exit 1
	echo "$version origin/${prefix}${version} RELDATE $base v$base $($git log -1 --date=short --pretty=format:%cd v$base)" >> $psd
}

# check requirements
require lftp
require git
require rsync
require quilt

# Download current Preempt-RT mirror
echo "syncing rt patch mirror..."
lftp -e "mirror --continue --depth-first --only-missing --parallel=10 \
	--verbose $mirror $mirror_dst ; exit"  \
	 || die "syncing mirror failed"

# Unpack patches
for release in $(find $mirror_dst -name "patches*.gz")
do
	# check if it is already unpacked
	rtversion=$(sed -e 's/.*patches-\(.*\).tar.gz/\1/' <<< $release)
	quilt_dir="${quilt_dst}/$rtversion"
	if [ -d $quilt_dir ]
	then
		continue
	fi

	# Unpack patch stack
	echo "Unpacking $rtversion..."
	mkdir -p $quilt_dir
	tar xvf $release -C $quilt_dir 2>&1 > /dev/null
done

stacks=$(ls $quilt_dst | sort | uniq)
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
		apply $stack
	fi
done
