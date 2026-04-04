#!/bin/sh

ROOT=$(dirname $0)
VENV=${ROOT}/venv
PY=${VENV}/bin/python3

${PY} ${ROOT}/app/aioweb.py $@
