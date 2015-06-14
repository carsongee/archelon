#!/bin/bash

EXPECTED_ARGS=1
E_BADARGS=65
MAX_PYLINT_VIOLATIONS=1
MAX_PEP8_VIOLATIONS=1
PACKAGE_NAME=archelond

progname=$(basename $0) 
usage()
{

	cat <<EOF
Usage: test.sh [options]
Run the test runner and optional quality checks
Options:
 --help print this help message
 -d or --diff-cover report of coverage in diff from origin/master
 -c or --with-coveralls run coveralls at the end (prompting for repo token)
EOF
}

SHORTOPTS="cd"
LONGOPTS="help,with-coveralls,diff-cover"

if $(getopt -T >/dev/null 2>&1) ; [ $? = 4 ] ; then # New longopts getopt.
 OPTS=$(getopt -o $SHORTOPTS --long $LONGOPTS -n "$progname" -- "$@")
else # Old classic getopt.
 # Special handling for --help on old getopt.
 case $1 in --help) usage ; exit 0 ;; esac
 OPTS=$(getopt $SHORTOPTS "$@")
fi

if [ $? -ne 0 ]; then
 echo "'$progname --help' for more information" 1>&2
 exit 1
fi

eval set -- "$OPTS"
quality=false
coveralls=false
diffcover=false
while [ $# -gt 0 ]; do
	: debug: $1
	case $1 in
		--help)
			usage
			exit 0
			;;
		-c|--with-coveralls)
			coveralls=true
			shift
			;;
		-d|--diff-cover)
			diffcover=true
			shift
			;;
		--)
			shift
			break
			;;
		*)
			echo "Internal Error: option processing error: $1" 1>&2
			exit 1
			;;
	esac
done


DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Using git version $(git --version)"

pushd $PACKAGE_NAME
py.test
test_results=$?
cp .coverage ../
popd

if $diffcover; then
	coverage xml -i
	diff-cover coverage.xml
	rm coverage.xml
fi

if [[ $test_results -ne 0 ]]; then
	echo "Unit tests failed, failing test"
	exit_code=$[exit_code + 1]
fi

if $coveralls; then
	echo "What is the coverall repo token?"
	read token
	echo "repo_token: $token" > $DIR/.coveralls.yml
	coveralls
	rm $DIR/.coveralls.yml
fi

exit_code=0

exit $exit_code
