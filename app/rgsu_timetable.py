#!/usr/bin/env python
# Volodin Yuriy (volodinjuv@rgsu.net), 2020
# Parsing teacher's timetable on SDO.RSSU.NET
# ==================== Version 1.4 ===========================================
from bs4 import BeautifulSoup  # Install it if you need: pip3 install bs4
import csv                    # Install it if you need: pip3 install csv
from datetime import datetime, timedelta
from lxml.html import parse
import re
import requests               # Install it if you need: pip3 install requests


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


def make_timetable(teacher):
    begin_date = datetime.strptime('01.09.2020', '%d.%m.%Y')
    end_date = datetime.strptime('01.01.2021', '%d.%m.%Y')
    rssu_url = 'https://rgsu.net/for-students/timetable/timetable.html?template=&action=index&admin_mode=&nc_ctpl=935&Teacher='
    rssu_url += teacher
    html = get_html(rssu_url)

    soup = BeautifulSoup(html, 'html.parser')

    trs = soup.find('div', class_="row collapse").find_all('tr')

    date_sett = []
    while begin_date <= end_date:
        date_sett.append(begin_date.strftime("%d.%m.%y"))
        begin_date += timedelta(1)

    data = []
    for tr in trs[1:]:
        cells = tr.find_all('td')
        dates = re.findall(r'\d{2}\.\d{2}\.\d{2}', cells[3].text)
        dates = list(set(date_sett).intersection(set(dates)))
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
            p = re.compile(r'\d+')
            hmhm = p.findall(cells[1].text.strip())
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

    print(f'Load in selected period equals {2 * len(datalines)} hours. '
          f'It is {7 * 2 * len(datalines) / max(1, len(date_sett)):.1f} hours per week in average.')

    f_name = 'static/csv/calendar_' + teacher + '.csv'
    f = open(f_name, 'w', newline='', encoding='utf8')
    with f:
        writer = csv.writer(f)
        writer.writerow(['Start Date', 'Start Time', 'End Date', 'End Time', 'Location', 'Description', 'Subject'])
        writer.writerows(datalines)
    print('=' * 80)
    print(f'OK! Timetable was done - see file [{f_name}] in this directory.\nImport it to your Google Calendar.')
    return f_name
