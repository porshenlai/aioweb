#!/usr/bin/env python3

from sys import argv, exit
from os import path as Path, makedirs
from json import load as readJSON
from aiohttp import web, ClientSession as aSession
from aiofiles import open as aopen

# Gemini HelpME
# 1. Please create a web service with aiohttp listening on port 8080
# 2. Please service static data at Path.join(Path.dirname(__file__),"docs/")
# 3. If the docs directory doesn't exist, please built it automatically when app initializing 
# 4. When http GET request referring to the directory without filename, please send index.html or 404 error
# 5. Please listen the HTTP post request at "/__api__/echo" to response the data in request body.
# 6. When reading data from server, please use aiofiles to ensure server performance
# 7. Please wrap the web service as a class, with the following member functions:
#  - a: play() to start service
#  - b: config_cors() to enable cors support
#  - c: config_https() to enable SSL support
# 8. Please listen the HTTP post requst at "/__api__/proxy" to response the response from another post request to specific web site with the sample body of post request.

class MyWebService:
	def __init__(self, args):
		self.host = args['host']
		self.port = int(args['port'])
		self.docs_path = args['docs']

		self.app = web.Application()
		
		# 3. 初始化時自動建立 docs 目錄
		if not Path.exists(self.docs_path):
			makedirs(self.docs_path)
			# 建立一個預設的 index.html 方便測試
			with open(Path.join(self.docs_path, "index.html"), "w", encoding="utf-8") as f:
				f.write("<h1>Web Service is Running!</h1>")

		self._setup_routes()

		if 'cors' in args :
			# CORS {'cors':'*'}
			self.config_cors(args['cors'])
	
		if 'crt' in args and 'key' in args :
			# HTTPS {'crt':'server.crt', 'key':'server.key'}
			self.config_https(args['crt'], args['key'])
	

	def _setup_routes(self):
		"""配置路由架構，方便後續擴充"""
		# Echo API
		self.app.router.add_post("/__api__/echo", self.api_echo)
		# Proxy API
		self.app.router.add_post("/__api__/proxy", self.api_proxy)
		# 靜態檔案處理 (放在最後面，作為 fallback)
		self.app.router.add_get("/{tail:.*}", self.handle_static)

	# --- API 實作區塊 ---

	async def api_echo(self, request):
		""" 回傳 Request Body 的內容"""
		try:
			body = await request.read()
			return web.Response(body=body, content_type=request.content_type)
		except Exception as e:
			return web.json_response({"error": str(e)}, status=400)

	async def api_proxy(self, request):
		""" 將請求轉發至特定網站並回傳結果"""
		try:
			data = await request.json()
			target_url = data.get("url")
			payload = data.get("body", {})

			if not target_url:
				return web.json_response({"error": "Missing target url"}, status=400)

			async with aSession() as session:
				async with session.post(target_url, json=payload) as resp:
					result = await resp.read()
					return web.Response(body=result, status=resp.status)
		except Exception as e:
			return web.json_response({"error": f"Proxy error: {str(e)}"}, status=500)

	# --- 靜態檔案處理 ---

	async def handle_static(self, request):
		"""2 & 4. 處理靜態檔案與目錄索引"""
		rel_path = request.match_info['tail']
		full_path = Path.join(self.docs_path, rel_path)

		# 如果是目錄，嘗試讀取 index.html
		if Path.isdir(full_path):
			full_path = Path.join(full_path, "index.html")

		if Path.exists(full_path) and Path.isfile(full_path):
			# 6. 使用 aiofiles 讀取檔案確保效能
			async with aopen(full_path, mode='rb') as f:
				content = await f.read()
			
			# 簡單的 MIME Type 判斷
			content_type = "text/html"
			if full_path.endswith(".js"): content_type = "application/javascript"
			elif full_path.endswith(".css"): content_type = "text/css"
			
			return web.Response(body=content, content_type=content_type)
		
		return web.Response(text="404: Not Found", status=404)

	# --- 成員函式 (功能配置) ---

	def config_cors(self, allow='*'):
		"""7-b. 啟用 CORS 支援 (簡易版)"""
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

	def config_https(self, certfile, keyfile):
		from ssl import create_default_context, Purpose
		"""7-c. 啟用 SSL 支援"""
		ssl_context = create_default_context(Purpose.CLIENT_AUTH)
		ssl_context.load_cert_chain(certfile, keyfile)
		self._ssl_context = ssl_context
		print("[System] HTTPS/SSL enabled.")

	def play(self):
		"""7-a. 啟動服務"""
		print(f"[System] Starting web service on http://{self.host}:{self.port}")
		ssl_ctx = getattr(self, '_ssl_context', None)
		web.run_app(self.app, host=self.host, port=self.port, ssl_context=ssl_ctx)

# --- 執行範例 ---
if __name__ == "__main__":

	args={
		'docs': Path.join(Path.dirname(__file__),'docs'),
		'host': "0.0.0.0",
		'port': 8080
	}
	for a in argv[1:] :
		a = a.split('=')
		if len(a) == 1 :
			if Path.isfile(a[0]) :
				with open(a[0],"r") as cf :
					args.update(readJSON(cf))
				continue;
			elif Path.isdir(a[0]) :
				a.insert(0, 'docs')
		args[a[0]] = '='.join(a[1:])

	MyWebService(args).play();
