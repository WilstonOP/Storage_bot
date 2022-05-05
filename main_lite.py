import logging
from aiogram import Bot, Dispatcher, executor, types
from os import getenv
from sys import exit
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import database
import re

bot_token = getenv("BOT_TOKEN")
if not bot_token:
    exit("Ошибка, токен отсутствует")

bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)


class Order_load(StatesGroup):
    name = State()
    photo = State()


class Order_view(StatesGroup):
    choose = State()


@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    await message.answer("Выберите действие", reply_markup=keyboard)


@dp.message_handler(text="Показать")
async def without_puree(message: types.Message, state=None):
    await Order_view.choose.set()
    await database.sql_names_command(message)
    if len(await database.sql_names()) == 0:
        await cancel_handler(message, state)
        await message.answer("Попробуйте сначала загрузить какой-либо файл.")


@dp.message_handler(state=Order_view.choose)
async def process_name(message: types.Message, state: FSMContext):
    if message.text not in await database.sql_names():
        await message.answer("Пожалуйста, выберите файл, используя клавиатуру ниже.")
        return
    photo_name = message.text
    await database.sql_read_command(message, photo_name)
    await state.finish()
    await cmd_start(message)


@dp.message_handler(text="Загрузить")
async def without_puree(message: types.Message, state=None):
    await Order_load.name.set()
    await message.reply("Напишите название файла", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=['help'])
async def help_handler(message: types.Message):
    await message.reply("Используйсте кнопки снизу для навигации.\nДля отмены загрузки, напишите 'отмена'\n"
                        "Для начала работы введите /start.\n"
                        "Принимаемые типы файлов: аудио, документ, анимация(gif), фото, видео, текст")


@dp.message_handler(state=Order_load.name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text in await database.sql_names():
        await message.answer("Пожалуйста, выберите уникальное название")
        return
    if len(message.text) > 18:
        await message.answer("Размер названия не должен превышать 18 символов")
        return
    if re.search(r'[^a-zA-Zа-яА-Я0-9_ёЁ]', message.text):
        await message.answer("Название должно состоять из кириллицы, латинских букв, цифр и '_'")
        return
    await message.answer("Теперь отправьте ваш файл ('отмена' для отмены действия)")
    async with state.proxy() as data:
        data['name'] = message.text
    await Order_load.next()


@dp.message_handler(content_types=['photo', 'video', 'document', 'animation',
                                   'audio', 'text', 'sticker', 'video_note', 'voice'], state=Order_load.photo)
async def process_file(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.content_type == 'video':
            data['id'] = message.video.file_id
            data['type'] = 'video'
        elif message.content_type == 'photo':
            data['id'] = message.photo[0].file_id
            data['type'] = 'photo'
        elif message.content_type == 'audio':
            data['id'] = message.audio.file_id
            data['type'] = 'audio'
        elif message.content_type == 'animation':
            data['id'] = message.animation.file_id
            data['type'] = 'animation'
        elif message.content_type == 'voice':
            data['id'] = message.voice.file_id
            data['type'] = 'voice'
        elif message.content_type == 'sticker':
            data['id'] = message.sticker.file_id
            data['type'] = 'sticker'
        elif message.content_type == 'video_note':
            data['id'] = message.video_note.file_id
            data['type'] = 'video_note'
        elif message.content_type == 'document':
            data['id'] = message.document.file_id
            data['type'] = 'document'
        elif message.content_type == 'text':
            data['id'] = message.text
            data['type'] = 'text'
        data['user'] = message.from_user.id
        data['time'] = str(message.date)
    try:
        await database.sql_add_command(state)
        await message.reply(str(data))
        await bot.send_message(message.chat.id, 'Успешно загружено', reply_markup=keyboard)
        await state.finish()
    except IndexError:
        await state.finish()


@dp.message_handler(state='*', commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):

    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Отмена действия', reply_markup=keyboard)


@dp.message_handler(lambda m: True)
async def echo_all(message: types.Message):
    await message.reply("Пожалуйста, используйте клавиатуру снизу")

if __name__ == "__main__":
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Загрузить", "Показать"]
    keyboard.add(*buttons)
    database.sql_start()
    executor.start_polling(dp, skip_updates=True)
