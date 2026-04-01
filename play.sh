#!/bin/sh

ROOT=$(dirname $0)
VENV=${ROOT}/venv
PY=${VENV}/bin/python3

echo ${PY} ${ROOT}/bin/aioweb.py $@
