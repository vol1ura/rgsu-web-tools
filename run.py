#!env/bin/python
from flask import Flask
from flask import render_template, request
from app.rgsu_timetable import make_timetable, get_teachers

app = Flask(__name__)


@app.route('/', methods=['POST',  'GET'])
def index():
    teachers = get_teachers()
    if request.method == 'POST':
        res = make_timetable(request.form['teacher'], request.form['date1'], request.form['date2'])
        if res.code == 0:
            return render_template('index.html', teachers=teachers,
                                   file=res.file, pn=res.pair_num, dn=max(1, res.days_num))
    return render_template('index.html', teachers=teachers)


@app.errorhandler(404)
def http_404_handler(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def http_500_handler(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)  # debug=True
