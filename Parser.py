# coding: utf-8

# Файл с парсером. Ключ для дешифровки находится в файле 'BL-Key'.

import pgpy


def parse_decoded_text(plain_text: str) -> str:
	pass

def decrypt_plain(encrypted_text: str) -> str:
	"""Дешифровывает plain-файл, зашифрованный PGP-Ключем (который хранится в файле `BL-Key`) с Secret phrase (в файле `BL-SecretPhrase`) и выдаёт дешифрованный результат. Код у данной функции немного кривой, ибо я понятия не имею как *должным* образом работать с библиотекой pgpy.

	Args:
		encrypted_text (str): Зашифрованный текст, который должен быть дешифрован PGP-Ключём. (Не путь к файлу, а его содержимое!)

	Returns:
		str: Дешифрованный текст.
	"""

	encrypted_text 	= pgpy.PGPMessage.from_blob(encrypted_text)
	key, _			= pgpy.PGPKey.from_file("BL-Key")

	with key.unlock( open("BL-SecretPhrase", "r", encoding = "utf-8").read() ):
		return key.decrypt(encrypted_text).message.decode("utf-8")