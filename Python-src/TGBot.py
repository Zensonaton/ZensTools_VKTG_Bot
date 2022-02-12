# coding: utf-8

import 	json
from 	typing import Any, Tuple
from    aiogram             import 	Bot, types, md
from    aiogram.dispatcher  import 	Dispatcher
from    aiogram.utils       import 	executor, markdown
from 	aiogram.types 		import 	ReplyKeyboardRemove, \
									ReplyKeyboardMarkup, KeyboardButton, \
									InlineKeyboardMarkup, InlineKeyboardButton, Update, MediaGroup, InputFile, InputMedia
import 	aiohttp
from    dotenv              import 	load_dotenv
import 	BL_Utils			as _BL
import 	BL_AutoParser		as BL	
from 	Utils 				import 	convert_datetime_to_string, int_to_emojis, load_data, parse_date_as_string, random_uuid, save_data, seconds_to_userfriendly_string, today_date, today_date_as_local_string, today_date_small_year, unix_time
from 	textwrap 			import 	shorten
import 	Screenshoter
import 	traceback
import 	datetime
import 	logging
import 	asyncio
import 	time
import 	sys
import 	os

# Меняем Timezone:
os.environ["TZ"] = "Asia/Almaty"
time.tzset()

# Загружаем .env файл.
load_dotenv()

# Инициализируем Телеграм-бота.
bot = Bot(
	token       = os.environ["TG_TOKEN"],
	parse_mode  = types.ParseMode.HTML
)

PROD = (os.getenv("PRODUCTION", "false").lower() == "true")


# Обработчик команд.
dp = Dispatcher(bot)

if not os.path.exists("./Logs/"):
	os.mkdir("./Logs/")

# Логирование.
logger = logging.getLogger(__name__)
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(logging.Formatter("[%(levelname)-8s %(asctime)s at %(name)s.%(funcName)s]: %(message)s", "%d.%d.%Y %H:%M:%S"))
streamHandler.setLevel(logging.DEBUG)
logger.addHandler(streamHandler)
fileHandler = logging.FileHandler("Logs/TGBot.log")
fileHandler.setFormatter(logging.Formatter("[%(levelname)-8s %(asctime)s at %(name)s.%(funcName)s]: %(message)s", "%d.%d.%Y %H:%M:%S"))
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(fileHandler)

# Для маленьких кнопок:
smaller_lesson_names = {
	"Алгебра и начала анализа": "Алгебра",
	"Русская литература": "Рус. лит.",
	"Английский язык": "Англ. яз.",
	"Казахский язык и литература": "Каз. яз/лит.",
	"Информатика (5-11 классы)": "Информатика",
	"Физическая культура": "Физ/ра",
	"История Казахстана": "История Каз.",
	"Основы предпринимательства и бизнеса": "Осн. бизнеса",
}

UPTIME = unix_time()
WHITELIST = [str(i) for i in load_data("Whitelist.json")]

# Whitelist
@dp.message_handler(lambda msg: not (str(msg.from_user.id) in WHITELIST or msg.from_user.username in WHITELIST))
async def non_whitelisted_handler(msg: types.Message):
	if not msg.is_command():
		return
	full_user_name = f"{msg.from_user.first_name} {msg.from_user.last_name}"

	logger.info(f"Стучится юзер '{full_user_name}' с ID: {msg.from_user.id}, никнеймом: {msg.from_user.username}")
	await msg.answer("Нет доступа.")
	await bot.send_message(os.environ["ADMIN_TELEGRAM_ID"], f"🗒 Не в белом списке: <code>{full_user_name}</code>, с ID: <code>{msg.from_user.id}</code>, никнеймом: <code>{msg.from_user.username}</code>.\nКоманда для добавления: <code>/add {msg.from_user.username or msg.from_user.id}</code>", disable_notification=True)

