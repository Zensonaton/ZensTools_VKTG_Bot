# coding: utf-8

import 	json
from 	typing import Any, Tuple
from    aiogram             import 	Bot, types, md
from    aiogram.dispatcher  import 	Dispatcher
from    aiogram.utils       import 	executor, markdown
from 	aiogram.types 		import 	ReplyKeyboardRemove, \
									ReplyKeyboardMarkup, KeyboardButton, \
									InlineKeyboardMarkup, InlineKeyboardButton, Update
import 	aiohttp
from    dotenv              import 	load_dotenv
import 	BL_Utils			as _BL
import 	BL_AutoParser		as BL
from 	Utils 				import 	int_to_emojis, load_data, random_uuid, save_data, seconds_to_userfriendly_string, today_date, unix_time
from 	textwrap 			import 	shorten
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

# Обработчик команд.
dp = Dispatcher(bot)

# // TODO: ссылки для быстрого перехода на урок через /[a]schedule

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

@dp.message_handler(commands = ["start", "start", "старт",])
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
		f"За <b>{(datetime.datetime.now() - startDate).days}</b> дней своей работы, <i>(период с <b>{startDate}</b> по сегодняшний день)</i> бот сумел проанализировать <b>{bot_data['WeeksAnalyzed']}</b> учебных недель, с общим количеством анализированных уроков — <b>{bot_data['LessonsAnalyzed']}</b>. Активных <s>списывающих</s> проверяющих себя пользователей у бота — <b>{bot_data['UniqueUsers']}</b>, сессий восстановлено <i>(токенов перевыпущено)</i>: <b>{bot_data['TokensGotRefreshed']}</b>. Uptime бота: <b>{seconds_to_userfriendly_string(unix_time() - UPTIME, weeks=True, months=True)}</b>."
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
	login_result = await BL.login(arguments[0], arguments[1], msg.from_user.id, True)

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

