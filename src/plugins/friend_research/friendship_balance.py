"""
Friendship Balance Analyzer
Анализирует баланс общения между участниками группы.
Кто с кем больше общается, кто игнорирует кого.
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
    
    st.subheader(f"⚖️ Баланс Дружбы — {chat_name}")
    st.markdown("Анализ взаимодействий между участниками группы")
    
    # Собираем статистику
    user_stats = defaultdict(lambda: {
        'messages': 0,
        'chars': 0,
        'replies_to': defaultdict(int),  # Кому отвечает
        'replies_from': defaultdict(int),  # Кто отвечает
        'mentions': defaultdict(int),  # Кого упоминает
    })
    
    # Карта ID -> отправитель
    id_to_sender = {}
    for msg in messages:
        msg_id = msg.get('id')
        sender = msg.get('from')
        if msg_id and sender:
            id_to_sender[msg_id] = sender
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        text = get_text(msg)
        user_stats[sender]['messages'] += 1
        user_stats[sender]['chars'] += len(text)
        
        # Анализ ответов
        reply_to_id = msg.get('reply_to_message_id')
        if reply_to_id and reply_to_id in id_to_sender:
            replied_to = id_to_sender[reply_to_id]
            if replied_to != sender:
                user_stats[sender]['replies_to'][replied_to] += 1
                user_stats[replied_to]['replies_from'][sender] += 1
        
        # Анализ упоминаний (@username)
        if isinstance(msg.get('text'), list):
            for part in msg['text']:
                if isinstance(part, dict) and part.get('type') == 'mention':
                    mentioned = part.get('text', '').lstrip('@')
                    if mentioned and mentioned != sender:
                        user_stats[sender]['mentions'][mentioned] += 1
    
    users = list(user_stats.keys())
    
    if len(users) < 2:
        st.warning("Нужно минимум 2 участника для анализа.")
        return
    
    # Основная статистика
    st.markdown("### 📊 Общая активность")
    
    table_data = []
    for user in users:
        stats = user_stats[user]
        total_replies_to = sum(stats['replies_to'].values())
        total_replies_from = sum(stats['replies_from'].values())
        reply_ratio = total_replies_from / total_replies_to if total_replies_to > 0 else 0
        
        table_data.append({
            'Участник': user,
            'Сообщений': stats['messages'],
            'Символов': stats['chars'],
            'Ответил другим': total_replies_to,
            'Получил ответов': total_replies_from,
            'Коэфф. отклика': f"{reply_ratio:.2f}"
        })
    
    df = pd.DataFrame(table_data)
    df = df.sort_values('Сообщений', ascending=False)
    st.dataframe(df, hide_index=True)
    
    # Матрица взаимодействий
    st.markdown("### 🔗 Матрица ответов")
    st.caption("Строка → Столбец: сколько раз пользователь из строки ответил пользователю из столбца")
    
    # Создаём матрицу
    matrix_data = []
    for user_from in users:
        row = {'От': user_from}
        for user_to in users:
            if user_from == user_to:
                row[user_to] = '—'
            else:
                row[user_to] = user_stats[user_from]['replies_to'].get(user_to, 0)
        matrix_data.append(row)
    
    df_matrix = pd.DataFrame(matrix_data)
    df_matrix = df_matrix.set_index('От')
    st.dataframe(df_matrix)
    
    # Визуализация
    st.markdown("### 📊 Визуализация")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Круговая диаграмма активности
        fig1, ax1 = plt.subplots(figsize=(6, 6))
        msg_counts = [user_stats[u]['messages'] for u in users]
        ax1.pie(msg_counts, labels=users, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Доля сообщений')
        st.pyplot(fig1)
    
    with col2:
        # Топ пар по взаимодействию
        pairs = []
        for user1 in users:
            for user2 in users:
                if user1 < user2:  # Избегаем дублей
                    interaction = (
                        user_stats[user1]['replies_to'].get(user2, 0) +
                        user_stats[user2]['replies_to'].get(user1, 0)
                    )
                    if interaction > 0:
                        pairs.append((user1, user2, interaction))
        
        pairs.sort(key=lambda x: x[2], reverse=True)
        
        if pairs:
            st.markdown("**🤝 Топ пар по общению:**")
            for u1, u2, count in pairs[:10]:
                st.write(f"**{u1}** ↔ **{u2}**: {count} ответов")
        else:
            st.info("Нет данных о взаимных ответах")
    
    # Анализ изолированных участников
    st.markdown("### 🔍 Анализ")
    
    for user in users:
        stats = user_stats[user]
        total_replies_to = sum(stats['replies_to'].values())
        total_replies_from = sum(stats['replies_from'].values())
        
        if stats['messages'] > 10:
            if total_replies_from == 0 and total_replies_to > 5:
                st.warning(f"⚠️ **{user}**: много отвечает другим, но не получает ответов")
            elif total_replies_to == 0 and stats['messages'] > 20:
                st.info(f"📝 **{user}**: активен, но не отвечает на сообщения других")
            elif total_replies_from > total_replies_to * 3:
                st.success(f"⭐ **{user}**: очень популярен в группе (получает в 3+ раз больше ответов)")
    
    # Взаимность
    st.markdown("### 💫 Взаимность общения")
    
    for user in users:
        stats = user_stats[user]
        if sum(stats['replies_to'].values()) > 5:
            # Находим с кем чаще всего общается
            top_partner = max(stats['replies_to'].items(), key=lambda x: x[1], default=(None, 0))
            if top_partner[0]:
                # Проверяем взаимность
                reverse = user_stats[top_partner[0]]['replies_to'].get(user, 0)
                ratio = reverse / top_partner[1] if top_partner[1] > 0 else 0
                
                if ratio > 0.7:
                    st.success(f"✅ **{user}** и **{top_partner[0]}**: взаимное активное общение")
                elif ratio < 0.3:
                    st.info(f"📊 **{user}** больше общается с **{top_partner[0]}** ({top_partner[1]}), чем наоборот ({reverse})")

