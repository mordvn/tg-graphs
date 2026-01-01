"""
Love Language Analyzer
Анализирует "языки любви" в переписке:
- Слова одобрения (комплименты, поддержка)
- Качественное время (планирование встреч)
- Подарки (обсуждение)
- Акты служения (помощь, забота)
- Физическое прикосновение (упоминания)
"""
from collections import defaultdict, Counter
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

# Маркеры языков любви
WORDS_OF_AFFIRMATION = {
    # Комплименты
    'красивая', 'красивый', 'красотка', 'красавчик', 'gorgeous', 'beautiful', 'handsome',
    'умница', 'умный', 'умная', 'smart', 'талантливый', 'талантливая',
    'молодец', 'proud', 'горжусь', 'amazing', 'incredible', 'wonderful',
    # Поддержка
    'верю в тебя', 'ты справишься', 'ты сможешь', 'все получится', 'поддерживаю',
    'ты лучший', 'ты лучшая', 'ты особенный', 'ты особенная',
    # Благодарность
    'спасибо', 'благодарю', 'ценю', 'appreciate', 'grateful',
    # Выражение чувств
    'люблю', 'обожаю', 'нравишься', 'love', 'adore', 'скучаю', 'miss you',
}

QUALITY_TIME = {
    # Планирование встреч
    'давай встретимся', 'хочу увидеть', 'когда увидимся', 'скоро увидимся',
    'пойдём', 'пойдем', 'сходим', 'поехали', 'поедем',
    # Места
    'ресторан', 'кино', 'кафе', 'парк', 'прогулка', 'погулять', 'гулять',
    'вместе', 'together', 'вдвоём', 'вдвоем',
    # Время
    'выходные', 'weekend', 'вечер', 'evening', 'свидание', 'date',
    'проведём время', 'проведем время', 'время вместе',
}

ACTS_OF_SERVICE = {
    # Помощь
    'помогу', 'помочь', 'помощь', 'help', 'сделаю для тебя',
    'приготовлю', 'готовлю', 'cook', 'уберу', 'clean',
    # Забота
    'позабочусь', 'забочусь', 'care', 'принесу', 'привезу', 'куплю',
    'отвезу', 'встречу', 'провожу',
    # Решение проблем
    'разберусь', 'решу', 'займусь', 'сделаю',
    'не беспокойся', 'не переживай', 'я разберусь',
}

GIFTS = {
    # Подарки
    'подарок', 'gift', 'present', 'сюрприз', 'surprise',
    # Покупки
    'купил', 'купила', 'куплю', 'bought', 'buy',
    'заказал', 'заказала', 'order',
    # Цветы
    'цветы', 'flowers', 'букет', 'roses', 'розы',
}

PHYSICAL_TOUCH = {
    # Объятия
    'обнимаю', 'обнять', 'hug', 'обнимашки', 'cuddle',
    # Поцелуи
    'целую', 'поцелуй', 'kiss', 'чмок',
    # Близость
    'прижаться', 'прижмусь', 'рядом', 'близко', 'тепло',
    'руку', 'держать за руку', 'hold hands',
    # Нежность
    'погладить', 'гладить', 'массаж', 'massage',
}


def extract_text(msg):
    text = msg.get("text", "")
    if isinstance(text, list):
        parts = []
        for part in text:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text", ""))
        return " ".join(parts)
    return str(text)


