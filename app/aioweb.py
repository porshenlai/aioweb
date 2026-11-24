#!/usr/bin/env python3

import os, sys, json
from datetime import datetime
from importlib import import_module
from asyncio import get_running_loop
from aiohttp import web, ClientSession as aSession
from aiofiles import open as aopen
from aiohttp import web

sys.path.insert(0,os.path.dirname(__file__))
from ModuleTools import ensure_modules

class FSMask :
	def __init__ (self, root) :
		self.Root=root;
		self.Map={};

	def configure (self, args) :
		self.Map=args;
		for key in self.Map :
			print(f"[Route] add link {key} -> {args[key]}")

	def resolve (self, path) :
		for k in self.Map :
			if path.startswith(f'{k}/') : return os.path.normpath(os.path.join(self.Map[k],path[len(k)+1:]))
		return os.path.normpath(os.path.join(self.Root,path))

class MyWebService :
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

	def __init__ (self, args) :
		self.host = args['host']
		self.port = int(args['port'])

		self.app = web.Application()
		self.mods = {}
		self.apipfx = args['apipfx']

		docs_root = args['docs']
		try : # search for docs root
			for dp in args['docs'] :
				if os.path.exists(os.path.join(dp,"index.html")) :
					docs_root = dp
					break
		except Exception as x :
			pass

		try : # install backend service api module
			# static GET
			print(f"[System] Documents : {docs_root}")
			self.FSMask = FSMask(docs_root);
			if 'fsmap' in args :
				self.FSMask.configure(args['fsmap'])
			self.app.router.add_get("/{tail:.*}", self.handle_static)
			# system service
			self.install(self)

			"""
			layout:{
				"aioweb_wks":["WKStorage"]
				"aioweb_user":["mods"]
			}
			"""
			if 'layout' in args :
				for mn in args['layout'] :
					self.install(import_module(mn).WBModule, args=args['layout'][mn], name=mn[7:])

		except Exception as x:
			print(f"Exception: {str(x):s}")
			pass

		if 'cors' in args:
			# CORS {'cors':'*'}
			self.config_cors(args['cors'])
	
		if 'ssl_crt' in args and 'ssl_key' in args:
			# HTTPS {'ssl_crt':'ssl_server.crt', 'key':'server.key'}
			self.config_https(args['ssl_crt'], args['ssl_key'])

	def install (self, Class, args=[], name=None) :
		if callable(Class) :
			mod = Class(*args)
			if not name : name = Class.__name__
			pfx = f"{self.apipfx}{name}/"
			self.mods[name] = mod
		else :
			mod = Class
			pfx = f"{self.apipfx}"
		
		# 自動掃描 [post|get]api_ 開頭的函式並加入路由
		for m in dir(mod):
			if m.startswith("postapi_") :
				route_path = f"{pfx}{m[8:]}"
				self.app.router.add_post(route_path, getattr(mod, m))
				print(f"[Route] add service <- POST:{route_path}")
			elif m.startswith("getapi_") :
				route_path = f"{pfx}{m[7:]}"
				self.app.router.add_get(route_path, getattr(mod, m))
				print(f"[Route] add service <- GET:{route_path}")

	async def postapi_echo (self, request) :
		try:
			body = await request.read()
			return web.Response(body=body, content_type=request.content_type)
		except Exception as e:
			return web.json_response({"error": str(e)}, status=400)

	async def postapi_proxy (self, request) :
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

	def trigger_graceful_exit(self):
		raise web.GracefulExit()

	async def getapi_stop_server (self, request):
		print("[System] Stop AIOWeb Server")
		get_running_loop().call_later(0.1, self.trigger_graceful_exit)
		return web.Response(text="Server is shutting down...\n")

	async def _send_file (self, full_path) :
		print("[API] Send static: ",full_path);
		if os.path.exists(full_path) and os.path.isfile(full_path):
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

	async def handle_static (self, request) :
		rel_path = request.match_info['tail']
		if rel_path and os.path.basename(rel_path)[0] == '.' :
			return web.Response(text="404: Not Found", status=404)
		full_path = self.FSMask.resolve(rel_path);
		if os.path.isdir(full_path):
			full_path = os.path.join(full_path, "index.html")
		return await self._send_file(full_path)

	def config_cors (self, allow='*') :
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

	def config_https (self, certfile, keyfile) :
		from ssl import create_default_context, Purpose
		"""啟用 SSL 支援"""
		ssl_context = create_default_context(Purpose.CLIENT_AUTH)
		ssl_context.load_cert_chain(certfile, keyfile)
		self._ssl_context = ssl_context
		print("[System] HTTPS/SSL enabled.")

	def play (self) :
		"""啟動服務"""
		print(f"[System] Serving at http://{self.host}:{self.port}")
		ssl_ctx = getattr(self, '_ssl_context', None)
		web.run_app(self.app, host=self.host, port=self.port, ssl_context=ssl_ctx)

# --- 執行範例 ---
if __name__ == "__main__":
	"""
	([ Usage ])
		apipfx=... docs=... host=... port=...
	"""
	ensure_modules('aiohttp','aiofiles','aiohttp_cors')
	try :
		env={
			"awd":os.path.realpath(os.path.join(os.path.dirname(__file__),'..')).replace('\\','/'),
			"cwd":os.getcwd().replace('\\','/'),
		}
		args = {
			'apipfx': "/__API__/",
			'docs': os.path.join(env['awd'], 'docs'),
			'host': "0.0.0.0",
			'port': 8080
		}
		with open(os.path.join(env['awd'],'etc/aioweb.json')) as fo :
			args.update(json.loads(fo.read().format(**env)));
		for a in sys.argv[1:]:
			parts = a.split('=')
			if len(parts) == 1:
				if os.path.isfile(parts[0]):
					with open(parts[0], "r") as cf:
						args.update(json.load(cf))
					continue
				elif os.path.isdir(parts[0]):
					args['docs'] = parts[0]
			else:
				args[parts[0]] = '='.join(parts[1:])
		print(json.dumps(args, indent=4));
		MyWebService(args).play()
	except Exception as x :
		print("Exception: ",x)
