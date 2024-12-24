import aiosqlite
import asyncio

DB_NAME = 'quiz_bot.db'

async def func_return(cursor):
    # Возвращаем результат
    results = await cursor.fetchone()
    if results is not None:
        return results[0]
    else:
        return 0
    
    
async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect('quiz_bot.db') as db: # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER, rating_player INTEGER)''') # Сохраняем изменения
        await db.commit()

async def get_quiz_index(user_id, flag=False):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        if flag == False:
            async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
                return await func_return(cursor) 
        else:
            async with db.execute('SELECT rating_player FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
                return await func_return(cursor)

async def get_player_rating():
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id, rating_player FROM quiz_state ORDER BY rating_player DESC LIMIT 3') as cursor:
                # Возвращаем результат
                results = await cursor.fetchall()
                if results is not None:
                    return results
                else:
                    return 0
                         
async def update_quiz_index(user_id, index, flag=False):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        if  flag == False:
            await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index) VALUES (?, ?)', (user_id, index))
        else:
            await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, rating_player) VALUES (?, ?)', (user_id, index))
        # Сохраняем изменения
        await db.commit()