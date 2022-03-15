# coding: utf-8

"""

Файл с функциями для автоматического парсера и расстановки всех ответов в Bilimland.

Предупреждение: Код здесь очень сильно сломан, и в нём наверняка очень много багов, а так же он нечитабелен ввиду конченной структуры у файла index.json в Bilimland.

"""





import base64
import os
import aiohttp
import asyncio
import json
import hashlib
import random
import pgpy
import re
import time
from Utils import random_useragent, toMD5, to_b64_str
import Utils

class LessonIsEmpty(Exception):
	pass

class UnknownQuestionType(Exception):
	pass

class SummativeAssignmentFound(Exception):
	pass

class TooManyLessonPages(Exception):
	pass

DWNE = "______!DATA_WAS_NOT_EDITED_EDIT_ASAP!______"

default_data = {
	"lessonId": DWNE, #34434 из extended lesson info
	"progress": 10, #10 даже в самом начале оно 10, судя по всему
	"isFinished": 0, 
	"result": 0,
	"lessonVersion": DWNE, # в index.json
	"teacherId": DWNE, # где-то
	"subjectId": DWNE, # где-то
	"userId": DWNE, # id юзера
	"scheduleUuid": DWNE, # из расписания
	"passedExercises": 0, # меняется при каждом задании, в начале 0
	"allExerciseCount": 9,
	"course_id": 121212121212,
	"course_lesson_id": 343443343434,
	"lessonState": { # HERE ЗДЕСЬ +
		"loading": False,
		"state": {
			"modules": {
				"%info%": {},
				"%result%": {}
				# All other modules should be here.
			},
			"checked": {
				# "Конспект": 1, и далее идут остальные уроки, которые просмотрели
			},
			"page": 0,
			"mid": DWNE, 
			"prevMid": DWNE, # None если самое-самое начало, %info% если повезёт, и запрос отправится когда конспект был прочитан
			"expandedPages": {
				"0": 1
			},
			"isFinished": False,
			"isLocked": False,
			"showLoadingIndicator": True,
			"content": { "tblock": {} },
			"isSidePanelCollapsed": False,
			"isFullscreened": False,
			"isScrollLocked": False,
			"onceFailed": {},
			"adapt": [],
			"pageErr": {},
			"pageReadonly": {},
			"isTeacher": False,
			"chainsActive": False,
			"defaultLevelChain": 1,
			"checkedTimes": {
				#: 1, FI и все последующие модули
			},
			"customHintsPrev": {
				#: {}, FI и все последующие модули
			},
			"solvedModules": [
				# FI, и все последующие модули
			],
			"isOnlineLesson": True,
			"lessonClass": None,
			"descriptors": {},
			"time": 0,
			"isStudentState": False,
			"teacherIsFinished": False,
			"newAdaptive": {
				"category": "A",
				"level": 1,
				"currentMark": 0,
				"adaptiveModules": [
					DWNE # не знаю, но идёт после FI
				],
				"isFinished": False,
				"correctStrike": 0,
				"isAdaptiveChoice": False,
				"isAdaptiveFailed": False
			},
			"moduleTickets": {},
			"adaptiveHint": "",
			"currentProgress": 10,
			"moduleError": False,
			"finishLoading": False,
			"pages": [
				{
					"id": 0,
					"modules": [
						# Все модули тут должны быть тут,
						# 
						# "UUID",
						# "UUID",
						# "UUID"
					],
					"title": DWNE # TITLE
				}
			],
			"enabledModules": [
				"%info%"
				# Текущий UUID задания
				# UUID следующего задания
			]
		},
		"uiLang": DWNE,						# доставать с index.json, иначе всё будет на английском
		"platformVersion": DWNE, # возможно стоит доставать с манифеста?
		"buffer": {
			"initialPag": {
				"mid": "",
				"prevLink": "",
				"nextLink": ""
			}
		},
		"err": None
	},
}

default_lesson_module_data = {
	"exerciseCount": 1,
	"title": "",
	"isInteractive": True,
	"isVideoModule": False,
	"descriptors": {},
	"currentTime": None
}