@dp.message_handler(lambda msg: str(msg.from_user.id) == os.environ["ADMIN_TELEGRAM_ID"], commands = ["add"])
async def add_to_whitelist_handler(msg: types.Message):
	global WHITELIST

	old_list = load_data("Whitelist.json")
	arguments = msg.get_args().split(" ")
	if len(arguments) != 1 or arguments[0] == "":
		await msg.answer(f"<code>/add username</code> или <code>/add telegram_user_id</code>")
		
		return

	if not arguments[0] in old_list:
		old_list.append(arguments[0])
		save_data(old_list, "Whitelist.json")
		WHITELIST = old_list

	await msg.answer(f"Успешно добавил.\nНовый лист: {', '.join([('<code>' + str(i) + '</code>') for i in old_list])}.")

@dp.message_handler(commands = ["start", "start", "старт"])
async def message_handler(msg: types.Message):
	#У бота есть <a href='https://github.com/Zensonaton/ZensonatonTools_TGBot'>открытый исходный код</a>, поэтому ты можешь проверить что он делает 'за кулисами'.
	await msg.answer(
		"<b>Привет!</b> 👋\nДанный бот может отправлять дешифрованные ответы на задания от Bilimland после отправки логина + пароля. <i>(однако бот не может работать с СОРами или СОЧами.)</i>\n\nДля ознакомления я советую использовать команду <code>/help</code>, однако ты можешь сразу попробовать команду <code>/login логин пароль</code> в действии."
	)

@dp.message_handler(commands=["help", "команды", "помощь", "info", "инфо"])
async def help(msg: types.Message):
	await msg.answer(
		f"ℹ️ <b>Список команд у данного бота</b>:\n\n/login логин пароль — вход в аккаунт Bilimland.\n/schedule — получить список расписания уроков в Bilimland, а так же ссылки на ответы. Так же возможно указать дату, на которой нужно получить расписание: <code>/schedule дд.мм.гг</code>. <i>Эта команда работает только после авторизации.</i>\n/feedback — возможность написать автору бота в случае, к примеру, бага.\n/stats — различная статистика бота.\n/logout — выход из аккаунта Bilimland, и дальнейшее удаление сохранённых ботом данных о данном пользователе.\n\n🐛🔫 В данный момент, у бота существуют некоторые проблемы, из которых:\n<b>1</b>. Невозможность получать список расписания в 23:00 - 00:00.\nВсе эти проблемы будут исправлены в скором времени.\n\n<span class=\"tg-spoiler\">🚧 Функция, в которой <b>бот, сам, в автоматическом режиме</b>, будет расставлять правильные ответы уже почти готова!</span>"
	)

@dp.message_handler(commands=["stats", "stat", "статы", "statistics", "статистика"])
async def stats(msg: types.Message):
	bot_data = load_data("Bot.json")

	startDate = datetime.datetime.strptime(bot_data['StartTimestamp'], '%d.%m.%Y %H:%M:%S')

	await msg.answer(
		f"За <b>{(datetime.datetime.now() - startDate).days}</b> дней своей работы, <i>(период с <b>{startDate}</b> по сегодняшний день)</i> бот сумел проанализировать <b>{bot_data['WeeksAnalyzed']}</b> учебных недель, с общим количеством анализированных уроков — <b>{bot_data['LessonsAnalyzed']}</b>. Активных <s>списывающих</s> проверяющих себя пользователей у бота — <b>{bot_data['UniqueUsers']}</b>, сессий восстановлено <i>(токенов перевыпущено)</i>: <b>{bot_data['TokensGotRefreshed']}</b>. Uptime бота: <b>{seconds_to_userfriendly_string(unix_time() - UPTIME, weeks=True, months=True)}</b>. Бот запущен {'на хостинге' if PROD else '<b><u>локально</u></b>'}."
	)

