# coding: utf-8

import asyncio
import datetime
import sys
from    aiogram             import 	Bot, types, md
from    aiogram.dispatcher  import 	Dispatcher
from    aiogram.utils       import 	executor, markdown
from 	aiogram.types 		import 	ReplyKeyboardRemove, \
									ReplyKeyboardMarkup, KeyboardButton, \
									InlineKeyboardMarkup, InlineKeyboardButton, Update
from    dotenv              import 	load_dotenv
import 	BL_Utils			as BL
from 	Utils 				import 	int_to_emojis, load_data, random_uuid, save_data, seconds_to_userfriendly_string, today_date, unix_time
from 	textwrap 			import 	shorten
import 	traceback
import 	logging
import 	os

# Загружаем .env файл.
load_dotenv()

# Инициализируем Телеграм-бота.
bot = Bot(
	token       = os.environ["TG_TOKEN"],
	parse_mode  = types.ParseMode.HTML
)

# Обработчик команд.
dp  = Dispatcher(bot)

if not os.path.exists("./Logs/"):
	os.mkdir("./Logs/")

# Логирование.
logging.basicConfig(
	filename="Logs/TGBot.log",
)
logger = logging.getLogger(__name__)
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(logging.Formatter("[%(levelname)-8s %(asctime)s at %(name)s.%(funcName)s]: %(message)s", "%d.%d.%Y %H:%M:%S"))
streamHandler.setLevel(logging.INFO)
logger.addHandler(streamHandler)

UPTIME = unix_time()

@dp.message_handler(commands = ["start", "start", "старт",])
async def message_handler(msg: types.Message):
	#У бота есть <a href='https://github.com/Zensonaton/ZensonatonTools_TGBot'>открытый исходный код</a>, поэтому ты можешь проверить что он делает 'за кулисами'.
	await msg.answer(
		"<b>Привет!</b> 👋\nДанный бот может отправлять дешифрованные ответы на задания от Bilimland после отправки логина + пароля. <i>(однако бот не может работать с СОРами или СОЧами.)</i>\n\nДля ознакомления я советую использовать команду <code>/help</code>, однако ты можешь сразу попробовать команду <code>/login логин пароль</code> в действии."
	)

@dp.message_handler(commands=["help", "команды", "помощь", "info", "инфо"])
async def help(msg: types.Message):
	await msg.answer(
		f"ℹ️ <b>Список команд у данного бота</b>:\n\n/login логин пароль — вход в аккаунт Bilimland.\n/schedule — получить список расписания уроков в Bilimland, а так же ссылки на ответы. <i>Работает только после авторизации.</i>\n/feedback — возможность написать автору бота в случае, к примеру, бага.\n\n🐛🔫 В данный момент, у бота существуют некоторые проблемы, из которых:\n<b>1</b>. Невозможность получать список расписания в 23:00 - 00:00.\nВсе эти проблемы будут исправлены в скором времени.\n\n<span class=\"tg-spoiler\">🚧 В будущем планируется добавление функции, при которой <b>бот, сам, в автоматическом режиме</b>, будет расставлять правильные ответы, однако шанс разработки таковой функции достаточно мал ввиду технических ограничений.</span>"
	)

@dp.message_handler(commands=["stats", "stat", "статы", "statistics", "статистика"])
async def stats(msg: types.Message):
	bot_data = load_data("Bot.json")

	startDate = datetime.datetime.strptime(bot_data['StartTimestamp'], '%d.%m.%Y %H:%M:%S')

	await msg.answer(
		f"За <b>{(datetime.datetime.now() - startDate).days}</b> дней своей работы, <i>(период с <b>{startDate}</b> по сегодняшний день)</i> бот сумел проанализировать <b>{bot_data['WeeksAnalyzed']}</b> учебных недель, с общим количеством анализированных уроков — <b>{bot_data['LessonsAnalyzed']}</b>. Активных <s>списывающих</s> проверяющих себя пользователей у бота — <b>{bot_data['UniqueUsers']}</b>, сессий восстановлено <i>(токенов перевыпущено)</i>: <b>{bot_data['TokensGotRefreshed']}</b>. Uptime бота: <b>{seconds_to_userfriendly_string(unix_time() - UPTIME, weeks=True, months=True)}</b>."
	)

