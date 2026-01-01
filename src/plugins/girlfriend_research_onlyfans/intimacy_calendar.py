"""
Intimacy Calendar 📅
Календарь интимной активности.
Визуализация паттернов на календаре.
"""
from collections import defaultdict
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import calendar


# Интимные маркеры
INTIMACY_MARKERS = {
    'секс', 'sex', 'трах', 'кончить',
    'хочу тебя', 'хочу к тебе', 'приезжай', 'приходи',
    'соскучилась', 'соскучился', 'жду тебя',
    'целую', 'обнимаю', 'хочу обнять', 'хочу целовать',
    '🍆', '🍑', '💦', '🥵', '😈', '😏', '💋', '🔥', '❤️‍🔥',
    'голая', 'голый', 'раздеться', 'nude',
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
    
    st.subheader(f"📅 Календарь Интимности — {chat_name}")
    st.markdown("Визуализация интимной активности на календаре")
    
    # Собираем данные по дням
    daily_score = defaultdict(float)
    
    for msg in messages:
        text = get_text(msg)
        if not text:
            continue
        
        try:
            dt = parse_date(msg['date'])
            date_key = dt.date()
        except:
            continue
        
        score = count_markers(text, INTIMACY_MARKERS)
        daily_score[date_key] += score
    
    if not daily_score:
        st.info("Нет данных для отображения.")
        return
    
    dates = sorted(daily_score.keys())
    
    # Выбор месяца для отображения
    months_available = sorted(set(d.strftime('%Y-%m') for d in dates))
    
    if not months_available:
        st.warning("Нет данных.")
        return
    
    selected_month = st.selectbox("Выберите месяц", months_available, index=len(months_available)-1)
    
    year, month = map(int, selected_month.split('-'))
    
    # Создаём календарь
    st.markdown(f"### 🗓️ {calendar.month_name[month]} {year}")
    
    # Получаем данные для месяца
    cal = calendar.monthcalendar(year, month)
    
    # Создаём heatmap
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Матрица для heatmap
    heatmap_data = np.zeros((len(cal), 7))
    heatmap_data[:] = np.nan
    
    for week_idx, week in enumerate(cal):
        for day_idx, day in enumerate(week):
            if day != 0:
                date = datetime(year, month, day).date()
                score = daily_score.get(date, 0)
                heatmap_data[week_idx, day_idx] = score
    
    # Рисуем
    cmap = plt.cm.Reds
    cmap.set_bad('white')
    
    im = ax.imshow(heatmap_data, cmap=cmap, aspect='auto', vmin=0, vmax=max(daily_score.values()) if daily_score else 1)
    
    # Подписи
    days_header = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    ax.set_xticks(range(7))
    ax.set_xticklabels(days_header)
    ax.set_yticks(range(len(cal)))
    ax.set_yticklabels([f'Неделя {i+1}' for i in range(len(cal))])
    
    # Добавляем числа дней
    for week_idx, week in enumerate(cal):
        for day_idx, day in enumerate(week):
            if day != 0:
                date = datetime(year, month, day).date()
                score = daily_score.get(date, 0)
                text_color = 'white' if score > 2 else 'black'
                ax.text(day_idx, week_idx, str(day), ha='center', va='center', 
                       fontsize=12, fontweight='bold', color=text_color)
    
    plt.colorbar(im, ax=ax, label='Intimacy Score')
    ax.set_title(f'{calendar.month_name[month]} {year}')
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Статистика месяца
    month_dates = [d for d in dates if d.strftime('%Y-%m') == selected_month]
    month_scores = [daily_score[d] for d in month_dates]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Активных дней", len([s for s in month_scores if s > 0]))
    
    with col2:
        st.metric("Всего очков", f"{sum(month_scores):.0f}")
    
    with col3:
        st.metric("Макс. за день", f"{max(month_scores) if month_scores else 0:.0f}")
    
    with col4:
        avg = np.mean(month_scores) if month_scores else 0
        st.metric("Среднее", f"{avg:.1f}")
    
    # Годовой обзор
    st.markdown("### 📊 Годовой обзор")
    
    # Группируем по месяцам
    monthly_totals = defaultdict(float)
    for date, score in daily_score.items():
        monthly_totals[date.strftime('%Y-%m')] += score
    
    months = sorted(monthly_totals.keys())
    values = [monthly_totals[m] for m in months]
    
    fig2, ax2 = plt.subplots(figsize=(14, 5))
    
    colors = ['#ff4444' if v > np.mean(values) else '#ff8888' for v in values]
    ax2.bar(months, values, color=colors)
    ax2.axhline(y=np.mean(values), color='gray', linestyle='--', alpha=0.7, label=f'Среднее: {np.mean(values):.1f}')
    ax2.set_xlabel('Месяц')
    ax2.set_ylabel('Intimacy Score')
    ax2.set_title('Интимная активность по месяцам')
    ax2.tick_params(axis='x', rotation=45)
    ax2.legend()
    
    plt.tight_layout()
    st.pyplot(fig2)
    
    # Топ дней
    st.markdown("### 🔥 Топ-10 самых горячих дней")
    
    top_days = sorted(daily_score.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for date, score in top_days:
        weekday = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][date.weekday()]
        st.write(f"🔥 **{date.strftime('%d.%m.%Y')}** ({weekday}): {score:.0f} очков")
    
    # Паттерны по дням недели
    st.markdown("### 📅 Паттерны по дням недели")
    
    weekday_scores = defaultdict(list)
    for date, score in daily_score.items():
        weekday_scores[date.weekday()].append(score)
    
    weekday_avg = {d: np.mean(scores) if scores else 0 for d, scores in weekday_scores.items()}
    
    days_ru = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    
    values = [weekday_avg.get(i, 0) for i in range(7)]
    colors = ['#ff4444' if i >= 4 else '#ff8888' for i in range(7)]  # Пт-Вс выделяем
    ax3.bar(days_ru, values, color=colors)
    ax3.set_ylabel('Средний Score')
    ax3.set_title('Средняя интимность по дням недели')
    
    plt.tight_layout()
    st.pyplot(fig3)
    
    hottest_day = days_ru[np.argmax(values)]
    st.info(f"🔥 Самый горячий день недели: **{hottest_day}**")
    
    # Выводы
    st.markdown("### 💡 Выводы")
    
    # Тренд
    if len(months) >= 4:
        first_half = sum(values[:len(values)//2])
        second_half = sum(values[len(values)//2:])
        
        if first_half > 0:
            change = (second_half - first_half) / first_half * 100
            
            if change > 30:
                st.success(f"📈 Интимная активность выросла на {change:.0f}%!")
            elif change < -30:
                st.warning(f"📉 Интимная активность снизилась на {abs(change):.0f}%")
            else:
                st.info("➡️ Интимная активность стабильна")
    
    # Регулярность
    total_days = (dates[-1] - dates[0]).days + 1 if dates else 0
    active_days = len([s for s in daily_score.values() if s > 0])
    
    if total_days > 0:
        frequency = active_days / total_days * 100
        st.info(f"📊 Интимные дни: **{frequency:.0f}%** от всех дней ({active_days} из {total_days})")