@dp.message_handler(commands = ["login", "логин"])
async def login_handler(msg: types.Message):
	arguments = msg.get_args().split(" ") # pyright: reportOptionalMemberAccess=false

	if len(arguments) != 2:
		await msg.answer("Для входа нужен логин <b>и</b> пароль.\n\nПример использования команды: <code>/login alexey_victor 123456</code>")
		return

	# Удаляем сообщение юзера с логином и паролем безопасности данных ради.
	await msg.delete()

	await msg.answer("Отлично! Я получил твой логин и пароль, прямо сейчас я попробую войти на сайт, пожалуйста, ожидай. 🙃👍\n\n<i>(предыдущее сообщение с логином и паролем было удалено для сохранения конфиденциальности твоих данных.)</i> 👀")
	greet_sticker = await msg.answer_sticker("CAACAgEAAxkBAAEDEzlhZ-J2G8SuIVt0ahDnsHMAAbt-jfwAAudrAAKvGWIHhIr-D4PhzQQhBA")

	# Пытаемся авторизоваться.
	login_result = await _BL.login(arguments[0], arguments[1], msg.from_user.id, True)

	# В случае ошибки, login_result будет содержать сообщение об ошибке, которое находится в атрибуте "message".
	if "message" in login_result:
		# Удаляем радостный стикер.
		await greet_sticker.delete()

		await msg.answer_sticker("CAACAgEAAxkBAAEDEzthZ-PBNrIKxd1YItQmcTItwNi1VwACcIMAAq8ZYgfAbLJhK3qxuiEE")

		if login_result["message"] == "Неправильный логин или пароль":
			await msg.answer("Упс, что-то пошло не так: <b>Пароль и/ли логин не верны</b>. Попробуй снова!") 
		else:
			await msg.answer(f"Упс, что-то пошло не так, я не готов к такой ошибке: <code>{login_result['message']}</code>.") 

		return

	await msg.answer(f"Прекрасно, пароль и логин верны, и у меня получилось подключиться к твоему аккаунту, <b><i>{login_result['FirstName']}!</i></b> 👍\n\nТеперь ты можешь получить доступ к расписанию: /schedule")

@dp.message_handler(commands = ["logout", "logoff", "leave", "stop", "quit", "выход"])
async def logout_handler(msg: types.Message):
	# Получим пол человека, и далее удалим данные.
	user_data = load_data(f"User-{msg.from_user.id}.json")
	male = user_data.get("Male")

	if male is None:
		# Юзер вообще не находится в системе.
		await msg.answer("Похоже, что ты уже вышел<i>(-шла)</i> из своего аккаунта Bilimland.\n\nИспользуй команду <code>/login логин пароль</code>, что бы войти в свой аккаунт снова.")
		return 

	os.remove(f"Data/User-{msg.from_user.id}.json")

	await msg.answer_sticker("CAACAgEAAxkBAAEDueFh6rb-9Kfrru1hc5Xe9WeysajuugACpYMAAq8ZYgfsx0PGPxH8hCME")
	await msg.answer(f"Ты успешно {'вышел' if male else 'вышла'} из своего аккаунта Bilimland, твои данные были удалены. Мне очень сильно жаль, что так вышло. 😞👋\n\nЕсли это произошло по-ошибке, то, пожалуйста, воспользуйся командой <code>/login логин пароль</code>, что бы вернуть всё назад!")

