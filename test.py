from vkbottle.bot import Bot, Message
from vkbottle import CtxStorage
import random


bot = Bot(token = "vk1.a.B1eSGaeJGstXcosuDIYw3x013Ok57qocqZFLW1bgQVlw4Qa-2WBwkC_x6w60fuXDdNife6BXFdGeOrlDxRf-BFfYDnv_Otd2LMgOPLw-k8Kn4cUzK_Ui2LNu2U_WQaxNUxFugi1j4N06gaqQt28gBGYY6op-Ov4yWJ61rLOEl9lCVB6L8N01RYRXnQAjUgIS2CeHI8A6R-qtHKvaV5AXdw")
ctx = CtxStorage()


ALLOWED_USER_ID = 505612959

answers = [
    "Без сомнений.", "Определённо да.", "Несомненно.", "Да, однозначно.",
    "Можешь на это положиться.", "На мой взгляд, да.", "Скорее всего.",
    "Хорошие перспективы.", "Да.", "Знаки говорят – да.",
    "Ответ неясен, попробуй снова.", "Спроси позже.", "Лучше не рассказывать сейчас.",
    "Невозможно предсказать сейчас.", "Сосредоточься и спроси снова.",
    "Не рассчитывай на это.", "Мой ответ – нет.", "Мои источники говорят – нет.",
    "Перспективы не очень хорошие.", "Очень сомнительно."
]


@bot.on.message(text="Бот шар <any>")
async def magic_ball_handler(message: Message):
    await message.reply(random.choice(answers))


async def get_random_members(peer_id: int, count: int = 5):
    members = await bot.api.messages.get_conversation_members(peer_id=peer_id)

    # Фильтруем только тех, кто активен (не имеет ограничений)
    active_members = [
        member for member in members.items
        if not getattr(member, "is_restricted_to_write", False)
    ]
    admin_members = [
        member for member in members.items
        if getattr(member, "is_admin", False)
    ]

    # Получаем список профилей активных участников
    active_profiles = [
        profile for profile in members.profiles
        if profile.id in [member.member_id for member in active_members]
    ]

    admin_profiles = [
        profile for profile in members.profiles
        if profile.id in [member.member_id for member in admin_members]
    ]

    # Если участников меньше, чем нужно выбрать, возвращаем всех
    if len(active_profiles) <= count:
        return {'members': [{"id": user.id, "name": f"{user.first_name} {user.last_name}"} for user in active_profiles],
                'admins': [{"id": user.id, "name": f"{user.first_name} {user.last_name}"} for user in admin_profiles]}

    # Выбираем случайных участников
    random_profiles = random.sample(active_profiles, count)

    return {'members': [{"id": user.id, "name": f"{user.first_name} {user.last_name}"} for user in random_profiles],
            'admins': [{"id": user.id, "name": f"{user.first_name} {user.last_name}"} for user in admin_profiles]}


@bot.on.message(text="/инфо")
async def get_info(message: Message):
    msg = """Доступные команды:

1. Бот список <что-то> - Возвращает 5 случайных участников.
2. Бот кто <кто-то> - Возвращает одного случайного участника.
3. Бот инфа <на что-то> - Возвращает процент от 0 до 100.
4. Бот шар <что-то> - Классический шар предсказаний «8» (Magic 8-Ball).
5. [Только для админов] Бот кик <ссылка на пользователя> - Исключает пользователя из чата."""
    await message.reply(msg)


@bot.on.message(text="Бот список <any>")
async def random_members_handler(message: Message):
    try:
        random_members = await get_random_members(message.peer_id)
        random_members = random_members['members']
        result = ""
        num = 0
        for member in random_members:
            num+=1
            result += f"{num}. {member['name']}\n"
        await message.reply(result)
    except Exception as e:
        await message.reply(f"Не удалось получить участников123: {e}")


@bot.on.message(text="Бот кто <any>")
async def one_random_member_handler(message: Message):
    try:
        random_member = await get_random_members(message.peer_id)
        random_member = random_member['members']
        result = f"{random_member[0]['name']}"
        await message.reply(result)
    except Exception as e:
        await message.reply(f"Не удалось определить участника: {e}")


@bot.on.message(text="Бот инфа <any>")
async def determination_of_probability_handler(message: Message):
    try:
        random_number = random.randint(0, 100)
        result = f"{random_number}%"
        await message.reply(result)
    except Exception as e:
        await message.reply(f"Не удалось получить вероятность: {e}")


async def get_user_id_by_link(user_link: str):
    # Извлекаем логин из ссылки
    username = user_link.split("/")[-1]  # Получаем часть после "vk.com/"

    try:
        # Получаем информацию о пользователе по логину
        user_info = await bot.api.users.get(user_ids=username)
        
        if user_info:
            return user_info[0].id  # Возвращаем ID пользователя
        else:
            return None  # Если пользователь не найден
    except Exception as e:
        print(f"Ошибка при получении информации о пользователе: {e}")
        return None


@bot.on.message(text="Бот кик <any>")
async def temp_ban_handler(message: Message, any: str):
    admins = await get_random_members(message.peer_id)
    admins = admins['admins']
    admin_ids = [ALLOWED_USER_ID]
    for admin in admins:
        admin_ids.append(admin['id'])
    if message.from_id not in admin_ids:
        return
    user_link = str(any).strip()
    user_id = await get_user_id_by_link(user_link)
    try:
        await bot.api.messages.remove_chat_user(
            chat_id=message.peer_id - 2000000000,
            member_id=user_id
        )
    except:
        await message.reply(f"Не удалось найти ID пользователя по ссылке {user_link}.")


if __name__ == "__main__":
    bot.run_forever()
