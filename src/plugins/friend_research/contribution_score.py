"""
Contribution Score Analyzer
Оценивает вклад каждого участника в группу.
Учитывает количество, качество, полезность сообщений.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re


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


# Маркеры полезного контента
USEFUL_MARKERS = {
    'ссылка', 'link', 'http', 'https', 'www',
    'инструкция', 'гайд', 'tutorial', 'совет', 'рекомендую',
    'решение', 'ответ', 'помог', 'работает', 'исправил',
}

# Маркеры вопросов (инициирует обсуждение)
QUESTION_MARKERS = {
    '?', 'как', 'почему', 'зачем', 'где', 'когда', 'кто', 'что',
    'подскажите', 'помогите', 'знает кто', 'кто-нибудь',
}

# Маркеры юмора (развлекает группу)
HUMOR_MARKERS = {
    'хаха', 'хехе', 'хихи', 'лол', 'lol', 'ахах', 'ржу',
    '😂', '🤣', '😆', '😹', '💀', 'кек', 'ору',
}


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"🏆 Вклад в Общение — {chat_name}")
    st.markdown("Оценка полезности и активности каждого участника")
    
    # Карта ID -> отправитель для подсчёта реакций
    id_to_sender = {}
    for msg in messages:
        msg_id = msg.get('id')
        sender = msg.get('from')
        if msg_id and sender:
            id_to_sender[msg_id] = sender
    
    # Статистика
    user_stats = defaultdict(lambda: {
        'messages': 0,
        'chars': 0,
        'words': 0,
        'links': 0,
        'questions': 0,
        'answers': 0,  # Ответы на чужие сообщения
        'humor': 0,
        'media': 0,  # Фото, видео, файлы
        'reactions_received': 0,
        'replies_received': 0,
        'stickers': 0,
        'voice': 0,
        'useful': 0,  # Полезный контент
    })
    
    # Подсчёт ответов на сообщения
    reply_counts = defaultdict(int)
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        text = get_text(msg)
        text_lower = text.lower()
        
        user_stats[sender]['messages'] += 1
        user_stats[sender]['chars'] += len(text)
        user_stats[sender]['words'] += len(text.split())
        
        # Ссылки
        if re.search(r'https?://', text):
            user_stats[sender]['links'] += 1
        
        # Вопросы
        if '?' in text or any(m in text_lower for m in ['подскажите', 'помогите', 'знает кто']):
            user_stats[sender]['questions'] += 1
        
        # Юмор
        if any(m in text_lower for m in HUMOR_MARKERS):
            user_stats[sender]['humor'] += 1
        
        # Полезный контент
        if any(m in text_lower for m in USEFUL_MARKERS):
            user_stats[sender]['useful'] += 1
        
        # Медиа
        if msg.get('photo') or msg.get('file'):
            user_stats[sender]['media'] += 1
        
        # Стикеры
        if msg.get('media_type') == 'sticker':
            user_stats[sender]['stickers'] += 1
        
        # Голосовые
        if msg.get('media_type') == 'voice_message':
            user_stats[sender]['voice'] += 1
        
        # Ответы
        reply_to = msg.get('reply_to_message_id')
        if reply_to and reply_to in id_to_sender:
            replied_to = id_to_sender[reply_to]
            if replied_to != sender:
                user_stats[sender]['answers'] += 1
                user_stats[replied_to]['replies_received'] += 1
        
        # Реакции
        for reaction in msg.get('reactions', []):
            count = reaction.get('count', 0)
            user_stats[sender]['reactions_received'] += count
    
    users = list(user_stats.keys())
    
    if not users:
        st.warning("Нет данных для анализа.")
        return
    
    # Вычисляем баллы
    scores = []
    for user in users:
        stats = user_stats[user]
        
        # Базовые баллы за количество
        base_score = stats['messages'] * 1
        
        # Бонусы за качество
        quality_score = (
            stats['links'] * 5 +  # Полезные ссылки
            stats['useful'] * 3 +  # Полезный контент
            stats['answers'] * 2 +  # Ответы другим
            stats['media'] * 1 +  # Медиа контент
            stats['humor'] * 1  # Юмор
        )
        
        # Бонусы за социальный вклад
        social_score = (
            stats['replies_received'] * 2 +  # Получает ответы
            stats['reactions_received'] * 1  # Получает реакции
        )
        
        # Штрафы за "шум"
        noise_penalty = stats['stickers'] * 0.5  # Много стикеров = меньше пользы
        
        # Средняя длина сообщения (бонус за развёрнутость)
        avg_length = stats['chars'] / stats['messages'] if stats['messages'] > 0 else 0
        length_bonus = min(avg_length / 50, 2)  # Макс +2 балла
        
        total_score = base_score + quality_score + social_score - noise_penalty + length_bonus
        
        scores.append({
            'user': user,
            'total': total_score,
            'base': base_score,
            'quality': quality_score,
            'social': social_score,
            'stats': stats
        })
    
    # Сортируем по баллам
    scores.sort(key=lambda x: x['total'], reverse=True)
    
    # Основная таблица
    st.markdown("### 📊 Рейтинг участников")
    
    table_data = []
    for i, s in enumerate(scores):
        stats = s['stats']
        rank = ['🥇', '🥈', '🥉'][i] if i < 3 else f'{i+1}'
        
        table_data.append({
            'Место': rank,
            'Участник': s['user'],
            '🏆 Баллы': f"{s['total']:.0f}",
            '💬 Сообщ.': stats['messages'],
            '🔗 Ссылки': stats['links'],
            '❓ Вопросы': stats['questions'],
            '💡 Ответы': stats['answers'],
            '😂 Юмор': stats['humor'],
            '📷 Медиа': stats['media'],
            '❤️ Реакции': stats['reactions_received'],
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # Визуализация
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏆 Топ-10 по баллам")
        
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        
        top_10 = scores[:10]
        names = [s['user'][:15] for s in top_10]
        values = [s['total'] for s in top_10]
        
        colors = ['gold', 'silver', '#cd7f32'] + ['steelblue'] * 7
        ax1.barh(names[::-1], values[::-1], color=colors[:len(names)][::-1])
        ax1.set_xlabel('Баллы')
        ax1.set_title('Топ-10 участников')
        
        plt.tight_layout()
        st.pyplot(fig1)
    
    with col2:
        st.markdown("#### 📊 Распределение баллов")
        
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        
        # Stacked bar для топ-5
        top_5 = scores[:5]
        names = [s['user'][:15] for s in top_5]
        base = [s['base'] for s in top_5]
        quality = [s['quality'] for s in top_5]
        social = [s['social'] for s in top_5]
        
        x = range(len(names))
        ax2.bar(x, base, label='Базовые', color='steelblue')
        ax2.bar(x, quality, bottom=base, label='Качество', color='green')
        ax2.bar(x, social, bottom=[b+q for b,q in zip(base, quality)], label='Социальные', color='orange')
        
        ax2.set_xticks(x)
        ax2.set_xticklabels(names, rotation=45, ha='right')
        ax2.set_ylabel('Баллы')
        ax2.legend()
        
        plt.tight_layout()
        st.pyplot(fig2)
    
    # Роли участников
    st.markdown("### 🎭 Роли участников")
    
    roles = []
    for s in scores:
        stats = s['stats']
        user = s['user']
        
        # Определяем роль
        role_scores = {
            '🔗 Линкер': stats['links'],
            '❓ Любопытный': stats['questions'],
            '💡 Эксперт': stats['answers'] + stats['useful'],
            '😂 Весельчак': stats['humor'],
            '📷 Контент-мейкер': stats['media'] + stats['voice'],
            '⭐ Популярный': stats['reactions_received'] + stats['replies_received'],
        }
        
        if max(role_scores.values()) > 0:
            main_role = max(role_scores.items(), key=lambda x: x[1])
            roles.append({
                'Участник': user,
                'Роль': main_role[0],
                'Сила роли': main_role[1]
            })
    
    # Группируем по ролям
    role_groups = defaultdict(list)
    for r in roles:
        role_groups[r['Роль']].append(r['Участник'])
    
    for role, members in sorted(role_groups.items(), key=lambda x: len(x[1]), reverse=True):
        st.markdown(f"**{role}**: {', '.join(members[:5])}" + 
                   (f" (+{len(members)-5})" if len(members) > 5 else ""))
    
    # Инсайты
    st.markdown("### 💡 Инсайты")
    
    if scores:
        # MVP
        mvp = scores[0]
        st.success(f"🏆 **MVP группы: {mvp['user']}** с {mvp['total']:.0f} баллами!")
        
        # Главный помощник
        helper = max(scores, key=lambda x: x['stats']['answers'] + x['stats']['useful'])
        if helper['stats']['answers'] + helper['stats']['useful'] > 5:
            st.info(f"💡 **Главный помощник: {helper['user']}** — часто отвечает и делится полезным")
        
        # Главный весельчак
        funny = max(scores, key=lambda x: x['stats']['humor'])
        if funny['stats']['humor'] > 10:
            st.info(f"😂 **Весельчак группы: {funny['user']}** — поднимает настроение")
        
        # Самый популярный
        popular = max(scores, key=lambda x: x['stats']['reactions_received'])
        if popular['stats']['reactions_received'] > 10:
            st.info(f"⭐ **Звезда группы: {popular['user']}** — получает больше всего реакций")