@dp.message_handler(commands = ["sched", "schedule", "расписание", "задания", "список", "уроки"])
async def schedule_handler(msg: types.Message):
	user_data = load_data(f"User-{msg.from_user.id}.json")

	schedule_date = today_date()
	arguments = msg.get_args().split(" ")
	dateWasGiven = False
	if len(arguments) == 1 and arguments[0] != "":
		try:
			schedule_date = convert_datetime_to_string(parse_date_as_string(arguments[0]))
			dateWasGiven = True
		except ValueError:
			await msg.answer(f"<i>Упс</i>, ты {'использовал' if user_data['Male'] else 'использовала'} неверный формат даты. 👀\n\nℹ️ Правильный формат даты: <code>дд.мм.гг</code>.\nПример сегодняшней даты: <code>{today_date_small_year()}</code>.")
			
			return

	try:
		full_schedule = await _BL.get_schedule(
			user_data, user_data["Token"], schedule_date)
	except:
		await msg.answer_sticker("CAACAgEAAxkBAAEDEzthZ-PBNrIKxd1YItQmcTItwNi1VwACcIMAAq8ZYgfAbLJhK3qxuiEE")

		await msg.answer("<i>Упс</i>, что-то пошло не так, и система авторизации сломалась 😨\n\nПопробуй авторизоваться снова, ведь я специально де-авторизовал тебя из системы. Это можно сделать, введя команду <code>/login логин пароль</code>.\nЕсли проблема продолжается, то сообщи об этом создателю бота, прописав команду /feedback.")
		del user_data["Token"]
		save_data(user_data, f"User-{msg.from_user.id}.json")

		return

	# Проверяем, есть ли указанная дата в расписании.
	if schedule_date not in full_schedule["days"]:
		await msg.answer(f"<i>Упс!</i> {'Похоже, что я' if dateWasGiven else 'Я'} столкнулся с внутренней ошибкой, связанной с расписанием. {'Вероятнее всего, это произошло из за даты, которую ты ввёл<i>(-а)</i>, либо же это произошло из-за бага, что' if dateWasGiven else 'Этот баг'} мне известен, он будет исправлен позже. А сейчас, ты можешь лишь подождать <code>00:00</code>, а ещё будет лучше попробовать снова завтра днём!")

		return

	# Проверяем, есть ли у нас уроки в указанный день.
	if len(full_schedule["days"][schedule_date]["schedule"]) == 0:
		await msg.answer_video("BAACAgIAAxkBAAIIPmHrijfK_J-iksoe4ebNUkPl1jzzAALIEgACeJ5ZS9mS95ZUO8wAASME") 
		# ;)

		return

	# Проверка, выключен ли урок?
	if full_schedule["days"][schedule_date]["isDisabledWeek"]:
		await msg.answer(f"😔 Увы, но дата <code>{schedule_date}</code> временно недоступна в самом Bilimland, попробуй позже!")

		return

	day_schedule 				= full_schedule["days"][schedule_date]
	sched_str, sched_keyboard 	= await generate_schedule_string(msg, full_schedule, schedule_date, dateWasGiven, user_data["Token"], True)

	await msg.answer(
		f"📆 Расписание на {'указанную тобой дату' if dateWasGiven else 'сегодня'}, <code>{schedule_date}</code>. {'В эту дату указывается' if dateWasGiven else 'У тебя сегодня'} {int_to_emojis(len(day_schedule['schedule']))} уроков, из которых:\n{sched_str}\n<code>{'ㅤ' * 30}</code>\nКликни на кнопку ниже для открытия сайта с дешифрованным уроком! 😜\nНажав на название урока выше, ты можешь перейти открыть Bilimland с этим уроком. Вау, технологии<a href=\"https://www.youtube.com/watch?v=Fqyes1_IJ1c\">! 😱</a>\nТак же, ты можешь воспользоваться командой <code>/schedule дд.мм.гг</code>, для получения расписания за другую дату. 👀",
		reply_markup=sched_keyboard,
		disable_web_page_preview=True
	)

@dp.message_handler(commands = ["debug", "test"])
async def debug_handler(msg: types.Message):
	# await msg.answer_photo("AgACAgIAAxkDAAOFYff7xTXsYpkIW3qrHvfa5cjlS5wAAiO4MRsGeMFLvs0GzDt8jJcBAAMCAANzAAMjBA")
	pass

