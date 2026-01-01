"""
Sexting Analyzer 📱
Анализ секстинга и интимной переписки.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re


# Паттерны секстинга
SEXTING_PATTERNS = {
    'описание_действий': {
        'я бы', 'хочу чтобы ты', 'представь', 'представляю',
        'если бы ты был', 'если бы ты была',
        'я бы сделала', 'я бы сделал',
        'когда ты', 'когда я',
    },
    'описание_тела': {
        'твоё тело', 'твоя грудь', 'твои губы', 'твои руки',
        'моё тело', 'моя грудь', 'мои губы',
        'хочу трогать', 'хочу целовать', 'хочу лизать',
    },
    'желание': {
        'хочу тебя', 'так хочу', 'очень хочу',
        'жажду', 'мечтаю', 'сгораю',
        'не могу ждать', 'не могу терпеть',
    },
    'реакция': {
        'мокрая', 'мокрый', 'wet', 'возбуждена', 'возбуждён',
        'течёт', 'стоит', 'hard', 'horny',
        'хочется', 'заводит', 'возбуждает',
    },
    'nudes': {
        'фото', 'скинь фото', 'пришли фото', 'покажи',
        'хочу увидеть', 'хочу посмотреть',
        'видео', 'запись', 'записала', 'записал',
        'снимаю', 'снимаюсь', 'сфоткала', 'сфоткал',
    },
}

# Эмодзи секстинга
SEXTING_EMOJIS = {
    '🍆': 3, '🍑': 3, '💦': 3, '🥵': 2, '😈': 2,
    '😏': 1.5, '🔥': 1.5, '❤️‍🔥': 2, '💋': 1,
    '👅': 2, '🫦': 2, '💄': 1, '🌶️': 2,
    '🍒': 1.5, '🥒': 2, '🍌': 2, '🦴': 1.5,
}


def get_text(msg):
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


def analyze_sexting(text):
    """Анализирует текст на признаки секстинга"""
    text_lower = text.lower()
    
    scores = {}
    found = {}
    
    for category, patterns in SEXTING_PATTERNS.items():
        scores[category] = 0
        found[category] = []
        for pattern in patterns:
            if pattern in text_lower:
                scores[category] += 1
                found[category].append(pattern)
    
    # Эмодзи
    emoji_score = 0
    emoji_found = []
    for emoji, weight in SEXTING_EMOJIS.items():
        if emoji in text:
            emoji_score += weight
            emoji_found.append(emoji)
    
    scores['emojis'] = emoji_score
    found['emojis'] = emoji_found
    
    # Длинные сообщения с интимным контентом (описания)
    if sum(scores.values()) > 0 and len(text) > 100:
        scores['descriptive'] = 2
    else:
        scores['descriptive'] = 0
    
    total_score = sum(scores.values())
    
    return {
        'scores': scores,
        'found': found,
        'total': total_score,
        'is_sexting': total_score >= 2,
    }


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"📱 Анализ Секстинга — {chat_name}")
    st.markdown("""
    Анализ интимной переписки: кто инициирует, как развивается, стиль.
    """)
    
    # Анализ всех сообщений
    user_stats = defaultdict(lambda: {
        'messages': 0,
        'sexting_messages': 0,
        'total_score': 0,
        'categories': defaultdict(int),
        'examples': [],
    })
    
    sexting_sessions = []  # Сессии секстинга
    current_session = []
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        text = get_text(msg)
        if not text:
            continue
        
        user_stats[sender]['messages'] += 1
        
        analysis = analyze_sexting(text)
        
        if analysis['is_sexting']:
            user_stats[sender]['sexting_messages'] += 1
            user_stats[sender]['total_score'] += analysis['total']
            
            for cat, score in analysis['scores'].items():
                user_stats[sender]['categories'][cat] += score
            
            if len(user_stats[sender]['examples']) < 10:
                user_stats[sender]['examples'].append({
                    'text': text[:150],
                    'score': analysis['total'],
                    'found': analysis['found'],
                })
            
            # Добавляем в сессию
            try:
                dt = parse_date(msg['date'])
                current_session.append({
                    'datetime': dt,
                    'sender': sender,
                    'score': analysis['total'],
                    'text': text[:100],
                })
            except:
                pass
        else:
            # Проверяем завершение сессии
            if len(current_session) >= 3:
                sexting_sessions.append(current_session)
            current_session = []
    
    # Добавляем последнюю сессию
    if len(current_session) >= 3:
        sexting_sessions.append(current_session)
    
    users = list(user_stats.keys())
    
    if not users:
        st.info("Секстинга не обнаружено.")
        return
    
    # Основная статистика
    st.markdown("### 📊 Статистика")
    
    table_data = []
    for user in users:
        stats = user_stats[user]
        sexting_pct = stats['sexting_messages'] / stats['messages'] * 100 if stats['messages'] > 0 else 0
        
        table_data.append({
            'Участник': user,
            'Всего сообщений': stats['messages'],
            '📱 Секстинг': stats['sexting_messages'],
            '% секстинга': f"{sexting_pct:.1f}%",
            '🔥 Score': f"{stats['total_score']:.0f}",
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # Категории
    st.markdown("### 📋 По категориям")
    
    categories_ru = {
        'описание_действий': '📝 Описание действий',
        'описание_тела': '👁️ Описание тела',
        'желание': '💋 Желание',
        'реакция': '🥵 Реакция',
        'nudes': '📷 Nudes/фото',
        'emojis': '😈 Эмодзи',
        'descriptive': '📜 Развёрнутые',
    }
    
    cat_data = []
    for cat in SEXTING_PATTERNS.keys():
        row = {'Категория': categories_ru.get(cat, cat)}
        for user in users:
            row[user] = user_stats[user]['categories'].get(cat, 0)
        cat_data.append(row)
    
    # Добавляем эмодзи и descriptive
    for cat in ['emojis', 'descriptive']:
        row = {'Категория': categories_ru.get(cat, cat)}
        for user in users:
            row[user] = user_stats[user]['categories'].get(cat, 0)
        cat_data.append(row)
    
    df_cat = pd.DataFrame(cat_data)
    st.dataframe(df_cat, hide_index=True)
    
    # Визуализация
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🥧 Вклад в секстинг")
        
        fig1, ax1 = plt.subplots(figsize=(6, 6))
        
        scores = {user: user_stats[user]['total_score'] for user in users}
        if sum(scores.values()) > 0:
            ax1.pie(scores.values(), labels=scores.keys(), autopct='%1.0f%%', 
                   startangle=90, colors=['#ff6b6b', '#ffa502'])
            ax1.set_title('Кто больше сексит')
        
        st.pyplot(fig1)
    
    with col2:
        st.markdown("#### 📊 Стиль секстинга")
        
        if len(users) >= 1:
            user = users[0]
            categories = list(SEXTING_PATTERNS.keys()) + ['emojis']
            values = [user_stats[user]['categories'].get(c, 0) for c in categories]
            labels = [categories_ru.get(c, c).split()[1] for c in categories]
            
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            
            if sum(values) > 0:
                ax2.bar(labels, values, color='coral')
                ax2.set_title(f'Стиль: {user}')
                ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            st.pyplot(fig2)
    
    # Сессии секстинга
    if sexting_sessions:
        st.markdown(f"### 💬 Сессии секстинга ({len(sexting_sessions)})")
        
        for i, session in enumerate(sexting_sessions[:10]):
            start = session[0]['datetime']
            end = session[-1]['datetime']
            duration = (end - start).total_seconds() / 60
            initiator = session[0]['sender']
            total_score = sum(m['score'] for m in session)
            
            with st.expander(f"💬 Сессия {i+1} — {start.strftime('%d.%m.%Y %H:%M')} ({len(session)} сообщ., {duration:.0f} мин)"):
                st.caption(f"Инициатор: **{initiator}** | Score: {total_score:.0f}")
                
                for msg in session[:15]:
                    st.caption(f"[{msg['datetime'].strftime('%H:%M')}] **{msg['sender']}**: _{msg['text']}..._")
                
                if len(session) > 15:
                    st.caption(f"... и ещё {len(session) - 15} сообщений")
        
        # Кто инициирует
        initiators = defaultdict(int)
        for session in sexting_sessions:
            initiators[session[0]['sender']] += 1
        
        st.markdown("**Кто начинает секстинг:**")
        for user, count in sorted(initiators.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(sexting_sessions) * 100
            st.write(f"**{user}**: {count} раз ({pct:.0f}%)")
    
    # Примеры
    st.markdown("### 🔍 Примеры")
    
    for user in users:
        examples = user_stats[user]['examples']
        if examples:
            with st.expander(f"👤 {user} — примеры секстинга"):
                for ex in examples[:5]:
                    st.caption(f"[Score: {ex['score']:.0f}] «_{ex['text']}..._»")
    
    # Выводы
    st.markdown("### 💡 Выводы")
    
    if len(users) >= 2:
        user1, user2 = users[0], users[1]
        score1 = user_stats[user1]['total_score']
        score2 = user_stats[user2]['total_score']
        
        if score1 > score2 * 2:
            st.info(f"📱 **{user1}** значительно активнее в секстинге")
        elif score2 > score1 * 2:
            st.info(f"📱 **{user2}** значительно активнее в секстинге")
        else:
            st.success("📱 Примерно равный вклад в секстинг — отлично!")
    
    # Стиль секстинга
    for user in users:
        categories = user_stats[user]['categories']
        if sum(categories.values()) > 0:
            top_cat = max(categories.items(), key=lambda x: x[1])
            st.caption(f"**{user}** предпочитает: {categories_ru.get(top_cat[0], top_cat[0])}")

