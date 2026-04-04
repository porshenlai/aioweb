
class Constant :
	@property
	def MimeDB(self) :
		return {
			"js": "application/javascript",
			"css": "text/css",
			"jpg": "image/jpeg",
			"png": "image/png",
			"pdf": "application/pdf",
			"html": "text/html"
		}

C=Constant();

print(C.MimeDB['pdf'])
C.MimeDB=100
