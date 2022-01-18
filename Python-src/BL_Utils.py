# coding: utf-8

import requests
import Utils
import json
import os
import aiohttp


class TokenHasBeenExpired(Exception):
	"""Вызывается, если токен просрочен."""

	pass

async def get_index_json(lesson_id: int or str) -> str:
	"""Загружает `index.json` файл через данный этой функции `lesson_id`.

	Args:
		lesson_id (int | str): Строка, или число, определяющее номер урока.

	Returns:
		str: Содержимое `index.json` файла.
	"""

	url = "https://onlinemektep.net/upload/online_mektep/lesson/{}/index.json"

	if isinstance(lesson_id, int):
		lesson_id = f"L_{lesson_id}"

	# По хуй пойми какой причине, в BL решили делать MD5 из MD5 строки вида `L_123456`. Почему? Я не ебу.
	lesson_id = Utils.toMD5(Utils.toMD5(lesson_id))

	# Вставляем в URL номер урока. (который является MD5 хешем, завёрнутый в MD5 хеш.)
	url = url.format(lesson_id)

	async with aiohttp.ClientSession() as session:
		async with session.get(url) as response:
			# Выдаём содержимое загруженного файла. Не забываем, что это *не* JSON.

			return await response.text()

def login(username: str, password: str, user_id: int, force_login: bool = False) -> dict:
	"""Пытаемся залогиниться на сайте.

	Args:
		username (str): Логин.
		password (str): Пароль.
		user_id (int): Идентификатор пользователя.
		force_login (bool, optional): `True`, если функция будет переавторизоваться, наплевав на кэш.

	Returns:
		dict: `dict`-объект со всей информацией о пользователе.
	"""

	if not force_login and os.path.exists(f"Data/User-{user_id}.json"):
		return Utils.load_data(f"User-{user_id}.json")

	url = "https://onlinemektep.net/api/v2/os/login"

	response = requests.post(
		url, json = {
			"login": username, "password": password
		}, 
		headers = {
			"User-Agent": Utils.random_useragent(),
			"Accept": "*/*",
		}
	)

	login_result = response.json()

	if "message" in login_result:
		return login_result

	# Вместо того, что бы хранить *всю* инфу о юзерах с BL, я 
	# решил сохранять лишь маленький кусочек данной информации,
	# конфиденциальности ради.
	data = {
		"FirstName": 		login_result["user_info"]["firstname"],
		"Token": 			login_result["access_token"],
		"Refresh-Token": 	login_result["refresh_token"],
		"Male": 			login_result["user_info"]["gender"] == "m",
		"ID":				user_id,
		"InlineButtons": 	{},
		# "School": 		login_result["user_info"]["school"]["name"],
		# "Location": 		login_result["user_info"]["school"]["address"],
		# "Class": 			login_result["user_info"]["group"]["name"],
	}

	Utils.save_data(data, f"User-{user_id}.json")

	return data


def refreshToken(refresh_token: str) -> dict:
	"""Пытаемся обновить токен.

	Args:
		user_id (int): Идентификатор пользователя.

	Returns:
		dict: `dict`-объект со всей информацией о пользователе.
	"""

	url = "https://onlinemektep.net/api/v2/os/refresh_token"

	response = requests.post(
		url, json={
            "refreshToken": refresh_token
        },
		headers={
			"User-Agent": Utils.random_useragent()
		}
	)
		
	return response.json()

def tokenMayExpire(func) -> dict:
	def wrapper(*args, **kwargs):


		try:
			return func(*args, **kwargs)
		except TokenHasBeenExpired:
			user_data = args[0]
			old_token = user_data["Token"]

			result = refreshToken(user_data["Refresh-Token"])

			user_data["Token"] = result["access_token"]
			user_data["Refresh-Token"] = result["refresh_token"]

			Utils.save_data(user_data, f"User-{user_data['ID']}.json")

			# Попытаться снова.
			args = list(args)
			for index, arg in enumerate(args):
				if arg == old_token:
					args[index] = user_data["Token"]

			# Сохраняем статистику бота:

			bot_data = Utils.load_data("Bot.json")
			bot_data["TokensGotRefreshed"] += 1
			Utils.save_data(bot_data, "Bot.json")

			return func(*args, **kwargs)

		except Exception as error:
			raise error

	return wrapper


@tokenMayExpire
async def get_schedule(user_data, token: str):
	url = "https://onlinemektep.net/api/v2/os/schedules"

	async with aiohttp.ClientSession() as session:
		async with session.get(url, headers={
			"Authorization": f"Bearer {token}",
			"X-Localization": "ru"
		}) as response:
			if response.status == 426:
				raise TokenHasBeenExpired("Токен истёк.")

			response_json = await response.json()

			returnDict = {
				"days": {},
				"weeks": response_json["weeks"],
				"groupInfo": response_json["groupInfo"]
			}

			for element in response_json["days"]:
				returnDict["days"].update({
					element["dateFormat"]: element
				})

			return returnDict


async def get_lesson_info(less_id: str, token: str) -> dict:
	url = f"https://onlinemektep.net/api/v2/os/schedule/lesson/{less_id}"

	async with aiohttp.ClientSession() as session:
		async with session.get(url, headers={
			"Authorization": f"Bearer {token}",
			"X-Localization": "ru"
		}) as response:

			return await response.json()


async def decode_url(file_data: str, lesson_id: str) -> str:
	url = "https://bilimlandbot.eu.pythonanywhere.com/api/decode"

	async with aiohttp.ClientSession() as session:
		async with session.post(url, json={"File": file_data, "LessonID": lesson_id}) as response:
			return await response.text()
