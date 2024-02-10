# File for using bot in groups/supergroups

from string import punctuation
from aiogram import types, Router, Bot
from aiogram.filters import Command
from custom_filters.chat_types import ChatTypeFilter


# Additional Router
user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))


# Banned words in groups
res_words = {'додік', 'кабан', 'свиня', 'лох', 'дурак'}


# Removing banned words
def clean_text(text: str):
    return text.translate(str.maketrans('', '', punctuation))


# Handlers for commands 
@user_group_router.message(Command("admin"))
async def get_admins(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)

    # generator
    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == "creator" or member.status == "administrator"
    ]
    bot.my_admins_list = admins_list
    if message.from_user.id in admins_list:
        await message.delete()

          
@user_group_router.edited_message()
@user_group_router.message()
async def cleaner(message: types.Message):
    if res_words.intersection(clean_text(message.text.lower()).split()):
        await message.answer(f'{message.from_user.first_name}, ти чо , а ну виражайся культурно')
        await message.delete()