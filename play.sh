#!/bin/sh

ROOT=$(dirname $0)
VENV=${ROOT}/venv
PY=${VENV}/bin/python3

test -f "${PY}" || {
	echo "Install on POSIX"
	python3 -m venv ${VENV}
}
test -f "${PY}" || {
	echo "${PY} not found"
	exit 1
}

${PY} ${ROOT}/app/aioweb.py $@
