#!/usr/bin/env python
# Volodin Yuriy (volodinjuv@rgsu.net), 2020
# Parsing teacher's timetable on SDO.RSSU.NET
# ==================== Version 1.5 ===========================================
from bs4 import BeautifulSoup
from collections import namedtuple
import csv
from datetime import datetime, timedelta
from lxml.html import parse
import re
import requests


def get_teachers():
    result = requests.get('https://rgsu.net/for-students/timetable/?nc_ctpl=935', stream=True)
    result.raw.decode_content = True
    tree = parse(result.raw)
    return tree.xpath('//select[@id="teacher"]/option/@value')[1:]


WEEKDAYS = {'Понедельник': 1, 'Вторник': 2, 'Среда': 3, 'Четверг': 4, 'Пятница': 5, 'Суббота': 6}


def make_timetable(teacher, date1, date2):
    Result = namedtuple('Result', 'code file pair_num days_num')
    begin_date = datetime.strptime(date1, '%Y-%m-%d')
    end_date = datetime.strptime(date2, '%Y-%m-%d')
    if end_date < begin_date:
        return Result(1, '', None, None)

    payload = {'template': '', 'action': 'index', 'admin_mode': '', 'nc_ctpl': 935, 'Teacher': teacher}
    rssu_url = 'https://rgsu.net/for-students/timetable/timetable.html'
    timetable = requests.get(rssu_url, params=payload)
    if not timetable.ok:
        return Result(1, '', None, None)

    soup = BeautifulSoup(timetable.text, 'html.parser')

    trs = soup.find('div', class_="row collapse").find_all('tr')

    date_now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    while date_now.isoweekday() != 1:
        date_now -= timedelta(1)  # step back to monday
    if "Нечетная" in soup.find('div', class_="panel-green").find('p', class_="heading").text:
        date_now += timedelta(7)  # change week to synchronize oddness
    # Sunday belongs to next week on this site
    # if datetime.now().isoweekday() == 7:
    #     date_now -= timedelta(7)  # change week to correct oddness in sunday

    date_range = [begin_date + timedelta(i) for i in range((end_date - begin_date).days + 1)]

    data = []
    for tr in trs[1:]:
        cells = tr.find_all('td')
        dates = re.findall(r'\d{2}\.\d{2}\.\d{2}', cells[3].text)
        if dates:
            date_range_str = [date.strftime("%d.%m.%y") for date in date_range]
            dates = list(set(date_range_str).intersection(set(dates)))
        else:
            weekday = WEEKDAYS[cells[0].text.strip()]
            week = 0 if 'Четная' in cells[2].text else 1
            dates = [date.strftime("%d.%m.%y") for date in date_range
                     if (date.isoweekday() == weekday) and ((date - date_now).days // 7 % 2 == week)]

        if dates:
            discipline = re.findall(r'[а-яА-ЯёЁ -]+', cells[3].text)[0].strip()
            if len(discipline) > 16:
                discipline_s = ''.join([(w if len(w) == 1 else w[0].upper()) for w in discipline.split(' ')])
            else:
                discipline_s = discipline
            lesson_type = cells[4].text.strip()
            if lesson_type.lower() == 'лабораторная работа':
                lesson_type_s = 'лаба'
            elif lesson_type.lower() == 'практическое занятие':
                lesson_type_s = 'практика'
            else:
                lesson_type_s = lesson_type
            location = cells[5].text.strip()
            group = cells[6].text.strip()
            lesson_time = re.findall(r'\d{1,2}:\d{2}', cells[1].text)
            if len(lesson_time) != 2:
                print(f'Bad time format: [ {cells[1].text} ].\n'
                      'See timetable and manually correct time for:', cells[0].text, cells[2].text, group)
                lesson_time = ['8:00', '22:00']

            for date in dates:
                data.append([date, lesson_time[0], lesson_time[1], location, group,
                             discipline, lesson_type, discipline_s + ' ' + lesson_type_s])

    datalines = []
    for i in range(len(data)):
        j = i + 1
        while j < len(data):
            if data[i][0] == data[j][0] and data[i][1] == data[j][1] and data[i][7] == data[j][7]:
                if data[i][3] != data[j][3]:
                    data[j][3] += ' / ' + data[i][3]
                data[j][4] += ', ' + data[i][4]
                break
            j += 1
        else:
            datalines.append([data[i][0], data[i][1], data[i][0], data[i][2], data[i][3],
                              data[i][4] + ': ' + data[i][5] + ', ' + data[i][6], data[i][7]])

    f_name = 'static/csv/calendar_' + teacher + '.csv'
    f = open(f_name, 'w', newline='', encoding='utf8')
    with f:
        writer = csv.writer(f)
        writer.writerow(['Start Date', 'Start Time', 'End Date', 'End Time', 'Location', 'Description', 'Subject'])
        writer.writerows(datalines)
    print(f'OK! Timetable was done - see file [{f_name}]')
    return Result(0, f_name, len(datalines), len(date_range))