default_lesson_module_data_by_types = {
	"simple": {
		"exerciseCorrectCount": 1
	},

	"choice": {
		"selMultiple": {},
		"selSingle": "",
	},

	"expressions": {
		"val": {}
	},

	"connection": {
		"lines": [],
		"sel": {
			"left": None,
			"right": None
		},
	},

	"sort": {
		"ids": []
	},

	"select": {
		"sel": None
	},

	"markWords": {
		"sel": {}
	}
}

def listWalker(list_to_extract_from, allowed_types_inside_lists = []):
	def _walker(l):
		if isinstance(l, list):
			for item in l:
				if isinstance(item, list):
					yield from _walker(item)
				elif isinstance(item, dict):
					yield item
				else:
					for type in allowed_types_inside_lists:
						if isinstance(item, type):
							yield item
		elif isinstance(l, dict):
			yield l


	return list(_walker(list_to_extract_from))

def dictWalker(obj: dict, values_to_fallthrough: list, return_if_found_value: list, value_cannot_be_with_value: list):
	obj = obj.copy()

	if not isinstance(obj, dict):
		return obj

	for index, value in enumerate(return_if_found_value):
		if value in obj and obj[value] not in value_cannot_be_with_value:
			return obj

	for value in values_to_fallthrough:
		if value in obj:
			return dictWalker(obj[value], values_to_fallthrough, return_if_found_value, value_cannot_be_with_value)

	return obj

def merge(source, destination):
	for key, value in source.items():
		if isinstance(value, dict):
			node = destination.setdefault(key, {})
			merge(value, node)
		elif key not in destination or not isinstance(destination[key], dict):
			destination[key] = value

	return destination

class TokenHasBeenExpired(Exception):
	"""Вызывается, если токен просрочен."""

	pass

class TokenIsBroken(Exception):
	"""Вызывается, если токену пизда."""
	
	pass

async def refreshToken(refresh_token: str) -> dict:
	"""Пытаемся обновить токен.

	Args:
		user_id (int): Идентификатор пользователя.

	Returns:
		dict: `dict`-объект со всей информацией о пользователе.
	"""

	url = "https://onlinemektep.net/api/v2/os/refresh_token"

	async with aiohttp.ClientSession() as session:
		async with session.post(url, headers={
			"User-Agent": Utils.random_useragent()
		}, json={
			"refreshToken": refresh_token
		}) as response:
			return await response.json()

def tokenMayExpire(func):
	async def wrapper(*args, **kwargs):
		try:
			return await func(*args, **kwargs)
		except TokenHasBeenExpired:
			user_data = args[0]
			old_token = user_data["Token"]

			result = await refreshToken(user_data["Refresh-Token"])

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

			return await func(*args, **kwargs)

		except Exception as error:
			raise error

	return wrapper

@tokenMayExpire
async def get_user_data(userData: dict, token: str):
	URL = "https://onlinemektep.net/api/v2/os/user-info"

	async with aiohttp.ClientSession() as session:
		async with session.get(URL, headers={
			"Authorization": f"Bearer {token}",
			"X-Localization": "ru",
			"X-Quarter": "20221",
			"User-Agent": random_useragent()
		}) as response:
			if response.status != 200:
				raise Exception(f"Error {response.status}. Probably token has been expired?")

			return await response.json()

@tokenMayExpire
async def get_schedule(userData: dict, token: str, schedule_date: str): 
	URL = f"https://onlinemektep.net/api/v2/os/schedules?date={schedule_date}"

	async with aiohttp.ClientSession() as session:
		async with session.get(URL, headers={
			"Authorization": f"Bearer {token}",
			"X-Localization": "ru",
			"X-Quarter": "20221",
		}) as response:
			if response.status != 200:
				raise Exception(f"Error {response.status}. Probably token has been expired?")

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

@tokenMayExpire
async def get_lesson_info(userData: dict, token: str, schedule_id: str):
	URL = f"https://onlinemektep.net/api/v2/os/schedule/lesson/{schedule_id}"

	async with aiohttp.ClientSession() as session:
		async with session.get(URL, headers={
			"Authorization": f"Bearer {token}",
			"X-Localization": "ru",
			"X-Quarter": "20213",
			"User-Agent": random_useragent()
		}) as response:
			if response.status != 200:
				print(await response.text())

				raise Exception(f"Error {response.status}. Probably token has been expired?")

			return await response.json()

