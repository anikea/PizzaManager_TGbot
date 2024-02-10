# File for using bot in private messages like Administrator

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, or_f
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import orm_add_product, orm_get_products, orm_get_product, orm_update_product, orm_delete_product
from keybrds.inline import get_callback_btns
from custom_filters.chat_types import ChatTypeFilter, isAdmin
from keybrds.reply import get_keyboard


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), isAdmin())


ADMIN_KB = get_keyboard(
    "Додати товар",
    "Асортимент",
    placeholder="Оберіть дію",
    sizes=(2, ),
)


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    image = State()
    
    product_for_change = None
    
    texts = {
        'AddProduct:name': 'Введіть назву товару знову:',
        'AddProduct:description': 'Введіть опис знову:',
        'AddProduct:price': 'Введіть вартість знову:',
        'AddProduct:image': 'Останній стан',
    }
    

@admin_router.message(Command("admin"))
async def add_product(message: types.Message):
    await message.answer("Що хотіли б зробити?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == "Асортимент")
async def starring_at_product(message: types.Message, session: AsyncSession):
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image,
            caption=f'<strong>{product.name}\
                </strong>\n{product.description}\nЦіна: {round(product.price, 2)}грн',
                parse_mode='HTML',
                reply_markup=get_callback_btns(btns={
                    'Видалити товар': f'delete_{product.id}',
                    'Змінити товар': f'change_{product.id}'
                })
        )
    
    await message.answer("ОК, ось список товарів ⬆️")
    

@admin_router.callback_query(F.data.startswith('delete_'))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    
    product_id = callback.data.split('_')[-1]
    await orm_delete_product(session, int(product_id))
    
    await callback.answer("Товар видалено")
    await callback.message.answer("Товар видалено!")


@admin_router.callback_query(StateFilter(None), F.data.startswith('change_'))
async def change_product(callback: types.CallbackQuery, state:FSMContext, session: AsyncSession):
    product_id = callback.data.split('_')[-1]
    product_for_change = await orm_get_product(session, int(product_id))
    
    AddProduct.product_for_change = product_for_change
    await callback.answer()
    await callback.message.answer(
        'Введіть назву товару', reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.name)

#Код для машини станів (FSM)


@admin_router.message(StateFilter(None), F.text == "Додати товар")
async def add_product(message: types.Message, state: FSMContext):
    await message.answer(
        "Введіть назву товару", reply_markup=types.ReplyKeyboardRemove()
    )
    
    await state.set_state(AddProduct.name)


@admin_router.message(StateFilter('*'), Command("cancel"))
@admin_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddProduct.product_for_change:
        AddProduct.product_for_change = None
    
    await state.clear()
    await message.answer("Дії скасовано", reply_markup=ADMIN_KB)


@admin_router.message(StateFilter('*'), Command("back"))
@admin_router.message(F.text.casefold() == "back")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == AddProduct.name:
        await message.answer("Ви повернулись на початок, введіть назву товару або введіть '/cancel'")
    
    previous = None
    
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"добре, ви повернулись на крок назад \n {AddProduct.texts[previous.state]}")
            return
        previous = step

@admin_router.message(AddProduct.name, or_f(F.text, F.text == "."))
async def add_name(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(name=AddProduct.product_for_change.name)
    else:
        if len(message.text) >= 100:
            await message.answer(
                'Надто довгий опис.\nВведіть наново'
            )
            return
        await state.update_data(name=message.text)
    await message.answer("Введіть опис товару")
    await state.set_state(AddProduct.description) 


@admin_router.message(AddProduct.description, or_f(F.text, F.text == "."))
async def add_description(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(description=AddProduct.product_for_change.description)
    else:
        await state.update_data(description=message.text)
    await message.answer("Введіть ціну товару")
    await state.set_state(AddProduct.price)


@admin_router.message(AddProduct.description)
async def add_description2(message: types.Message, state: FSMContext):
    await message.answer("Незрозумілі дані, введіть норм текст")


@admin_router.message(AddProduct.price, or_f(F.text, F.text == "."))
async def add_price(message: types.Message, state: FSMContext):
    if message.text == ".":
        await state.update_data(price=AddProduct.product_for_change.price)
    else:
        try:
            float(message.text)
        except ValueError:
            await message.answer("Введіть коректну ціну")
            return

        await state.update_data(price=message.text)
    await message.answer("Завантажте фотографію товару")
    await state.set_state(AddProduct.image)


@admin_router.message(AddProduct.price)
async def add_price2(message: types.Message, state: FSMContext):
    await message.answer("Ви ввели помилкову ціну")


@admin_router.message(AddProduct.image, or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == ".":
        await state.update_data(image=AddProduct.product_for_change.image)

    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    try:
        if AddProduct.product_for_change:
            await orm_update_product(session, AddProduct.product_for_change.id, data)
        else:
            await orm_add_product(session, data)
        await message.answer("Товар додано/змінено", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        await message.answer(
            f"Помилка: \n{str(e)}\Зверніться до сис адміна",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    AddProduct.product_for_change = None  


@admin_router.message(AddProduct.image)
async def add_image2(message: types.Message, state: FSMContext):
    await message.answer("Відправте фотографію")
