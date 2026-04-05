from sqlite3 import connect as sqlite3_connect
from time import time
from os import path as Path, makedirs
from uuid import uuid4

from MySQLite import DB

class User(DB):
	def __init__(self, db_path):
		super().__init__(Path.join(db_path, "user_system_202604.db"))
		self.execute([
("""CREATE TABLE IF NOT EXISTS users (
uid TEXT PRIMARY KEY,
phone TEXT,
email TEXT,
key TEXT,
active INTEGER DEFAULT 1
)""",),
("""CREATE TABLE IF NOT EXISTS sessions (
sid TEXT PRIMARY KEY,
uid TEXT,
tsl INTEGER,
tss INTEGER
)""",)
])

	async def api_enroll(self, request):
		""" 註冊新用戶 """
		try:
			data = await request.json()
			phone = data.get("phone")
			email = data.get("email")
			key = data.get("key") # 預期前端已傳入 sha256 字串
			uid = str(uuid4())
			self.execute(
				"INSERT INTO users (uid, phone, email, key) VALUES (?, ?, ?, ?)",
				(uid, phone, email, key)
			)
			return web.json_response({"R": "OK", "uid": uid})
		except Exception as e:
			return web.json_response({"E": str(e)}, status=400)

	async def api_login(self, request):
		""" 驗證登入並建立 Session """
		try:
			data = await request.json()
			phone = data.get("phone")
			email = data.get("email")
			key = data.get("key")

			user = self.query(
				*("SELECT uid, active FROM users WHERE phone=? AND key=?", (phone, key))
				if phone else
				*("SELECT uid, active FROM users WHERE email=? AND key=?", (email, key))
			).FOUND
				
			if not user:
				return web.json_response({"E": "身分驗證失敗"}, status=401)
			if not user[1]: # active column
				return web.json_response({"E": "帳號已停用"}, status=403)

			uid = user[0]
			sid = str(uuid4())
			now = int(time())
				
			self.execute(
				"INSERT INTO sessions (sid, uid, tsl, tss) VALUES (?, ?, ?, ?)",
				(sid, uid, now, now)
			)
			return web.json_response({"R": f"{sid}:{key}"})
		except Exception as e:
			return web.json_response({"E": str(e)}, status=400)

	async def api_disable(self, request):
		""" 停用帳號 """
		return await self._set_active(request, 0)

	async def api_enable(self, request):
		""" 啟用帳號 """
		return await self._set_active(request, 1)

	async def _set_active(self, request, status):
		try:
			data = await request.json()
			sid = data.get("sid")
			res = self.query("SELECT uid FROM sessions WHERE sid=?", (sid,)).FOUND
			if not res :
				return web.json_response({"E": "Invalid SID"}, status=401)
			self.execute("UPDATE users SET active=? WHERE uid=?", (status, res[0]))
			return web.json_response({"R": "OK"})
		except Exception as e:
			return web.json_response({"E": str(e)}, status=400)

	async def api_logout(self, request):
		""" 移除 Session """
		try:
			data = await request.json()
			sid = data.get("sid")
			self.execute("DELETE FROM sessions WHERE sid=?", (sid,))
			return web.json_response({"R": "OK"})
		except Exception as e:
			return web.json_response({"E": str(e)}, status=400)
