import sys, subprocess, site
import urllib.request
from importlib.util import find_spec

def ensure_modules (*args) :
	if find_spec('pip') is None :
		url = "https://bootstrap.pypa.io/get-pip.py"
		with urllib.request.urlopen(url) as response :
			status = response.status
			body = response.read().decode("utf-8")
			with open('get-pip.py', 'w', encoding='utf-8') as fo :
				fo.write(body)
			subprocess.run([sys.executable, "get-pip.py"], check=True)

	for package in args :
		if find_spec(package) is None :
			subprocess.run([sys.executable, "-m", "pip", "install", package])
			site.main()
