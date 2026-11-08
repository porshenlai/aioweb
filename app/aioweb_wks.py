import json
from os import path as Path, makedirs
from datetime import datetime
from aiohttp.web import Request, json_response
from aiofiles import open as aopen

class WKS():
	def __init__(self, path):
		self.Root = path;
		makedirs(self.Root, exist_ok=True)

	async def api_commit(self, request: Request):
		""" 上傳資料
		Request: { ... }
		Response: { "R":"OK" } or { "E":Exception }
		"""
		# 1. 取得客戶端 IP（若取不到則預設為 unknown）
		client_ip = request.remote or "unknown"

		# 2. 解析 JSON Body
		try:
			data = await request.json()
		except Exception:
			return json_response(
				{"status": "error", "message": "無效的 JSON 格式"},
				status=400
			)

		# 3. 產生時間戳記與檔名
		# 格式範例：20261108_201530_123456
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
		# 將 IP 中的冒號或特殊符號替換（主要預防 IPv6 如 ::1 的非法檔名字元）
		safe_ip = client_ip.replace(":", "_")
		filename = f"{safe_ip}_{timestamp}.json"
		file_path = Path.join(self.Root, filename)

		# 4. 非同步寫入檔案
		try:
			async with aopen(file_path, mode="w", encoding="utf-8") as f:
				await f.write(json.dumps(data, ensure_ascii=False, indent=2))
		except Exception as e:
			return json_response(
				{"status": "error", "message": f"檔案儲存失敗: {str(e)}"},
				status=500
			)

		# 5. 回應客戶端成功訊息與存檔路徑
		return json_response({
			"status": "success",
			"saved_as": filename,
			"client_ip": client_ip
		})
