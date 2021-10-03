# coding: utf-8

import pytest

from Parser import decrypt_plain
import pgpy
import json

def test_decrypt():
	try:
		json_loaded = json.loads(
			decrypt_plain(
				open("Example Files/EncryptedTest.txt", "r").read()
			)
		)
		assert json_loaded["Success"]
	except Exception as error:
		assert False, f"Ошибка при декодировании тестового сообщения: {error}"