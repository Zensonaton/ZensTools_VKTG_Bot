# coding: utf-8

from    aiogram             import Bot, types, md
from    aiogram.dispatcher  import Dispatcher
from    aiogram.utils       import executor
from    dotenv              import load_dotenv
import  os

load_dotenv()
 
bot = Bot(
	token       = os.environ["TG_TOKEN"],
	parse_mode  = types.ParseMode.MARKDOWN_V2
)

dp  = Dispatcher(bot)



@dp.message_handler()
async def message_handler(msg: types.Message):
	await msg.reply("Тест")

@dp.message_handler(content_types = types.ContentType.DOCUMENT)
async def process_document(msg: types.Message):
	if msg.document.mime_type == "application/json":
		await msg.reply("JSON")
		return
	elif msg.document.mime_type == "text/plain":
		await msg.reply("PLAIN")
		return
		
	await msg.reply("⚠ Отправленный тобою файл не является `\.JSON`\-файлом\. Вероятнее всего, ты отправил не тот файл\.")




executor.start_polling(dp)