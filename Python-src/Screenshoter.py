# coding: utf-8

"""

Микромодуль с Selenium для создания скриншотов заданий с ответами в Bilimland.

"""


import time
from geckodriver_autoinstaller.utils import get_firefox_version, get_latest_geckodriver_version, get_geckodriver_filename, get_geckodriver_url # // TODO: Replace me.
import io
import os
import urllib
import tarfile
import os
import urllib.request
import urllib.error
import tarfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

class DriverStrings:
	"""

	Класс с множеством строк-скриптов и XPath'ей.
	
	"""

	_GETBYXPATHFUNC = "function getByXPath(path) { return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue; }"

	LESSON_LOADED_FIRSTMODULE_XPATH = "/html/body/div/div[1]/div/div[4]/div/div[2]/div[1]/div/div/div/div/div/div/div/div[1]/div[2]/div[2]"
	LESSON_QUESTION_XPATH  = "/html/body/div/div[1]/div/div[4]/div/div[2]/div[1]/div/div/div/div/div/div/div/div[1]/div[2]/div[3]/div[{}]" # Starts from 2
	QUESTION_SCREENSHOT_BODY_XPATH = "/html/body/div/div[1]/div/div[4]/div/div[2]/div[1]/div/div/div/div/div/div/div/div[3]/div"
	LESSON_QUESTION_IS_CORRECT_XPATH = "/html/body/div/div[1]/div/div[4]/div/div[2]/div[1]/div/div/div/div/div/div/div/div[3]/div/div[1]"
	IS_LESSON_COLLAPSED_XPATH = "/html/body/div/div[1]/div/div[4]/div/div[2]/div[1]/div/div/div/div/div/div/div/div[1]"
	OPEN_COLLAPSED_LESSON_XPATH = "/html/body/div/div[1]/div/div[4]/div/div[2]/div[1]/div/div/div/div/div/div/div/div[1]/span"

	HINT_SUCCESS_JS = "document.getElementsByClassName(\"bllp-adapt-hints__wrapper\")[0].style.display = \"none\";"
	FIX_ANSWER_SCREENSHOT_SIZE_JS = "document.getElementsByClassName(\"bllp-box-body\")[0].style.flex = 0;"
	HIDE_SENSITIVE_INFO_JS = f"var CENSORED = \"CENSORED\"; {_GETBYXPATHFUNC}\n\ngetByXPath(\"/html/body/div/div[1]/div/div[2]/div[2]/div[1]\").innerText = CENSORED;\ngetByXPath(\"/html/body/div/div[1]/div/div[2]/div[2]/div[2]/div\").lastChild.textContent = CENSORED;\ngetByXPath(\"/html/body/div/header/div[1]/div/div[2]/div[3]\").style.display = \"none\";\ngetByXPath(\"/html/body/div/div[1]/div/div[2]/div[1]/div\").style.display = \"none\";\ndocument.getElementsByClassName(\"bllx-icon bllp-icon-resize-full-alt bllx-icon-btn bllp-box-fullscreen-btn\")[0].style.display = \"none\";\ngetByXPath(\"/html/body/div/div[1]/div/div[5]/div\").style.display = \"none\";\n\n// Not used?\n// getByXPath(\"/html/body/div/div[1]/div/div[2]/div[2]/div[1]/span\").style.display = \"none\";\n// getByXPath(\"/html/body/div/div[1]/div/div[4]/div/div[2]/div[1]/div/div/div/div/div/div/div/div[3]/div\").height = 0; "
	INJECT_JSFUNCS_FOR_LESSONSTATE = _GETBYXPATHFUNC + "\n\nfunction question_state(is_right) {\n\t// Удаляем старое\n\tvar old_state = document.getElementById(\"question-style-modifier\"); if (old_state) { old_state.remove() };\n\n\tconst color_right = \"#4FC168\"; const color_wrong = \"red\"\n\n\tconst style = document.createElement(\"style\", { id: \"question-style-modifier\" })\n\tstyle.innerHTML = `.bllp-platform-wrapper { background: #fffffa !important; };`\n\n\tconst fullscreenButton = getByXPath(\"/html/body/div/div[1]/div/div[4]/div/div[2]/div[1]/div/div/div/div/div/div/div/div[4]/span\")\n\tfullscreenButton.classList.remove(\"bllp-icon-resize-full-alt\")\n\n\tconst hintsBlock = getByXPath(\"/html/body/div/div[1]/div/div[4]/div/div[2]/div[1]/div/div/div/div/div/div/div/div[3]/div/div[2]\")\n\n\tif (is_right) {\n\t\tfullscreenButton.style = `background-color: ${color_right}; display: block; border-radius: 0; text-align: center; height: unset; font-size: 1.5em; padding: 10px; margin-right: 80px; width: 100%; `\n\t\tfullscreenButton.innerHTML = \"ПРАВИЛЬНЫЙ ОТВЕТ\"\n\t\thintsBlock.style.display = \"none\"\n\t} else {\n\t\tfullscreenButton.style = `background-color: ${color_wrong}; display: block; border-radius: 0; text-align: center; height: unset; font-size: 1.5em; padding: 10px; margin-right: 80px; width: 100%; `\n\t\tfullscreenButton.innerHTML = \"НЕПРАВИЛЬНЫЙ ОТВЕТ!\"\n\t\thintsBlock.style.display = \"block\"\n\t}\n\n\tdocument.head.appendChild(style)\n}; "

	URL_FOR_SETTING_COOKIES = "https://onlinemektep.net/404"