@tokenMayExpire
async def get_lesson_access(userData: dict, token: str, lesson_id: int):
	URL = "https://onlinemektep.net/api/v2/os/lesson-access"

	async with aiohttp.ClientSession() as session:
		async with session.post(URL, json={
			"lessonId": lesson_id,
		}, headers={
			"Authorization": f"Bearer {token}",
			"User-Agent": random_useragent()
		}) as response:
			if response.status != 200:
				print(await response.text())

				raise Exception(f"Error {response.status}. Probably token has been expired?")

			return await response.json()

async def get_lesson_answers_link(lesson_id: int | str, is_a_summative: bool = False, is_a_soch_summative: bool = False):
	URL = ("https://onlinemektep.net/upload/files/" + ("soch" if is_a_soch_summative else "sor") + "/q20213/{}/index.json") if is_a_summative else "https://onlinemektep.net/upload/online_mektep/lesson/{}/index.json"

	if isinstance(lesson_id, int):
		lesson_id = f"L_{lesson_id}"

	if is_a_summative:
		# Дан СОР/СОЧ.

		return URL.format(lesson_id)
	else:
		# Дан обычный урок.
		lesson_hash = toMD5(toMD5(lesson_id)) # MD5(MD5("L_123456"))

		return URL.format(lesson_hash)

async def get_lesson_answers_file(lesson_index_file_url: str, secure_token: str = None):
	headers = {}
	if secure_token:
		headers.update({
			"secure-token": secure_token
		})

	async with aiohttp.ClientSession() as session:
		async with session.get(lesson_index_file_url, headers = headers) as response:
			if response.status != 200:
				raise Exception(f"Error {response.status}. This can happen because Bilimland does not allow getting index.json file without sending other requests.")

			return await response.text()

async def decode_lesson_answers_file(lesson_answers_file_content: str, json_decode: bool = True):
	emsg   = pgpy.PGPMessage.from_blob(lesson_answers_file_content)
	key, _ = pgpy.PGPKey.from_file("BLKeys/Private key")

	with key.unlock(open("BLKeys/Secret phrase", "r").read()):
		decoded = key.decrypt(emsg).message.decode("utf-8")
		
		if json_decode:
			return json.loads(decoded)
		else:
			return decoded

