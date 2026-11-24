$ErrorActionPreference = "Stop"

$ROOT = $PSScriptRoot
$PY = Join-Path $ROOT "python\python.exe"
$URL = "https://www.python.org/ftp/python/3.14.10/python-3.14.10-embed-amd64.zip"

if (-not (Test-Path -Path $PY -PathType Leaf)) {
	if (-not (Test-Path -Path python.zip -PathType Leaf)) {
		irm -OutFile python.zip $URL
	}
	expand-Archive python.zip -DestinationPath python
	$PTH = Get-ChildItem -Path "python/python*._pth"
	Add-Content -Path $PTH -Value "import site"
}