@dp.message_handler(commands = ["login", "логин"])
async def login_handler(msg: types.Message):
	arguments = msg.get_args().split(" ")

	if len(arguments) != 2:
		await msg.answer("Для входа нужен логин <b>и</b> пароль.\n\nПример использования команды: <code>/login alexey_victor 123456</code>")
		return

	# Удаляем сообщение юзера с логином и паролем безопасности данных ради.
	await msg.delete()

	await msg.answer("Отлично! Я получил твой логин и пароль, прямо сейчас я попробую войти на сайт, пожалуйста, ожидай. 🙃👍\n\n<i>(предыдущее сообщение с логином и паролем было удалено для сохранения конфиденциальности твоих данных.)</i> 👀")
	greet_sticker = await msg.answer_sticker("CAACAgEAAxkBAAEDEzlhZ-J2G8SuIVt0ahDnsHMAAbt-jfwAAudrAAKvGWIHhIr-D4PhzQQhBA")

	# Пытаемся авторизоваться.
	login_result = await BL.login(arguments[0], arguments[1], msg.from_user.id)

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

@dp.message_handler(commands = ["sched", "schedule", "расписание", "задания", "список", "уроки"])
async def sched_handler(msg: types.Message):
	user_data 					= load_data(f"User-{msg.from_user.id}.json")

	if not "Token" in user_data:
		await msg.answer("Данная команда доступна только после входа в бота, используя логин и пароль от Bilimland:\n\n<code>/login логин пароль</code>")

		return

	today = today_date()
	try:
		full_schedule = await BL.get_schedule(
			user_data, user_data["Token"])
	except:
		await msg.answer_sticker("CAACAgEAAxkBAAEDEzthZ-PBNrIKxd1YItQmcTItwNi1VwACcIMAAq8ZYgfAbLJhK3qxuiEE")

		await msg.answer("<i>Упс</i>, что-то пошло не так, и система авторизации сломалась 😨\n\nПопробуй авторизоваться снова, ведь я специально де-авторизовал тебя из системы. Это можно сделать, введя команду <code>/login логин пароль</code>.\nЕсли проблема продолжается, то сообщи об этом создателю бота, прописав команду /feedback.")
		del user_data["Token"]
		save_data(user_data, f"User-{msg.from_user.id}.json")

		return

	# Проверяем, есть ли сегодняшняя дата в расписании.
	if today not in full_schedule["days"]:
		await msg.answer("У-упс! Я столкнулся с внутренней ошибкой, связанной с расписанием. Этот баг мне известен, он будет исправлен позже. А сейчас, ты можешь лишь подождать <code>00:00</code>, а ещё будет лучше попробовать снова завтра днём!")

		return

	todays_schedule 			= full_schedule["days"][today]
	sched_str, sched_keyboard 	= await generate_schedule_string(msg, full_schedule, True)

	await msg.answer(
		# f"Расписание на сегодня, <code>{today}</code>. У тебя сегодня {int_to_emojis(len(todays_schedule['schedule']))} уроков, из которых:\n{sched_str}\n<code>{'ㅤ' * 30}</code>\nКакой из данных предметов ты хочешь автоматически выполнить? 🤔\n<i>(заметка: балл, который ты хочешь получить можно будет указать после выбора предмета.)</i>",
		f"📆 Расписание на сегодня, <code>{today}</code>. У тебя сегодня {int_to_emojis(len(todays_schedule['schedule']))} уроков, из которых:\n{sched_str}\n<code>{'ㅤ' * 30}</code>\nКликни на кнопку ниже для открытия сайта с дешифрованным уроком! 😜",
		reply_markup=sched_keyboard
	)
	
# @dp.message_handler(content_types = types.ContentType.DOCUMENT)
# async def process_document(msg: types.Message):
# 	if msg.document.mime_type == "application/json":
# 		await msg.reply("JSON")
# 		return
# 	elif msg.document.mime_type == "text/plain":
# 		await msg.reply("PLAIN")
# 		return
		
# 	await msg.reply("⚠ Отправленный тобою файл не является `\.JSON`\-файлом\. Вероятнее всего, ты отправил не тот файл\.")

