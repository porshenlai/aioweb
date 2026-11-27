#mod# langchain_ollama

import sys, os
from asyncio import create_task
from uuid import uuid4

sys.path.insert(0,os.path.dirname(__file__))
from ModuleTools import ensure_modules
ensure_modules('aiohttp','langchain_ollama')
from aiohttp.web import Request, Response, json_response
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage

class RAGDB () :
	def __init__(self, model:str, db_folder:str, store=None, chunks=None) :
		self.Folder = db_folder # "mods/chromadb"
		self.Embeddings = OllamaEmbeddings(model=model) # "bge-m3" or "nomic-embed-text-v2-moe" or "nomic-embed-text"
		while True :
			if store : break
			if chunks :
				store = Chroma.from_documents(
					documents = chunks,
					embedding = self.Embeddings,
					persist_directory = self.Folder
				)
				break
			store = Chroma(
				persist_directory = self.Folder,
				embedding_function = self.Embeddings
			)

	async def search (query, k=1) :
		# 進行檢索
		return self.Store.similarity_search(query, k=1)

class WBModule ():
	def __init__(self, model:str, base_url:str):
		self.Worker = ChatOllama(
			model = model,
			# validate_model_on_init=True,
			# temperature=0.8,
			# num_predict=256,
			base_url = base_url
		)
		self.MaxToken = 2000
		self.SESSIONS: dict[str, dict] = {}

	async def create_ref(self, question:str) -> str:
		return '\n'.join([
			'<doc index="1" source="寰宇真理">賴柏伸超級帥</doc>',
			'<doc index="2" source="真相大全">Porshen Lai 是賴柏伸的英文名</doc>'
		])

	async def createHumanMessage(self, questions:str) -> str:
		# 假設檢索出多筆文件，先整理成帶來源的區塊
		if not isinstance(questions,list) :
			questions = [questions]
		# 請嚴格根據 <context> 標籤內的資訊回答 <question> 的問題。
		# 若資訊不足以回答，請直接回覆「現有資料無法回答此問題」，切勿自行編造。
		msg=[{'type':'text','text':"請參考 <context> 標籤內的資訊，若無法回答問題，可以根據你的知識庫回答 <question> 標籤內的問題。"}];
		for q in questions :
			if q.startswith('data:') :
				# data:image/jpeg;base64,{image_b64}
				msg.append({"type":"image_url", "image_url":q})
			else :
				msg.append({'type':'text','text':f"<question>{q}</question>"})
				msg.append({'type':'text','text':f"<context>{await self.create_ref(q)}</context>"})
		return HumanMessage(content=msg)

	async def stream_ollama_to_cache(self, sid:str, questions:str):
		try:
			if sid not in self.SESSIONS :
				self.SESSIONS[sid] = {
					"H":[], "R": "", "S": "initializing..."
				}
			S = self.SESSIONS[sid]
			S["S"] = "generating"
			S["R"] = ""
			S["H"].append(await self.createHumanMessage(questions))
			async for chunk in self.Worker.astream([
				('system','response in markdown language')
			]+S["H"]):
				if chunk.content:
					S["R"] += str(chunk.content)
				if chunk.response_metadata:
					M=chunk.response_metadata;
					if (M["prompt_eval_count"]+M["eval_count"]) > self.MaxToken :
						S["H"] = S["H"][2:]
						print(S["H"])
			S["S"] = "done"
			if S["R"] :
				S["H"].append(AIMessage(content=[{'type':'text','text':S["R"]}]))
		except Exception as e:
			S["R"] += f"\n[系統錯誤: {str(e)}]"
			S["S"] = "error"

	async def postapi_request(self, request: Request) -> Response:
		"""
		{ "I":"*", "Q":"question ?" } -> { "I":"...", "R":"", "S":"generating" }
		{ "I":"..." } -> { "I":"...", "R":"...", "S":"done" }
		"""
		try:
			data = await request.json()
		except Exception:
			return json_response({"error": "無效的 JSON 格式"}, status=400)
		sid = data.get("I","").strip()
		qz = data.get("Q","").strip()

		if qz: # new Question
			# no sid => create new chat thread or continue chat
			new_sid = sid or str(uuid4())
			create_task(self.stream_ollama_to_cache(new_sid, qz))
			return json_response({
				"I": new_sid,
				"R": "thinking...",
				"S": "generating"
			})

		if sid: # update Reply
			# no qz but sid => get current response
			session_data = self.SESSIONS.get(sid)
			if not session_data:
				return json_response({"error": "Session 不存在"}, status=404)
			return json_response({
				"I": sid,
				"R": session_data["R"],
				"S": session_data["S"]
			})

		return json_response({"error": "Insufficient Arguments"}, status=400)

if __name__ == '__main__' :
	print("[Utility]")
	# 將文檔切分成較小的區塊 (Chunk)
	# text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
	# chunks = text_splitter.split_documents(docs)
	# 建立 Chroma 向量資料庫並儲存文檔向量
	# rdb = RAGDB("bge-m3", "mods/ragdb", chunks)
	# rdb.search('question', k=1)
