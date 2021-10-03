# coding: utf-8

import re

def is_a_valid_index_url(url: str) -> bool:
	"""Выдаёт `True`, если `url` является правильной ссылкой для файла index.json."""
	return bool(re.match(r"https:\/\/onlinemektep\.net\/upload\/online_mektep\/lesson\/[a-fA-F0-9]{32}\/index.json$", url))