@dp.message_handler(commands = ["auto", "autoschedule", "asched", "aschedule", "autowork"])
async def aschedule_handler(msg: types.Message):
	return # Не используется.
	
	async def _downloadMoreInfo(token: str, scheduleID: str, lesson: dict):
		oldLesson = lesson.copy()

		more_lesson_data = await BL.get_lesson_info(token, scheduleID)
		BL.merge(oldLesson, more_lesson_data["data"])

		return more_lesson_data["data"]

	user_data = load_data(f"User-{msg.from_user.id}.json", required_keys=["Token"])
	bot_data = load_data("Bot.json")

	agreement = user_data.get("AutoLessonCompletionAgreement", False)
	male = user_data["Male"]

	if not agreement:
		user_data.update({"AScheduleCommandUsedTimestamp": unix_time()})

		await msg.answer(
f"""⚠️⚠️⚠️ <b>Перед тем как я позволю пользоваться тебе этой командой, тебе нужно кое что принять, и согласиться, <u>поэтому ВНИМАТЕЛЬНО ПРОЧТИ ВСЁ ЧТО НАПИСАНО НИЖЕ!</u></b> ⚠️⚠️⚠️

Данная функция находится в <b>бета-тесте</b>, и поэтому у неё есть баги, ошибки, и прочие беды. С этим, в данный момент, ничего поделать нельзя: Во время создания этой функции, у меня не было достаточного количества информации, что бы эту функцию сделать без багов.
Теперь я хочу что бы ты прочитал{'' if male else 'а'} следующие предупреждения:
<b><u>1. Данная функция иногда ломает уроки, что в них даже нельзя заходить</u></b>. Учителя могут видеть <i>(не факт?)</i>, что у урока есть выполнение и его балл, но, если они зайдут в него, то увидят ошибку (если её видишь ты, в уроках, в которой ошибки нет, всё будет хорошо и у учителя). Тут можно включить хитрость, и сказать, что <i>«У меня билимленд тоже очень странные вещи показывал!»</i>.
<b><u>2. Бот не всегда делает работу на 100% правильно</u></b>. Тут точно тоже самое, у меня, создателя, не было достаточного количества информации, но, со временем, если возможность просмотра ответов через файл index.json не уберут, то я эту функцию буду активно развивать.
<b><u>3. Эта функция и сам бот могут резко перестать работать</u></b>. Как было отмечено в пункте 2, эта функция, и сам бот полностью перестанут, если в Bilimland изменят кое-что, связанное с файлом index.json. для тех кто не читал, можно<a href="https://vk.com/zensonatontools?w=wall-199464710_40%2Fall">прочитать тут</a>.
<b><u>4. Соглашаясь, ты дашь возможность мне, создателю бота, заходить на твой аккаунт для улучшения работы этой функции, если какой-то урок не будет работать</u></b>. Это сделано для улучшения качества работы функции, всё правильно.
<b><u>5. Блокировка аккаунта</u></b>. Увы, но есть <b>очень маленький</b> шанс того, что создатели Bilimland заметят что-то странное, и заблокируют аккаунт. Если это произойдёт со мной, то я об этом обязательно предупрежу и запрещу доступ к этой функции, но если ты столкнешься с этим, то немедленно обратись ко мне: /feedback
 
После прочтения всего этого, если ты {'согласен' if male else 'согласна'}, то пропиши команду /aschedule_i_accept_the_fact_that_something_may_go_wrong. Но а если ты не {'согласен' if male else 'согласна'}, то просто <b>не</b> используй команду.""", disable_web_page_preview=True)
		save_data(user_data, f"User-{msg.from_user.id}.json")

		return

	# В данном куске кода, мы можем быть уверены, что пользователь согласен со всем выше.

	schedule_date = today_date()
	arguments = msg.get_args().split(" ")
	dateWasGiven = False
	if len(arguments) == 1 and arguments[0] != "":
		try:
			schedule_date_dt = datetime.datetime.strptime(arguments[0], "%d.%m.%y")
			schedule_date = schedule_date_dt.strftime("%d.%m.%Y") # Превращаем "1.2.33" в "1.2.3333"
			dateWasGiven = True
		except ValueError:
			await msg.answer(f"<i>Упс</i>, ты {'использовал' if user_data['Male'] else 'использовала'} неверный формат даты 👀.\n\nℹ️ Правильный формат даты: <code>дд.мм.гг</code>.\nПример сегодняшней даты: <code>{today_date()}</code>.")
			return

	try:
		full_schedule = await BL.get_schedule(
			user_data["Token"], schedule_date)
	except Exception as error:
		logger.exception(error)

		await msg.answer_sticker("CAACAgEAAxkBAAEDEzthZ-PBNrIKxd1YItQmcTItwNi1VwACcIMAAq8ZYgfAbLJhK3qxuiEE")

		await msg.answer("<i>Упс</i>, что-то пошло не так, и система авторизации сломалась 😨\n\nПопробуй авторизоваться снова, ведь я специально де-авторизовал тебя из системы. Это можно сделать, введя команду <code>/login логин пароль</code>.\nЕсли проблема продолжается, то сообщи об этом создателю бота, прописав команду /feedback.")
		# del user_data["Token"]
		save_data(user_data, f"User-{msg.from_user.id}.json")

		return

	# Проверяем, есть ли указанная дата в расписании.
	if schedule_date not in full_schedule["days"]:
		await msg.answer(f"<i>Упс!</i> {'Похоже, что я' if dateWasGiven else 'Я'} столкнулся с внутренней ошибкой, связанной с расписанием. {'Вероятнее всего, это произошло из за даты, которую ты ввёл<i>(-а)</i>, либо же это произошло из-за бага, что' if dateWasGiven else 'Этот баг'} мне известен, он будет исправлен позже. А сейчас, ты можешь лишь подождать <code>00:00</code>, а ещё будет лучше попробовать снова завтра днём!")

		return

	# Сохраним расписание.
	if not "LessonInfo" in bot_data:
		bot_data.update({
			"LessonInfo": {}
		})

	tasks = []
	for day in full_schedule["days"]:
		for lesson in full_schedule["days"][day]["schedule"]:
			if lesson["scheduleId"] not in bot_data["LessonInfo"]:
				tasks.append(asyncio.ensure_future(_downloadMoreInfo(user_data["Token"], lesson["scheduleId"], lesson)))

	if len(tasks) > 0:
		notification_msg = await msg.answer(f"<i>Прямо сейчас я загружаю все <b>{len(tasks)}</b> уроков на всю неделю, а так же занимаюсь процессом дешифровки уроков в этой неделе, пожалуйста, подожди, это может занять 10-30 секунд...</i>")

		all_lessons_downloaded = await asyncio.gather(*tasks)
		for lesson_downloaded in all_lessons_downloaded:
			bot_data["LessonInfo"].update({
				lesson_downloaded["scheduleId"]: lesson_downloaded
			})

		await notification_msg.delete()

	

	save_data(bot_data, f"Bot.json")
	day_schedule 				= full_schedule["days"][schedule_date]
	sched_str, sched_keyboard 	= await generate_autoschedule_string(msg, full_schedule, schedule_date, dateWasGiven, user_data["Token"])

	# Проверяем, есть ли у нас уроки в указанный день.
	if len(day_schedule["schedule"]) == 0:
		await msg.answer_video("BAACAgIAAxkBAAIIPmHrijfK_J-iksoe4ebNUkPl1jzzAALIEgACeJ5ZS9mS95ZUO8wAASME") # ;)
		return

	if day_schedule["isDisabledWeek"]:
		await msg.answer(f"😔 Увы, но дата <code>{schedule_date}</code> временно недоступна в самом Bilimland, попробуй позже!")
		return

	# Загрузим уроки в фоне:
	executor.asyncio.create_task(download_all_lesson_answers(day_schedule, True, user_data["Token"]))

	await msg.answer(
		f"<b><u>БЕТА ВЕРСИЯ</u></b> ⚠️ 🚧\n\n📆 Расписание на {'указанную тобой дату' if dateWasGiven else 'сегодня'}, <code>{schedule_date}</code>. {'В эту дату указывается' if dateWasGiven else 'У тебя сегодня'} {int_to_emojis(len(day_schedule['schedule']))} уроков, из которых:\n{sched_str}\n<code>{'ㅤ' * 30}</code>",
		reply_markup=sched_keyboard
	)