def count_markers(text, markers):
    text_lower = text.lower()
    count = 0
    for marker in markers:
        if marker in text_lower:
            count += 1
    return count


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"💕 Языки любви — {chat_name}")
    
    st.markdown("""
    Концепция "5 языков любви" Гэри Чепмена:
    - 💬 **Слова одобрения** — комплименты, поддержка, благодарность
    - ⏰ **Качественное время** — желание проводить время вместе
    - 🎁 **Подарки** — дарение и получение подарков
    - 🛠️ **Акты служения** — помощь, забота, решение проблем
    - 🤗 **Физическое прикосновение** — объятия, поцелуи, нежность
    """)
    
    # Считаем маркеры для каждого пользователя
    user_languages = defaultdict(lambda: {
        "words": 0,
        "time": 0,
        "gifts": 0,
        "service": 0,
        "touch": 0,
    })
    
    for msg in messages:
        sender = msg.get("from")
        if not sender:
            continue
        
        text = extract_text(msg)
        if not text.strip():
            continue
        
        user_languages[sender]["words"] += count_markers(text, WORDS_OF_AFFIRMATION)
        user_languages[sender]["time"] += count_markers(text, QUALITY_TIME)
        user_languages[sender]["gifts"] += count_markers(text, GIFTS)
        user_languages[sender]["service"] += count_markers(text, ACTS_OF_SERVICE)
        user_languages[sender]["touch"] += count_markers(text, PHYSICAL_TOUCH)
    
    if not user_languages:
        st.warning("Не удалось проанализировать сообщения.")
        return
    
    participants = sorted(user_languages.keys())
    
    # Таблица
    language_names = {
        "words": "💬 Слова одобрения",
        "time": "⏰ Качественное время",
        "gifts": "🎁 Подарки",
        "service": "🛠️ Акты служения",
        "touch": "🤗 Прикосновения",
    }
    
    data_rows = []
    for user in participants:
        row = {"Участник": user}
        langs = user_languages[user]
        for key, name in language_names.items():
            row[name] = langs[key]
        
        # Определяем основной язык
        if any(langs.values()):
            primary = max(langs.keys(), key=lambda k: langs[k])
            row["Основной язык"] = language_names[primary]
        else:
            row["Основной язык"] = "—"
        
        data_rows.append(row)
    
    df = pd.DataFrame(data_rows)
    st.dataframe(df, hide_index=True)
    
    # Визуализация
    if len(participants) >= 2:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Radar chart для сравнения (упрощённо через bar)
        categories = list(language_names.values())
        x = np.arange(len(categories))
        width = 0.35
        
        colors = ['#2196F3', '#FF9800']
        
        for i, user in enumerate(participants[:2]):
            langs = user_languages[user]
            values = [langs[k] for k in language_names.keys()]
            offset = width * (i - 0.5)
            axes[0].bar(x + offset, values, width, label=user, color=colors[i], alpha=0.7)
        
        axes[0].set_xticks(x)
        axes[0].set_xticklabels([name.split()[1] for name in categories], rotation=45, ha='right')
        axes[0].set_ylabel('Количество маркеров')
        axes[0].set_title('Сравнение языков любви')
        axes[0].legend()
        
        # Pie charts для каждого участника
        for i, user in enumerate(participants[:2]):
            langs = user_languages[user]
            values = [langs[k] for k in language_names.keys()]
            
            if sum(values) > 0:
                # Только если есть данные
                wedges, texts, autotexts = axes[1].pie(
                    values if i == 0 else [],  # Показываем только для первого
                    labels=[name.split()[0] for name in categories] if i == 0 else None,
                    autopct='%1.0f%%' if i == 0 else None,
                    startangle=90,
                )
        
        axes[1].set_title(f'Профиль языков: {participants[0]}' if participants else 'Профиль')
        
        plt.tight_layout()
        st.pyplot(fig)
    
    # Детальный анализ
    st.markdown("### 🔍 Детальный анализ")
    
    for user in participants:
        langs = user_languages[user]
        total = sum(langs.values())
        
        if total == 0:
            st.info(f"**{user}**: Недостаточно данных для определения языков любви.")
            continue
        
        # Сортируем по частоте
        sorted_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)
        
        st.markdown(f"**{user}**:")
        for lang_key, count in sorted_langs:
            percentage = count / total * 100 if total > 0 else 0
            bar_length = int(percentage / 5)  # Визуальная шкала
            bar = "█" * bar_length + "░" * (20 - bar_length)
            st.write(f"  {language_names[lang_key]}: {bar} {count} ({percentage:.0f}%)")
    
    # Совместимость
    if len(participants) >= 2:
        st.markdown("### 💞 Совместимость языков любви")
        
        user1_langs = user_languages[participants[0]]
        user2_langs = user_languages[participants[1]]
        
        # Находим основные языки каждого
        if sum(user1_langs.values()) > 0 and sum(user2_langs.values()) > 0:
            primary1 = max(user1_langs.keys(), key=lambda k: user1_langs[k])
            primary2 = max(user2_langs.keys(), key=lambda k: user2_langs[k])
            
            if primary1 == primary2:
                st.success(f"""
                ✅ **Отличная совместимость!**
                
                Оба участника предпочитают один язык любви: **{language_names[primary1]}**
                
                Это значит, что вы естественно понимаете друг друга и можете легко
                выражать любовь способом, который понятен партнёру.
                """)
            else:
                st.info(f"""
                ℹ️ **Разные основные языки:**
                
                - **{participants[0]}**: {language_names[primary1]}
                - **{participants[1]}**: {language_names[primary2]}
                
                Это не плохо! Просто важно осознавать разницу и стараться "переводить" 
                свою любовь на язык партнёра. Например, если партнёр ценит 
                {language_names[primary2].split()[1].lower()}, старайтесь больше это выражать.
                """)


import numpy as np