async def parse_lesson_answers(lesson_answers_decoded):
	answers_new = {}

	def _parse_main_type(obj):
		if obj["type"] == "choice":
			options_new = {}

			# For "isMultiple":
			for option in obj["options"]:
				if option["right"]:
					if obj["isMultiple"]:
						options_new.update({option["id"]: 1})
					else:
						obj["parsedModuleAnswers"] = option["id"]
						obj["parsedModuleAnswersToCopy"] = {
							"selSingle": option["id"]
						}
						break
					
			if obj["isMultiple"]:
				obj["parsedModuleAnswers"] = options_new
				obj["parsedModuleAnswersToCopy"] = {
					"selMultiple": options_new
				}
		elif obj["type"] == "sort":
			# Simply generate list from 0 to length of all items:

			obj["parsedModuleAnswers"] = list(range(len(obj["items"])))
			obj["parsedModuleAnswersToCopy"] = {
				"ids": obj["parsedModuleAnswers"]
			}
		elif obj["type"] == "connection":
			new_connections = []
			is_multiple = False

			for connection in obj["left"]:
				connectionId = connection
				connection = obj["left"][connection]

				if len(connection["val"]) > 1:
					is_multiple = True

				for lineLetter in connection["val"]:
					new_connections.append({
						"left": connectionId,
						"right": lineLetter
					})

			obj["parsedModuleAnswers"] = new_connections

			obj["parsedModuleAnswersToCopy"].update({
				"lines": new_connections,
				"sel": {
					"left": None,
					"right": None
				}
			})
		elif obj["type"] == "select":
			obj["parsedModuleAnswers"] = obj["right"]

			obj["parsedModuleAnswersToCopy"].update({
				"sel": obj["right"]
			})
		elif obj["type"] == "markWords":
			# "sel": {
			# 	"0::4": 1,
			# 	"0::8": 1,
			# 	"0::12": 1
			# },
			#
			# Жылы, биіктік, көрікті, тұщы, емдік, ыстық, термалды, ұсақ, асқазан, улану
			#                   *             *              *                         
			#   0     2         4       6     8      10      12	     14        16 	18
			#
			# {f"{paragraph_id}:{empty, but can be marker id?}:{word_id * 2}": marker_id?}
			#
			# "Жылы, биіктік, [m1]көрікті, тұщы, [m1]емдік, ыстық, [m1]термалды, ұсақ, асқазан, улану"

			# Check if markers count is more than 1:
			if len(obj["marks"]) > 1:
				raise NotImplementedError(f"Found more than 1 marker, {len(obj['markers'])}, in module id {obj['id']}")

			allTextContent = listWalker(obj["content"], [str])
			words_obj = {}

			for paragraphIndex, markContent in enumerate(allTextContent):
				markContent: str

				RE_WORDS = r"\[m\d+\](?:\w+)"
				RE_MARKER_ID = r"\[m(\d+)\]" # <- Thanks Github Copilot for this regex!

				markContent = markContent.lstrip("P:") # pyright: reportGeneralTypeIssues=false

				words = markContent.split(" ")
				words_re = re.findall(RE_WORDS, markContent)
				marker_ids = list(re.findall(RE_MARKER_ID, markContent))
				
				words_removed = 0

				for re_index, re_word in enumerate(words_re):
					for index, word in enumerate(words):
						if re_word in word:
							words_removed += 1

							words_obj.update({f"{paragraphIndex}::{(index + words_removed) * 2}": marker_ids[re_index]})


			obj["parsedModuleAnswers"] = words_obj
			obj["parsedModuleAnswersToCopy"] = {
				"sel": words_obj
			}
		else:
			raise UnknownQuestionType("Unknown module type", obj["type"], "inside", obj["id"])

	def _parse_list_type(insideListItem, extracted_dicts, obj):
		for listExpression in insideListItem:
			if listExpression["type"] in ["expression", "inlineGroup"]:
				if listExpression["kind"] == "choice":
					answers_new.update({listExpression["id"]: listExpression["right"]})
				elif listExpression["kind"] == "dragnest":
					all_dragitems = [
						i for i in extracted_dicts if i["type"] in ["expression", "inlineGroup"] and i["kind"] == "dragitem" 
					]
					dragitems_parsed = {}
					for dragitem in all_dragitems:
						dragitems_parsed.update({dragitem["id"]: dragitem})

					for value in listExpression["value"]:
						new_dragnest_value = {
							"isDragNode": True,
							"eid": value,
							"content": dragitems_parsed[value]
						}

						if value not in answers_new:
							answers_new.update({value: [new_dragnest_value]})
						else:
							answers_new[value].append(new_dragnest_value)
				else:
					raise UnknownQuestionType("Found unknown kind", listExpression["kind"], "in list expressions block, module id", obj["id"])
			elif listExpression["type"] == "formula":
				LATEX_INPUT_RE = r"\\Input{(.+?)}"

				if r"\Input" in listExpression["latex"]:
					found_input_values = re.findall(LATEX_INPUT_RE, listExpression["latex"])

					for index, input_value in enumerate(found_input_values):
						input_value_choosen = input_value.split("|")
						input_value_choosen = input_value_choosen[0] # I'm too lazy to parse shit like \Input{–2|\;–2}

						answers_new.update({
							f"{listExpression['fid']}.{index}": {
								"mask": input_value,
								"val": input_value_choosen
							}
						})
			else:
				raise UnknownQuestionType("Found unknown type", listExpression["type"], "in list expressions block, module id", obj["id"])

	def _parse_expression_type(obj):
		extracted_dicts = listWalker(obj["content"])

		answers_new.clear()

		for expression in extracted_dicts:
			another = listWalker(dictWalker(expression, ["list"], ["type"], ["set", "setItem"]))
			kind = expression.get("kind")

			if kind == "choice":
				answers_new.update({expression["id"]: expression["right"]})
			elif kind is None:
				for nested_answer in another:
					if nested_answer["type"] == "setItem":
						nested_list = listWalker(nested_answer["list"])
						for nested_answer in nested_list:
							if nested_answer.get("type", "formula") == "formula":
								if "\\Input" in nested_answer["latex"]:
									raise NotImplementedError("Support for 'input' in formulas is not fully implemented yet, in expression id", expression["id"])

								continue

							if nested_answer["kind"] == "dragnest":
								all_dragitems = [i for i in extracted_dicts if i.get("kind") == "dragitem"]
								dragitems_parsed = {}
								for dragitem in all_dragitems:
									dragitems_parsed.update({dragitem["id"]: dragitem["list"]})

								for dragnest_value in nested_answer["value"]:
									new_dragnest_value = {
										"isDragNode": True,
										"eid": dragnest_value,
										"content": dragitems_parsed[dragnest_value]
									}

									if nested_answer["id"] not in answers_new:
										answers_new.update({nested_answer["id"]: [new_dragnest_value.copy()]})
									else:
										answers_new[nested_answer["id"]].append(new_dragnest_value.copy())

							elif nested_answer["kind"] == "choice":
								answers_new.update({nested_answer["id"]: nested_answer["right"]})
							elif nested_answer["kind"] == "input":
								# 30|30.0
								values = nested_answer["value"].split("|")

								answers_new.update({nested_answer["id"]: random.choice(values)})
							else:
								raise UnknownQuestionType("Unknown answer kind", nested_answer["kind"], "in id", module["id"])
					elif nested_answer["type"] == "plot":
						plot = nested_answer["graph"]

						if plot.get("curves", []) != []:
							raise UnknownQuestionType("Found 'curves' object in plot with module id id", module["id"])

						curPoints = []

						for point in plot["points"]:
							curPoints.append({
								"x": point["x"],
								"y": point["y"]
							})

						answers_new.update({
							nested_answer["id"]: {
								"points": curPoints,
								"curves": {},
								"curvesMoved": {}
							}
						})
					elif nested_answer["type"] == "formula":
						LATEX_INPUT_RE = r"\\Input{(.+?)}"

						if "\\Input" in nested_answer["latex"]:
							found_input_values = re.findall(LATEX_INPUT_RE, nested_answer["latex"])

							for index, input_value in enumerate(found_input_values):
								input_value_choosen = input_value.split("|")
								input_value_choosen = input_value_choosen[0] # I'm too lazy to parse shit like \\Input{–2|\;–2}

								answers_new.update({
									f"{nested_answer['fid']}.{index}": {
										"mask": input_value,
										"val": input_value_choosen
									}
								})
					elif nested_answer["type"] == "table":
						nested_list = nested_answer["list"]

						for tableElement in nested_list:
							if tableElement["type"] == "tableRow":
								for tableCell in tableElement["list"]:
									if tableCell["type"] == "tableCell":
										tableCellKind = tableCell.get("kind")

										if tableCellKind == "heading":
											# We don't need to parse headings.
											continue
										elif tableCellKind is None:
											tableExpressions = listWalker(tableCell["list"])

											for tableExpression in tableExpressions:
												if obj["id"] == "7687fc70-3081-11eb-ab3d-d721b4cabba3":
													pass

												tableExpression.update({"isAFakeExpression": True})
												
												# answers_copy = answers_new.copy()
												_parse_expression_type({"content": [tableExpression]})
												# merge(answers_copy, answers_new)

											pass
										else:
											raise UnknownQuestionType("Found kind type", tableCell.get("kind"), "in tableRow block, module id", obj["id"])
									else:
										raise UnknownQuestionType("Found unknown type", tableCell["type"], "in tableRow block, module id", obj["id"])
							else:
								raise UnknownQuestionType("Found unknown type", tableElement["type"], "in type table block, module id", obj["id"])
					elif nested_answer["type"] == "paragraph":
						continue # We don't need to parse paragraphs.
					elif nested_answer["type"] == "toggleBlock":
						continue # We don't need to parse toggleBlocks.
					elif nested_answer["type"] == "text":
						continue # We don't need to parse text.
					elif nested_answer["type"] == "list":
						for listItem in nested_answer["list"]:
							if listItem["type"] == "listItem":
								insideListItem = listWalker(listItem["list"])

								_parse_list_type(insideListItem, extracted_dicts, obj)

							else:
								raise UnknownQuestionType("Found unknown type", listItem["type"], "in list block, module id", obj["id"])
					elif nested_answer["type"] == "inlineGroup":
						insideListItem = listWalker(nested_answer["list"])

						_parse_list_type(insideListItem, extracted_dicts, obj)
					else:
						raise UnknownQuestionType("Found unknown type", nested_answer["type"], "near nested_answer block, id", obj["id"])
			elif kind == "input":
				# 30|30.0
				values = expression["value"].split("|")

				answers_new.update({expression["id"]: random.choice(values)})
			elif kind == "dragitem":
				# ignore dragitems, all logic is handled in dragnest above

				continue
			elif kind == "dragnest":
				all_dragitems = [i for i in extracted_dicts if i.get("kind") == "dragitem"]
				dragitems_parsed = {}
				for dragitem in all_dragitems:
					dragitems_parsed.update({dragitem["id"]: dragitem["list"]})

				for dragnest_value in expression["value"]:
					new_dragnest_value = {
						"isDragNode": True,
						"eid": dragnest_value,
						"content": dragitems_parsed[dragnest_value]
					}

					if expression["id"] not in answers_new:
						answers_new.update({expression["id"]: [new_dragnest_value]})
					else:
						answers_new[expression["id"]].append(new_dragnest_value)

				obj["parsedModuleAnswersToCopy"].update({
					"val": answers_new
				})
			elif kind == "sortable":
				answers_new.update({expression["id"]: expression["list"]})

				# // TODO: Add obj["parsedModuleAnswersToCopy"]...
			else:
				raise UnknownQuestionType("Unknown kind found", kind, "in module id", obj["id"], "with id", expression.get("id"))

		# Loop ended
		obj["parsedModuleAnswers"] = answers_new.copy()
		obj["parsedModuleAnswersToCopy"] = {
			"val": answers_new.copy()
		}

	lesson_answers_parsed = {"modules": {}, "moduleIDsOrdered": [], "allModulesList": [], "moduleTypes": {}, "nonInteractiveModules": [], **lesson_answers_decoded}

	if "purposes" in lesson_answers_decoded:
		raise SummativeAssignmentFound(f"Summative assignments are not supported yet. (label: {lesson_answers_decoded['label']})")

	for pageIndex, page in enumerate(lesson_answers_decoded["pages"]):
		for category in page["categories"]:
			categoryObj = page["categories"][category]

			for num in categoryObj:
				numObj = categoryObj[num]

				# Получаем последнее значение в списке
				lesson_answers_parsed["moduleIDsOrdered"].append(numObj[-1])

		for moduleIndex, module in enumerate(page["modules"]):
			lesson_answers_parsed["modules"].update({module["id"]: module})

	# We should parse our data now:
	for moduleIndex, module in enumerate(lesson_answers_parsed["modules"]):
		module = lesson_answers_parsed["modules"][module]
		module.update({
			"parsedModuleAnswers": {},
			"parsedModuleAnswersToCopy": {},
			"defaultAnswerToCopy": {}
		})
		lesson_answers_parsed["allModulesList"].append(module["id"])
		lesson_answers_parsed["moduleTypes"].update({module["id"]: module["type"]})

		if not module["type"] in default_lesson_module_data_by_types:
			raise UnknownQuestionType("Unknown module type: " + module["type"] + " in module id: " + module["id"])

		module["defaultAnswerToCopy"] = default_lesson_module_data_by_types.get(module["type"], {}).copy()

		# prevModule = None
		# if moduleIndex > 0:
		# 	prevModule = lesson_answers_parsed["modules"][lesson_answers_parsed["allModulesList"][moduleIndex - 1]]["id"]

		if module.get("type", "simple") == "simple":
			# Simple modules are interactive.
			lesson_answers_parsed["nonInteractiveModules"].append(module["id"])
			module.update({
				"isInteractive": False
			})
			
			continue

		module.update({
			"isInteractive": True
		})
		if module["type"] == "expressions":
			_parse_expression_type(module)
		else:
			_parse_main_type(module)

		# Sanity checks:
		if module.get("parsedModuleAnswers", {}) == {}:
			raise Exception("No 'parsedModuleAnswers' found in module id", module["id"])

		if module.get("parsedModuleAnswersToCopy", {}) == {}:
			raise Exception("No 'parsedModuleAnswersToCopy' found in module id", module["id"])

	# For loop ended.
	# lesson_answers_parsed["moduleIDsOrdered"].insert(0, *lesson_answers_parsed["nonInteractiveModules"])
	lesson_answers_parsed["moduleIDsOrdered"] = [lesson_answers_parsed["nonInteractiveModules"][0], *lesson_answers_parsed["moduleIDsOrdered"]]



	return lesson_answers_parsed

