from database.orm_query import orm_get_products
from custom_filters.chat_types import ChatTypeFilter
from aiogram import types, Router, F
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession

from keybrds import reply

# Additional router
user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))


# Start Handler
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer("Дарова, я помічничок", 
                         reply_markup=reply.get_keyboard
                         (
                             "Меню",
                             "Інфо",
                             "Допомога",
                             "Оплата",
                             placeholder='Що вас цікавить?',
                             sizes=(2,2)
                         ),
                        )


# Some Text handelrs for managing data
@user_private_router.message(F.text.lower() == 'меню')
async def menu_cmd(message: types.Message, session: AsyncSession):
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image,
            caption=f'<strong>{product.name}\
                </strong>\n{product.description}\nЦіна: {round(product.price, 2)}грн',
                parse_mode='HTML'
        )
    await message.answer('Меню:')


@user_private_router.message(F.text.lower() == 'допомога')
async def help_cmd(message: types.Message):
    await message.answer('Допомога')


@user_private_router.message(F.text.lower() == 'інфо')
async def about_cmd(message: types.Message):
    await message.answer('Про нас:')


@user_private_router.message(F.text.lower() == 'оплата')
async def payments_cmd(message: types.Message):
    await message.answer('Способи оплати:')
        
        
# Handlers for sending contacts and locations
@user_private_router.message(F.contact)
async def contact_cmd(message: types.Message):
    await message.answer('Контакт отримано')
    await message.answer(str(message.contact))


@user_private_router.message(F.location)
async def location_cmd(message: types.Message):
    await message.answer('Гео отримано')
    await message.answer(str(message.location))