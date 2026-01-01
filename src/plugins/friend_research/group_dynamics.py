"""
Group Dynamics Analyzer
Анализирует динамику группы: активность по времени, 
кто уходит/приходит, как меняется атмосфера.
"""
from collections import defaultdict
from datetime import datetime, timedelta
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
    
    st.subheader(f"👥 Динамика Группы — {chat_name}")
    st.markdown("Как группа развивается со временем")
    
    # Парсим даты и сортируем
    messages_parsed = []
    for msg in messages:
        try:
            dt = parse_date(msg['date'])
            sender = msg.get('from')
            if sender:
                messages_parsed.append({
                    'datetime': dt,
                    'sender': sender,
                    'month': dt.strftime('%Y-%m'),
                    'week': dt.strftime('%Y-W%W'),
                    'text': get_text(msg)
                })
        except:
            continue
    
    if len(messages_parsed) < 10:
        st.warning("Недостаточно сообщений для анализа.")
        return
    
    messages_parsed.sort(key=lambda x: x['datetime'])
    
    # Статистика по месяцам
    monthly_stats = defaultdict(lambda: defaultdict(int))
    monthly_users = defaultdict(set)
    
    for msg in messages_parsed:
        month = msg['month']
        sender = msg['sender']
        monthly_stats[month][sender] += 1
        monthly_users[month].add(sender)
    
    months = sorted(monthly_stats.keys())
    
    # Общая активность
    st.markdown("### 📈 Активность по месяцам")
    
    fig, ax = plt.subplots(figsize=(12, 5))
    
    total_per_month = [sum(monthly_stats[m].values()) for m in months]
    users_per_month = [len(monthly_users[m]) for m in months]
    
    ax.bar(months, total_per_month, alpha=0.7, label='Сообщений')
    ax.set_xlabel('Месяц')
    ax.set_ylabel('Количество сообщений')
    ax.tick_params(axis='x', rotation=45)
    
    # Вторая ось для количества участников
    ax2 = ax.twinx()
    ax2.plot(months, users_per_month, 'r-o', label='Активных участников')
    ax2.set_ylabel('Участников', color='red')
    
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Анализ участников
    st.markdown("### 👤 Активность участников по месяцам")
    
    all_users = set()
    for users in monthly_users.values():
        all_users.update(users)
    
    # Создаём таблицу активности
    activity_data = []
    for user in sorted(all_users):
        row = {'Участник': user}
        for month in months:
            row[month] = monthly_stats[month].get(user, 0)
        activity_data.append(row)
    
    df_activity = pd.DataFrame(activity_data)
    df_activity['Всего'] = df_activity[months].sum(axis=1)
    df_activity = df_activity.sort_values('Всего', ascending=False)
    st.dataframe(df_activity, hide_index=True)
    
    # Heatmap активности
    st.markdown("### 🗓️ Тепловая карта активности")
    
    users_sorted = df_activity['Участник'].tolist()[:15]  # Топ 15
    
    if len(users_sorted) > 1 and len(months) > 1:
        matrix = []
        for user in users_sorted:
            row = [monthly_stats[m].get(user, 0) for m in months]
            matrix.append(row)
        
        fig2, ax2 = plt.subplots(figsize=(max(12, len(months)), max(6, len(users_sorted) * 0.4)))
        
        im = ax2.imshow(matrix, aspect='auto', cmap='YlOrRd')
        
        ax2.set_xticks(range(len(months)))
        ax2.set_xticklabels(months, rotation=45, ha='right')
        ax2.set_yticks(range(len(users_sorted)))
        ax2.set_yticklabels(users_sorted)
        
        plt.colorbar(im, ax=ax2, label='Сообщений')
        plt.tight_layout()
        st.pyplot(fig2)
    
    # Анализ "ухода" и "прихода"
    st.markdown("### 📊 Появление и уход участников")
    
    first_seen = {}
    last_seen = {}
    
    for msg in messages_parsed:
        user = msg['sender']
        month = msg['month']
        
        if user not in first_seen:
            first_seen[user] = month
        last_seen[user] = month
    
    # Новички по месяцам
    newcomers = defaultdict(list)
    for user, month in first_seen.items():
        newcomers[month].append(user)
    
    # Кто ушёл (не писал 3+ месяца)
    last_month = months[-1] if months else None
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🆕 Новые участники по месяцам:**")
        for month in months[-12:]:  # Последние 12 месяцев
            if newcomers[month]:
                st.write(f"**{month}**: {', '.join(newcomers[month][:5])}" + 
                        (f" (+{len(newcomers[month])-5} ещё)" if len(newcomers[month]) > 5 else ""))
    
    with col2:
        if last_month:
            # Определяем "ушедших" - не писали последние 3 месяца
            recent_months = months[-3:] if len(months) >= 3 else months
            recent_users = set()
            for m in recent_months:
                recent_users.update(monthly_users[m])
            
            all_time_users = set()
            for m in months[:-3] if len(months) > 3 else months[:1]:
                all_time_users.update(monthly_users[m])
            
            inactive = all_time_users - recent_users
            
            if inactive:
                st.markdown("**👋 Давно не писали:**")
                for user in list(inactive)[:10]:
                    last = last_seen.get(user, 'неизвестно')
                    st.write(f"**{user}**: последний раз в {last}")
    
    # Тренды
    st.markdown("### 📉 Тренды")
    
    if len(months) >= 6:
        first_half = sum(sum(monthly_stats[m].values()) for m in months[:len(months)//2])
        second_half = sum(sum(monthly_stats[m].values()) for m in months[len(months)//2:])
        
        if first_half > 0:
            change = (second_half - first_half) / first_half * 100
            
            if change > 30:
                st.success(f"📈 Активность группы выросла на {change:.0f}%")
            elif change < -30:
                st.warning(f"📉 Активность группы упала на {abs(change):.0f}%")
            else:
                st.info(f"➡️ Активность группы стабильна (изменение: {change:+.0f}%)")
    
    # Пиковые периоды
    if months:
        peak_month = max(months, key=lambda m: sum(monthly_stats[m].values()))
        low_month = min(months, key=lambda m: sum(monthly_stats[m].values()))
        
        st.markdown(f"""
        **📊 Статистика:**
        - 🔥 Пиковый месяц: **{peak_month}** ({sum(monthly_stats[peak_month].values())} сообщений)
        - 📉 Самый тихий месяц: **{low_month}** ({sum(monthly_stats[low_month].values())} сообщений)
        - 👥 Всего участников за всё время: **{len(all_users)}**
        """)

