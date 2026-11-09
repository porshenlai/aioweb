#!/bin/sh

ROOT=$(dirname $0)
VENV=${ROOT}/venv
PY=${VENV}/Scripts/python.exe
THPY=/d/apps/thonny/python.exe

test -f "${PY}" || {
	test -f "${THPY}" || {
		echo "Install from thonny"
		${THPY} -m venv ${VENV}
		${PY} -m pip install --upgrade pip aiohttp aiohttp_cors aiofiles
	}
}
test -f "${PY}" || {
	echo "${PY} not found"
	exit 1
}

${PY} ${ROOT}/app/aioweb.py $@