@dp.message_handler(commands=["aschedule_i_accept_the_fact_that_something_may_go_wrong"])
async def aschedule_accept(msg: types.Message):
	user_data = load_data(f"User-{msg.from_user.id}.json")
	male = user_data["Male"]

	timestamp: int  = user_data.get("AScheduleCommandUsedTimestamp")

	# Проверяем, сколько времени прошло.
	if (unix_time() - timestamp <= 50):
		await msg.answer(f"Больно быстро ты читаешь. А ну, беги перечитывать, администратор не будет виноват в том, что ты не прочитал{'' if male else 'а'}!")
		return


	user_data.update({"AutoLessonCompletionAgreement": True})
	save_data(user_data, f"User-{msg.from_user.id}.json")

	await msg.answer(f"Принято. Факт, что ты {'согласился' if male else 'согласилась'}, был сохранён, и теперь ты можешь пользоваться данной командой: /aschedule")

@dp.message_handler(commands = ["sched", "schedule", "расписание", "задания", "список", "уроки"])
async def schedule_handler(msg: types.Message):
	user_data = load_data(f"User-{msg.from_user.id}.json")

	schedule_date = today_date()
	arguments = msg.get_args().split(" ")
	dateWasGiven = False
	if len(arguments) == 1 and arguments[0] != "":
		try:
			schedule_date_dt = datetime.datetime.strptime(arguments[0], "%d.%m.%y")
			schedule_date = schedule_date_dt.strftime("%d.%m.%Y") # Превращаем "1.2.33" в "1.2.3333"
			dateWasGiven = True
		except ValueError:
			await msg.answer(f"<i>Упс</i>, ты {'использовал' if user_data['Male'] else 'использовала'} неверный формат даты 👀.\n\nℹ️ Правильный формат даты: <code>дд.мм.гг</code>.\nПример сегодняшней даты: <code>{today_date()}</code>.")
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
		await msg.answer_video("BAACAgIAAxkBAAIIPmHrijfK_J-iksoe4ebNUkPl1jzzAALIEgACeJ5ZS9mS95ZUO8wAASME") # ;)

		return

	# Проверка, выключен ли урок?
	if full_schedule["days"][schedule_date]["isDisabledWeek"]:
		await msg.answer(f"😔 Увы, но дата <code>{schedule_date}</code> временно недоступна в самом Bilimland, попробуй позже!")

		return

	day_schedule 				= full_schedule["days"][schedule_date]
	sched_str, sched_keyboard 	= await generate_schedule_string(msg, full_schedule, schedule_date, dateWasGiven, user_data["Token"], True)

	await msg.answer(
		f"📆 Расписание на {'указанную тобой дату' if dateWasGiven else 'сегодня'}, <code>{schedule_date}</code>. {'В эту дату указывается' if dateWasGiven else 'У тебя сегодня'} {int_to_emojis(len(day_schedule['schedule']))} уроков, из которых:\n{sched_str}\n<code>{'ㅤ' * 30}</code>\nКликни на кнопку ниже для открытия сайта с дешифрованным уроком! 😜\nНажав на название урока выше, ты можешь перейти открыть Bilimland с этим уроком. Вау, технологии<a href=\"https://www.youtube.com/watch?v=Fqyes1_IJ1c\">! 😱</a>\nТак же, ты можешь воспользоваться командой <code>/schedule дд.мм.гг</code>, для получения расписания за другую дату. 👀",
		reply_markup=sched_keyboard
	)

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

		# Проверяем, есть ли URL к скачанному уроку.
		if lesson["scheduleId"] not in bot_data["DecodedLessonURLs"]:
			# URL к текущему уроку нету, закачиваем.

			# Получаем LessonID
			lesson_info = await BL.get_lesson_info(user_data, user_data["Token"], lesson["scheduleId"])

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
					lesson_decoded_url = await _BL.decode_url(lesson_downloaded, lesson["scheduleId"])

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
			del bot_data["DecodedLessonURLs"][lesson["scheduleId"]]

			

		

	lessons_list += "."

	keyboard.add(*keys)
	# keyboard.add(InlineKeyboardButton("Выбрать другой день этой недели", callback_data = "a"))
	save_data(user_data, f"User-{msg.from_user.id}.json")
	save_data(bot_data, "Bot.json")
	if notification_msg is not None:
		await notification_msg.delete()

	return lessons_list, keyboard