@dp.message_handler(commands = ["screenshots", "screenshot", "ss", "скриншоты", "скриншот"])
async def screenshots_handler(msg: types.Message):
	user_data = load_data(f"User-{msg.from_user.id}.json")
	male = user_data["Male"]

	schedule_date = today_date()
	arguments = msg.get_args().split(" ")
	dateWasGiven = False
	if len(arguments) == 1 and arguments[0] != "":
		try:
			schedule_date = convert_datetime_to_string(parse_date_as_string(arguments[0]))
			dateWasGiven = True
		except ValueError:
			await msg.answer(f"<i>Упс</i>, ты {'использовал' if user_data['Male'] else 'использовала'} неверный формат даты. 👀\n\nℹ️ Правильный формат даты: <code>дд.мм.гг</code>.\nПример сегодняшней даты: <code>{today_date_small_year()}</code>.")
			
			return

	try:
		full_schedule = await _BL.get_schedule(
			user_data, user_data["Token"], schedule_date)
	except:
		await msg.answer_sticker("CAACAgEAAxkBAAEDEzthZ-PBNrIKxd1YItQmcTItwNi1VwACcIMAAq8ZYgfAbLJhK3qxuiEE")

		await msg.answer("<i>Упс</i>, что-то пошло не так, и система авторизации сломалась 😨\n\nПопробуй авторизоваться снова, ведь я специально де-авторизовал тебя из системы. Это можно сделать, введя команду <code>/login логин пароль</code>.\nЕсли проблема продолжается, то сообщи об этом создателю бота, прописав команду /feedback.")
		del user_data["Token"]
		save_data(user_data, f"User-{msg.from_user.id}.json")

		return

	# Проверяем, есть ли указанная дата в расписании.
	if schedule_date not in full_schedule["days"]:
		await msg.answer(f"<i>Упс!</i> {'Похоже, что я' if dateWasGiven else 'Я'} столкнулся с внутренней ошибкой, связанной с расписанием. {'Вероятнее всего, это произошло из за даты, которую ты ввёл<i>(-а)</i>, либо же это произошло из-за бага, что' if dateWasGiven else 'Этот баг'} мне известен, он будет исправлен позже. А сейчас, ты можешь лишь подождать <code>00:00</code>, а ещё будет лучше попробовать снова завтра днём!")

		return

	# Проверяем, есть ли у нас уроки в указанный день.
	if len(full_schedule["days"][schedule_date]["schedule"]) == 0:
		await msg.answer_video("BAACAgIAAxkBAAIIPmHrijfK_J-iksoe4ebNUkPl1jzzAALIEgACeJ5ZS9mS95ZUO8wAASME") 
		# ;)

		return

	# Проверка, выключен ли урок?
	if full_schedule["days"][schedule_date]["isDisabledWeek"]:
		await msg.answer(f"😔 Увы, но дата <code>{schedule_date}</code> временно недоступна в самом Bilimland, попробуй позже!")

		return

	day_schedule = full_schedule["days"][schedule_date]
	completed_lessons = [i for i in day_schedule["schedule"] if i["lesson"]["score"] is not None]

	# Проверяем, есть ли хотя бы один завершённый урок.
	if len(completed_lessons) == 0:
		await msg.answer(f"<i>Ой!</i> Похоже, что ты ещё не выполнил{'' if male else 'а'} ни один урок на сегодня. 👀\nВыполни уроки, и пропиши эту команду снова что бы я сумел сделать красивые скриншоты!\n\n🤔 Если ты на самом деле выполнил{'' if male else 'а'} работу, но я дальше буду упрямиться и отказываться работать, то подожди 5-10 минут перед повторным использованием этой команды: Увы, у Bilimland'а есть баг, из-за которого он не сразу обновляет оценки за уроки :(")

		return

	inform_message = await msg.answer(f"Отлично, я увидел в твоём расписании {int_to_emojis(len(completed_lessons))} выполненных уроков! 😌\n\nА теперь, пожалуйста, подожди перед тем, как я отправлю тебе скриншоты.\nК сожалению, этот процесс и вправду долгий, и <b>он может занять от 40 секунд до 2 минут! Это время полностью зависит от количества скриншотов, которое бот должен будет сделать.</b> 😕")

	# Устанавливаем браузер.
	driver = None
	lessons_count = {}

	try:
		TEMP_BROWSER_DIRECTORY = os.path.join(os.getcwd(), "temp-browser")
		driver = Screenshoter.setup_firefox_browser(user_data["Token"], user_data["Refresh-Token"], temp_dir=TEMP_BROWSER_DIRECTORY, headless=PROD)
		
		# Браузер установлен, проходим по всем урокам.
		for lesson in completed_lessons:
			bot_data = load_data("Bot.json")

			# Для начала проверяем, существует ли скриншот этого урока в кэше:
			if lesson["scheduleId"] in bot_data.get("LessonScreenshots", {}):
				# Такой урок есть. Так что мы просто берём, и выходим из цикла.
				lesson.update({
					"screenshotPhotoIDs": bot_data["LessonScreenshots"][lesson["scheduleId"]]
				})

				continue

			LESSON_DIR = os.path.join(TEMP_BROWSER_DIRECTORY, "lesson-screenshots", lesson['scheduleId'])
			lesson_url = f"https://onlinemektep.net/schedule/{schedule_date}/lesson/{lesson['scheduleId']}"

			count = lessons_count.get(lesson["subject"]["subjectId"], 0) + 1
			lessons_count.update({
				lesson["subject"]["subjectId"]: count
			})
			lesson.update({
				"count": count
			})

			if os.path.exists(LESSON_DIR):
				# Скриншоты урока уже были созданы, поэтому выходим
				lesson.update({
					"screenshots": [os.path.join(LESSON_DIR, i) for i in os.listdir(LESSON_DIR) if not "Main.png" in i and os.path.isfile(os.path.join(LESSON_DIR, i))]
				})

				continue

			os.makedirs(LESSON_DIR, exist_ok=True)

			lessonScreenshots = Screenshoter.get_lesson_screenshots(driver, lesson_url, LESSON_DIR)

			lesson.update({
				"screenshots": lessonScreenshots
			})

		# Скриншоты готовы, теперь их стоит отправить.
		for lesson in completed_lessons:
			media = MediaGroup()
			numOfScreenshots = len(lesson.get("screenshots", []))
			are_photo_cached = False
			lesson_url = f"https://onlinemektep.net/schedule/{schedule_date}/lesson/{lesson['scheduleId']}"
			# // TODO: Добавить стату.

			# Если у нас есть "screenshotPhotoIDs" в lesson, то мы должны использовать их:
			if "screenshotPhotoIDs" in lesson:
				are_photo_cached = True
				numOfScreenshots = len(lesson.get("screenshotPhotoIDs", []))

				for index, screenshotID in enumerate(lesson["screenshotPhotoIDs"]):
					media.attach_photo(
						screenshotID,
						
						f"Задание №<code>{index+1}</code> из <code>{numOfScreenshots}</code>, взятое с урока <b><i>«{lesson['subject']['label']}»</i></b>, на дату <code>{schedule_date}</code>.\n<i>кэшированное</i>"
					)
			else:
				for index, screenshotPath in enumerate(lesson["screenshots"]):
					media.attach_photo(
						InputFile(
							screenshotPath
						),

						f"Задание №<code>{index+1}</code> из <code>{numOfScreenshots}</code>, взятое с урока <b><i>«{lesson['subject']['label']}»</i></b>, на дату <code>{schedule_date}</code>."
					)

			await msg.answer(f"#бл <a href=\"{lesson_url}\"><b><u>{lesson['subject']['label'][0]}</u>{lesson['subject']['label'][1:]}</b></a>{(' <b>(' + str(lesson['count']) + '/' + str(lessons_count[lesson['subject']['subjectId']]) + ')</b>') if lessons_count.get(lesson['subject']['subjectId'], 0) > 1 else ''}, <b>{today_date()}</b>: <i>«{lesson['theme']['label']}»</i>.")
			res_messages_list = await bot.send_media_group(msg.chat.id, media, disable_notification=True)

			if not are_photo_cached:
				# Сохраняем ID фото для последующего использования.
				bot_data = load_data("Bot.json")
				saved_lesson_screenshots_photo_ids = bot_data.get("LessonScreenshots", {})
				if not lesson["scheduleId"] in saved_lesson_screenshots_photo_ids:
					saved_lesson_screenshots_photo_ids.update({
						lesson["scheduleId"]: []
					})

				for message_sent in res_messages_list:
					photo = message_sent["photo"][-1]

					if not photo["file_id"] in saved_lesson_screenshots_photo_ids[lesson["scheduleId"]]:
						saved_lesson_screenshots_photo_ids[lesson["scheduleId"]].append(photo["file_id"])

				bot_data.update({"LessonScreenshots": saved_lesson_screenshots_photo_ids})
				save_data(bot_data, "Bot.json")
				await asyncio.sleep(2 if are_photo_cached else 5)

		await inform_message.delete()
		
	finally:
		driver.close()

