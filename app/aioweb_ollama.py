#mod# langchain_ollama

from os import makedirs
from asyncio import create_task
from aiohttp.web import Request, Response, json_response
from langchain_ollama import ChatOllama
from uuid import uuid4

class WBModule():
	def __init__(self, model, base_url):
		self.LLM = ChatOllama(model=model,base_url=base_url)
		self.SESSIONS: dict[str, dict] = {}

	async def stream_ollama_to_cache(self, sid: str, question: str):
		try:
			async for chunk in self.LLM.astream(question):
				if chunk.content:
					self.SESSIONS[sid]["R"] += str(chunk.content)
				count+=1
			self.SESSIONS[sid]["S"] = "done"
		except Exception as e:
			self.SESSIONS[sid]["R"] += f"\n[系統錯誤: {str(e)}]"
			self.SESSIONS[sid]["S"] = "error"

	async def postapi_request(self, request: Request) -> Response:
		"""
		{ "I":"*", "Q":"question ?" } -> { "I":"...", "R":"", "S":"generating" }
		{ "I":"..." } -> { "I":"...", "R":"...", "S":"done" }
		"""
		try:
			data = await request.json()
		except Exception:
			return json_response({"error": "無效的 JSON 格式"}, status=400)
		sid = data.get("I")
		qz = data.get("Q")

		if qz: # new Question
			new_sid = sid or str(uuid4())
			self.SESSIONS[new_sid] = {"R": "", "S": "generating"}
			create_task(self.stream_ollama_to_cache(new_sid, qz))
			return json_response({"I": new_sid, "R": "", "S": "generating"})

		if sid: # update Reply
			session_data = self.SESSIONS.get(sid)
			print("DEBUG",session_data);
			if not session_data:
				return json_response({"error": "Session 不存在"}, status=404)
			return json_response({
				"I": sid,
				"R": session_data["R"],
				"S": session_data["S"]
			})

		return json_response({"error": "Insufficient Arguments"}, status=400)