def download_geckodriver(directory: str = "temp/"):
	"""Скачивает файл для управления браузером и возвращает путь к нему."""

	geckodriver_version = get_latest_geckodriver_version()

	geckodriver_dir = directory
	geckodriver_filename = get_geckodriver_filename()
	geckodriver_filepath = os.path.join(geckodriver_dir, geckodriver_filename)

	if not os.path.isdir(geckodriver_dir):
		os.mkdir(geckodriver_dir)

	url = get_geckodriver_url(geckodriver_version)

	try:
		response = urllib.request.urlopen(url)
		if response.getcode() != 200:
			raise urllib.error.URLError('Not Found')
	except urllib.error.URLError:
		raise RuntimeError(f'Failed to download geckodriver archive: {url}')
	archive = io.BytesIO(response.read())

	tar = tarfile.open(fileobj=archive, mode='r:gz')
	tar.extractall(geckodriver_dir)
	tar.close()
		
	return geckodriver_filepath

def setup_firefox_browser(bilimland_token: str, bilimland_refresh_token: str, temp_dir: str = "temp", headless: bool = True):
	"""Делает установку Firefox'а.

	Args:
		headless (bool, optional): Указывает, будет ли использоваться headless-режим. В headless-режиме браузер работает *почти* как обычно, однако, у такого нет интерфейса, и он может работать даже на серверах.
	"""

	# Создаём временную папку.
	os.makedirs(temp_dir, exist_ok=True)

	# Скачиваем geckodriver: (для управления Firefox'а)
	if not os.path.exists(os.path.join(temp_dir, "geckodriver")):
		download_geckodriver(temp_dir)

	# Создаём браузер.
	# Опции браузера:
	options = Options()
	options.headless = headless
	options.add_argument("-width=1920")
	options.add_argument("-height=1080")

	# Создаём сам браузер:
	driver = webdriver.Firefox(executable_path=os.path.join(temp_dir, "geckodriver"), options=options, service_log_path=os.devnull)

	# Делаем так, что бы браузер загрузил первую страницу, и засунул туда cookie с авторизацией.
	driver.get(DriverStrings.URL_FOR_SETTING_COOKIES)
	driver.add_cookie({
		"name": "r_t", # Refresh token
		"value": bilimland_refresh_token
	})
	driver.execute_script(f"localStorage.setItem('token', '{bilimland_token}');")


	return driver

def get_lesson_screenshots(driver: webdriver.Firefox, lesson_url: str, output_dir: str):
	"""Создаёт скриншоты ответов урока, и засовывает их в особую папку, и далее возвращает list со всеми путями к скриншотам.

	Args:
		driver (webdriver.Firefox): [description]
		lesson_url (str): [description]
		output_dir (str): Output-путь.
	"""

	# Загружаем страницу с уроком.
	driver.get(lesson_url)

	# Ждём, когда урок полностью загрузится.
	WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, DriverStrings.LESSON_LOADED_FIRSTMODULE_XPATH)))

	# После загрузки урока, кликаем на кнопку для раскрытия всех заданий.
	try: driver.find_element_by_xpath(DriverStrings.LESSON_LOADED_FIRSTMODULE_XPATH).click()
	except: pass

	# Прячем всякий шлак, по типу надписи "молодец хуй пизда 100% баллов партия тобой довольна", а так же прячем чувствительную инфу.
	driver.execute_script(DriverStrings.FIX_ANSWER_SCREENSHOT_SIZE_JS)
	driver.execute_script(DriverStrings.HIDE_SENSITIVE_INFO_JS)

	# Проверяем, свёрнута ли боковая панель?
	sidepanel = driver.find_element_by_xpath(DriverStrings.IS_LESSON_COLLAPSED_XPATH)
	sidepanel_property = sidepanel.get_attribute("data-collapsed") 

	if sidepanel_property is not None:
		driver.find_element_by_xpath(DriverStrings.OPEN_COLLAPSED_LESSON_XPATH).click()

	# Создаём скриншот после загрузки сайта. Почему бы и нет? :глаза:
	driver.get_screenshot_as_file(os.path.join(output_dir, "Main.png"))

	# А теперь проходимся по всем урокам. Это нужно, что бы Bilimland загрузил все формулы, изображения, и прочее.
	num_of_questions = 0
	start_from = 0
	index = 0
	try:
		while True:
			driver.find_element_by_xpath(DriverStrings.LESSON_QUESTION_XPATH.format(index + 1)).click()
			# Проверяем тип вопроса. Если это simple, то добавляем к start_from.
			element_class = driver.find_element_by_xpath(DriverStrings.LESSON_QUESTION_IS_CORRECT_XPATH).get_attribute("class")
			is_simple = "bllp-module-simple" in element_class
			index += 1

			if is_simple:
				start_from += 1
			else:
				num_of_questions += 1
	except: pass

	# Чуть-чуть отдыхаем.
	time.sleep(0.5)

	# Создаём лист:
	screenshots_list = []

	# А теперь снова проходимся по вопросам, и на этот раз и вправду делаем скриншоты!
	for i in range(start_from + 1, start_from + num_of_questions + 1): # Walk thru all questions
		screenshot_path = os.path.join(output_dir, f"{i - 1}.png")

		driver.find_element(By.XPATH, DriverStrings.LESSON_QUESTION_XPATH.format(i)).click()

		element_class = driver.find_element_by_xpath(DriverStrings.LESSON_QUESTION_IS_CORRECT_XPATH).get_attribute("class")
		is_correct = ("bllp-correct" in element_class) or ("bllp-module-simple" in element_class)
		driver.execute_script(DriverStrings.INJECT_JSFUNCS_FOR_LESSONSTATE + f"question_state({'true' if is_correct else 'false'})")

		driver.find_element_by_xpath(DriverStrings.QUESTION_SCREENSHOT_BODY_XPATH).screenshot(screenshot_path)

		screenshots_list.append(screenshot_path)

	return screenshots_list

