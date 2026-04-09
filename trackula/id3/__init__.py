from struct import unpack

from .parser import parse_frames
from .buffer import decode_int
from .builder import build_id3
from ..models.tag import Tag


class ID3:
	def __init__(self, filepath):
		self.filepath = filepath
		self.tag = None
		self.filesize = None
		self.tag_size = None
		self.audio_bytes = None

		self.load()

	def __repr__(self):
		return f"=============\n"\
				f"filesize: {self.filesize}\n"\
				f"filepath: {self.filepath}\n"\
				f"=============\n"


	def load(self):
		frames = self.fetch_tag_frames()
		self.tag = Tag(frames)


	def save(self, output=None):
		tag_bytes = build_id3(self.tag.frames)
		with open(output or self.filepath, "wb") as f:
			f.write(tag_bytes + self.audio_bytes)


	def fetch_tag_frames(self):
		with open(self.filepath, "rb") as f:
			f.seek(0, 2)
			self.filesize = f.tell()
			f.seek(0)
			self.bs = f.read()
			f.seek(0)


			header = f.read(10)

			# main header is always 10 bytes long
			# in ID3v2, header is located at the beginning of the file
			# identifier: 3 bytes - always "ID3"
			# version: 	  2 bytes - major version and revision eg. 03 00 for v2.3.0
			# flags:      1 byte  - bitwise indicator
			# size:       4 bytes - total size of the tag, excluding 10 byte header

			if len(header) < 10:
				raise Exception("ID3 header data too short")

			identifier, version, revision, flags, size_bytes = unpack('>3sBBB4s', header)
			if identifier != b"ID3":
				raise Exception("Missing ID3 identifier")

			size = decode_int(size_bytes, synchsafe=True)

			frames_body = f.read(size)
			frames = parse_frames(frames_body, version)

			self.audio_bytes = f.read()

			return frames
