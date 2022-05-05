from main_lite import bot
from aiogram import types
import psycopg2
from psycopg2 import Error
from os import getenv


def sql_start():
    global connection
    global cursor
    try:
        connection = psycopg2.connect(user="postgres",
                                      password=getenv("POSTGRESQL_PASSWORD"),
                                      host="127.0.0.1",
                                      port="5432",
                                      database="postgres")

        cursor = connection.cursor()
        create_table_query = '''CREATE TABLE IF NOT EXISTS CONTENT
                              (NAME TEXT PRIMARY KEY,
                              FILE_ID TEXT NOT NULL, FILE_TYPE TEXT NOT NULL, USER_ID NUMERIC,
                              DATE TIMESTAMP); '''
        cursor.execute(create_table_query)
        connection.commit()
        print("Таблица инициализована в PostgreSQL")

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)


async def sql_add_command(state):
    async with state.proxy() as data:
        val = tuple(data.values())
        cursor.execute(f"INSERT INTO content (name, file_id, file_type, user_id, date) "
                       f"VALUES ('{val[0]}', '{val[1]}', '{val[2]}','{val[3]}','{val[4]}')")
        connection.commit()


async def sql_read_command(message, file_name):
    cursor.execute(f"SELECT * FROM content WHERE name = '{file_name}'")
    rows = cursor.fetchall()
    for file_data in rows:
        if file_data[2] == 'photo':
            await bot.send_photo(message.from_user.id, file_data[1], reply_to_message_id=message.message_id)
        elif file_data[2] == 'video':
            await bot.send_video(message.from_user.id, file_data[1], reply_to_message_id=message.message_id)
        elif file_data[2] == 'document':
            await bot.send_document(message.from_user.id, file_data[1], reply_to_message_id=message.message_id)
        elif file_data[2] == 'animation':
            await bot.send_animation(message.from_user.id, file_data[1], reply_to_message_id=message.message_id)
        elif file_data[2] == 'audio':
            await bot.send_audio(message.from_user.id, file_data[1], reply_to_message_id=message.message_id)
        elif file_data[2] == 'sticker':
            await bot.send_sticker(message.from_user.id, file_data[1], reply_to_message_id=message.message_id)
        elif file_data[2] == 'voice':
            await bot.send_voice(message.from_user.id, file_data[1], reply_to_message_id=message.message_id)
        elif file_data[2] == 'video_note':
            await bot.send_video_note(message.from_user.id, file_data[1],
                                      reply_to_message_id=message.message_id)
        elif file_data[2] == 'text':
            await bot.send_message(message.from_user.id, file_data[1], reply_to_message_id=message.message_id)
        else:
            await bot.send_message(message.from_user.id, 'Ошибка при отправке. Неизвестный тип')


async def sql_names():
    total = list()
    cursor.execute('SELECT name FROM content')
    rows = cursor.fetchall()
    for ret in rows:
        total.append(ret[0])
    return total


async def sql_names_command(message):
    buttons = []
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cursor.execute('SELECT name FROM content')
    rows = cursor.fetchall()
    for ret in rows:
        buttons.append(ret[0])
    if len(buttons) == 0:
        await bot.send_message(message.from_user.id, "База данных пуста")
    else:
        keyboard.add(*buttons)
        await bot.send_message(message.from_user.id, "Выберите файл по названию", reply_markup=keyboard)
