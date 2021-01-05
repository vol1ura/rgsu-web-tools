#!/usr/bin/env python
# Volodin Yuriy (volodinjuv@rgsu.net), 2020
# Parsing teacher's timetable on SDO.RSSU.NET
# ==================== Version 1.4 ===========================================
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


def get_html(url):
    r = requests.get(url)  # Response
    if r.status_code != 200:
        print("Can't get page. Check connection to rgsu.net and try to restart this script.")
    return r.text  # Return html page code


def make_timetable(teacher, date1, date2):
    Result = namedtuple('Result', 'code file pair_num days_num')
    begin_date = datetime.strptime(date1, '%Y-%m-%d')
    end_date = datetime.strptime(date2, '%Y-%m-%d')
    if end_date < begin_date:
        return Result(1, '', None, None)

    rssu_url = 'https://rgsu.net/for-students/timetable/timetable.html' + \
               '?template=&action=index&admin_mode=&nc_ctpl=935&Teacher=' + teacher
    html = get_html(rssu_url)
    soup = BeautifulSoup(html, 'html.parser')
    trs = soup.find('div', class_="row collapse").find_all('tr')

    dates_interval = [(begin_date + timedelta(i)).strftime("%d.%m.%y") for i in range((end_date-begin_date).days + 1)]

    data = []
    for tr in trs[1:]:
        cells = tr.find_all('td')
        dates = re.findall(r'\d{2}\.\d{2}\.\d{2}', cells[3].text)
        dates = list(set(dates_interval).intersection(set(dates)))
        if len(dates) > 0:
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
            hmhm = re.findall(r'\d+', cells[1].text.strip())
            lesson_time = ['', '']
            try:
                for i in range(2):
                    lesson_time[i] += hmhm[2*i]+':'+hmhm[1 + 2*i]
            except:
                print(f'Bad time format: [ {cells[1].text} ]')
                print('See timetable and manually correct time for:', cells[0].text, cells[2].text, group)
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
    return Result(0, f_name, len(datalines), len(dates_interval))
