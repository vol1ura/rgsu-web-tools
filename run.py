# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from app.rgsu_timetable import make_timetable, get_teachers

app = Flask(__name__)


@app.route('/', methods=['POST',  'GET'])
def index():
    teachers = get_teachers()
    if request.method == 'POST':
        res = make_timetable(request.form['teacher'], request.form['date1'], request.form['date2'])
        if res.code == 0:
            return render_template('index.html', teachers=teachers,
                                   file=res.file,
                                   sum_load=2 * res.pair_num,
                                   avr_load='{0:.1f}'.format(7 * 2 * res.pair_num / max(1, res.days_num))
                                   )
    return render_template('index.html', teachers=teachers)


@app.errorhandler(404)
def http_404_handler(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def http_500_handler(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')  # debug=True