async def download_all_lesson_answers(schedule: dict, use_lesson_access, token: str):
	return

	async def _download(lesson_id: int, scheduleID: str, use_lesson_access: bool):
		url = await BL.get_lesson_answers_link(lesson_id)
		indexjson_encrypted = None
		if use_lesson_access:
			access_response = await BL.get_lesson_access(token, lesson_id)
			indexjson_encrypted = await BL.get_lesson_answers_file(url, access_response["data"]["jwt"])
		else:
			indexjson_encrypted = await BL.get_lesson_answers_file(url)

		# Загрузим файл на мой сайт.
		lesson_decoded_url = await _BL.decode_url(indexjson_encrypted, lesson["scheduleId"])

		# Расшифровываем, парсим.
		decoded = await BL.decode_lesson_answers_file(indexjson_encrypted)
		parsed = await BL.parse_lesson_answers(decoded)

		return json.dumps(parsed, ensure_ascii=False, sort_keys=True, indent=4)

	tasks = []

	for lesson in schedule["schedule"]:
		tasks.append(asyncio.ensure_future(_download(lesson["calendarPlanLesson"]["entityId"], lesson["scheduleId"], use_lesson_access)))

	all_lessons_downloaded = await asyncio.gather(*tasks)

	for index, lesson in enumerate(all_lessons_downloaded):
		filepath = f"Data/Index-{schedule['schedule'][index]['scheduleId']}.jsonc"
		if not os.path.exists(filepath):
			open(filepath, "w", encoding="utf-8").write(lesson)

async def generate_autoschedule_string(msg: types.Message, full_schedule: dict, schedule_date: str, date_was_chosen_by_user: bool = False, user_access_token: str = None) -> Tuple[str, types.InlineKeyboardMarkup]:
	keys = []
	todays_schedule = full_schedule["days"][schedule_date]
	lessons_list = ""
	keyboard = InlineKeyboardMarkup(row_width = 4)
	# user_data = load_data(f"User-{msg.from_user.id}.json")
	# bot_data = load_data(f"Bot.json")
	notification_msg = None

	for index, lesson in enumerate(todays_schedule["schedule"]):
		lessonScheduleID = lesson["scheduleId"]

		if index > 0:
			lessons_list += ";\n"

		score = lesson['lesson']['score'] or 0
		score = round((score / 10) * 100)

		lesson_name = smaller_lesson_names.get(
			lesson['subject']['label'], lesson['subject']['label'])
		lesson_name_full = lesson['subject']['label']

		lessons_list += f" • {'✅' if score else ' ' * 6} <b>[{index + 1}]</b> <a href=\"https://onlinemektep.net/schedule/{schedule_date}/lesson/{lessonScheduleID}\">{lesson_name_full}</a>: {score}%"

		keys.append(InlineKeyboardButton(
			f"[{index + 1}] {lesson_name}", callback_data=f"openlesson!{lessonScheduleID}"))
		

	lessons_list += "."

	keyboard.add(*keys)
	# save_data(user_data, f"User-{msg.from_user.id}.json")
	# save_data(bot_data, "Bot.json")
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

