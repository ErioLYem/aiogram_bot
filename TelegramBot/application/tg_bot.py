import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.filters.command import Command
from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import F
import savedata
import questions_quiz_data
from dotenv import load_dotenv
import os

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

load_dotenv()
API_TOKEN = os.getenv('TOKEN')


# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()

quiz_data = questions_quiz_data.quiz_data
count_answers = 0

def generate_options_keyboard(answer_options, right_answer):
    st = ''
    builder = InlineKeyboardBuilder()
    for option in answer_options:
        if option == right_answer:
            st = "right_answer"
        else:
            st = "wrong_answer"
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f'{st}:{answer_options.index(option)}')
        )
        

    builder.adjust(1)
    return builder.as_markup()

async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    await savedata.update_quiz_index(user_id, current_question_index)

    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)

async def get_question(message, user_id):

    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await savedata.get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = quiz_data[current_question_index]['correct_option']
    # Получаем список вариантов ответа для текущего вопроса
    opts = quiz_data[current_question_index]['options']

    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)

async def one_chapter(callback: types.CallbackQuery, current_question_index):
    # редактируем текущее сообщение с целью убрать кнопки (reply_markup=None)
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    s = callback.data.split(':')[1]
    await callback.message.answer(f"Ваш ответ: {quiz_data[current_question_index]['options'][int(s)]}")
    
async def two_chapter(callback: types.CallbackQuery, current_question_index):
    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await savedata.update_quiz_index(callback.from_user.id, current_question_index)
    # Проверяем достигнут ли конец квиза
    if current_question_index < len(quiz_data):
        # Следующий вопрос
        await get_question(callback.message, callback.from_user.id)
    else:
        # Уведомление об окончании квиза
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        await callback.message.answer(f"Вы ответили правильно {count_answers}/{len(quiz_data)}")
        await savedata.update_quiz_index(callback.from_user.id, count_answers, flag=True)

@dp.callback_query(F.data.contains("right_answer"))
async def right_answer(callback: types.CallbackQuery):
    global count_answers
    # Получение текущего вопроса для данного пользователя
    current_question_index = await savedata.get_quiz_index(callback.from_user.id)
    await one_chapter(callback, current_question_index)
    # Отправляем в чат сообщение, что ответ верный
    await callback.message.answer("Верно!")
    count_answers += 1
    await two_chapter(callback, current_question_index)

@dp.callback_query(F.data.contains("wrong_answer"))
async def wrong_answer(callback: types.CallbackQuery):
    global count_answers
    # Получение текущего вопроса для данного пользователя
    current_question_index = await savedata.get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']
    await one_chapter(callback, current_question_index)
    # Отправляем в чат сообщение об ошибке с указанием верного ответа
    await callback.message.answer(f"Неправильно. Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")
    await two_chapter(callback, current_question_index)

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))

# Хэндлер на команды /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    global count_answers
    # Отправляем новое сообщение без кнопок
    await message.answer(f"Давайте начнем квиз!")
    count_answers = 0
    # Запускаем новый квиз
    await new_quiz(message)

# Хэндлер на команды /ratingplayer
@dp.message(Command("ratingplayer"))
async def rating_quiz(message: types.Message):
    # Отправляем новое сообщение без кнопок
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id
    quiz_rating_player = await savedata.get_quiz_index(user_id, flag=True)
    await message.answer(f"Здравствуйте, {message.from_user.first_name}! Ваш последний результат: {quiz_rating_player}/{len(quiz_data)}!")

# Хэндлер на команды /ratingall
@dp.message(Command("ratingall"))
async def rating_quiz_all(message: types.Message):
    quiz_rating_player = await savedata.get_player_rating()
    print(quiz_rating_player)
    await message.answer(f"Рейтинг игроков:")
    j = 1
    for pair in quiz_rating_player:
        await message.answer(f'{j}. {" -> ".join(map(str, pair))}')
        j += 1
    
# Запуск процесса поллинга новых апдейтов
async def main():
    # Запускаем создание таблицы базы данных
    await savedata.create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())