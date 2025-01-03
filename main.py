import random
from vkbottle.bot import Bot, Message
from vkbottle.dispatch.rules import ABCRule
from vkbottle import CtxStorage
from dotenv import load_dotenv
import os


class StartsWithRule(ABCRule[Message]):
    def __init__(self, text: str):
        self.text = text

    async def check(self, message: Message) -> bool:
        return message.text.lower().startswith(self.text)


class VKBot:
    def __init__(self, token):
        self.bot = Bot(token=token)
        self.ctx = CtxStorage()
        self.magic_ball_answers = [
            "Без сомнений.", "Определённо да.", "Несомненно.", "Да, однозначно.",
            "Можешь на это положиться.", "На мой взгляд, да.", "Скорее всего.",
            "Хорошие перспективы.", "Да.", "Знаки говорят – да.",
            "Ответ неясен, попробуй снова.", "Спроси позже.", "Лучше не рассказывать сейчас.",
            "Невозможно предсказать сейчас.", "Сосредоточься и спроси снова.",
            "Не рассчитывай на это.", "Мой ответ – нет.", "Мои источники говорят – нет.",
            "Перспективы не очень хорошие.", "Очень сомнительно."
        ]
        self.allowed_user_id = os.getenv("allowed_user_id")

    async def init_elimination_handler(self, message: Message):
        # Инициализация выбивания
        try:
            text = message.text.split(" ", 4)
            if len(text) < 4:
                await message.reply("Неверный формат. Пример: 'Бот убывание кто <...> login1, login2, login3'")
                return

            description = text[3]
            members = text[4].split(", ")
            self.ctx.set(f"elimination_{message.peer_id}", {"description": description, "members": members})
            members_list = "\n".join(f"{i + 1}. {member}" for i, member in enumerate(members))
            await message.reply(f"Кто останется, тот {description}:\n{members_list}")
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

    async def eliminate_one_handler(self, message: Message):
        # Удаление одного участника
        elimination_data = self.ctx.get(f"elimination_{message.peer_id}")
        if not elimination_data:
            await message.reply("Процесс выбивания не начат. Используйте 'Бот убывание кто <...> login1, login2, login3'.")
            return

        members = elimination_data["members"]
        removed = random.choice(members)
        members.remove(removed)
        elimination_data["members"] = members
        self.ctx.set(f"elimination_{message.peer_id}", elimination_data)

        members_list = "\n".join(f"{i + 1}. {member}" for i, member in enumerate(members))
        if len(members) > 1:
            await message.reply(f"Участник {removed} выбыл!\nОставшиеся:\n{members_list}")
        else:
            await message.reply(f"Игра окончена, {elimination_data['description']} определён! Это {members[0]}")

    async def magic_ball_handler(self, message: Message):
        await message.reply(random.choice(self.magic_ball_answers))

    async def get_random_members(self, peer_id: int, count: int = 5):
        members = await self.bot.api.messages.get_conversation_members(peer_id=peer_id)
        active_members = [
            member for member in members.items
            if not getattr(member, "is_restricted_to_write", False)
        ]
        admin_members = [
            member for member in members.items
            if getattr(member, "is_admin", False)
        ]
        active_profiles = [
            profile for profile in members.profiles
            if profile.id in [member.member_id for member in active_members]
        ]
        admin_profiles = [
            profile for profile in members.profiles
            if profile.id in [member.member_id for member in admin_members]
        ]
        if len(active_profiles) <= count:
            return {
                'members': [
                    {"id": user.id, "name": f"{user.first_name} {user.last_name}"} 
                    for user in active_profiles
                ],
                'admins': [
                    {"id": user.id, "name": f"{user.first_name} {user.last_name}"} 
                    for user in admin_profiles
                ]
            }
        random_profiles = random.sample(active_profiles, count)
        return {
            'members': [
                {"id": user.id, "name": f"{user.first_name} {user.last_name}"} 
                for user in random_profiles
            ],
            'admins': [
                {"id": user.id, "name": f"{user.first_name} {user.last_name}"} 
                for user in admin_profiles
            ]
        }

    async def get_info_handler(self, message: Message):
        msg = ("""Доступные команды:

1. Бот список <что-то> - Возвращает 5 случайных участников.
2. Бот кто <кто-то> - Возвращает одного случайного участника.
3. Бот инфа <на что-то> - Возвращает процент от 0 до 100.
4. Бот шар <что-то> - Классический шар предсказаний «8» (Magic 8-Ball).
5. [Только для админов] Бот кик <ссылка на пользователя> - Исключает пользователя из чата.""")
        await message.reply(msg)

    async def random_members_handler(self, message: Message):
        try:
            random_members = await self.get_random_members(message.peer_id)
            random_members = random_members['members']
            result = "\n".join(f"{i + 1}. {member['name']}" for i, member in enumerate(random_members))
            await message.reply(result)
        except Exception as e:
            await message.reply(f"Не удалось получить участников: {e}")

    async def one_random_member_handler(self, message: Message):
        try:
            random_member = await self.get_random_members(message.peer_id)
            random_member = random_member['members']
            result = f"{random_member[0]['name']}"
            await message.reply(result)
        except Exception as e:
            await message.reply(f"Не удалось определить участника: {e}")

    async def determination_of_probability_handler(self, message: Message):
        try:
            random_number = random.randint(0, 100)
            result = f"{random_number}%"
            await message.reply(result)
        except Exception as e:
            await message.reply(f"Не удалось получить вероятность: {e}")

    async def get_user_id_by_link(self, user_link: str):
        username = user_link.split("/")[-1]
        try:
            user_info = await self.bot.api.users.get(user_ids=username)
            return user_info[0].id if user_info else None
        except Exception as e:
            print(f"Ошибка при получении информации о пользователе: {e}")

    async def temp_ban_handler(self, message: Message, any: str):
        admins = await self.get_random_members(message.peer_id)
        admins = admins['admins']
        admin_ids = [self.allowed_user_id] + [admin['id'] for admin in admins]
        if message.from_id not in admin_ids:
            return
        user_id = await self.get_user_id_by_link(any.strip())
        try:
            await self.bot.api.messages.remove_chat_user(
                chat_id=message.peer_id - 2000000000,
                member_id=user_id
            )
        except:
            await message.reply(f"Не удалось найти ID пользователя по ссылке {any}.")

    def register_handlers(self):
        self.bot.on.message(StartsWithRule("бот убывание кто"))(self.init_elimination_handler)
        self.bot.on.message(StartsWithRule("бот минус один"))(self.eliminate_one_handler)
        self.bot.on.message(StartsWithRule("бот шар"))(self.magic_ball_handler)
        self.bot.on.message(StartsWithRule("бот инфо"))(self.get_info_handler)
        self.bot.on.message(StartsWithRule("бот список"))(self.random_members_handler)
        self.bot.on.message(StartsWithRule("бот кто"))(self.one_random_member_handler)
        self.bot.on.message(StartsWithRule("бот инфа"))(self.determination_of_probability_handler)
        self.bot.on.message(StartsWithRule("бот кик"))(self.temp_ban_handler)

    def run(self):
        self.register_handlers()
        self.bot.run_forever()

if __name__ == "__main__":
    load_dotenv(dotenv_path='/root/main/vk_bot/.env')
    vk_bot = VKBot(token=os.getenv("token"))
    vk_bot.run()
