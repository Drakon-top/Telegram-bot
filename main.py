from telebot import types
from datetime import datetime
from PIL import Image
import qrcode
import sqlite3
import telebot
import os

DataBase = "base_event.db"
bot = telebot.TeleBot("1931658449:AAGlNY0980NBjgY3g1GXjKK_qW5P8RfbnDM")

# Основные списки и словарь, в которых хранится описание и общая информация по мероприятиям
EVENTS_LIST = []
KEY_KODE_EVENTS = []
INFO_ABOUT_EVENTS = {}


# Метод для считывания ввода пользователя
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "/start":
        bot.send_message(message.from_user.id, "Привет! Это бот для регистрации на мероприятия, "
                                               "проходящие на Федеральной территории Сириус. "
                                               "Чтобы узнать команды бота введети /help")
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "/my_events - с помощью это команды Вы моежет посмотреть мероприятия, "
                                               "на которые заргистрированы и также занового распечатать qr, который является пропуском"
                         + "\n" + "/events - с помощью это команды Вы моежет посмотреть все мероприятия и прочитать описния к ним"
                         + "\n" + "/events_register - с помощью это команды Вы моежет зергистрироваться на мероприятия и получить пропуск")
    elif message.text == "/my_events":
        conn = sqlite3.connect(DataBase)
        cur = conn.cursor()
        _list_events = cur.execute("""SELECT id_event, number_seats FROM Persons WHERE id_person == ?""",
                                   (message.from_user.id,)).fetchall()
        if _list_events != []:
            bot.send_message(message.from_user.id, text='Вы зарегистрированы на мероприятия:')
            for i in range(len(_list_events)):
                keyboard = types.InlineKeyboardMarkup()
                event = cur.execute("""SELECT * FROM Events WHERE id == ?""",
                        (_list_events[i][0],)).fetchall()[0]
                text = event[1] + "\n" + "Мероприятие будет проходить " \
                       + datetime.fromtimestamp(event[4]).strftime("%d.%m.%Y") \
                       + "в " + datetime.fromtimestamp(event[4]).strftime("%H:%M")  \
                       + "\n" + "У Вас билет на " + str(_list_events[1]) + "\n" \
                       + "Если хотите занового распечатать билет нажмите кнопку под мероприятием"
                key_but = types.InlineKeyboardButton(text="Ticket",
                                                     callback_data="print/" + str(event[0]))
                keyboard.add(key_but)
                bot.send_message(message.from_user.id, text, reply_markup=keyboard)
        else:
            bot.send_message(message.from_user.id, "Вы еще не зарегистрированы ни на одно мероприятие. "
                                                   "Давайте это исправим! Наберите /events, чтобы посмотреть мероприятия")
        conn.commit()
        conn.close()
    elif message.text == "/events":
        conn = sqlite3.connect(DataBase)
        cur = conn.cursor()
        dat = datetime.today()
        seconds = dat.timestamp()
        _list_events = cur.execute("""SELECT * FROM Events WHERE date >= ?""", (seconds,)).fetchall()
        if _list_events != []:
            bot.send_message(message.from_user.id, "Сейчас проходят мероприятия:")
            for i in range(len(_list_events)):
                text = _list_events[i][1] + "\n" + _list_events[i][5] + "\n" + "Мероприятие будет проходить " \
                       + datetime.fromtimestamp(_list_events[i][4]).strftime("%d.%m.%Y") \
                       + " в " + datetime.fromtimestamp(_list_events[i][4]).strftime("%H:%M")  \
                       + "\n" + "Максимальное количество человек в билете " + str(_list_events[i][6])
                bot.send_message(message.from_user.id, text)
        else:
            bot.send_message(message.from_user.id, "К сожалению, сейчас никаких мероприятий нет")
    elif message.text == "/events_register":
        if len(EVENTS_LIST) != 0:
            keyboards = types.InlineKeyboardMarkup()
            for i in range(len(EVENTS_LIST)):
                key_buton = types.InlineKeyboardButton(text=EVENTS_LIST[i],
                                                     callback_data=KEY_KODE_EVENTS[i])
                keyboards.add(key_buton)
            bot.send_message(message.from_user.id, text='Выберите мероприятие',
                             reply_markup=keyboards)
        else:
            bot.send_message(message.from_user.id, "К сожалению сейчас никаких мероприятий нет, "
                                                   "посмотрите позже")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши /help.")


# метод для создания qr кода с даннами
def create_qrcode(id_user, id_event, number_seats):
    conn = sqlite3.connect(DataBase)
    cur = conn.cursor()
    _list = cur.execute("""SELECT * FROM Events WHERE id == ?""", (id_event,)).fetchall()[0]
    data = [_list[1], _list[4], number_seats]
    p = os.path.abspath('main.py')[:-7]
    filename = p + "qrcode_image/" + str(id_user) + "+" + str(id_event)
    img = qrcode.make(data)  # создание кода с данными
    img.save(filename)
    conn.commit()
    conn.close()
    return filename


