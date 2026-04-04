#!/bin/sh

ROOT=$(realpath $0)
ROOT=${ROOT%/bin/*}
VENV=${ROOT}/venv

if test -d "${VENV}"; then
	echo "Virtual environment already exist, please remove it manual and run install again"
	exit 0
fi
echo "Install virtual environment at ${VENV}."
python3 -m venv "${VENV}"

${VENV}/bin/python3 -m pip install --upgrade pip aiofiles aiohttp aiohttp_cors
