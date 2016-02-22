#!/bin/bash

port=9000

function usage {
    echo "VisualSMATCH starter"
    echo
    echo "usage: $0 [--port PORT] [--] [docker run options...]"
    echo
	echo "--port PORT   change port to listen on (default: $port)"
    echo
    echo "Requires docker: https://www.docker.com/"
    echo
}

for arg in $@; do
    if [ "$arg" == "--help" ] || [ "$arg" == "-h" ]; then
        usage
        exit 0
    fi
done

while [ $# -gt 0 ]; do
    if [ "$1" == "--" ]; then
        shift
        break
    elif [ "$1" == "--port" ] || [ "$1" == "-p" ]; then
        shift
        port="$1"
        shift
    else
        echo "unknown argument: $1"
        exit 1
    fi
done

if [ "$DOCKER_MACHINE_NAME" != "" ] && [ "`which docker-machine`" != "" ]; then
	echo
	echo "VisualSMATCH will be available at address http://`docker-machine ip $DOCKER_MACHINE_NAME`:$port"
	echo
fi

docker run -it -p $port:9000 $@ didzis/visualsmatch
