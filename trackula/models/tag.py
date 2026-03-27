class Tag:
	def __init__(self, frames=None):
		self.frames = frames or {}

	def get(self, key):
		return self.frames.get(key)

	def set(self, key, value):
		self.frames[key] = value

	@property
	def title(self):
		return self.get("TIT2")

	@title.setter
	def title(self, value):
		self.set("TIT2", value)

	@property
	def artist(self):
		return self.get("TPE1")

	@artist.setter
	def artist(self, value):
		self.set("TPE1", value)
	