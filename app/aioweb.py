#!/usr/bin/env python3

from sys import argv
from os import path as Path, makedirs
from json import load as readJSON
from aiohttp import web, ClientSession as aSession
from aiofiles import open as aopen

class MyWebService:
	@property
	def MIME (self) :
		return {
			"css": "text/css",
			"html": "text/html",
			"jpg": "image/jpeg",
			"js": "application/javascript",
			"pdf": "application/pdf",
			"png": "image/png",
			"svg": "image/svg+xml",
			"*":"binary/octet-stream"
		}

	def __init__(self, args):
		self.apipfx = args['apipfx']
		self.host = args['host']
		self.port = int(args['port'])
		self.docs_path = args['docs']
		self.mods_path = args['mods']

		self.app = web.Application()
		self.mods = {}
		
		# 3. 初始化時自動建立 docs 目錄
		if not Path.exists(self.docs_path):
			makedirs(self.docs_path)
			with open(Path.join(self.docs_path, "index.html"), "w", encoding="utf-8") as f:
				f.write("<h1>Web Service is Running!</h1>")

		# 安裝模組
		try :
			from aioweb_user import User as UM
			self.install(UM)
		except Exception as x:
			pass

		self._setup_routes()

		if 'cors' in args:
			# CORS {'cors':'*'}
			self.config_cors(args['cors'])
	
		if 'crt' in args and 'key' in args:
			# HTTPS {'crt':'server.crt', 'key':'server.key'}
			self.config_https(args['crt'], args['key'])

	def install(self, Class):
		# 初始化模組實例，傳入 mods 路徑供資料庫儲存
		mod = Class(self.mods_path)
		class_name = Class.__name__
		pfx = f"{self.apipfx}{class_name}/"
		
		# 自動掃描 api_ 開頭的函式並加入路由
		for m in dir(mod):
			if m.startswith("api_"):
				api_func = getattr(mod, m)
				api_name = m[4:]
				route_path = f"{pfx}{api_name}"
				self.app.router.add_post(route_path, api_func)
				print(f"[Route] Registered: {route_path}")
		
		self.mods[class_name] = mod

	def _setup_routes(self):
		self.app.router.add_post(f"{self.apipfx}echo", self.api_echo)
		self.app.router.add_post(f"{self.apipfx}proxy", self.api_proxy)
		self.app.router.add_get("/{tail:.*}", self.handle_static)

	async def api_echo(self, request):
		try:
			body = await request.read()
			return web.Response(body=body, content_type=request.content_type)
		except Exception as e:
			return web.json_response({"error": str(e)}, status=400)

	async def api_proxy(self, request):
		try:
			data = await request.json()
			target_url = data.get("url")
			payload = data.get("body", {})
			async with aSession() as session:
				async with session.post(target_url, json=payload) as resp:
					result = await resp.read()
					return web.Response(body=result, status=resp.status)
		except Exception as e:
			return web.json_response({"error": str(e)}, status=500)

	async def _send_file(self, full_path):
		print("[API] Send static: ",full_path);
		if Path.exists(full_path) and Path.isfile(full_path):
			try:
				async with aopen(full_path, mode='rb') as f:
					ct = full_path.lower()
					try :
						ct = self.MIME[ct[ct.rfind('.')+1:]]
					except :
						ct = self.MIME['*']
					return web.Response(body = await f.read(), content_type = ct)
			except Exception as X:
				print("Exception:",X)
		return web.Response(text="404: Not Found", status=404)

	async def handle_static(self, request):
		rel_path = request.match_info['tail']
		full_path = Path.normpath(Path.join(self.docs_path, rel_path))
		if Path.isdir(full_path):
			full_path = Path.join(full_path, "index.html")
		return await self._send_file(full_path)

	def config_cors(self, allow='*'):
		"""啟用 CORS 支援 (簡易版)"""
		try:
			from aiohttp_cors import setup, ResourceOptions
			cors = setup(self.app, defaults={
				"*": ResourceOptions(
					allow_credentials=True,
					expose_headers=allow,
					allow_headers=allow,
				)
			})
			for route in list(self.app.router.routes()):
				cors.add(route)
			print("[System] CORS enabled.")
		except ImportError:
			print("[Warning] aiohttp_cors not installed.")

	def config_https(self, certfile, keyfile):
		from ssl import create_default_context, Purpose
		"""啟用 SSL 支援"""
		ssl_context = create_default_context(Purpose.CLIENT_AUTH)
		ssl_context.load_cert_chain(certfile, keyfile)
		self._ssl_context = ssl_context
		print("[System] HTTPS/SSL enabled.")

	def play(self):
		"""啟動服務"""
		print(f"[System] Serving at http://{self.host}:{self.port}")
		ssl_ctx = getattr(self, '_ssl_context', None)
		web.run_app(self.app, host=self.host, port=self.port, ssl_context=ssl_ctx)

# --- 執行範例 ---
if __name__ == "__main__":
	args = {
		'apipfx': "/__API__/",
		'docs': Path.join(Path.dirname(__file__), '..', 'docs'),
		'mods': Path.join(Path.dirname(__file__), '..', 'mods'),
		'host': "0.0.0.0",
		'port': 8080
	}
	
	for a in argv[1:]:
		parts = a.split('=')
		if len(parts) == 1:
			if Path.isfile(parts[0]):
				with open(parts[0], "r") as cf:
					args.update(readJSON(cf))
				continue
			elif Path.isdir(parts[0]):
				args['docs'] = parts[0]
		else:
			args[parts[0]] = '='.join(parts[1:])

	MyWebService(args).play()