async def get_lesson_state(lesson_id: int, user_id: int, teacher_user_id: int | None=None, for_finished_lesson: bool=False):
	toBeHashed = f"state_{lesson_id}_{user_id}" if teacher_user_id is None else f"state_{lesson_id}_{user_id}_{teacher_user_id}"
	hashedString = toMD5(toBeHashed)

	URL = f"https://lesson-state-service.onlinemektep.net/v2/state/{'finished_' if for_finished_lesson else ''}{hashedString}"

	async with aiohttp.ClientSession() as session:
		async with session.get(URL) as response:
			if response.status != 200:
				raise LessonIsEmpty(f"Lesson does not exist, send data by yourself")
				
			return await response.json()

async def generate_lesson_state_post_content(parsed_answers: dict, merged_lesson: dict, user_info: dict):
	default_lesson_data = default_data.copy()

	if len(parsed_answers["pages"]) > 1:
		raise TooManyLessonPages("Found more than one page in lesson answers.")

	new_lesson_data = default_lesson_data
	new_lesson_data.update({
		"lessonId": merged_lesson["lessonId"],
		"progress": 10,
		"isFinished": 0, 
		"result": 0,
		"lessonVersion": parsed_answers["version"],
		"teacherId": merged_lesson["teacher"]["userId"],
		"subjectId": merged_lesson["lessonMeta"]["subjectId"],
		"userId": user_info["BilimlandID"],
		"scheduleUuid": merged_lesson.get("scheduleId"),
		"passedExercises": 0
	})

	lesson_state = new_lesson_data["lessonState"]
	lesson_state.update({
		"platformVersion": "API-20.04.12", # // TODO
		"uiLang": parsed_answers["interfaceLang"]
	})

	lesson_state["state"]["pages"][0]["title"] = parsed_answers["title"]
	lesson_state["state"]["checkedTimes"].update({parsed_answers["moduleIDsOrdered"][0]: 1})
	lesson_state["state"]["customHintsPrev"].update({parsed_answers["moduleIDsOrdered"][0]: {}})
	lesson_state["state"]["checked"].update({parsed_answers["moduleIDsOrdered"][0]: 1})
	lesson_state["state"]["solvedModules"].append(parsed_answers["moduleIDsOrdered"][0])
	lesson_state["state"]["enabledModules"].append(parsed_answers["moduleIDsOrdered"][0])
	lesson_state["state"]["enabledModules"].append(parsed_answers["moduleIDsOrdered"][1])
	lesson_state["state"]["mid"] = parsed_answers["moduleIDsOrdered"][1]
	lesson_state["state"]["prevMid"] = parsed_answers["moduleIDsOrdered"][0]
	# lesson_state["state"]["prevMid"] = "%info%"
	lesson_state["state"]["newAdaptive"]["adaptiveModules"] = [ parsed_answers["allModulesList"][1] ]

	for module in parsed_answers["modules"]:
		moduleObj = parsed_answers["modules"][module]

		lesson_state["state"]["modules"].update({
			module: default_lesson_module_data.copy() # Я потратил, сука, минут 15, что бы понять, что питон меняет значения всех значений так как я забыл .copy(), блять.
		})

		lessonStateModule = lesson_state["state"]["modules"][module]

		lesson_state["state"]["pages"][0]["modules"].append(module)

		# Check if this is a interactive module:
		if module in parsed_answers["nonInteractiveModules"]:
			lessonStateModule["isInteractive"] = False

		lessonStateModule.update(moduleObj["defaultAnswerToCopy"])	



	return new_lesson_data	

