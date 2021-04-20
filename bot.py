from logging import ERROR
import telebot
import datetime
import requests
from bs4 import BeautifulSoup

TOKEN = '1619531266:AAGiEAXzjNuL42e8MUc6veYqiW98XPv0KU8'
NOW_DAY = datetime.datetime.weekday(datetime.datetime.today()) + 1
# NOW_DAY =  1
WEEK_DAYS = dict(zip(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'), [i for i in range(1, 7)]))
# WEB_PAGES = dict.fromkeys(['0', '1', '2'],dict.dict.fromkeys([i for i in range(1, 7)]+['all'], 0))
NOW_TIME = datetime.datetime.time(datetime.datetime.today())
# NOW_TIME = datetime.datetime.time(datetime.datetime.strptime('10:30', '%H:%M'))

def get_page(group, day='', week=''):
    if week: week = str(week) + "/"
    url = f'https://itmo.ru/ru/schedule/0/{group}/{week}raspisanie_zanyatiy_{group}.htm'
    response = requests.get(url)
    web_page = response.text
    # if week: WEB_PAGES[week.rstrip('/')][day] = web_page
    return web_page

def get_schedule(web_page, day = 0, more1 = False):
    soup = BeautifulSoup(web_page, "html5lib")

    day_list = []
    times_list = []
    locations_list = []
    aud_list = []
    lessons_list = []
    for d in range(day, (day+1)*(not more1) + 7*more1):
        schedule_table = soup.find("table",attrs={"id": f"{d}day"})
        day_list += [key.capitalize() for key in WEEK_DAYS.keys() if WEEK_DAYS[key] == d]
        # Время проведения занятий
        times_list_s = schedule_table.find_all("td", attrs={"class": "time"})
        times_list += [time.span.text for time in times_list_s]
        # Место проведения занятий
        locations_list_s = schedule_table.find_all("td", attrs={"class": "room"})
        locations_list += [room.span.text for room in locations_list_s]
        # Аудитория
        aud_list_s = schedule_table.find_all("dd", attrs={"class": "rasp_aud_mobile"})
        aud_list += [aud.text for aud in aud_list_s]
        # Название дисциплин и имена преподавателей
        lessons_list_s = schedule_table.find_all("td", attrs={"class": "lesson"})
        lessons_list_s = [lesson.text.split('\n\n') for lesson in lessons_list_s]
        day_list += ['' for les in range(len(lessons_list_s)-1)]
        lessons_list += [', '.join([info for info in lesson_info if info]) for lesson_info in lessons_list_s]
    lessons_list = [" ".join(lesson.split()) for lesson in lessons_list]
    return day_list, times_list, locations_list, aud_list, lessons_list

def get_week(web_page):
    soup = BeautifulSoup(web_page, "html5lib")
    gweek = soup.find("h2", attrs={"class": "schedule-week"})
    return gweek.text

NOW_WEEK = get_week(get_page('Y2334', 'all'))

lb5_bot = telebot.TeleBot(TOKEN)

@lb5_bot.message_handler(commands=['day'])
def get_day(message):
    try: 
        _, day, week, group = message.text.split()
    except ValueError:
        lb5_bot.send_message(message.chat.id, 'Неправильный ввод')
        return ERROR
    # if WEB_PAGES[week][WEEK_DAYS[day]] == 0:
    web_page = get_page(group, day, week)
    # else: web_page = WEB_PAGES[week][WEEK_DAYS[day]]
    try:
        day_lst, times_lst, locations_lst, lessons_lst, aud_lst = get_schedule(web_page, WEEK_DAYS[day])
    except AttributeError:
        lb5_bot.send_message(message.chat.id, '<strong>Неправильный ввод</strong>', parse_mode='HTML')
        return ERROR
    resp = f'{day_lst[0]}\n'
    for time, location, aud, lession in zip(times_lst, locations_lst, lessons_lst, aud_lst):
        resp += '<b>{}</b>, {}, {}, {}\n'.format(time, location, aud, lession)

    lb5_bot.send_message(message.chat.id, resp, parse_mode='HTML')

@lb5_bot.message_handler(commands=['near_lesson'])
def get_near_lesson(message):
    try:    
        _, group = message.text.split()
    except ValueError or AttributeError:
        lb5_bot.send_message(message.chat.id, 'Неправильный ввод')
        return ERROR
    
    global NOW_DAY
    if 'четная' in NOW_WEEK: week = '1'
    else: week = '2'
    if NOW_DAY == 7: 
        if week == '1': week = '2'
        else: week = '1'
        NOW_DAY = 1
    
    # if WEB_PAGES[week][NOW_DAY] == 0:
    web_page = get_page(group, NOW_DAY, week)
    # else: web_page = WEB_PAGES[week][NOW_DAY]
    try:
        day_lst, times_lst, locations_lst, lessons_lst, aud_lst = get_schedule(web_page, NOW_DAY, True)
    except AttributeError:
        lb5_bot.send_message(message.chat.id, '<strong>Неправильный ввод</strong>', parse_mode='HTML')
        return ERROR
    resp = ''
    for d, time, location, lession, aud in zip(day_lst, times_lst, locations_lst, lessons_lst, aud_lst):
        if [d] == [key.capitalize() for key in WEEK_DAYS.keys() if WEEK_DAYS[key] == NOW_DAY+1]:
            if datetime.datetime.time(datetime.datetime.strptime(f'{"8:00"}', '%H:%M')):
                resp += '{}\n <b>{}</b>, {}, {}, {}\n'.format(d, time, location, aud, lession)
                break
        else: 
            if NOW_TIME < datetime.datetime.time(datetime.datetime.strptime(f'{time[0:5]}', '%H:%M')):
                resp += '{}\n <b>{}</b>, {}, {}, {}\n'.format(d, time, location, aud, lession)
                break
    
    lb5_bot.send_message(message.chat.id, resp, parse_mode='HTML')


@lb5_bot.message_handler(commands=['tomorrow'])
def get_tomorrow(message):
    try:    
        _, group = message.text.split()
    except ValueError or AttributeError:
        lb5_bot.send_message(message.chat.id, 'Неправильный ввод')
        return ERROR
    
    global NOW_DAY
    if 'четная' in NOW_WEEK: week = '1'
    else: week = '2'
    if NOW_DAY == 7: 
        if week == '1': week = '2'
        else: week = '1'
        NOW_DAY = 0
    
    # if WEB_PAGES[week][NOW_DAY+1] == 0:
    web_page = get_page(group, NOW_DAY+1, week)
    # else: web_page = WEB_PAGES[week][NOW_DAY+1]
    try:
        date_lst, times_lst, locations_lst, lessons_lst, aud_lst = get_schedule(web_page, NOW_DAY+1)
    except AttributeError:
        lb5_bot.send_message(message.chat.id, '<strong>Нет пар</strong>', parse_mode='HTML')
        return ERROR

    resp = f'{date_lst[0]}\n'
    for time, location, lession, aud in zip(times_lst, locations_lst, lessons_lst, aud_lst):
        resp += '<b>{}</b>, {}, {}, {}\n'.format(time, location, aud, lession)
        
    lb5_bot.send_message(message.chat.id, resp, parse_mode='HTML')


@lb5_bot.message_handler(commands=['all'])
def get_all(message):
    try: 
        _, week, group = message.text.split()
    except ValueError or AttributeError:
        lb5_bot.send_message(message.chat.id, 'Неправильный ввод')
        return ERROR
    # if WEB_PAGES[week]['all'] == 0:
    #     web_page = get_page(group, 'all', week)
    # else: web_page = WEB_PAGES[week]['all']
    web_page = get_page(group, 'all', week)
    try:
        day_lst, times_lst, locations_lst, lessons_lst, aud_lst = get_schedule(web_page, 1, True)
    except AttributeError:
            lb5_bot.send_message(message.chat.id, '<strong>Неправильный ввод</strong>', parse_mode='HTML')
            return ERROR
    resp = ''
    for d, time, location, lession, aud in zip(day_lst, times_lst, locations_lst, lessons_lst, aud_lst):
        resp += '{}\n <b>{}</b>, {}, {}, {}\n'.format(d, time, location, lession, aud)
    

    lb5_bot.send_message(message.chat.id, resp, parse_mode='HTML')


if __name__ == '__main__':
    lb5_bot.polling(none_stop=True)