@dp.callback_query_handler(lambda call: call.data.startswith("openlesson!"))
async def callback_asched_lesson(query: types.CallbackQuery):
	bot_data = load_data("Bot.json")
	lessonScheduleID = query.data.split("!")[1]
	lessonInfo = bot_data["LessonInfo"][lessonScheduleID]

	keyboard = InlineKeyboardMarkup(row_width = 1)
	keys = []

	keys.append(InlineKeyboardButton(
		"WIP Автоматически выполнить", callback_data=f"lessonwork!{lessonScheduleID}"))
	keys.append(InlineKeyboardButton(
		"Открыть ответы", url=f"https://bilimlandbot.eu.pythonanywhere.com/f/?f={lessonScheduleID}.html"))
	keys.append(InlineKeyboardButton(
		"Загрузить index.json", callback_data=f"indexjson!{lessonScheduleID}"))

	keyboard.add(*keys)

	await bot.send_message(query.message.chat.id, f"✔️ Окей, теперь выбери действие с уроком <i>«{lessonInfo['subject']['label']}»:</i>", reply_markup=keyboard)
	
	await bot.answer_callback_query(query.id)

@dp.callback_query_handler(lambda call: call.data.startswith("lessonwork!"))
async def callback_lessonwork(query: types.CallbackQuery):
	return

	await bot.answer_callback_query(query.id, text="Пытаюсь выполнить этот урок, пожалуйста, подожди.")

	lessonId = query.data.split("!")[1]
	bot_data = load_data("Bot.json")
	user_info = load_data(f"User-{query.from_user.id}.json")
	lessonInfo = bot_data["LessonInfo"][lessonId]
	lessonAnswers = json.load(open(f"Data/Index-{lessonId}.jsonc", "r", encoding="utf-8"))

	lesson_state = {}
	try:
		try:
			lesson_state_finished = await BL.get_lesson_state(lessonInfo["lessonId"], user_info["BilimlandID"], for_finished_lesson=True)
			if lesson_state_finished.get("isFinished") == 1:
				await query.message.answer("Этот урок уже выполнен.")
				return
		except:
			pass

		# Получаем содержимое.
		lesson_state = await BL.get_lesson_state(lessonInfo["lessonId"], user_info["BilimlandID"])

	except BL.LessonIsEmpty:
		# Если мы получаем эту ошибку, то вероятнее всего, урок пуст, и мы должны сами отправить содержимое.

		# Создаём пустое содержимое для запроса.
		new_lesson_data = await BL.generate_lesson_state_post_content(lessonAnswers, lessonInfo, user_info)

		# Добавляем конспект. На самом деле, эта функция добавляет не конспект, а выполненный урок, однако, в данном случае мы можем добавить именно конспект.
		new_lesson_state_data = await BL.add_answer_to_state(new_lesson_data, lessonAnswers)

		# Отправляем данные на сервер Bilimland, что бы он их сохранил.
		lesson_state_change_response = await BL.send_lesson_new_state(user_info["Token"], new_lesson_state_data, lessonInfo["lessonId"], user_info["BilimlandID"], True)

		lesson_state = new_lesson_data

	# Отлично, мы получили состояние урока. Теперь отправляем ответы на вопросы.

	try:
		for i in range(len(lessonAnswers["moduleIDsOrdered"]) - 1):
			# Выполняем все 9 уроков. // TODO: Добавить проверку, что бот выполнил все уроки.

			# Добавляем 1 ответ.
			lesson_state = await BL.add_answer_to_state(lesson_state, lessonAnswers)

			# Отправляем данные на сервер Bilimland, что бы он их сохранил.
			lesson_new_state_response = await BL.send_lesson_new_state(user_info["Token"], lesson_state, lessonInfo["lessonId"], user_info["BilimlandID"], ignore_duplicate=True)
	except:
		pass
		# Вероятнее всего, всё ок, так что отправляем последний запрос.

	final_lesson_state = await BL.mark_lesson_state_as_complete(lesson_state)

	# Отправляем данные на сервер Bilimland, что бы он их сохранил.
	lesson_new_state_response = await BL.send_lesson_new_state(user_info["Token"], final_lesson_state, lessonInfo["lessonId"], user_info["BilimlandID"], ignore_duplicate=True)
		

	await query.message.answer("<i>Процесс завершён, однако, так как эта функция ещё в бете, что-то могло поломаться, и, на самом деле, бот мог остановиться на каком-то задании либо вообще забить на выполнение, или вообще сломать задание.</i>")
	
@dp.callback_query_handler(lambda call: call.data.startswith("indexjson!"))
async def callback_indexjsondownload(query: types.CallbackQuery):
	lessonScheduleID = query.data.split("!")[1]

	await bot.send_document(
		query.message.chat.id, 
		types.InputFile(f"Data/Index-{lessonScheduleID}.jsonc", filename=f"index-{lessonScheduleID}.json"),
		caption="Держи. Этот файл немного отличается от стандартного <code>index.json</code> файла.",
	)
	
	await bot.answer_callback_query(query.id)



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