@tokenMayExpire
async def send_lesson_new_state(userData: dict, token: str, new_data: dict, lesson_id: int, user_id: int, teacher_user_id: int | None=None, for_finished_lesson: bool=False, ignore_duplicate: bool=False):
	toBeHashed = f"state_{lesson_id}_{user_id}" if teacher_user_id is None else f"state_{lesson_id}_{user_id}_{teacher_user_id}"
	hashedString = toMD5(toBeHashed)

	URL = f"https://lesson-state-service.onlinemektep.net/v2/state/{'finished_' if for_finished_lesson else ''}{hashedString}"

	async with aiohttp.ClientSession() as session:
		async with session.post(URL, data = to_b64_str(json.dumps(new_data, ensure_ascii=False)), headers={
			"Authorization": token
		}) as response:
			if (await response.json())["status"] == "duplicate" and not ignore_duplicate:
				raise Exception("Duplicate found.")

			if response.status != 200:
				raise Exception(f"Error {response.status}. Probably token has been expired?")

			return await response.json()

async def add_answer_to_state(prev_state: dict, parsed_answers: dict):
	new_state = prev_state.copy()

	new_state["lessonState"]["state"]["adaptiveHint"] = "correct"
	new_state["lessonState"]["state"]["currentProgress"] += 10
	new_state["progress"] += 10
	new_state["passedExercises"] += 1

	prev_lesson_id = new_state['lessonState']['state']['prevMid']
	cur_lesson_id = new_state['lessonState']['state']['mid']
	if cur_lesson_id == "%info%":
		cur_lesson_id = parsed_answers["moduleIDsOrdered"][0]

	cur_lesson_id_index = parsed_answers["moduleIDsOrdered"].index(cur_lesson_id)
	next_lesson_id = parsed_answers["moduleIDsOrdered"][cur_lesson_id_index + 1]
	next_next_lesson_id = "%result%"
	if cur_lesson_id_index > len(parsed_answers["moduleIDsOrdered"]):
		# All done. Let next_next_lesson_id be "%result%"
		pass
	else:
		next_next_lesson_id = parsed_answers["moduleIDsOrdered"][cur_lesson_id_index + 2]

	new_state["lessonState"]["state"]["modules"][next_lesson_id].update({
		"exerciseCorrectCount": 1,
		"time": round(random.uniform(15, 130), 2),
		**parsed_answers["modules"][next_lesson_id]["parsedModuleAnswersToCopy"],
	})
	new_state["lessonState"]["state"]["solvedModules"].append(next_lesson_id)
	new_state["lessonState"]["state"]["checked"].update({next_lesson_id: 1})
	new_state["lessonState"]["state"]["checkedTimes"].update({next_lesson_id: 1})
	new_state["lessonState"]["state"]["customHintsPrev"].update({next_lesson_id: {}})

	new_state["lessonState"]["state"]["enabledModules"].append(next_next_lesson_id)
	new_state["lessonState"]["state"]["mid"] = next_lesson_id
	new_state["lessonState"]["state"]["prevMid"] = cur_lesson_id



	

	return new_state

