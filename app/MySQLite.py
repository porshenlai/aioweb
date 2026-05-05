from sqlite3 import connect, Row
from os import path as Path, makedirs

class DB:
	def __init__ (self, dbf, layout=None) :
		self.db = dbf
		self.db_root = Path.dirname(dbf)
		self.cursor = None
		if not Path.exists(self.db_root) :
			makedirs(self.db_root)
		if layout :
			self.commit(f"CREATE TABLE IF NOT EXISTS {layout[0]} ({layout[1]})");

	# "INSERT INTO tasks (symbol, year, tid, status) VALUES (?, ?, ?, 'Pending')", (symbol, year, tid)
	def commit(self, *cmds) :
		""" 更新資料
commit("INSERT OR REPLACE INFO 表格 (欄位A,欄位B) VALUES (?,?)",(數值A,數值B))
commit("DELETE FROM 表格 WHERE 欄位A=? AND 欄位B=?", (數值A, 數值B))
"""
		with connect(self.db) as conn:
			for i in range(0,len(cmds),2) :
				conn.execute(cmds[i],cmds[i+1])
			conn.commit()
		return self

	def query(self, *args) :
		""" 檢索資料
	row = query("SELECT 欄位s FROM 表格 WHERE 欄位A=? AND 欄位B=?", (數值A, 數值B)).FOUND
	list = query("SELECT 欄位s FROM 表格 WHERE 欄位A=? AND 欄位B=?", (數值A, 數值B)).DICT
	for row in query("SELECT 欄位s FROM 表格 WHERE 欄位A=? AND 欄位B=?", (數值A, 數值B)).ROWS :
		...
		"""
		self.cursor = None
		with connect(self.db) as conn:
			conn.row_factory = Row
			self.cursor = conn.cursor()
			self.cursor.execute(*args);
		return self

	@property
	def FOUND (self) :
		if not self.cursor : return False
		row = self.cursor.fetchone()
		return None if not row else dict(row)

	@property
	def ROWS (self) :
		if not self.cursor : return None
		return self.cursor.fetchall()

	@property
	def DICT (self) :
		if not self.cursor : return None
		rows = self.cursor.fetchall()
		return [dict(row) for row in rows] # 將 sqlite3.Row 轉為 list of dict
