from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class KeyboardFactory:
    """Фабрика клавиатур для бота"""
    
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Создание главного меню"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Финансы", callback_data="menu:finances"),
                InlineKeyboardButton(text="⚖️ Вес и сон", callback_data="menu:health")
            ],
            [
                InlineKeyboardButton(text="🏋️‍♂️ Тренировки", callback_data="menu:workout"),
                InlineKeyboardButton(text="🎯 Цели", callback_data="menu:goals")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="menu:stats"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings")
            ]
        ])

    @staticmethod
    def get_finances_menu() -> InlineKeyboardMarkup:
        """Меню финансового раздела"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Доход", callback_data="finance:income"),
                InlineKeyboardButton(text="➖ Расход", callback_data="finance:expense")
            ],
            [
                InlineKeyboardButton(text="💳 Баланс", callback_data="finance:balance"),
                InlineKeyboardButton(text="🔄 История", callback_data="finance:history")
            ],
            [
                InlineKeyboardButton(text="🏦 Накопления", callback_data="finance:savings"),
                InlineKeyboardButton(text="📋 Категории", callback_data="finance:categories")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")
            ]
        ])

    @staticmethod
    def get_health_menu() -> InlineKeyboardMarkup:
        """Меню раздела веса и сна"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⚖️ Записать вес", callback_data="health:weight"),
                InlineKeyboardButton(text="😴 Записать сон", callback_data="health:sleep")
            ],
            [
                InlineKeyboardButton(text="📈 График веса", callback_data="health:weight_graph"),
                InlineKeyboardButton(text="📊 Анализ сна", callback_data="health:sleep_analysis")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")
            ]
        ])

    @staticmethod
    def get_workout_menu() -> InlineKeyboardMarkup:
        """Меню раздела тренировок"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Записать упражнение", callback_data="workout:add"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="workout:stats")
            ],
            [
                InlineKeyboardButton(text="📋 История тренировок", callback_data="workout:history"),
                InlineKeyboardButton(text="💪 Рекорды", callback_data="workout:records")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")
            ]
        ])

    @staticmethod
    def get_goals_menu() -> InlineKeyboardMarkup:
        """Меню раздела целей"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Новая цель", callback_data="goals:new")
            ],
            [
                InlineKeyboardButton(text="📋 Активные цели", callback_data="goals:active"),
                InlineKeyboardButton(text="✅ Достигнутые", callback_data="goals:completed")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")
            ]
        ])

    @staticmethod
    def get_settings_menu() -> InlineKeyboardMarkup:
        """Меню настроек"""
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Округление", callback_data="settings:rounding"),
                InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings:notifications")
            ],
            [
                InlineKeyboardButton(text="📊 Формат отчетов", callback_data="settings:reports"),
                InlineKeyboardButton(text="⌚️ Часовой пояс", callback_data="settings:timezone")
            ],
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")
            ]
        ])