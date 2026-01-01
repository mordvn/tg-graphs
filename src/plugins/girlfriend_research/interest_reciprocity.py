"""
Interest Reciprocity Analyzer
Анализирует взаимный интерес к жизни друг друга.
Кто чаще спрашивает о делах, планах, чувствах.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

# Вопросы о жизни/делах
LIFE_QUESTIONS = {
    'как дела', 'как ты', 'как день', 'как прошёл день', 'как твой день',
    'что нового', 'что новенького', 'что интересного',
    'как настроение', 'как самочувствие',
    'чем занимаешься', 'чем занимался', 'чем занималась',
    'что делаешь', 'что делал', 'что делала',
    'как провёл', 'как провела', 'как провёл день', 'как провела день',
    'как выходные', 'как отдохнул', 'как отдохнула',
}

# Вопросы о работе/учёбе
WORK_QUESTIONS = {
    'как на работе', 'как работа', 'как дела на работе',
    'как учёба', 'как в универе', 'как в школе', 'как экзамены',
    'как проект', 'как задание', 'как встреча', 'как собеседование',
    'справился', 'справилась', 'успел', 'успела',
    'много работы', 'завал на работе',
}

# Вопросы о планах
PLANS_QUESTIONS = {
    'какие планы', 'что планируешь', 'чем будешь заниматься',
    'что будешь делать', 'что на сегодня', 'что на завтра',
    'куда пойдёшь', 'куда поедешь', 'с кем встречаешься',
    'во сколько', 'когда освободишься', 'когда вернёшься',
    'что на выходных', 'планы на выходные', 'планы на вечер',
}

# Вопросы о чувствах/здоровье
FEELINGS_QUESTIONS = {
    'как себя чувствуешь', 'как ты себя чувствуешь',
    'всё хорошо', 'всё нормально', 'ты в порядке',
    'что случилось', 'что-то случилось', 'что не так',
    'почему грустишь', 'почему расстроен', 'почему расстроена',
    'устал', 'устала', 'плохо себя чувствуешь',
    'болит что-нибудь', 'как здоровье', 'выздоровел', 'выздоровела',
}

# Вопросы о мнении
OPINION_QUESTIONS = {
    'что думаешь', 'как думаешь', 'как считаешь',
    'что скажешь', 'как тебе', 'понравилось',
    'согласен', 'согласна', 'как ты к этому',
    'твоё мнение', 'ты за или против', 'хочешь',
}

# Упоминания важного для партнёра
REMEMBERING_MARKERS = {
    'ты же говорил', 'ты же говорила', 'ты рассказывал', 'ты рассказывала',
    'помню ты', 'ты упоминал', 'ты упоминала',
    'тот проект', 'та встреча', 'тот человек',
    'как тот', 'как та', 'как то',
    'помнишь рассказывал', 'помнишь рассказывала',
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


def count_questions(text):
    """Считает количество вопросов в тексте"""
    return len(re.findall(r'\?', text))


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"❓ Взаимный Интерес — {chat_name}")
    st.markdown("""
    Анализ того, кто больше интересуется жизнью партнёра.
    
    Вопросы — это проявление интереса. В здоровых отношениях оба спрашивают друг друга.
    """)
    
    categories = {
        '🌅 Жизнь/Дела': LIFE_QUESTIONS,
        '💼 Работа/Учёба': WORK_QUESTIONS,
        '📅 Планы': PLANS_QUESTIONS,
        '💭 Чувства/Здоровье': FEELINGS_QUESTIONS,
        '🤔 Мнение': OPINION_QUESTIONS,
        '🧠 Память': REMEMBERING_MARKERS,
    }
    
    # Статистика
    user_stats = defaultdict(lambda: {
        'total_messages': 0,
        'total_questions': 0,  # Все вопросы (по ?)
        'interest_questions': 0,  # Вопросы о партнёре
        'categories': {cat: {'count': 0, 'examples': []} for cat in categories}
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
        user_stats[sender]['total_questions'] += count_questions(text)
        
        has_interest = False
        for cat_name, markers in categories.items():
            count, found = count_markers(text, markers)
            if count > 0:
                has_interest = True
                user_stats[sender]['categories'][cat_name]['count'] += count
                if len(user_stats[sender]['categories'][cat_name]['examples']) < 5:
                    user_stats[sender]['categories'][cat_name]['examples'].append({
                        'text': text[:100],
                        'markers': found
                    })
        
        if has_interest:
            user_stats[sender]['interest_questions'] += 1
            try:
                dt = parse_date(msg['date'])
                monthly_stats[dt.strftime('%Y-%m')][sender] += 1
            except:
                pass
    
    if not user_stats:
        st.warning("Не удалось проанализировать сообщения.")
        return
    
    users = list(user_stats.keys())
    
    # Основная статистика
    st.markdown("### 📊 Статистика интереса")
    
    table_data = []
    for user in users:
        stats = user_stats[user]
        total_interest = sum(stats['categories'][cat]['count'] for cat in categories)
        interest_ratio = stats['interest_questions'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        
        table_data.append({
            'Пользователь': user,
            'Сообщений': stats['total_messages'],
            'Всего вопросов (?)': stats['total_questions'],
            'Интерес к партнёру': total_interest,
            'Доля вопросов': f"{interest_ratio:.1f}%"
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # По категориям
    st.markdown("### 📋 По типам вопросов")
    
    cat_data = []
    for cat_name in categories:
        row = {'Категория': cat_name}
        for user in users:
            row[user] = user_stats[user]['categories'][cat_name]['count']
        cat_data.append(row)
    
    df_cat = pd.DataFrame(cat_data)
    st.dataframe(df_cat, hide_index=True)
    
    # Визуализация
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Распределение по категориям")
        
        fig1, ax1 = plt.subplots(figsize=(6, 5))
        
        categories_list = list(categories.keys())
        x = range(len(categories_list))
        width = 0.35
        
        for i, user in enumerate(users[:2]):
            values = [user_stats[user]['categories'][cat]['count'] for cat in categories]
            offset = -width/2 + i*width
            ax1.bar([xi + offset for xi in x], values, width, label=user)
        
        ax1.set_xticks(x)
        ax1.set_xticklabels([c.split()[1] for c in categories_list], rotation=45, ha='right')
        ax1.legend()
        ax1.set_ylabel('Количество')
        plt.tight_layout()
        st.pyplot(fig1)
    
    with col2:
        st.markdown("#### 🥧 Кто больше интересуется")
        
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        
        totals = {user: sum(user_stats[user]['categories'][cat]['count'] for cat in categories) for user in users}
        
        if sum(totals.values()) > 0:
            ax2.pie(
                totals.values(),
                labels=totals.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=['#ff9999', '#66b3ff', '#99ff99'][:len(users)]
            )
            ax2.set_title('Соотношение интереса')
        st.pyplot(fig2)
    
    # Примеры
    st.markdown("### 🔍 Примеры проявления интереса")
    
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
        st.markdown("### 📈 Динамика интереса по месяцам")
        
        months = sorted(monthly_stats.keys())
        
        fig3, ax3 = plt.subplots(figsize=(12, 5))
        
        for user in users:
            values = [monthly_stats[m].get(user, 0) for m in months]
            ax3.plot(months, values, marker='o', label=user, linewidth=2)
        
        ax3.set_xlabel('Месяц')
        ax3.set_ylabel('Вопросов о партнёре')
        ax3.set_title('Как меняется интерес со временем')
        ax3.legend()
        ax3.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig3)
        
        # Тренды
        st.markdown("#### 📉 Тренды")
        for user in users:
            values = [monthly_stats[m].get(user, 0) for m in months]
            if len(values) >= 4:
                first_half = sum(values[:len(values)//2])
                second_half = sum(values[len(values)//2:])
                
                if first_half > 0:
                    change = (second_half - first_half) / first_half * 100
                    if change < -30:
                        st.warning(f"📉 **{user}**: интерес снизился на {abs(change):.0f}%")
                    elif change > 30:
                        st.success(f"📈 **{user}**: интерес вырос на {change:.0f}%")
                    else:
                        st.info(f"➡️ **{user}**: интерес стабилен")
    
    # Анализ баланса
    st.markdown("### ⚖️ Баланс интереса")
    
    if len(users) >= 2:
        user1, user2 = users[0], users[1]
        
        total1 = sum(user_stats[user1]['categories'][cat]['count'] for cat in categories)
        total2 = sum(user_stats[user2]['categories'][cat]['count'] for cat in categories)
        
        # Нормализуем
        ratio1 = total1 / user_stats[user1]['total_messages'] * 100 if user_stats[user1]['total_messages'] > 0 else 0
        ratio2 = total2 / user_stats[user2]['total_messages'] * 100 if user_stats[user2]['total_messages'] > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"{user1}", f"{ratio1:.1f}%")
        with col2:
            st.metric(f"{user2}", f"{ratio2:.1f}%")
        with col3:
            ratio = max(ratio1, ratio2) / min(ratio1, ratio2) if min(ratio1, ratio2) > 0 else 0
            st.metric("Разница", f"{ratio:.1f}x")
        
        diff = abs(ratio1 - ratio2)
        more_interested = user1 if ratio1 > ratio2 else user2
        less_interested = user2 if ratio1 > ratio2 else user1
        
        if diff > 5:
            st.warning(f"""
            ⚠️ **Дисбаланс интереса**
            
            **{more_interested}** значительно чаще спрашивает о делах **{less_interested}**.
            
            Это может означать:
            - Разный уровень вовлечённости в отношения
            - **{less_interested}** принимает внимание как должное
            - Разные стили общения (но лучше уточнить)
            
            💡 В здоровых отношениях оба интересуются жизнью друг друга
            """)
        elif diff > 2:
            st.info(f"""
            📊 **Небольшой дисбаланс**
            
            **{more_interested}** немного чаще проявляет интерес.
            Это не критично, но стоит обратить внимание.
            """)
        else:
            st.success(f"""
            ✅ **Отличный баланс!**
            
            Оба партнёра примерно одинаково интересуются жизнью друг друга.
            Это признак здоровых отношений.
            """)
    
    # Особые инсайты
    st.markdown("### 💡 Инсайты")
    
    for user in users:
        stats = user_stats[user]
        
        # Память
        memory_count = stats['categories']['🧠 Память']['count']
        if memory_count > 5:
            st.success(f"🧠 **{user}** часто вспоминает то, что рассказывал партнёр — это отличный признак внимательности!")
        elif memory_count == 0:
            st.info(f"📝 **{user}** редко ссылается на ранее сказанное партнёром")
        
        # Чувства vs Дела
        feelings = stats['categories']['💭 Чувства/Здоровье']['count']
        life = stats['categories']['🌅 Жизнь/Дела']['count']
        
        if feelings > life * 2 and feelings > 5:
            st.info(f"💭 **{user}** больше интересуется чувствами, чем событиями")
        elif life > feelings * 2 and life > 5:
            st.info(f"📋 **{user}** больше интересуется событиями, чем чувствами")
    
    st.markdown("---")
    st.caption("""
    **Как читать результаты:**
    - Высокий уровень вопросов = проявление интереса и заботы
    - Дисбаланс может указывать на неравномерную вовлечённость
    - Снижение интереса со временем — тревожный знак
    - Вопросы о чувствах важнее вопросов о делах
    """)

