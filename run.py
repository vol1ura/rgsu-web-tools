#!env/bin/python
from flask import Flask
from flask import render_template, request, make_response, url_for, session
from app.rgsu_timetable import make_timetable, get_teachers

app = Flask(__name__)


@app.route('/', methods=['POST',  'GET'])
def index():
    file = ''
    if request.method == 'POST':
        file = make_timetable(request.form['teacher'], request.form['date1'], request.form['date2'])
    return render_template('index.html', teachers=get_teachers(), file='/' + file)


@app.errorhandler(404)
def http_404_handler():
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run()  # debug=True
