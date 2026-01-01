"""
Sex Islands Detector 🏝️
Детектор "островов секса" — кластеризация периодов интимной активности.

Острова = периоды повышенной сексуальной активности в переписке,
окружённые "океаном" обычного общения.
"""
from collections import defaultdict
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# Сексуальные маркеры
SEX_MARKERS = {
    # Прямые
    'секс', 'sex', 'трах', 'ебать', 'кончить', 'оргазм',
    'сосать', 'лизать', 'минет', 'куни',
    
    # Анатомия
    'член', 'хуй', 'dick', 'cock',
    'вагина', 'пизда', 'pussy', 'киска',
    'сиськи', 'tits', 'boobs', 'грудь',
    'попа', 'жопа', 'ass',
    
    # Действия
    'раздеться', 'голая', 'голый', 'naked', 'nude',
    'мастурб', 'дрочить',
    
    # Желание
    'хочу тебя', 'трахнуть', 'выебать',
    'сделай мне', 'сделаю тебе',
    'кончи', 'хочу кончить',
    
    # Эмодзи
    '🍆', '🍑', '💦', '🥵', '😈', '🔞',
}

# Пред-секс маркеры (разогрев)
FOREPLAY_MARKERS = {
    'хочу к тебе', 'приезжай', 'приходи',
    'жду', 'скучаю', 'соскучилась', 'соскучился',
    'хочу обнять', 'хочу целовать', 'хочу тебя',
    'думаю о тебе', 'представляю',
    'когда приедешь', 'когда увидимся',
    '😏', '😘', '💋', '🔥', '❤️‍🔥',
}

