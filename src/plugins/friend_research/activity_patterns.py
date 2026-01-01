"""
Activity Patterns Analyzer
Анализирует паттерны активности: когда кто пишет,
какие дни недели самые активные, ночные совы vs жаворонки.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


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


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"📈 Паттерны Активности — {chat_name}")
    st.markdown("Когда участники наиболее активны")
    
    # Статистика
    user_hourly = defaultdict(lambda: [0] * 24)
    user_daily = defaultdict(lambda: [0] * 7)  # Пн-Вс
    hourly_total = [0] * 24
    daily_total = [0] * 7
    
    for msg in messages:
        try:
            dt = parse_date(msg['date'])
            sender = msg.get('from')
            if sender:
                hour = dt.hour
                weekday = dt.weekday()
                
                user_hourly[sender][hour] += 1
                user_daily[sender][weekday] += 1
                hourly_total[hour] += 1
                daily_total[weekday] += 1
        except:
            continue
    
    users = list(user_hourly.keys())
    
    if not users:
        st.warning("Не удалось проанализировать активность.")
        return
    
    # Общая активность по часам
    st.markdown("### 🕐 Активность по часам")
    
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    
    hours = list(range(24))
    ax1.bar(hours, hourly_total, alpha=0.7, color='steelblue')
    ax1.set_xlabel('Час')
    ax1.set_ylabel('Сообщений')
    ax1.set_xticks(hours)
    ax1.set_title('Общая активность группы по часам')
    
    plt.tight_layout()
    st.pyplot(fig1)
    
    # По дням недели
    st.markdown("### 📅 Активность по дням недели")
    
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.bar(days, daily_total, alpha=0.7, color='coral')
    ax2.set_xlabel('День недели')
    ax2.set_ylabel('Сообщений')
    ax2.set_title('Активность по дням недели')
    
    plt.tight_layout()
    st.pyplot(fig2)
    
    # Heatmap по часам и дням
    st.markdown("### 🗓️ Тепловая карта: часы × дни")
    
    # Собираем данные для heatmap
    heatmap_data = [[0] * 24 for _ in range(7)]
    
    for msg in messages:
        try:
            dt = parse_date(msg['date'])
            hour = dt.hour
            weekday = dt.weekday()
            heatmap_data[weekday][hour] += 1
        except:
            continue
    
    fig3, ax3 = plt.subplots(figsize=(14, 6))
    
    im = ax3.imshow(heatmap_data, aspect='auto', cmap='YlOrRd')
    
    ax3.set_xticks(range(24))
    ax3.set_xticklabels([f'{h}:00' for h in range(24)], rotation=45, ha='right')
    ax3.set_yticks(range(7))
    ax3.set_yticklabels(days)
    ax3.set_xlabel('Час')
    ax3.set_ylabel('День недели')
    
    plt.colorbar(im, ax=ax3, label='Сообщений')
    plt.tight_layout()
    st.pyplot(fig3)
    
    # Анализ по участникам
    st.markdown("### 👤 Профили активности участников")
    
    # Определяем тип активности для каждого
    profiles = []
    for user in users:
        hourly = user_hourly[user]
        total = sum(hourly)
        
        if total < 10:
            continue
        
        # Ночь: 0-6, Утро: 6-12, День: 12-18, Вечер: 18-24
        night = sum(hourly[0:6])
        morning = sum(hourly[6:12])
        afternoon = sum(hourly[12:18])
        evening = sum(hourly[18:24])
        
        # Определяем тип
        max_period = max([
            ('🌙 Ночная сова', night),
            ('🌅 Жаворонок', morning),
            ('☀️ Дневной', afternoon),
            ('🌆 Вечерний', evening)
        ], key=lambda x: x[1])
        
        # Пиковый час
        peak_hour = hourly.index(max(hourly))
        
        profiles.append({
            'Участник': user,
            'Сообщений': total,
            'Тип': max_period[0],
            'Пиковый час': f'{peak_hour}:00',
            '🌙 Ночь': f"{night/total*100:.0f}%",
            '🌅 Утро': f"{morning/total*100:.0f}%",
            '☀️ День': f"{afternoon/total*100:.0f}%",
            '🌆 Вечер': f"{evening/total*100:.0f}%",
        })
    
    df_profiles = pd.DataFrame(profiles)
    df_profiles = df_profiles.sort_values('Сообщений', ascending=False)
    st.dataframe(df_profiles, hide_index=True)
    
    # График сравнения топ участников
    st.markdown("### 📊 Сравнение профилей топ-5")
    
    top_users = df_profiles['Участник'].head(5).tolist()
    
    if len(top_users) >= 2:
        fig4, ax4 = plt.subplots(figsize=(12, 6))
        
        hours = list(range(24))
        
        for user in top_users:
            hourly = user_hourly[user]
            # Нормализуем для сравнения
            total = sum(hourly)
            normalized = [h/total*100 for h in hourly] if total > 0 else hourly
            ax4.plot(hours, normalized, marker='o', label=user, linewidth=2, markersize=4)
        
        ax4.set_xlabel('Час')
        ax4.set_ylabel('% от всех сообщений пользователя')
        ax4.set_xticks(hours)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_title('Профили активности (нормализованные)')
        
        plt.tight_layout()
        st.pyplot(fig4)
    
    # Интересные факты
    st.markdown("### 💡 Интересные факты")
    
    # Самый активный час
    peak_hour = hourly_total.index(max(hourly_total))
    st.info(f"🔥 Самый активный час группы: **{peak_hour}:00** ({hourly_total[peak_hour]} сообщений)")
    
    # Самый активный день
    peak_day = daily_total.index(max(daily_total))
    st.info(f"📅 Самый активный день: **{days[peak_day]}** ({daily_total[peak_day]} сообщений)")
    
    # Ночные совы
    night_owls = [p for p in profiles if '🌙' in p['Тип']]
    if night_owls:
        st.markdown(f"🌙 **Ночные совы:** {', '.join(p['Участник'] for p in night_owls[:5])}")
    
    # Жаворонки
    early_birds = [p for p in profiles if '🌅' in p['Тип']]
    if early_birds:
        st.markdown(f"🌅 **Жаворонки:** {', '.join(p['Участник'] for p in early_birds[:5])}")
    
    # Выходные vs будни
    weekday_msgs = sum(daily_total[:5])
    weekend_msgs = sum(daily_total[5:])
    
    if weekday_msgs + weekend_msgs > 0:
        weekend_ratio = weekend_msgs / (weekday_msgs + weekend_msgs) * 100
        if weekend_ratio > 35:
            st.success(f"🎉 Группа активна на выходных ({weekend_ratio:.0f}% сообщений)")
        else:
            st.info(f"💼 Группа больше активна в будни ({100-weekend_ratio:.0f}% сообщений)")