async def generate_schedule_string(msg: types.Message, full_schedule: dict, schedule_date: str, date_was_chosen_by_user: bool = False, user_access_token: None | str = None, smaller_version: bool = True) -> Tuple[str, types.InlineKeyboardMarkup]:
	keys = []
	todays_schedule = full_schedule["days"][schedule_date]
	lessons_list = ""
	keyboard = InlineKeyboardMarkup(row_width = 4)
	user_data = load_data(f"User-{msg.from_user.id}.json")
	bot_data = load_data(f"Bot.json")
	notification_msg = None

	# Проверяем, есть ли нескачанный урок:
	non_downloaded_lessons = [i for i in todays_schedule["schedule"] if i["scheduleId"] not in bot_data["DecodedLessonURLs"]]
	if non_downloaded_lessons:
		bot_data["WeeksAnalyzed"] += 1

		notification_msg = await msg.answer(f"<i>Прямо сейчас я загружаю все <b>{len(non_downloaded_lessons)}</b> уроков в {'расписании на тот день, что был указан мне' if date_was_chosen_by_user else 'твоём сегодняшнем расписании'}, а так же занимаюсь процессом их дешифрования, пожалуйста, подожди, это может занять 5-20 секунд...</i>")

	for index, lesson in enumerate(todays_schedule["schedule"]):
		if index > 0:
			lessons_list += ";\n"

		score = lesson['lesson']['score'] or 0
		score = round((score / 10) * 100)

		lesson_name = smaller_lesson_names.get(
			lesson['subject']['label'], lesson['subject']['label'])
		lesson_name_full = lesson['subject']['label']

		# Проверяем, есть ли URL к скачанному уроку. В unique_lesson_id мы создаём строку с уникальным идентификатором урока, который будет использоваться для поиска его в базе данных.
		unique_lesson_id = f"{lesson['scheduleId']}_{msg.from_user.id}"

		if unique_lesson_id not in bot_data["DecodedLessonURLs"]:
			# URL к текущему уроку нету, закачиваем.

			# Получаем LessonID
			lesson_info = await BL.get_lesson_info(user_data, user_data["Token"], unique_lesson_id)

			# Получаем index.json
			index_json_url: Any = await BL.get_lesson_answers_link(
				lesson_info["data"]["lessonId"]
			)

			lesson_downloaded: str = ""
			access = await BL.get_lesson_access(user_data, user_data["Token"], lesson_info["data"]["lessonId"])
			lesson_downloaded = await BL.get_lesson_answers_file(index_json_url, access["data"]["jwt"])

			retries = 3
			lesson_decoded_url = None
			while retries > 0:
				try:
					# Декодируем URL
					lesson_decoded_url = await _BL.decode_url(lesson_downloaded, unique_lesson_id)

					# Проверяем, нету ли ошибки:
					if "Something went wrong :-(" in lesson_decoded_url:
						raise Exception("Ошибка при получении урока, вероятнее всего, сервер дешифровки ответов упал.")
					
					break

				except:
					if retries <= 0:
						break

					await msg.answer(f"<i>Что-то пошло не так, и я не сумел связаться с сервером дешифровки ответов. Я попробую ещё {retries} раз, но с большей задержкой. Если у меня не получится, то я пропущу урок, из-за которого возникает ошибка.</i>")
					await asyncio.sleep(5)
				finally:
					retries -= 1

			if lesson_decoded_url is None:
				await msg.answer("Сайт с ответами упал. Попробуй получить расписание позже.")
				raise Exception("Сайт с ответами упал.")

					

			# Сохраняем URL
			bot_data["DecodedLessonURLs"][unique_lesson_id] = lesson_decoded_url

			# Статистика:
			bot_data["LessonsAnalyzed"] += 1

		decoded_url = bot_data["DecodedLessonURLs"][unique_lesson_id]
		broken_url = "Something went wrong :-(" in decoded_url

		if broken_url:
			# На всякий.
			decoded_url = "www.error.com"

		if smaller_version:
			# Мобильная версия
			lessons_list += f" • {'✅' if score else ' ' * 6} <b>[{index + 1}]</b> <a href=\"https://onlinemektep.net/schedule/{schedule_date}/lesson/{lesson['scheduleId']}\">{lesson_name_full}</a>: {score}%"

			if not broken_url:
				keys.append(InlineKeyboardButton(
					f"[{index + 1}] {lesson_name}", url=decoded_url))
		else:
			# PC-Версия
			lessons_list += f" • {'✅' if score else ' ' * 6} <b>[{index + 1}]</b>: {lesson['subject']['label']}, <i>«{shorten(lesson['theme']['label'], 40, placeholder = '...')}»</i>: {score}%"
			
			if not broken_url:
				keys.append(InlineKeyboardButton(
					f"{lesson['subject']['label']}, «{lesson['theme']['label']}»", url=decoded_url))

		if broken_url:
			keys.append(InlineKeyboardButton(
				f"[{index + 1}] ОШИБКА", callback_data="error-button"))

			# Удаляем сломанный URL:
			del bot_data["DecodedLessonURLs"][unique_lesson_id]

			

		

	lessons_list += "."

	keyboard.add(*keys)
	# keyboard.add(InlineKeyboardButton("Выбрать другой день этой недели", callback_data = "a"))
	save_data(user_data, f"User-{msg.from_user.id}.json")
	save_data(bot_data, "Bot.json")
	if notification_msg is not None:
		await notification_msg.delete()

	return lessons_list, keyboard

