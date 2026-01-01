"""
Support Balance Analyzer
Анализирует кто кого поддерживает чаще.
Здоровые отношения — взаимная поддержка.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Фразы поддержки и утешения
SUPPORT_PHRASES = {
    # Прямая поддержка
    'всё будет хорошо', 'всё наладится', 'всё получится', 'ты справишься',
    'я в тебя верю', 'верю в тебя', 'ты сможешь', 'ты молодец',
    'ты умница', 'ты лучший', 'ты лучшая', 'горжусь тобой',
    'я рядом', 'я с тобой', 'я здесь', 'не переживай',
    'не волнуйся', 'успокойся', 'всё хорошо', 'всё ок',
    
    # Сочувствие
    'мне жаль', 'сочувствую', 'понимаю тебя', 'понимаю как тебе',
    'это тяжело', 'это сложно', 'бедный', 'бедная', 'бедненький',
    'как ты себя чувствуешь', 'как ты', 'что случилось',
    'расскажи', 'поделись', 'хочешь поговорить',
    
    # Помощь
    'могу помочь', 'чем помочь', 'как помочь', 'давай помогу',
    'хочешь я', 'могу приехать', 'давай вместе', 'подсказать',
    'если нужна помощь', 'обращайся', 'звони если что',
    
    # Комплименты и одобрение
    'ты красивая', 'ты красивый', 'ты умный', 'ты умная',
    'ты классный', 'ты классная', 'ты особенный', 'ты особенная',
    'ты талантливый', 'ты талантливая', 'ты способный', 'ты способная',
    'мне повезло', 'рад что ты есть', 'рада что ты есть',
    'спасибо что ты есть', 'ценю тебя', 'благодарен', 'благодарна',
    
    # Любовь и нежность
    'люблю тебя', 'обожаю тебя', 'скучаю', 'скучаю по тебе',
    'целую', 'обнимаю', 'хочу к тебе', 'хочу обнять',
    'мой хороший', 'моя хорошая', 'солнышко', 'малыш', 'котик', 'зая',
}

# Фразы заботы о здоровье
CARE_PHRASES = {
    'выздоравливай', 'не болей', 'береги себя', 'отдохни',
    'поспи', 'выспись', 'покушай', 'поел', 'поела', 'не забудь поесть',
    'тепло оденься', 'не простынь', 'как себя чувствуешь',
    'принял таблетки', 'приняла таблетки', 'к врачу',
    'как здоровье', 'лучше себя чувствуешь',
}

# Эмодзи поддержки
SUPPORT_EMOJIS = {
    '❤️', '💕', '💖', '💗', '💓', '💘', '💝', '🥰', '😍', '😘',
    '🤗', '🫂', '💪', '🙏', '✨', '🌟', '⭐', '👍', '👏', '🎉',
}

# Вопросы о делах (показывает интерес)
INTEREST_QUESTIONS = {
    'как дела', 'как ты', 'как день', 'как прошёл день',
    'что делаешь', 'чем занят', 'чем занята', 'что нового',
    'как на работе', 'как учёба', 'как встреча',
    'как доехал', 'как доехала', 'добрался', 'добралась',
    'как настроение', 'всё хорошо',
}


def get_text(msg):
    """Извлекает текст из сообщения"""
    text = msg.get('text', '')
    if isinstance(text, list):
        parts = []
        for part in text:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and 'text' in part:
                parts.append(part['text'])
        return ' '.join(parts)
    return str(text) if text else ''


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def count_markers(text, markers):
    """Считает маркеры в тексте"""
    text_lower = text.lower()
    count = 0
    found = []
    for marker in markers:
        if marker in text_lower:
            count += 1
            found.append(marker)
    return count, found


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"🤝 Баланс Поддержки — {chat_name}")
    st.markdown("""
    Анализ того, кто чаще поддерживает, утешает и проявляет заботу.
    
    В здоровых отношениях поддержка взаимна.
    """)
    
    categories = {
        '💬 Поддержка': SUPPORT_PHRASES,
        '💊 Забота': CARE_PHRASES,
        '❓ Интерес': INTEREST_QUESTIONS,
    }
    
    # Собираем статистику
    user_stats = defaultdict(lambda: {
        'total_messages': 0,
        'support_messages': 0,
        'categories': {cat: {'count': 0, 'examples': []} for cat in categories},
        'emojis': 0
    })
    
    monthly_stats = defaultdict(lambda: defaultdict(int))
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
            
        text = get_text(msg)
        if not text:
            continue
        
        user_stats[sender]['total_messages'] += 1
        
        is_supportive = False
        for cat_name, markers in categories.items():
            count, found = count_markers(text, markers)
            if count > 0:
                is_supportive = True
                user_stats[sender]['categories'][cat_name]['count'] += count
                if len(user_stats[sender]['categories'][cat_name]['examples']) < 5:
                    user_stats[sender]['categories'][cat_name]['examples'].append({
                        'text': text[:100],
                        'markers': found
                    })
        
        # Эмодзи поддержки
        emoji_count = sum(1 for emoji in SUPPORT_EMOJIS if emoji in text)
        user_stats[sender]['emojis'] += emoji_count
        if emoji_count > 0:
            is_supportive = True
        
        if is_supportive:
            user_stats[sender]['support_messages'] += 1
            try:
                dt = parse_date(msg['date'])
                monthly_stats[dt.strftime('%Y-%m')][sender] += 1
            except:
                pass
    
    if not user_stats:
        st.warning("Не удалось проанализировать сообщения.")
        return
    
    # Основная статистика
    st.markdown("### 📊 Кто чаще поддерживает")
    
    users = list(user_stats.keys())
    
    table_data = []
    for user in users:
        stats = user_stats[user]
        total_support = sum(stats['categories'][cat]['count'] for cat in categories) + stats['emojis']
        support_ratio = stats['support_messages'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        
        table_data.append({
            'Пользователь': user,
            'Всего сообщений': stats['total_messages'],
            '💬 Поддержка': stats['categories']['💬 Поддержка']['count'],
            '💊 Забота': stats['categories']['💊 Забота']['count'],
            '❓ Интерес': stats['categories']['❓ Интерес']['count'],
            '❤️ Эмодзи': stats['emojis'],
            'ВСЕГО': total_support,
            'Доля': f"{support_ratio:.1f}%"
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # Визуализация
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 По категориям")
        
        fig1, ax1 = plt.subplots(figsize=(6, 5))
        
        categories_list = list(categories.keys()) + ['❤️ Эмодзи']
        x = range(len(categories_list))
        width = 0.35
        
        for i, user in enumerate(users[:2]):  # Максимум 2 пользователя
            values = [user_stats[user]['categories'].get(cat, {}).get('count', 0) for cat in categories]
            values.append(user_stats[user]['emojis'])
            offset = -width/2 + i*width
            ax1.bar([xi + offset for xi in x], values, width, label=user)
        
        ax1.set_xticks(x)
        ax1.set_xticklabels([c.split()[1] if ' ' in c else c for c in categories_list], rotation=45, ha='right')
        ax1.legend()
        ax1.set_ylabel('Количество')
        plt.tight_layout()
        st.pyplot(fig1)
    
    with col2:
        st.markdown("#### 🥧 Соотношение поддержки")
        
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        
        totals = {user: sum(user_stats[user]['categories'][cat]['count'] for cat in categories) + user_stats[user]['emojis'] for user in users}
        
        if sum(totals.values()) > 0:
            ax2.pie(
                totals.values(),
                labels=totals.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=['#66b3ff', '#ff9999', '#99ff99', '#ffcc99'][:len(users)]
            )
            ax2.set_title('Кто чаще поддерживает')
        st.pyplot(fig2)
    
    # Детали
    st.markdown("### 🔍 Примеры поддержки")
    
    for user in users:
        stats = user_stats[user]
        with st.expander(f"👤 {user}"):
            for cat_name in categories:
                cat_stats = stats['categories'][cat_name]
                if cat_stats['count'] > 0:
                    st.markdown(f"**{cat_name}** — {cat_stats['count']} раз")
                    for example in cat_stats['examples'][:3]:
                        st.caption(f"_{example['text']}..._ → {', '.join(example['markers'])}")
                    st.divider()
    
    # Динамика
    if len(monthly_stats) > 1:
        st.markdown("### 📈 Динамика поддержки по месяцам")
        
        months = sorted(monthly_stats.keys())
        
        fig3, ax3 = plt.subplots(figsize=(12, 5))
        
        for user in users:
            values = [monthly_stats[m].get(user, 0) for m in months]
            ax3.plot(months, values, marker='o', label=user, linewidth=2)
        
        ax3.set_xlabel('Месяц')
        ax3.set_ylabel('Сообщений с поддержкой')
        ax3.set_title('Как меняется уровень поддержки')
        ax3.legend()
        ax3.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig3)
    
    # Анализ баланса
    st.markdown("### ⚖️ Анализ баланса")
    
    if len(users) >= 2:
        user1, user2 = users[0], users[1]
        
        total1 = sum(user_stats[user1]['categories'][cat]['count'] for cat in categories) + user_stats[user1]['emojis']
        total2 = sum(user_stats[user2]['categories'][cat]['count'] for cat in categories) + user_stats[user2]['emojis']
        
        # Нормализуем по количеству сообщений
        ratio1 = total1 / user_stats[user1]['total_messages'] * 100 if user_stats[user1]['total_messages'] > 0 else 0
        ratio2 = total2 / user_stats[user2]['total_messages'] * 100 if user_stats[user2]['total_messages'] > 0 else 0
        
        diff = abs(ratio1 - ratio2)
        more_supportive = user1 if ratio1 > ratio2 else user2
        less_supportive = user2 if ratio1 > ratio2 else user1
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"{user1}", f"{ratio1:.1f}%", help="Процент сообщений с поддержкой")
        with col2:
            st.metric(f"{user2}", f"{ratio2:.1f}%", help="Процент сообщений с поддержкой")
        with col3:
            ratio = max(ratio1, ratio2) / min(ratio1, ratio2) if min(ratio1, ratio2) > 0 else 0
            st.metric("Разница", f"{ratio:.1f}x")
        
        if diff > 10:
            st.warning(f"""
            ⚠️ **Заметный дисбаланс поддержки**
            
            **{more_supportive}** поддерживает значительно чаще чем **{less_supportive}**.
            
            Это может означать:
            - Разную эмоциональную вовлечённость
            - Один партнёр постоянно "вытягивает" поддержку
            - Разные стили общения
            
            💡 Поддержка должна быть взаимной
            """)
        elif diff > 5:
            st.info(f"""
            📊 **Небольшой дисбаланс**
            
            **{more_supportive}** немного чаще проявляет поддержку.
            В целом нормально, но стоит обратить внимание.
            """)
        else:
            st.success(f"""
            ✅ **Отличный баланс!**
            
            Оба партнёра примерно одинаково часто поддерживают друг друга.
            Это признак здоровых отношений.
            """)
    
    # Интересные инсайты
    st.markdown("### 💡 Инсайты")
    
    for user in users:
        stats = user_stats[user]
        
        # Какой тип поддержки преобладает
        cat_counts = {cat: stats['categories'][cat]['count'] for cat in categories}
        max_cat = max(cat_counts, key=cat_counts.get) if any(cat_counts.values()) else None
        
        if max_cat:
            st.info(f"**{user}** чаще всего проявляет: **{max_cat}**")
        
        # Интерес vs поддержка
        interest = stats['categories']['❓ Интерес']['count']
        support = stats['categories']['💬 Поддержка']['count']
        
        if interest > support * 2:
            st.caption(f"📝 {user} больше интересуется делами, чем активно поддерживает")
        elif support > interest * 2:
            st.caption(f"💪 {user} больше активно поддерживает, чем спрашивает о делах")

