# coding: utf-8

import json
import re
import os
import random
from datetime import datetime
import json
import base64
import hashlib
import time
from typing import Any
import uuid

def load_data(filename: str, store_folder: str = "Data", throw_error_if_does_not_exists: bool = True, required_keys: list = []) -> Any:
	"""Загружает информацию с файла `store_folder/filename`, и выдаёт `dict`-объект с информацией о пользователе. Данные хранятся как .JSON-файлы в папке `Data`.

	Args:
		user_id (int): ID пользователя, которого нужно загрузить.

	Returns:
		dict: Сохранённая о пользователе информация.
	"""

	path = f"{store_folder}/{filename}"

	if not os.path.exists(path):
		if throw_error_if_does_not_exists:
			raise FileNotFoundError("Файл не был найден.")

		return {}

	loaded = json.load(
		open(path, "r", encoding = "utf-8")
	)
	for key in required_keys:
		if key not in loaded:
			raise FileNotFoundError("Ключа нет")

	return loaded

def save_data(data: dict, filename: str, store_folder: str = "Data") -> dict:
	path = os.path.join(store_folder, filename)

	if not os.path.exists( os.path.dirname(path) ):
		os.makedirs(
			os.path.dirname(path)
		)

	# Проверяем, существовал ли ранее такой юзер или нет.
	if filename.startswith("User-") and not os.path.exists(path):
		bot_data = load_data("Bot.json")

		bot_data["UniqueUsers"] += 1

		save_data(bot_data, "Bot.json")



	json.dump(
		data,
		open(path, "w", encoding = "utf-8"),
		ensure_ascii = False,
		indent = "\t"  
	)

	return data

def random_useragent() -> str:
	return random.choice([
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:89.0) Gecko/20100101 Firefox/89.0",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
		"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.59",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 OPR/77.0.4054.172",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.70",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.203",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36 Edg/91.0.864.71",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
		"Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
		"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
		"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
		"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
		"Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
		"Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
		"Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
		"Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
		"Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
		"Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
		"Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
		"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
		"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0"
	])

def today_date() -> str:
	return datetime.today().strftime("%d.%m.%Y")

def today_date_small_year() -> str:
	return datetime.today().strftime("%d.%m.%y")

def debug_save_to_json(obj: dict or str, filename: str = "debug.json"):
	if isinstance(obj, str):
		open(filename, "w", encoding = "utf-8").write(obj)

		return

	json.dump(
		obj,
		open(filename, "w", encoding = "utf-8"),
		ensure_ascii = False,
		indent = "\t"
	)

def toMD5(input_str: str) -> str:
	"""Converts `input_str` to MD5 hash.

	Args:
		input_str (str): Input string that would be hashed using MD5.

	Returns:
		str: MD5 string.
	"""

	return hashlib.md5(input_str.encode("utf-8")).hexdigest()

def to_b64_str(input_str: str) -> str:
	"""Returns Base64 string from `input_str` string.

	Args:
		input_str (str): Input string that would be converted to B64.

	Returns:
		str: Base64 string. (Not bytes!)
	"""

	return base64.b64encode(
		input_str.encode("utf-8")
	).decode("utf-8")

def int_to_emojis(number: int or str) -> str:
	emojis = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

	return "".join(emojis[int(char)] for char in str(number) if char.isdigit)

def random_uuid() -> str:
	return str(uuid.uuid4())


def unix_time() -> int:
	"""Returns current UNIX-time (seconds passed since January 1st, 1970 at 00:00:00 UTC) as `int`.

	Returns:
		int: UNIX-Time in seconds.
	"""

	return int(time.time())


def unix_time_ms() -> int:
	"""Returns current UNIX-time in ms (milliseconds passed since January 1st, 1970 at 00:00:00 UTC) as `int`.

	Returns:
		int: UNIX-Time in milliseconds.
	"""

	return round(time.time() * 1000)


def seconds_to_userfriendly_string(seconds, max=2, minutes=True, hours=True, days=True, weeks=False, months=False, years=False, decades=False):
	"""Преобразовывает UNIX-время как строку вида "5 часов, 17 секунд".

	Args:
		seconds ([type]): [description]
		max (int, optional): [description]. Defaults to 2.
		minutes (bool, optional): [description]. Defaults to True.
		hours (bool, optional): [description]. Defaults to True.
		days (bool, optional): [description]. Defaults to True.
		weeks (bool, optional): [description]. Defaults to False.
		months (bool, optional): [description]. Defaults to False.
		years (bool, optional): [description]. Defaults to False.
		decades (bool, optional): [description]. Defaults to False.

	Returns:
		[type]: [description]
	"""

	seconds = int(seconds)

	if seconds < 0:
		seconds = -seconds
	newSeconds = seconds
	string = []
	values = [60, 3600, 86400, 604800, 2678400, 31536000, 315360000]
	maxCount = max
	valuesgot = {"decades": 0, "years": 0, "months": 0,
              "weeks": 0, "days": 0, "hours": 0, "minutes": 0, "seconds": 0}
	stringslocal = [["век", "века", "века", "века", "веков"], ["год", "года", "года", "года", "лет"], ["месяц", "месяца", "месяца", "месяца", "месяцев"], ["неделя", "недели",
                                                                                                                                                        "недели", "неделей"], ["день", "дня", "дня", "дней"], ["час", "часа", "часа", "часов"], ["минута", "минуты", "минуты", "минут", ], ["секунда", "секунды", "секунды", "секунд"]]
	while True:
		if newSeconds >= values[6] and decades:
			newSeconds -= values[6]
			valuesgot["decades"] += 1
		elif newSeconds >= values[5] and years:
			newSeconds -= values[5]
			valuesgot["years"] += 1
		elif newSeconds >= values[4] and months:
			newSeconds -= values[4]
			valuesgot["months"] += 1
		elif newSeconds >= values[3] and weeks:
			newSeconds -= values[3]
			valuesgot["weeks"] += 1
		elif newSeconds >= values[2] and days:
			newSeconds -= values[2]
			valuesgot["days"] += 1
		elif newSeconds >= values[1] and hours:
			newSeconds -= values[1]
			valuesgot["hours"] += 1
		elif newSeconds >= values[0] and minutes:
			newSeconds -= values[0]
			valuesgot["minutes"] += 1
		else:
			valuesgot["seconds"] += newSeconds
			newSeconds = 0
			break
	for index, key in enumerate(valuesgot):
		if valuesgot[key] != 0:
			if len(stringslocal[index]) > valuesgot[key]:
				string.append(str(valuesgot[key]) + " " +
				              stringslocal[index][valuesgot[key] - 1])
			else:
				string.append(str(valuesgot[key]) + " " +
				              stringslocal[index][len(stringslocal[index]) - 1])
	if len(string) == 0:
		string.append("0 секунд")
	newStr = []
	for formatted_string in string:
		if maxCount > 0:
			newStr.append(formatted_string)
			maxCount -= 1
		else:
			break
	return ", ".join(newStr)

def parse_date_as_string(date_string: str) -> datetime:
	"""Парсит `date_string` в формате дд.мм.гг 

	Args:
		date_string (str): Строка с датой.
	"""

	return datetime.strptime(date_string, "%d.%m.%y")

def convert_datetime_to_string(datetime_obj: datetime) -> str:
	return datetime_obj.strftime("%d.%m.%Y") # Превращаем "1.2.33" в "1.2.3333"

def today_date_as_local_string() -> str:
	return datetime.now().strftime("%d %B")