async def generate_schedule_string(msg: types.Message, full_schedule: dict, smaller_version: bool) -> str:
	keys = []
	today = today_date()
	todays_schedule = full_schedule["days"][today]
	lessons_list = ""
	keyboard = InlineKeyboardMarkup(row_width = 4)
	user_data = load_data(f"User-{msg.from_user.id}.json")
	bot_data = load_data(f"Bot.json")
	notification_msg = None

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

	# Проверяем, есть ли нескачанный урок:
	non_downloaded_lessons = [i for i in todays_schedule["schedule"] if i["scheduleId"] not in bot_data["DecodedLessonURLs"]]
	if non_downloaded_lessons:
		bot_data["WeeksAnalyzed"] += 1

		notification_msg = await msg.answer(f"<i>Прямо сейчас я загружаю все <b>{len(non_downloaded_lessons)}</b> уроков в твоём сегодняшнем расписании, а так же занимаюсь процессом их дешифрования, пожалуйста, подожди, это может занять 5-20 секунд...</i>")

	for index, lesson in enumerate(todays_schedule["schedule"]):
		if index > 0:
			lessons_list += ";\n"

		score = lesson['lesson']['score'] or 0
		score = round((score / 10) * 100)

		lesson_name = smaller_lesson_names.get(
			lesson['subject']['label'], lesson['subject']['label'])
		lesson_name_full = lesson['subject']['label']

		# Проверяем, есть ли URL к скачанному уроку.
		if lesson["scheduleId"] not in bot_data["DecodedLessonURLs"]:
			# URL к текущему уроку нету, закачиваем.

			# Получаем LessonID
			lesson_info = await BL.get_lesson_info(lesson["scheduleId"], user_data["Token"])
			# Получаем index.json
			lesson_downloaded = await BL.get_index_json(lesson_info["data"]["lessonId"])
			retries = 3
			lesson_decoded_url = None
			while retries > 0:
				try:
					# Декодируем URL
					lesson_decoded_url = await BL.decode_url(lesson_downloaded, lesson["scheduleId"])

					# Чекаем, нету ли ошибки:
					if "Something went wrong :-(" in lesson_decoded_url:
						raise Exception("Ошибка при получении урока, вероятнее всего сервер дешифровки ответов упал.")
					
					break

				except:
					await msg.answer(f"<i>Что-то пошло не так, и я не сумел связаться с сервером дешифровки ответов. Я попробую ещё {retries} раз, но с большей задержкой.</i>")
					await asyncio.sleep(5)
				finally:
					retries -= 1

			if lesson_decoded_url is None:
				await msg.answer("Сайт с ответами упал. Попробуй получить расписание позже.")

				return

					

			# Сохраняем URL
			bot_data["DecodedLessonURLs"][lesson["scheduleId"]] = lesson_decoded_url

			# Статистика:
			bot_data["LessonsAnalyzed"] += 1

		decoded_url = bot_data["DecodedLessonURLs"][lesson["scheduleId"]]
		broken_url = "Something went wrong :-(" in decoded_url

		if broken_url:
			# На всякий.
			decoded_url = "www.error.com"

		if smaller_version:
			# Мобильная версия
			lessons_list += f" • {'✅' if score else ' ' * 6} <b>[{index + 1}]</b> {lesson_name_full}: {score}%"

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
			del bot_data["DecodedLessonURLs"][lesson["scheduleId"]]

			

		

	lessons_list += "."

	keyboard.add(*keys)
	# keyboard.add(InlineKeyboardButton("Выбрать другой день этой недели", callback_data = "a"))
	save_data(user_data, f"User-{msg.from_user.id}.json")
	save_data(bot_data, "Bot.json")
	if notification_msg is not None:
		await notification_msg.delete()

	return lessons_list, keyboard


@dp.message_handler(commands=["contact", "feedback", "фидбэк", "фидбек", "отзывы"])
async def feedback(msg: types.Message):
	user_data = load_data(f"User-{msg.from_user.id}.json")
	male = user_data.get("Male", True)

	await msg.answer(f"Обратиться к администратору можно, если написать ему напрямую: @Zensonaton.\n\nЕсли ты столкнул{'ся' if male else 'ась'} с проблемой, то перешли это сообщение, так как администратор сможет быстрее разобраться в чём проблема благодаря следующему ID: <span class=\"tg-spoiler\">{msg.from_user.id}</span>")

@dp.errors_handler()
async def global_error_handler(update: Update, error: Exception):

	logger.exception(error)

	await update.message.answer(f"Упс, у бота произошла ошибка. Текст ошибки:\n\n<code>{traceback.format_exc()}</code>")
	return True


@dp.callback_query_handler(lambda call: call.data == "error-button")
async def vote_down_cb_handler(query: types.CallbackQuery):
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