# Пост-секс маркеры
AFTERGLOW_MARKERS = {
    'было круто', 'было классно', 'было хорошо',
    'понравилось', 'давай ещё', 'хочу ещё',
    'устала', 'устал', 'засыпаю',
    'спасибо', 'люблю тебя',
    'приятно', 'кайф', 'вау',
    '🥰', '😴', '💕', '🤗',
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
    
    st.subheader(f"🏝️ Острова Секса — {chat_name}")
    st.markdown("""
    Поиск периодов повышенной интимной активности в переписке.
    
    **Острова** = кластеры сообщений с сексуальным контентом, 
    окружённые обычным общением.
    """)
    
    # Собираем данные с точным временем
    messages_data = []
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        text = get_text(msg)
        if not text:
            continue
        
        try:
            dt = parse_date(msg['date'])
        except:
            continue
        
        sex_score = count_markers(text, SEX_MARKERS) * 3
        foreplay_score = count_markers(text, FOREPLAY_MARKERS) * 1.5
        afterglow_score = count_markers(text, AFTERGLOW_MARKERS) * 1
        
        total_score = sex_score + foreplay_score + afterglow_score
        
        if total_score > 0:
            messages_data.append({
                'datetime': dt,
                'date': dt.date(),
                'hour': dt.hour,
                'sender': sender,
                'text': text[:100],
                'sex_score': sex_score,
                'foreplay_score': foreplay_score,
                'afterglow_score': afterglow_score,
                'total_score': total_score,
            })
    
    if not messages_data:
        st.info("🏝️ Островов секса не обнаружено. Переписка довольно целомудренная!")
        return
    
    df = pd.DataFrame(messages_data)
    df = df.sort_values('datetime')
    
    st.success(f"🔥 Найдено **{len(df)}** сообщений с сексуальным контентом")
    
    # Кластеризация по времени
    st.markdown("### 🏝️ Обнаруженные острова")
    
    # Группируем сообщения в острова (если между ними < 4 часов)
    islands = []
    current_island = []
    
    for _, row in df.iterrows():
        if not current_island:
            current_island = [row]
        else:
            time_diff = (row['datetime'] - current_island[-1]['datetime']).total_seconds() / 3600
            if time_diff < 4:  # Меньше 4 часов — тот же остров
                current_island.append(row)
            else:
                # Новый остров
                if len(current_island) >= 2 or sum(r['total_score'] for r in current_island) > 5:
                    islands.append(current_island)
                current_island = [row]
    
    # Добавляем последний остров
    if current_island and (len(current_island) >= 2 or sum(r['total_score'] for r in current_island) > 5):
        islands.append(current_island)
    
    st.info(f"🏝️ Найдено **{len(islands)}** островов секса")
    
    if islands:
        # Статистика по островам
        island_stats = []
        for i, island in enumerate(islands):
            start = island[0]['datetime']
            end = island[-1]['datetime']
            duration = (end - start).total_seconds() / 60  # В минутах
            total_score = sum(r['total_score'] for r in island)
            
            island_stats.append({
                '🏝️ Остров': i + 1,
                '📅 Дата': start.strftime('%d.%m.%Y'),
                '🕐 Начало': start.strftime('%H:%M'),
                '🕐 Конец': end.strftime('%H:%M'),
                '⏱️ Длительность': f"{int(duration)} мин" if duration < 60 else f"{duration/60:.1f} ч",
                '💬 Сообщений': len(island),
                '🔥 Score': f"{total_score:.0f}",
            })
        
        df_islands = pd.DataFrame(island_stats)
        st.dataframe(df_islands, hide_index=True)
        
        # Топ островов
        st.markdown("### 🏆 Топ-5 самых горячих островов")
        
        islands_sorted = sorted(islands, key=lambda x: sum(r['total_score'] for r in x), reverse=True)
        
        for i, island in enumerate(islands_sorted[:5]):
            start = island[0]['datetime']
            total_score = sum(r['total_score'] for r in island)
            
            with st.expander(f"🏝️ #{i+1} — {start.strftime('%d.%m.%Y %H:%M')} (Score: {total_score:.0f})"):
                for msg in island[:10]:
                    st.caption(f"[{msg['datetime'].strftime('%H:%M')}] **{msg['sender']}**: _{msg['text']}..._")
                if len(island) > 10:
                    st.caption(f"... и ещё {len(island) - 10} сообщений")
    
    # Визуализация островов на таймлайне
    st.markdown("### 📈 Таймлайн активности")
    
    # Группируем по дням
    daily_score = df.groupby('date')['total_score'].sum()
    
    fig, ax = plt.subplots(figsize=(14, 5))
    
    ax.bar(daily_score.index, daily_score.values, color='coral', alpha=0.7)
    ax.set_xlabel('Дата')
    ax.set_ylabel('Sex Score')
    ax.set_title('Сексуальная активность по дням')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    
    # По часам
    st.markdown("### 🕐 В какое время острова?")
    
    hourly_score = df.groupby('hour')['total_score'].sum()
    
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    
    hours = list(range(24))
    values = [hourly_score.get(h, 0) for h in hours]
    
    colors = ['#ff4444' if h in [22, 23, 0, 1, 2, 3] else '#ff8888' for h in hours]
    ax2.bar(hours, values, color=colors)
    ax2.set_xlabel('Час')
    ax2.set_ylabel('Sex Score')
    ax2.set_xticks(hours)
    ax2.set_title('Активность по часам')
    
    # Выделяем "золотые часы"
    ax2.axvspan(21.5, 24, alpha=0.1, color='red', label='Ночь')
    ax2.axvspan(-0.5, 3.5, alpha=0.1, color='red')
    
    plt.tight_layout()
    st.pyplot(fig2)
    
    peak_hour = hours[np.argmax(values)]
    st.info(f"🔥 Пиковый час: **{peak_hour}:00**")
    
    # По дням недели
    st.markdown("### 📅 По дням недели")
    
    df['weekday'] = pd.to_datetime(df['date']).dt.dayofweek
    weekday_score = df.groupby('weekday')['total_score'].sum()
    
    days_ru = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    
    values = [weekday_score.get(i, 0) for i in range(7)]
    colors = ['#ff4444' if i >= 5 else '#ff8888' for i in range(7)]
    ax3.bar(days_ru, values, color=colors)
    ax3.set_ylabel('Sex Score')
    ax3.set_title('Активность по дням недели')
    
    plt.tight_layout()
    st.pyplot(fig3)
    
    peak_day = days_ru[np.argmax(values)]
    st.info(f"🔥 Самый горячий день: **{peak_day}**")
    
    # Статистика по участникам
    st.markdown("### 👥 Кто инициирует острова?")
    
    # Первое сообщение каждого острова
    initiators = defaultdict(int)
    for island in islands:
        initiator = island[0]['sender']
        initiators[initiator] += 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Кто начинает острова:**")
        for user, count in sorted(initiators.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(islands) * 100
            st.write(f"**{user}**: {count} раз ({pct:.0f}%)")
    
    with col2:
        # Общий вклад
        user_scores = df.groupby('sender')['total_score'].sum()
        st.markdown("**Общий вклад:**")
        for user, score in user_scores.items():
            st.write(f"**{user}**: {score:.0f} очков")
    
    # Фазы острова
    st.markdown("### 🌅 Фазы острова")
    
    phases = {
        '🌅 Foreplay': df['foreplay_score'].sum(),
        '🔥 Sex': df['sex_score'].sum(),
        '🌙 Afterglow': df['afterglow_score'].sum(),
    }
    
    fig4, ax4 = plt.subplots(figsize=(6, 6))
    colors = ['#ffcc00', '#ff4444', '#9966ff']
    ax4.pie(phases.values(), labels=phases.keys(), colors=colors, autopct='%1.0f%%', startangle=90)
    ax4.set_title('Распределение по фазам')
    st.pyplot(fig4)
    
    # Выводы
    st.markdown("### 💡 Выводы")
    
    if islands:
        # Средняя частота
        dates = sorted(set(df['date']))
        if len(dates) > 1:
            total_days = (dates[-1] - dates[0]).days + 1
            freq = len(islands) / total_days * 30  # Островов в месяц
            
            st.info(f"📊 Частота: примерно **{freq:.1f}** островов в месяц")
        
        # Тренд
        if len(islands) >= 4:
            first_half_islands = len([i for i in islands if i[0]['datetime'] < islands[len(islands)//2][0]['datetime']])
            second_half_islands = len(islands) - first_half_islands
            
            if second_half_islands > first_half_islands * 1.3:
                st.success("📈 Интимная активность **растёт** со временем!")
            elif second_half_islands < first_half_islands * 0.7:
                st.warning("📉 Интимная активность **снижается** со временем")
            else:
                st.info("➡️ Интимная активность стабильна")