async def mark_lesson_state_as_complete(lesson_state_dict: dict):
	new_state = lesson_state_dict.copy()

	new_state.update({
		"isFinished": 1,
		"passedExercises": 9,
		"progress": 100,
		"result": 100,
	})
	new_state["lessonState"]["state"].update({
		"isFinished": True,
        "isLocked": True,
		"mid": "%result%",
		"page": -2
	})

	return new_state

async def modify_lesson_state_for_final_store(final_state: dict):
	new_state = final_state.copy()

	del new_state["allExerciseCount"]
	del new_state["course_id"]
	del new_state["course_lesson_id"]
	del new_state["isFinished"]
	del new_state["lessonId"]
	del new_state["lessonVersion"]
	del new_state["passedExercises"]
	del new_state["progress"]
	del new_state["result"]
	del new_state["scheduleUuid"]
	del new_state["subjectId"]
	del new_state["teacherId"]
	del new_state["userId"]
	new_state.update(new_state["lessonState"])
	del new_state["lessonState"]

	return new_state

@tokenMayExpire
async def send_store_state(userData: dict, token: str, final_store_state: dict):
	URL = "https://onlinemektep.net/api/v2/os/platform/progress/store"

	async with aiohttp.ClientSession() as session:
		async with session.post(URL, json = final_store_state, headers={
			"Authorization": token
		}) as response:
			if response.status != 200:
				raise Exception(f"Error {response.status}. Probably token has been expired?")

			return await response.json()
