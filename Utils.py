# coding: utf-8

import json
import re
import os

def is_a_valid_index_url(url: str) -> bool:
	"""Выдаёт `True`, если `url` является правильной ссылкой для файла index.json."""
	return bool(re.match(r"https:\/\/onlinemektep\.net\/upload\/online_mektep\/lesson\/[a-fA-F0-9]{32}\/index.json$", url))

def load_user_info(user_id: int, store_folder: str = "UserData") -> dict:
	"""Загружает информацию пользователя с `user_id`, и выдаёт `dict`-объект с информацией о пользователе. Данные о пользователях хранятся как .JSON-файлы в папке `UserData`.

	Args:
		user_id (int): ID пользователя, которого нужно загрузить.

	Returns:
		dict: Сохранённая о пользователе информация.
	"""

	path = f"{store_folder}/{user_id}.json"

	if not os.path.exists(path):
		return {}

	return json.load(
		open(path, "r", encoding = "utf-8")
	)

def save_user_info(data: dict, user_id: int, store_folder: str = "UserData") -> None:
	path = f"{store_folder}/{user_id}.json"

	if not os.path.exists( os.path.dirname(path) ):
		os.makedirs(
			os.path.dirname(path)
		)


	json.dump(
		data,
		open(path, "w", encoding = "utf-8"),
		ensure_ascii = False,
		indent = "\t"  
	)

	return None