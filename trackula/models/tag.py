# 'TIT2', 'TPE1', 'TRCK', 'TALB', 'TPOS', 'TCON', 'TDAT', 'TYER', 'TOWN', 'TPE2', 'TSRC', 'TPUB', 'APIC'

class Tag:
	def __init__(self, frames=None):
		self.frames = frames or {}

	def get(self, key):
		return self.frames.get(key)

	def set(self, key, value):
		self.frames[key] = value

	# title
	@property
	def TIT2(self):
		return self.get("TIT2")

	# artist
	@property
	def TPE1(self):
		return self.get("TPE1")

	@property
	def TRCK(self):
		return self.get("TRCK")


	@property
	def TALB(self):
		return self.get("TALB")


	@property
	def TPOS(self):
		return self.get("TPOS")


	@property
	def TCON(self):
		return self.get("TCON")


	@property
	def TDAT(self):
		return self.get("TDAT")


	@property
	def TYER(self):
		return self.get("TYER")


	@property
	def TOWN(self):
		return self.get("TOWN")


	@property
	def TPE2(self):
		return self.get("TPE2")


	@property
	def TSRC(self):
		return self.get("TSRC")


	@property
	def TPUB(self):
		return self.get("TPUB")


	@property
	def APIC(self):
		return self.get("APIC")



	# title
	@TIT2.setter
	def TIT2(self, value):
		self.set("TIT2", value)

	# artist
	@TPE1.setter
	def TPE1(self, value):
		self.set("TPE1", value)

	@TRCK.setter
	def TRCK(self, value):
		self.set("TRCK", value)


	@TALB.setter
	def TALB(self, value):
		self.set("TALB", value)


	@TPOS.setter
	def TPOS(self, value):
		self.set("TPOS", value)


	@TCON.setter
	def TCON(self, value):
		self.set("TCON", value)


	@TDAT.setter
	def TDAT(self, value):
		self.set("TDAT", value)


	@TYER.setter
	def TYER(self, value):
		self.set("TYER", value)


	@TOWN.setter
	def TOWN(self, value):
		self.set("TOWN", value)


	@TPE2.setter
	def TPE2(self, value):
		self.set("TPE2", value)


	@TSRC.setter
	def TSRC(self, value):
		self.set("TSRC", value)


	@TPUB.setter
	def TPUB(self, value):
		self.set("TPUB", value)


	@APIC.setter
	def APIC(self, value):
		self.set("APIC", value)


