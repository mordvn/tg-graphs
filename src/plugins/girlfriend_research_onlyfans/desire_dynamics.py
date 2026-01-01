"""
Desire Dynamics 🔥
Динамика желания и страсти в отношениях.
Как меняется сексуальный интерес со временем.
"""
from collections import defaultdict
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# Маркеры желания
DESIRE_MARKERS = {
    'high': {
        'хочу тебя', 'хочу к тебе', 'жду встречи', 'соскучилась', 'соскучился',
        'мечтаю', 'представляю', 'думаю о тебе', 'не могу ждать',
        'приезжай', 'приходи', 'когда увидимся',
        '😍', '🥰', '😘', '💋', '🔥', '❤️‍🔥', '🥵', '😈',
    },
    'medium': {
        'скучаю', 'жду', 'хочу увидеть', 'хочу обнять',
        'целую', 'обнимаю', 'любимый', 'любимая',
        '❤️', '💕', '💖', '💗', '😊',
    },
    'low': {
        'ок', 'окей', 'хорошо', 'ладно', 'да', 'нет',
        'понятно', 'ясно', 'угу', 'ага',
    },
}

# Маркеры отторжения
REJECTION_MARKERS = {
    'устала', 'устал', 'не сегодня', 'не сейчас', 'потом',
    'голова болит', 'плохо себя чувствую', 'не хочу',
    'отстань', 'надоело', 'достал', 'достала',
    'давай не сегодня', 'давай потом', 'в другой раз',
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
    
    st.subheader(f"🔥 Динамика Желания — {chat_name}")
    st.markdown("""
    Как меняется страсть и желание со временем.
    
    Анализируем:
    - 🔥 Высокое желание — страстные сообщения
    - 💕 Среднее — тёплые, романтичные
    - 😐 Низкое — формальные ответы
    - ❌ Отторжение — отказы и отмазки
    """)
    
    # Собираем данные по месяцам
    monthly_data = defaultdict(lambda: defaultdict(lambda: {
        'messages': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
        'rejection': 0,
    }))
    
    weekly_data = defaultdict(lambda: defaultdict(lambda: {
        'desire_score': 0,
        'messages': 0,
    }))
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        text = get_text(msg)
        if not text:
            continue
        
        try:
            dt = parse_date(msg['date'])
            month = dt.strftime('%Y-%m')
            week = dt.strftime('%Y-W%W')
        except:
            continue
        
        monthly_data[month][sender]['messages'] += 1
        weekly_data[week][sender]['messages'] += 1
        
        # Считаем маркеры
        high = count_markers(text, DESIRE_MARKERS['high'])
        medium = count_markers(text, DESIRE_MARKERS['medium'])
        low = count_markers(text, DESIRE_MARKERS['low'])
        rejection = count_markers(text, REJECTION_MARKERS)
        
        monthly_data[month][sender]['high'] += high
        monthly_data[month][sender]['medium'] += medium
        monthly_data[month][sender]['low'] += low
        monthly_data[month][sender]['rejection'] += rejection
        
        # Desire score
        desire_score = high * 3 + medium * 1.5 - low * 0.5 - rejection * 2
        weekly_data[week][sender]['desire_score'] += desire_score
    
    users = set()
    for month_data in monthly_data.values():
        users.update(month_data.keys())
    users = list(users)
    
    if not users:
        st.warning("Не удалось проанализировать.")
        return
    
    months = sorted(monthly_data.keys())
    weeks = sorted(weekly_data.keys())
    
    # График динамики желания
    st.markdown("### 📈 Динамика желания по месяцам")
    
    fig, ax = plt.subplots(figsize=(14, 5))
    
    for user in users[:2]:
        values = []
        for month in months:
            data = monthly_data[month].get(user, {'high': 0, 'medium': 0, 'low': 0, 'rejection': 0, 'messages': 1})
            # Нормализуем на количество сообщений
            if data['messages'] > 0:
                score = (data['high'] * 3 + data['medium'] * 1.5 - data['low'] * 0.5 - data['rejection'] * 2) / data['messages'] * 10
            else:
                score = 0
            values.append(score)
        
        ax.plot(months, values, marker='o', linewidth=2, label=user)
    
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_xlabel('Месяц')
    ax.set_ylabel('Индекс желания')
    ax.set_title('Как меняется желание со временем')
    ax.legend()
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Анализ тренда
    if len(months) >= 4:
        for user in users:
            values = []
            for month in months:
                data = monthly_data[month].get(user, {'high': 0, 'medium': 0, 'low': 0, 'rejection': 0, 'messages': 1})
                if data['messages'] > 0:
                    score = (data['high'] * 3 + data['medium'] * 1.5 - data['low'] * 0.5 - data['rejection'] * 2) / data['messages']
                else:
                    score = 0
                values.append(score)
            
            first_half = np.mean(values[:len(values)//2])
            second_half = np.mean(values[len(values)//2:])
            
            if first_half != 0:
                change = (second_half - first_half) / abs(first_half) * 100
                
                if change > 30:
                    st.success(f"📈 **{user}**: желание растёт! (+{change:.0f}%)")
                elif change < -30:
                    st.warning(f"📉 **{user}**: желание угасает... ({change:.0f}%)")
                else:
                    st.info(f"➡️ **{user}**: желание стабильно")
    
    # Stacked bar по типам
    st.markdown("### 📊 Распределение по типам")
    
    fig2, axes = plt.subplots(1, min(2, len(users)), figsize=(12, 5))
    if len(users) == 1:
        axes = [axes]
    
    for idx, user in enumerate(users[:2]):
        total_high = sum(monthly_data[m].get(user, {}).get('high', 0) for m in months)
        total_medium = sum(monthly_data[m].get(user, {}).get('medium', 0) for m in months)
        total_low = sum(monthly_data[m].get(user, {}).get('low', 0) for m in months)
        total_rejection = sum(monthly_data[m].get(user, {}).get('rejection', 0) for m in months)
        
        values = [total_high, total_medium, total_low, total_rejection]
        labels = ['🔥 Высокое', '💕 Среднее', '😐 Низкое', '❌ Отторжение']
        colors = ['#ff4444', '#ff8888', '#888888', '#4444ff']
        
        axes[idx].pie(values, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90)
        axes[idx].set_title(user)
    
    plt.tight_layout()
    st.pyplot(fig2)
    
    # Сравнение
    st.markdown("### ⚖️ Сравнение желания")
    
    if len(users) >= 2:
        user1, user2 = users[0], users[1]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{user1}**")
            
            total_high = sum(monthly_data[m].get(user1, {}).get('high', 0) for m in months)
            total_medium = sum(monthly_data[m].get(user1, {}).get('medium', 0) for m in months)
            total_rejection = sum(monthly_data[m].get(user1, {}).get('rejection', 0) for m in months)
            
            st.metric("🔥 Высокое желание", total_high)
            st.metric("💕 Тёплое", total_medium)
            st.metric("❌ Отторжения", total_rejection)
        
        with col2:
            st.markdown(f"**{user2}**")
            
            total_high = sum(monthly_data[m].get(user2, {}).get('high', 0) for m in months)
            total_medium = sum(monthly_data[m].get(user2, {}).get('medium', 0) for m in months)
            total_rejection = sum(monthly_data[m].get(user2, {}).get('rejection', 0) for m in months)
            
            st.metric("🔥 Высокое желание", total_high)
            st.metric("💕 Тёплое", total_medium)
            st.metric("❌ Отторжения", total_rejection)
    
    # Недельный график
    if len(weeks) > 4:
        st.markdown("### 📉 Недельная динамика")
        
        fig3, ax3 = plt.subplots(figsize=(14, 5))
        
        for user in users[:2]:
            values = []
            for week in weeks:
                data = weekly_data[week].get(user, {'desire_score': 0, 'messages': 1})
                if data['messages'] > 0:
                    score = data['desire_score'] / data['messages'] * 10
                else:
                    score = 0
                values.append(score)
            
            # Сглаживание
            if len(values) > 3:
                values_smooth = np.convolve(values, np.ones(3)/3, mode='valid')
                ax3.plot(range(len(values_smooth)), values_smooth, linewidth=2, label=user, alpha=0.7)
        
        ax3.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax3.set_xlabel('Неделя')
        ax3.set_ylabel('Индекс желания')
        ax3.set_title('Недельная динамика (сглаженная)')
        ax3.legend()
        
        plt.tight_layout()
        st.pyplot(fig3)
    
    # Выводы
    st.markdown("### 💡 Выводы")
    
    # Соотношение желания и отторжения
    for user in users:
        total_desire = sum(monthly_data[m].get(user, {}).get('high', 0) + 
                         monthly_data[m].get(user, {}).get('medium', 0) for m in months)
        total_rejection = sum(monthly_data[m].get(user, {}).get('rejection', 0) for m in months)
        
        if total_rejection > 0:
            ratio = total_desire / total_rejection
            if ratio < 3:
                st.warning(f"⚠️ **{user}**: много отторжений относительно желания (соотношение {ratio:.1f}:1)")
            else:
                st.success(f"✅ **{user}**: желание преобладает над отторжением ({ratio:.1f}:1)")
        else:
            st.success(f"✅ **{user}**: нет признаков отторжения")
    
    st.markdown("""
    ---
    **Интерпретация:**
    - 📈 **Рост желания** — отношения развиваются, страсть растёт
    - 📉 **Падение желания** — возможное угасание страсти
    - ❌ **Много отторжений** — стоит обсудить интимную жизнь
    """)

