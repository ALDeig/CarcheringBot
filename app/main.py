import logging
import asyncio

from aiogram import Bot, Dispatcher, executor, filters
from aiogram.types import Message, ContentTypes
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.storage import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import API_TOKEN, CHAT_ID
from fsm import Form
from sheets import *


logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def send_to_admin(*args):
    """
    Отправляет сообщение администратору о том, что Бот запущен
    """
    await bot.send_message(chat_id=CHAT_ID, text='Бот запущен')


async def send_cars(*args):
    """
    Отправляет сообщение с машинами, которые не упоминались 2 недели и больше
    """
    text = get_cars_to_clear()
    await bot.send_message(chat_id=CHAT_ID, text=text)


async def send_total_day(*args):
    text = get_total_day()
    await bot.send_message(chat_id=CHAT_ID, text=text)


async def send_fuel_and_cars(*args):
    text = get_fuel_and_clear()
    await bot.send_message(chat_id=CHAT_ID, text=text)


@dp.message_handler(commands=['мойка'])
async def write_clear_car(message: Message):
    user_id_dict = get_dict_id()
    if str(message.from_user.id) in user_id_dict:
        initials = user_id_dict[str(message.from_user.id)]
    else:
        initials = '?'
    text = message.text.split()
    cell = get_cell(text[-1])
    if cell:
        write_value(cell, 'м', initials)
        await message.answer(f'Запись на машину "{text[-1]}" сохранена')
    else:
        await message.answer('Неверный запрос, повторите')


@dp.message_handler(commands=['заправка'])
async def write_fuel(message: Message, state: FSMContext):
    text = message.text.split()
    text[-1] = text[-1].replace(',', '.')
    user_id_dict = get_dict_id()
    if str(message.from_user.id) in user_id_dict:
        initials = user_id_dict[str(message.from_user.id)]
    else:
        initials = '?'
    if text[-1].replace('.', '').isdigit():
        cell = get_cell(text[-2])
        val = text[-1]
        if cell:
            if cell[-1] == '3' and cell[-2].isalpha():
                write_in_bak(cell=cell, value=val, initials=initials)
            else:
                write_value(cell, val, initials)
            await Form.next()
            await message.answer(f'Запись на машину "{text[-2]}" сохранена')
            await asyncio.sleep(30)
            data = await state.get_data()
            status = data.get('status')

            if status:
                pass
            else:
                await message.reply('Отправьте фото')
            await state.finish()
        else:
            await message.answer('Неверный номер машины')
    else:
        await message.answer('Неверный формат, повторите!')


@dp.message_handler(content_types=ContentTypes.PHOTO, state=Form.status)
async def get_photo_res(message: ContentTypes.PHOTO, state: FSMContext):
    await state.update_data(status=True)


@dp.message_handler(commands=['добавить'])
async def append_work(message: Message):
    """
    Принимает запрос на добавление техника в файл
    Формат сообещния "команда, id, инициалы
    :param message:
    :return:
    """
    id_worker = message.text.split()[-2]
    initials = message.text.split()[-1]
    res = append_worker(id_worker, initials)
    if res:
        await message.answer('Техник добавлен')


@dp.message_handler(commands=['запуск'])
async def write_start_car(message: Message):
    text = message.text.split()
    cell = get_cell(text[-1])
    if not cell:
        await message.answer('Неверный номер машины')
        return
    result = start_car(cell)
    if result:
        await message.answer('Машина отмечена')


@dp.message_handler(commands=['удалить'])
async def del_worker(message: Message):
    """
    Принимает запрос на удаление техника в файле.
    Формат сообщения: '\удалить id'
    """
    id_worker = message.text.split()[-1]
    res = delete_worker(id_worker)
    if res:
        await message.answer('Техник удален')


@dp.message_handler(commands=['техники'])
async def show_worker(message: Message):
    text = show_workers()
    await message.answer(text=text)


@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=[r'\w+\d*']))
async def other_commands(message: Message):
    await message.answer(text='Неверный формат. Повторите!')




if __name__ == '__main__':
    scheduler = AsyncIOScheduler()
    scheduler.start()
    scheduler.add_job(send_cars, 'cron', day='*', hour='8', minute='50')
    scheduler.add_job(send_fuel_and_cars, 'cron', day='*', hour='19', minute='30')
    scheduler.add_job(send_total_day, 'cron', day='*', hour='19', minute='35')
    scheduler.add_job(creat_total_json, 'cron', day='*', hour='5', minute='00')
    executor.start_polling(dp, skip_updates=True)

