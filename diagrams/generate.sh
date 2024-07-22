#!/bin/sh

set -x

path="$(dirname "$0")"

while true; do
	for diagramPath in "$path"/*.puml; do
		plantuml -tsvg "$diagramPath"
	done
	if [ "$1" = "--watch" ]; then
		inotifywait -e modify "$path"/*.puml
	else
		exit
	fi
done
