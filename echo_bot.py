import json
import requests
import telebot
from telebot import types

config = json.load(open('config.json'))
_users = []  # todo: save these in a file,
userStep = {}  # so they won't reset every time the bot restarts
commands = {  # command description used in the "help" command
    'start': 'Get used to the bot',
    'help': 'Gives you information about the available commands',
}


def get_user_step(uid):
    if uid not in userStep:
        userStep[uid] = 0
        print("New user ", uid)
    return userStep[uid]


def listener(messages):
    for m in messages:
        if m.content_type == 'text':
            if m.text == '/exit_force':
                exit()
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + str(m.text))


bot = telebot.TeleBot(config['tel_bot_token'])
bot.set_update_listener(listener)


def get_list_bus_stops(longitude: float, latitude: float):
    url_server = config['url_lad_lviv']
    url = f'{url_server}/closest?longitude={round(longitude, 2)}&latitude={round(latitude, 2)}'
    return requests.get(url).json()


bot.set_update_listener(listener)


def get_bus_stop(bus_stop_code):
    print(bus_stop_code, 'code')
    url_server = config['url_lad_lviv']
    url = f'{url_server}/stops/{str(bus_stop_code)}'
    return requests.get(url).json()


def get_bus_smile(type_t: str):
    if type_t == 'trol':
        return '🚎'
    if type_t == 'bus':
        return '🚌'
    return '🚋'


@bot.message_handler(commands=['start'])
def start(message):
    cid = message.chat.id
    if cid not in _users:
        _users.append(cid)
        command_help(message)
    userStep[cid] = 0
    markup = types.ReplyKeyboardMarkup()
    location = types.KeyboardButton('Location', request_location=True)
    markup.add(location)
    bot.send_message(message.chat.id, 'Please your location', reply_markup=markup)
    return


@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "The following commands are available: \n"
    for key in commands:
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)


@bot.message_handler(content_types=['location'], func=lambda message: get_user_step(message.chat.id) == 0)
def handle_location(message):
    if message.chat.type == 'private' and message.content_type == 'location':
        cid = message.chat.id
        bot.send_chat_action(cid, 'typing')
        bus_stops = get_list_bus_stops(latitude=message.location.latitude, longitude=message.location.longitude)
        if len(bus_stops) > 0:
            markup = types.ReplyKeyboardMarkup()
            for bus_stop in bus_stops:
                print(bus_stop)
                option = types.KeyboardButton(f"{bus_stop['name']}-{bus_stop['code']}")
                markup.add(option)
            userStep[cid] = 1
            bot.send_message(cid, f'You ID {message.from_user.id}', reply_markup=markup)


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def handel_user_bus_stop(message):
    cid = message.chat.id
    try:
        bus_stop_code = str(message.text).split('-')[1]
    except ValueError or IndexError:
        bot.send_message(cid, 'Bad select value.')
        return
    bot.send_chat_action(cid, 'typing')
    bus_stop = dict(get_bus_stop(bus_stop_code))
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_location(
        cid, latitude=bus_stop.get('latitude', 0), longitude=bus_stop.get('longitude', 0), reply_markup=markup
    )
    transports = bus_stop.get('timetable', None)
    if transports is not None and len(transports):
        msg = 'Transport list:\n'
        template = "{} {}-{},end_s:{}\n"
        for transport in transports:
            print('transport', transport)
            msg += template.format(
                get_bus_smile(transport['vehicle_type']),
                transport['route'],
                transport['time_left'],
                transport['end_stop']
            )
        bot.send_message(cid, msg)
    else:
        bot.send_message(cid, 'This bus station not have transports now.')
    userStep[cid] = 2


try:
    bot.polling()
except ConnectionError:
    print('ConnectionError')
