#!/bin/sh

ROOT=$(dirname $0)
VENV=${ROOT}/venv
PY=${VENV}/bin/python3

test -f "${PY}" || PY="${VENV}/Scripts/python.exe"
test -f "${PY}" || {
	THONNY=/d/apps/thonny/python.exe
	if test -f "${THONNY}"; then
		echo "Install from thonny"
		${THONNY} -m venv ${VENV}
		${PY} -m pip install --upgrade pip aiohttp aiohttp_cors aiofiles
	fi
}
test -f "${PY}" || {
	echo "${PY} not found"
	exit 1
}

${PY} ${ROOT}/app/aioweb.py $@
