#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""COPYPRINT.KZ - ПОЛНЫЙ БОТ"""

import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8342301001:AAHTuWsk315rzv9ijEcl-h5VF__QVAmJgSE"

LOCATIONS = {
    'spektr': {'name_ru': 'Copy Center Spektr', 'name_kk': 'Copy Center Spektr', 'name_en': 'Copy Center Spektr',
               'address': 'мкн Коктем-2, д.2', 'phone': '+7 771 143 5 143', 
               'hours_ru': '7:30-19:30 (Пн-Пт)', 'hours_kk': '7:30-19:30 (Дс-Жм)', 'hours_en': '7:30-19:30 (Mon-Fri)'},
    'copycenter': {'name_ru': 'CopyCenter', 'name_kk': 'CopyCenter', 'name_en': 'CopyCenter',
                   'address': 'мкн Коктем-2, д.2а', 'phone': '+7 776 136 7606',
                   'hours_ru': '9:00-17:00 (Пн-Пт)', 'hours_kk': '9:00-17:00 (Дс-Жм)', 'hours_en': '9:00-17:00 (Mon-Fri)'},
    'copyagrar': {'name_ru': 'CopyAgrar', 'name_kk': 'CopyAgrar', 'name_en': 'CopyAgrar',
                  'address': 'ул. Абая 8г/5', 'phone': '+7 777 586 8615',
                  'hours_ru': '8:00-17:00 (Пн-Пт)', 'hours_kk': '8:00-17:00 (Дс-Жм)', 'hours_en': '8:00-17:00 (Mon-Fri)'}
}

TEXTS = {
    'ru': {
        'welcome': '👋 Добро пожаловать в COPYPRINT.KZ!\n\n🌈 Ваш полный SPEKTR услуг\n\nВыберите язык:',
        'choose_location': '📍 Выберите ближайшую точку:',
        'choose_service': '🖨️ Что вам нужно?',
        'services': {'documents': '📄 Печать документов', 'polaroid': '📸 Фото Polaroid/Instax',
                     'diploma': '🏆 Создать грамоту', 'clean': '✨ Очистка текста AI',
                     'prices': '💰 Все цены'}
    },
    'kk': {
        'welcome': '👋 COPYPRINT.KZ-ге қош келдіңіз!\n\n🌈 Сіздің толық SPEKTR қызметтер\n\nТілді таңдаңыз:',
        'choose_location': '📍 Жақын нүктені таңдаңыз:',
        'choose_service': '🖨️ Сізге не керек?',
        'services': {'documents': '📄 Құжаттарды басып шығару', 'polaroid': '📸 Polaroid/Instax фото',
                     'diploma': '🏆 Грамота жасау', 'clean': '✨ AI мәтінді тазалау',
                     'prices': '💰 Барлық бағалар'}
    },
    'en': {
        'welcome': '👋 Welcome to COPYPRINT.KZ!\n\n🌈 Your full SPEKTR of services\n\nChoose language:',
        'choose_location': '📍 Choose nearest location:',
        'choose_service': '🖨️ What do you need?',
        'services': {'documents': '📄 Print documents', 'polaroid': '📸 Polaroid/Instax photos',
                     'diploma': '🏆 Create certificate', 'clean': '✨ AI text cleanup',
                     'prices': '💰 All prices'}
    }
}

user_data = {}

def clean_text_ai(text):
    """Умная очистка текста от мусора ChatGPT"""
    patterns = [r'Конечно[!,.]?\s*', r'Вот\s+(текст|вариант)[:\.]?\s*', r'Как вам\s+такой\s+вариант\??']
    for p in patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', re.sub(r'\n\n+', '\n\n', text)).strip()

def create_polaroid(image_path, style='polaroid'):
    """Создание Polaroid/Instax фото"""
    img = Image.open(image_path)
    if style == 'polaroid':
        frame = Image.new('RGB', (img.width + 40, img.height + 100), 'white')
        frame.paste(img, (20, 20))
    else:  # instax
        frame = Image.new('RGB', (img.width + 30, img.height + 30), 'white')
        frame.paste(img, (15, 15))
    return frame

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
                [InlineKeyboardButton("🇰🇿 Қазақша", callback_data='lang_kk')],
                [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')]]
    await update.message.reply_text(TEXTS['ru']['welcome'], reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if query.data.startswith('lang_'):
        lang = query.data.split('_')[1]
        user_data[user_id]['lang'] = lang
        keyboard = [[InlineKeyboardButton(f"📍 {LOCATIONS[k][f'name_{lang}']} - {LOCATIONS[k]['address']}", 
                                           callback_data=f'loc_{k}')] for k in LOCATIONS]
        await query.edit_message_text(TEXTS[lang]['choose_location'], reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith('loc_'):
        loc = query.data.split('_')[1]
        lang = user_data[user_id].get('lang', 'ru')
        user_data[user_id]['location'] = loc
        info = LOCATIONS[loc]
        keyboard = [[InlineKeyboardButton(TEXTS[lang]['services'][s], callback_data=f'srv_{s}')] 
                    for s in ['documents', 'polaroid', 'diploma', 'clean', 'prices']]
        await query.edit_message_text(
            f"✅ {info[f'name_{lang}']}\n📍 {info['address']}\n📞 {info['phone']}\n🕐 {info[f'hours_{lang}']}\n\n{TEXTS[lang]['choose_service']}",
            reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith('srv_'):
        service = query.data.split('_')[1]
        lang = user_data[user_id].get('lang', 'ru')
        
        if service == 'polaroid':
            keyboard = [[InlineKeyboardButton("📸 Polaroid (классический)", callback_data='style_polaroid')],
                        [InlineKeyboardButton("📸 Instax (квадратный)", callback_data='style_instax')]]
            await query.edit_message_text("Выберите стиль:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif service == 'diploma':
            await query.edit_message_text("🏆 Конструктор грамот\n\nИменная: 200₸\nУниверсальная: 2,000₸\n\nОтправьте текст для грамоты")
        elif service == 'clean':
            await query.edit_message_text("✨ Отправьте текст для очистки от мусора ChatGPT")
        elif service == 'prices':
            await query.edit_message_text("💰 ЦЕНЫ:\n\nЧ/Б: 30₸/стр\nЦветная (80г): от 100₸/стр\nPolaroid/Instax: 200₸\nГрамоты: от 200₸\nПереплет: от 500₸\n\n🌐 copyprint.kz")

    elif query.data.startswith('style_'):
        style = query.data.split('_')[1]
        user_data[user_id]['photo_style'] = style
        await query.edit_message_text(f"📸 Стиль: {style.capitalize()}\n\nОтправьте фото")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    cleaned = clean_text_ai(text)
    watermark = f"\n\n{'='*40}\n📄 COPYPRINT.KZ\n🌐 copyprint.kz\n📱 @spektr_almaty_bot\n{'='*40}"
    await update.message.reply_text(f"✅ Текст очищен!\n\n{cleaned}{watermark}\n\n💎 Убрать знак: 200₸")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    style = user_data.get(user_id, {}).get('photo_style', 'polaroid')
    await update.message.reply_text(f"📸 Обработка в стиле {style}...\n(Функция в разработке)\n\nПока приходите в точки!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    logger.info("🚀 БОТ ЗАПУЩЕН НА RAILWAY!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