@dp.message_handler(commands=["contact", "feedback", "фидбэк", "фидбек", "отзыв"])
async def feedback(msg: types.Message):
	user_data = load_data(f"User-{msg.from_user.id}.json")
	male = user_data.get("Male", True)

	await msg.answer(f"Обратиться к администратору можно, если написать ему напрямую: @Zensonaton.\n\nЕсли ты столкнул{'ся' if male else 'ась'} с проблемой, то перешли это сообщение, так как администратор сможет быстрее разобраться в чём проблема благодаря следующему ID: <span class=\"tg-spoiler\">{msg.from_user.id}</span>")

@dp.errors_handler()
async def global_error_handler(update: Update, error: Exception):

	if isinstance(error, FileNotFoundError):
		await update.message.answer("Данная команда доступна только после входа в бота, используя логин и пароль от Bilimland:\n\n<code>/login логин пароль</code>")
		return True

	logger.exception(error)

	await update.message.answer(f"Упс, у бота произошла ошибка. Текст ошибки:\n\n<code>{traceback.format_exc()}</code>")
	return True

@dp.callback_query_handler(lambda call: call.data == "error-button")
async def callback_schedule_error_button(query: types.CallbackQuery):
	await bot.answer_callback_query(query.id, text="⚠️ Что-то пошло не так, и этот урок сломался.\n\nℹ️ Пропиши команду /schedule снова, что бы попытаться исправить эту ошибку.", show_alert=True)

# Запускаем бота.
if __name__ == "__main__":
	logger.info("Пытаемся запустить бота...")

	if not os.path.exists("Data/Bot.json"):
		save_data({
			"DecodedLessonURLs": {},
			"StartTimestamp": datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
			"WeeksAnalyzed": 0,
			"LessonsAnalyzed": 0,
			"UniqueUsers": 0,
			"TokensGotRefreshed": 0
		}, "Bot.json")

	executor.start_polling(dp, on_startup=logger.info("Бот запущен!"))