# обновление списков и словря
def base_update():
    global EVENTS_LIST, KEY_KODE_EVENTS, INFO_ABOUT_EVENTS
    EVENTS_LIST = []
    KEY_KODE_EVENTS = []
    INFO_ABOUT_EVENTS = {}
    conn = sqlite3.connect(DataBase)
    cur = conn.cursor()
    dat = datetime.today()
    seconds = dat.timestamp()
    _list_event = cur.execute("""SELECT * FROM Events WHERE date >= ?""", (seconds,)).fetchall()
    EVENTS_LIST = list(map(lambda x: x[1], _list_event))
    KEY_KODE_EVENTS = list(map(lambda x: x[1] + "_kod", _list_event))
    for i in range(len(EVENTS_LIST)):
        INFO_ABOUT_EVENTS[KEY_KODE_EVENTS[i]] = {
            "id": _list_event[i][0],
            "name": _list_event[i][1],
            "date": datetime.fromtimestamp(_list_event[i][4]).strftime("%d.%m.%Y"),
            "max_count": _list_event[i][2],
            "now_count": _list_event[i][3],
            "time": datetime.fromtimestamp(_list_event[i][4]).strftime("%H:%M"),
            "info": _list_event[i][5],
            "one_person": _list_event[i][6]
        }
    conn.commit()
    conn.close()


# метод, обрабатывающий нажаитя на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    conn = sqlite3.connect(DataBase)
    cur = conn.cursor()
    if call.data in INFO_ABOUT_EVENTS:
        base_update()
        bot.send_message(call.message.chat.id, INFO_ABOUT_EVENTS[call.data]["name"])
        #bot.send_message(call.message.chat.id, INFO_ABOUT_EVENTS[call.data]["info"])
        count = "Свободных мест осталось " + str(INFO_ABOUT_EVENTS[call.data]["max_count"] -
                                                 INFO_ABOUT_EVENTS[call.data]["now_count"])
        bot.send_message(call.message.chat.id, count)
        bot.send_message(call.message.chat.id, "Дата и время проведения: " +
                         INFO_ABOUT_EVENTS[call.data]["date"] + " " + INFO_ABOUT_EVENTS[call.data][
                             "time"])
        number_seats = INFO_ABOUT_EVENTS[call.data]["max_count"] - INFO_ABOUT_EVENTS[call.data]["now_count"]
        _list_person = cur.execute("""SELECT * FROM Persons WHERE id_person == ? AND id_event == ?""",
                                   (call.message.chat.id, INFO_ABOUT_EVENTS[call.data]["id"])).fetchall()
        if _list_person != []:
            bot.send_message(call.message.chat.id, "Вы уже зарегистрированы. Количество мест в билете " +
                             str(_list_person[0][3]))
        elif number_seats > 0:
            keyboard = types.InlineKeyboardMarkup()
            for i in range(min(number_seats, INFO_ABOUT_EVENTS[call.data]["one_person"])):
                key_but = types.InlineKeyboardButton(text=str(i + 1),
                                                 callback_data=str(i + 1) + ".register/" + str(INFO_ABOUT_EVENTS[call.data]["id"]))
                keyboard.add(key_but)
            bot.send_message(call.message.chat.id, text='Для регистрации, выберите количество мест',
                         reply_markup=keyboard)
        conn.commit()
        conn.close()
    elif "register" in call.data:
        _id = int(call.data[call.data.find("/") + 1:])
        number_seats = int(call.data[:call.data.find(".")])
        _list_person = cur.execute(
            """SELECT * FROM Persons WHERE id_person == ? AND id_event == ?""",
            (call.message.chat.id, _id)).fetchall()
        if _list_person != []:
            bot.send_message(call.message.chat.id,
                             "Вы уже зарегистрированы. Количество мест в билете " +
                             str(_list_person[0][3]))
        else:
            name_qrcode = create_qrcode(call.message.chat.id, _id, number_seats)
            cur.execute(
                """INSERT INTO Persons (id_person, id_event, number_seats, qrcode) VALUES (?, ?, ?, ?);""",
                (call.message.chat.id, _id, number_seats, name_qrcode))
            num = number_seats + \
                  cur.execute("""SELECT * FROM Events WHERE id == ?""", (_id,)).fetchall()[0][3]
            cur.execute("""UPDATE Events SET now_count_person = ? WHERE id == ?;""",
                        (num, _id))
            bot.send_message(call.message.chat.id,
                             "Вы успешно зарегистрированы. Количество мест в билете " + str(
                                 number_seats))
            img = Image.open(name_qrcode)
            bot.send_photo(call.message.chat.id, img)
        conn.commit()
        conn.close()
    elif "print" in call.data:
        _id = int(call.data[call.data.find("/") + 1:])
        _list_person = cur.execute(
            """SELECT qrcode FROM Persons WHERE id_person == ? AND id_event == ?""",
            (call.message.chat.id, _id)).fetchall()[0]
        img = Image.open(_list_person[0])
        bot.send_photo(call.message.chat.id, img)



base_update()
bot.polling(none_stop=True, interval=0)