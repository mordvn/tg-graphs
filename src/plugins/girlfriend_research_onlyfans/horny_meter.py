"""
Horny Meter 🔥
Измеритель уровня возбуждения и сексуального интереса в переписке.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# Прямые сексуальные маркеры (высокий вес)
EXPLICIT_MARKERS = {
    # Прямые
    'секс', 'sex', 'трах', 'fuck', 'ебать', 'ебаться',
    'кончить', 'кончил', 'кончила', 'оргазм', 'cum',
    'сосать', 'лизать', 'отсос', 'минет', 'куни',
    'порно', 'porn', 'xxx', 'nsfw',
    
    # Части тела
    'член', 'хуй', 'dick', 'cock', 'писька', 'пенис',
    'вагина', 'пизда', 'pussy', 'киска',
    'сиськи', 'tits', 'boobs', 'грудь', 'титьки',
    'попа', 'жопа', 'ass', 'попка', 'задница',
    'клитор', 'clit',
    
    # Действия
    'раздеться', 'раздевайся', 'разденусь', 'голая', 'голый',
    'naked', 'nude', 'обнажённая', 'обнажённый',
    'мастурб', 'дрочить', 'дрочу', 'fap', 'jerk',
    
    # Эмодзи
    '🍆', '🍑', '💦', '🥵', '😈', '🔞', '69',
}

# Флирт и намёки (средний вес)
FLIRTY_MARKERS = {
    # Желание
    'хочу тебя', 'хочу к тебе', 'want you', 'need you',
    'скучаю по тебе', 'miss you', 'жду тебя',
    'представляю тебя', 'думаю о тебе', 'мечтаю о тебе',
    
    # Комплименты с подтекстом
    'сексуальный', 'сексуальная', 'sexy', 'hot', 'горячий', 'горячая',
    'красивое тело', 'красивая фигура', 'накачанный',
    
    # Физический контакт
    'обнять крепко', 'прижаться', 'лежать рядом',
    'касаться', 'гладить', 'трогать',
    'поцелуй', 'целовать', 'kiss', 'целую страстно',
    
    # Намёки
    'когда приедешь', 'приезжай скорее', 'жду ночи',
    'останешься ночевать', 'переночуй', 'не отпущу',
    'соскучилась', 'соскучился', 'так давно',
    
    # Эмодзи
    '😏', '😘', '😍', '🥰', '💋', '🔥', '❤️‍🔥', '😻', '💕', '💖',
}

# Романтика (низкий вес)
ROMANTIC_MARKERS = {
    'люблю', 'love', 'обожаю', 'adore',
    'любимый', 'любимая', 'милый', 'милая',
    'котик', 'зайка', 'малыш', 'солнышко',
    'красивый', 'красивая', 'beautiful', 'handsome',
    '❤️', '💗', '💓', '💘', '💝', '🥺', '🤗',
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
    
    st.subheader(f"🔥 Horny Meter — {chat_name}")
    st.markdown("""
    Измерение уровня сексуального интереса и возбуждения в переписке.
    
    **Уровни:**
    - 🔞 **Explicit** — прямые сексуальные упоминания
    - 🔥 **Flirty** — флирт и намёки
    - 💕 **Romantic** — романтика
    """)
    
    # Статистика по пользователям
    user_stats = defaultdict(lambda: {
        'messages': 0,
        'explicit': 0,
        'flirty': 0,
        'romantic': 0,
        'explicit_examples': [],
        'flirty_examples': [],
    })
    
    # По времени
    hourly_horny = defaultdict(lambda: defaultdict(float))
    daily_horny = defaultdict(float)
    monthly_horny = defaultdict(lambda: defaultdict(float))
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        text = get_text(msg)
        if not text:
            continue
        
        user_stats[sender]['messages'] += 1
        
        # Считаем маркеры
        explicit_count, explicit_found = count_markers(text, EXPLICIT_MARKERS)
        flirty_count, flirty_found = count_markers(text, FLIRTY_MARKERS)
        romantic_count, _ = count_markers(text, ROMANTIC_MARKERS)
        
        user_stats[sender]['explicit'] += explicit_count
        user_stats[sender]['flirty'] += flirty_count
        user_stats[sender]['romantic'] += romantic_count
        
        # Сохраняем примеры
        if explicit_found and len(user_stats[sender]['explicit_examples']) < 10:
            user_stats[sender]['explicit_examples'].append({
                'text': text[:100],
                'markers': explicit_found
            })
        if flirty_found and len(user_stats[sender]['flirty_examples']) < 10:
            user_stats[sender]['flirty_examples'].append({
                'text': text[:100],
                'markers': flirty_found
            })
        
        # Horny score
        horny_score = explicit_count * 3 + flirty_count * 1.5 + romantic_count * 0.5
        
        try:
            dt = parse_date(msg['date'])
            hourly_horny[dt.hour][sender] += horny_score
            daily_horny[dt.date()] += horny_score
            monthly_horny[dt.strftime('%Y-%m')][sender] += horny_score
        except:
            pass
    
    users = list(user_stats.keys())
    
    if not users:
        st.warning("Не удалось проанализировать.")
        return
    
    # Основная статистика
    st.markdown("### 📊 Статистика по участникам")
    
    table_data = []
    for user in users:
        stats = user_stats[user]
        total_horny = stats['explicit'] * 3 + stats['flirty'] * 1.5 + stats['romantic'] * 0.5
        horny_per_100 = total_horny / stats['messages'] * 100 if stats['messages'] > 0 else 0
        
        table_data.append({
            'Участник': user,
            'Сообщений': stats['messages'],
            '🔞 Explicit': stats['explicit'],
            '🔥 Flirty': stats['flirty'],
            '💕 Romantic': stats['romantic'],
            '🌡️ Horny Score': f"{total_horny:.0f}",
            'На 100 сообщ.': f"{horny_per_100:.1f}",
        })
    
    df = pd.DataFrame(table_data)
    df = df.sort_values('🌡️ Horny Score', ascending=False)
    st.dataframe(df, hide_index=True)
    
    # Визуализация
    st.markdown("### 🌡️ Термометр Horny")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Сравнение пользователей
        fig1, ax1 = plt.subplots(figsize=(6, 6))
        
        categories = ['🔞 Explicit', '🔥 Flirty', '💕 Romantic']
        x = np.arange(len(categories))
        width = 0.35
        
        for i, user in enumerate(users[:2]):
            stats = user_stats[user]
            values = [stats['explicit'], stats['flirty'], stats['romantic']]
            offset = -width/2 + i*width
            ax1.bar(x + offset, values, width, label=user)
        
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        ax1.set_ylabel('Количество')
        ax1.set_title('Сравнение участников')
        
        plt.tight_layout()
        st.pyplot(fig1)
    
    with col2:
        # Pie chart по типам
        if len(users) >= 1:
            user = users[0]
            stats = user_stats[user]
            
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            
            sizes = [stats['explicit'], stats['flirty'], stats['romantic']]
            labels = ['🔞 Explicit', '🔥 Flirty', '💕 Romantic']
            colors = ['#ff4444', '#ff8800', '#ff69b4']
            
            if sum(sizes) > 0:
                ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90)
                ax2.set_title(f'Профиль: {user}')
            
            st.pyplot(fig2)
    
    # Horny по часам
    st.markdown("### 🕐 Когда самые горячие часы?")
    
    fig3, ax3 = plt.subplots(figsize=(12, 5))
    
    hours = list(range(24))
    
    for user in users[:2]:
        values = [hourly_horny[h].get(user, 0) for h in hours]
        ax3.plot(hours, values, marker='o', label=user, linewidth=2)
    
    ax3.set_xlabel('Час')
    ax3.set_ylabel('Horny Score')
    ax3.set_xticks(hours)
    ax3.set_title('Активность по часам')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Выделяем ночные часы
    for h in [22, 23, 0, 1, 2, 3]:
        ax3.axvspan(h-0.5, h+0.5, alpha=0.1, color='red')
    
    plt.tight_layout()
    st.pyplot(fig3)
    
    # Находим пиковые часы
    total_by_hour = [sum(hourly_horny[h].values()) for h in hours]
    peak_hour = hours[np.argmax(total_by_hour)]
    st.info(f"🔥 Самый горячий час: **{peak_hour}:00**")
    
    # Динамика по месяцам
    if len(monthly_horny) > 1:
        st.markdown("### 📈 Динамика по месяцам")
        
        months = sorted(monthly_horny.keys())
        
        fig4, ax4 = plt.subplots(figsize=(12, 5))
        
        for user in users[:2]:
            values = [monthly_horny[m].get(user, 0) for m in months]
            ax4.plot(months, values, marker='o', label=user, linewidth=2)
        
        ax4.set_xlabel('Месяц')
        ax4.set_ylabel('Horny Score')
        ax4.set_title('Как меняется интерес со временем')
        ax4.legend()
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig4)
        
        # Тренд
        for user in users:
            values = [monthly_horny[m].get(user, 0) for m in months]
            if len(values) >= 4:
                first_half = sum(values[:len(values)//2])
                second_half = sum(values[len(values)//2:])
                
                if first_half > 0:
                    change = (second_half - first_half) / first_half * 100
                    if change > 30:
                        st.success(f"📈 **{user}**: страсть растёт! (+{change:.0f}%)")
                    elif change < -30:
                        st.warning(f"📉 **{user}**: страсть угасает... ({change:.0f}%)")
    
    # Примеры (спойлер)
    st.markdown("### 🔍 Примеры сообщений")
    
    for user in users:
        stats = user_stats[user]
        
        with st.expander(f"👤 {user} — примеры", expanded=False):
            if stats['explicit_examples']:
                st.markdown("**🔞 Explicit:**")
                for ex in stats['explicit_examples'][:3]:
                    st.caption(f"«_{ex['text']}..._» → {', '.join(ex['markers'][:3])}")
            
            if stats['flirty_examples']:
                st.markdown("**🔥 Flirty:**")
                for ex in stats['flirty_examples'][:3]:
                    st.caption(f"«_{ex['text']}..._» → {', '.join(ex['markers'][:3])}")
    
    # Итоги
    st.markdown("### 💡 Выводы")
    
    if len(users) >= 2:
        user1, user2 = users[0], users[1]
        score1 = user_stats[user1]['explicit'] * 3 + user_stats[user1]['flirty'] * 1.5
        score2 = user_stats[user2]['explicit'] * 3 + user_stats[user2]['flirty'] * 1.5
        
        if score1 > score2 * 1.5:
            st.info(f"🔥 **{user1}** значительно горячее в переписке")
        elif score2 > score1 * 1.5:
            st.info(f"🔥 **{user2}** значительно горячее в переписке")
        else:
            st.success("🔥 Примерно одинаковый уровень страсти — хороший знак!")

