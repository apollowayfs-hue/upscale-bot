import logging
import asyncio
import aiohttp
import aiofiles
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode

BOT_TOKEN = ‘8632120800:AAEOBHQ8A4vJyu2ovH8uEBbiS5bboFFJJ3k’
REPLICATE_TOKEN = ‘r8_2iazjxaLWCrgbQHr5Rbvon8AhArGfEl0yOXfS’

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
await message.answer(
‘Привет! Я бот для улучшения качества фото.\n\n’
‘Просто отправь мне фото и я увеличу его разрешение в 4 раза с помощью AI!\n\n’
‘Используется модель Real-ESRGAN’
)

@dp.message(F.photo)
async def handle_photo(message: types.Message):
await message.answer(‘Обрабатываю фото, подождите 20-40 секунд...’)

```
photo = message.photo[-1]
file = await bot.get_file(photo.file_id)
file_url = 'https://api.telegram.org/file/bot' + BOT_TOKEN + '/' + file.file_path

try:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://api.replicate.com/v1/predictions',
            headers={
                'Authorization': 'Token ' + REPLICATE_TOKEN,
                'Content-Type': 'application/json',
            },
            json={
                'version': '42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b',
                'input': {
                    'image': file_url,
                    'scale': 4,
                    'face_enhance': False,
                },
            },
        ) as resp:
            if resp.status != 201:
                await message.answer('Ошибка запуска. Попробуйте позже.')
                return
            prediction = await resp.json()
            prediction_id = prediction['id']

        result_url = None
        for _ in range(60):
            await asyncio.sleep(3)
            async with session.get(
                'https://api.replicate.com/v1/predictions/' + prediction_id,
                headers={'Authorization': 'Token ' + REPLICATE_TOKEN},
            ) as r:
                data = await r.json()
                status = data.get('status')
                if status == 'succeeded':
                    result_url = data['output']
                    break
                elif status == 'failed':
                    await message.answer('Обработка не удалась. Попробуйте другое фото.')
                    return

        if not result_url:
            await message.answer('Превышено время ожидания. Попробуйте позже.')
            return

        async with session.get(result_url) as img_resp:
            img_data = await img_resp.read()

        tmp_path = 'upscaled_' + str(message.from_user.id) + '.png'
        async with aiofiles.open(tmp_path, 'wb') as f:
            await f.write(img_data)

        doc = types.FSInputFile(tmp_path)
        await message.answer_document(
            doc,
            caption='Готово! Фото улучшено в 4x разрешении.'
        )
        os.remove(tmp_path)

except Exception as e:
    logger.exception('Error: %s', e)
    await message.answer('Что-то пошло не так. Попробуйте позже.')
```

@dp.message(F.document)
async def handle_doc(message: types.Message):
await message.answer(
‘Пожалуйста, отправьте фото как фотографию, а не как файл.\n’
‘В Telegram нажмите на скрепку и выберите Фото или видео’
)

async def main():
logger.info(‘Bot started’)
await dp.start_polling(bot)

if __name__ == ‘__main__’:
asyncio.run(main())
