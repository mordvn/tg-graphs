"""
Response Time Analyzer
Анализирует скорость ответа каждого участника
Показывает кто отвечает быстрее и как это меняется со временем
"""
from collections import defaultdict
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def format_duration(seconds):
    """Форматирует длительность в читаемый вид"""
    if seconds < 60:
        return f"{int(seconds)}с"
    elif seconds < 3600:
        return f"{int(seconds // 60)}м"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}ч {minutes}м" if minutes else f"{hours}ч"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}д {hours}ч" if hours else f"{days}д"


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"⏱️ Время Ответа — {chat_name}")
    st.markdown("Анализ скорости реакции на сообщения партнёра")
    
    # Максимальное время ожидания ответа (всё что больше — не считается ответом)
    max_response_hours = st.slider(
        "Максимальное время ответа (часы)", 
        min_value=1, max_value=48, value=12,
        help="Если ответ пришёл позже — не считаем это ответом на предыдущее сообщение"
    )
    max_response_time = timedelta(hours=max_response_hours)
    
    # Парсим и сортируем сообщения
    messages_sorted = []
    for msg in messages:
        try:
            dt = parse_date(msg["date"])
            sender = msg.get("from")
            if sender:
                messages_sorted.append({
                    'datetime': dt,
                    'sender': sender,
                    'month': dt.strftime('%Y-%m'),
                    'hour': dt.hour
                })
        except:
            continue
    
    messages_sorted.sort(key=lambda x: x['datetime'])
    
    if len(messages_sorted) < 2:
        st.warning("Недостаточно сообщений для анализа.")
        return
    
    # Собираем время ответов
    response_times = defaultdict(list)
    monthly_response_times = defaultdict(lambda: defaultdict(list))
    hourly_response_times = defaultdict(lambda: defaultdict(list))
    
    prev_msg = messages_sorted[0]
    
    for msg in messages_sorted[1:]:
        if msg['sender'] != prev_msg['sender']:
            # Это ответ на предыдущее сообщение
            response_time = (msg['datetime'] - prev_msg['datetime']).total_seconds()
            
            if response_time <= max_response_time.total_seconds():
                responder = msg['sender']
                response_times[responder].append(response_time)
                monthly_response_times[msg['month']][responder].append(response_time)
                hourly_response_times[msg['hour']][responder].append(response_time)
        
        prev_msg = msg
    
    if not response_times:
        st.warning("Не удалось вычислить время ответов.")
        return
    
    # Основная статистика
    st.markdown("### 📊 Статистика времени ответа")
    
    table_data = []
    for user, times in response_times.items():
        if times:
            avg_time = np.mean(times)
            median_time = np.median(times)
            min_time = min(times)
            max_time = max(times)
            
            # Быстрые ответы (< 5 минут)
            fast_responses = sum(1 for t in times if t < 300)
            fast_ratio = fast_responses / len(times) * 100
            
            # Медленные ответы (> 1 час)
            slow_responses = sum(1 for t in times if t > 3600)
            slow_ratio = slow_responses / len(times) * 100
            
            table_data.append({
                'Пользователь': user,
                'Ответов': len(times),
                'Среднее': format_duration(avg_time),
                'Медиана': format_duration(median_time),
                'Мин': format_duration(min_time),
                'Макс': format_duration(max_time),
                'Быстрых (<5м)': f"{fast_ratio:.0f}%",
                'Медленных (>1ч)': f"{slow_ratio:.0f}%"
            })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # Визуализация распределения
    st.markdown("### 📈 Распределение времени ответа")
    
    users = list(response_times.keys())
    
    fig, axes = plt.subplots(1, len(users), figsize=(6*len(users), 5))
    if len(users) == 1:
        axes = [axes]
    
    for idx, user in enumerate(users):
        times = response_times[user]
        # Конвертируем в минуты для лучшей читаемости
        times_minutes = [t / 60 for t in times]
        
        # Ограничиваем для визуализации
        times_capped = [min(t, 120) for t in times_minutes]  # Кап на 2 часах
        
        axes[idx].hist(times_capped, bins=30, alpha=0.7, color='steelblue', edgecolor='white')
        axes[idx].axvline(np.median(times_minutes), color='red', linestyle='--', label=f'Медиана: {format_duration(np.median(times)*60)}')
        axes[idx].set_xlabel('Минуты')
        axes[idx].set_ylabel('Количество')
        axes[idx].set_title(f'{user}')
        axes[idx].legend()
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Сравнение
    if len(users) == 2:
        st.markdown("### ⚖️ Сравнение")
        
        user1, user2 = users
        avg1 = np.mean(response_times[user1])
        avg2 = np.mean(response_times[user2])
        
        faster = user1 if avg1 < avg2 else user2
        slower = user2 if avg1 < avg2 else user1
        ratio = max(avg1, avg2) / min(avg1, avg2) if min(avg1, avg2) > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"{user1} (среднее)", format_duration(avg1))
        with col2:
            st.metric(f"{user2} (среднее)", format_duration(avg2))
        with col3:
            st.metric("Разница", f"{ratio:.1f}x")
        
        if ratio > 3:
            st.warning(f"""
            ⚠️ **{faster}** отвечает значительно быстрее (в {ratio:.1f} раз).
            
            Это может указывать на:
            - Разный уровень заинтересованности
            - Разную доступность (работа, учёба)
            - Разное отношение к переписке
            """)
        elif ratio > 1.5:
            st.info(f"📊 **{faster}** отвечает быстрее, но разница не критична")
        else:
            st.success("✅ Скорость ответов примерно одинакова — хороший признак!")
    
    # Динамика по месяцам
    if len(monthly_response_times) > 1:
        st.markdown("### 📈 Динамика по месяцам")
        
        months = sorted(monthly_response_times.keys())
        
        fig2, ax = plt.subplots(figsize=(12, 5))
        
        for user in users:
            avg_times = []
            for month in months:
                times = monthly_response_times[month].get(user, [])
                avg = np.mean(times) / 60 if times else None  # В минутах
                avg_times.append(avg)
            
            # Интерполяция для пропущенных месяцев
            ax.plot(months, avg_times, marker='o', label=user, linewidth=2)
        
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Среднее время ответа (минуты)')
        ax.set_title('Как меняется время ответа со временем')
        ax.legend()
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)
        
        # Анализ тренда
        st.markdown("#### 📉 Анализ тренда")
        for user in users:
            all_avgs = []
            for month in months:
                times = monthly_response_times[month].get(user, [])
                if times:
                    all_avgs.append(np.mean(times))
            
            if len(all_avgs) >= 4:
                first_half = np.mean(all_avgs[:len(all_avgs)//2])
                second_half = np.mean(all_avgs[len(all_avgs)//2:])
                
                change = (second_half - first_half) / first_half * 100 if first_half > 0 else 0
                
                if change > 30:
                    st.warning(f"📉 **{user}**: время ответа увеличилось на {change:.0f}% (отвечает медленнее)")
                elif change < -30:
                    st.success(f"📈 **{user}**: время ответа уменьшилось на {abs(change):.0f}% (отвечает быстрее)")
                else:
                    st.info(f"➡️ **{user}**: время ответа стабильно")
    
    # Время суток
    st.markdown("### 🕐 Время ответа по часам")
    
    fig3, ax = plt.subplots(figsize=(12, 5))
    
    hours = list(range(24))
    
    for user in users:
        avg_by_hour = []
        for h in hours:
            times = hourly_response_times[h].get(user, [])
            avg = np.mean(times) / 60 if times else None  # В минутах
            avg_by_hour.append(avg)
        
        ax.plot(hours, avg_by_hour, marker='o', label=user, linewidth=2)
    
    ax.set_xlabel('Час')
    ax.set_ylabel('Среднее время ответа (минуты)')
    ax.set_title('Когда отвечают быстрее?')
    ax.set_xticks(hours)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig3)
    
    # Интерпретация
    st.markdown("### 💡 Что это значит")
    
    st.markdown("""
    **Здоровые отношения:**
    - Оба партнёра отвечают в разумные сроки
    - Время ответа примерно одинаковое
    - Нет явного тренда на замедление
    
    **Тревожные признаки:**
    - Один отвечает в разы медленнее другого
    - Время ответа растёт со временем
    - Постоянные задержки в определённое время (возможно, есть что-то более интересное)
    
    **Важно помнить:**
    - Разница может объясняться работой/учёбой
    - Не все люди одинаково зависят от телефона
    - Смотрите на тренды, а не на абсолютные значения
    """)
