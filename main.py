# coding: utf-8

from flask import Flask, render_template

app = Flask(__name__)

app.template_folder 		= "www"
app.static_folder 			= "www"
app.templates_auto_reload 	= True

@app.route("/")
def main():
	return render_template("main.html")

if __name__ == "__main__":
	app.run()