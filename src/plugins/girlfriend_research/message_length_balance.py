"""
Message Length Balance Analyzer
Анализирует баланс длины и развёрнутости сообщений.
Кто пишет больше, развёрнутее, инвестирует больше усилий в общение.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def get_text(msg):
    """Извлекает текст из сообщения"""
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
    
    st.subheader(f"📏 Баланс Сообщений — {chat_name}")
    st.markdown("""
    Анализ длины и развёрнутости сообщений.
    
    Длина сообщений может показывать уровень вовлечённости в разговор.
    """)
    
    # Собираем статистику
    user_stats = defaultdict(lambda: {
        'message_lengths': [],
        'word_counts': [],
        'total_chars': 0,
        'total_words': 0,
        'one_word_messages': 0,  # Односложные ответы
        'long_messages': 0,  # Развёрнутые сообщения (100+ символов)
        'voice_messages': 0,
        'stickers': 0,
        'photos': 0,
    })
    
    monthly_stats = defaultdict(lambda: defaultdict(lambda: {'chars': 0, 'count': 0}))
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        # Голосовые сообщения
        if msg.get('media_type') == 'voice_message':
            user_stats[sender]['voice_messages'] += 1
            continue
        
        # Стикеры
        if msg.get('media_type') == 'sticker':
            user_stats[sender]['stickers'] += 1
            continue
        
        # Фото
        if msg.get('photo'):
            user_stats[sender]['photos'] += 1
        
        text = get_text(msg)
        if not text:
            continue
        
        text_len = len(text)
        words = text.split()
        word_count = len(words)
        
        user_stats[sender]['message_lengths'].append(text_len)
        user_stats[sender]['word_counts'].append(word_count)
        user_stats[sender]['total_chars'] += text_len
        user_stats[sender]['total_words'] += word_count
        
        # Односложные сообщения (1-2 слова, до 10 символов)
        if word_count <= 2 and text_len <= 15:
            user_stats[sender]['one_word_messages'] += 1
        
        # Развёрнутые сообщения
        if text_len >= 100:
            user_stats[sender]['long_messages'] += 1
        
        # По месяцам
        try:
            dt = parse_date(msg['date'])
            month = dt.strftime('%Y-%m')
            monthly_stats[month][sender]['chars'] += text_len
            monthly_stats[month][sender]['count'] += 1
        except:
            pass
    
    if not user_stats:
        st.warning("Не удалось проанализировать сообщения.")
        return
    
    users = list(user_stats.keys())
    
    # Основная статистика
    st.markdown("### 📊 Общая статистика")
    
    table_data = []
    for user in users:
        stats = user_stats[user]
        msg_count = len(stats['message_lengths'])
        
        if msg_count > 0:
            avg_len = np.mean(stats['message_lengths'])
            median_len = np.median(stats['message_lengths'])
            avg_words = np.mean(stats['word_counts'])
            one_word_ratio = stats['one_word_messages'] / msg_count * 100
            long_ratio = stats['long_messages'] / msg_count * 100
            
            table_data.append({
                'Пользователь': user,
                'Сообщений': msg_count,
                'Всего символов': stats['total_chars'],
                'Средняя длина': f"{avg_len:.0f}",
                'Медиана': f"{median_len:.0f}",
                'Слов/сообщение': f"{avg_words:.1f}",
                'Односложных': f"{one_word_ratio:.0f}%",
                'Развёрнутых': f"{long_ratio:.0f}%",
            })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # Дополнительная статистика по медиа
    st.markdown("### 📱 Медиа-контент")
    
    media_data = []
    for user in users:
        stats = user_stats[user]
        media_data.append({
            'Пользователь': user,
            '🎤 Голосовые': stats['voice_messages'],
            '🖼️ Стикеры': stats['stickers'],
            '📷 Фото': stats['photos'],
        })
    
    df_media = pd.DataFrame(media_data)
    st.dataframe(df_media, hide_index=True)
    
    # Визуализация распределения
    st.markdown("### 📈 Распределение длины сообщений")
    
    fig, axes = plt.subplots(1, min(len(users), 2), figsize=(12, 5))
    if len(users) == 1:
        axes = [axes]
    
    for idx, user in enumerate(users[:2]):
        lengths = user_stats[user]['message_lengths']
        # Кап на 200 для лучшей визуализации
        lengths_capped = [min(l, 200) for l in lengths]
        
        axes[idx].hist(lengths_capped, bins=40, alpha=0.7, color='steelblue', edgecolor='white')
        axes[idx].axvline(np.median(lengths), color='red', linestyle='--', label=f'Медиана: {np.median(lengths):.0f}')
        axes[idx].axvline(np.mean(lengths), color='orange', linestyle='--', label=f'Среднее: {np.mean(lengths):.0f}')
        axes[idx].set_xlabel('Длина сообщения (символы)')
        axes[idx].set_ylabel('Количество')
        axes[idx].set_title(f'{user}')
        axes[idx].legend()
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Сравнительный анализ
    if len(users) >= 2:
        st.markdown("### ⚖️ Сравнение")
        
        user1, user2 = users[0], users[1]
        
        avg1 = np.mean(user_stats[user1]['message_lengths']) if user_stats[user1]['message_lengths'] else 0
        avg2 = np.mean(user_stats[user2]['message_lengths']) if user_stats[user2]['message_lengths'] else 0
        
        total1 = user_stats[user1]['total_chars']
        total2 = user_stats[user2]['total_chars']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"{user1}", f"{avg1:.0f} симв./сообщ.")
            st.caption(f"Всего: {total1:,} символов")
        
        with col2:
            st.metric(f"{user2}", f"{avg2:.0f} симв./сообщ.")
            st.caption(f"Всего: {total2:,} символов")
        
        with col3:
            ratio = max(avg1, avg2) / min(avg1, avg2) if min(avg1, avg2) > 0 else 0
            st.metric("Разница", f"{ratio:.1f}x")
        
        # Интерпретация
        writes_more = user1 if avg1 > avg2 else user2
        writes_less = user2 if avg1 > avg2 else user1
        
        diff = abs(avg1 - avg2)
        diff_ratio = max(avg1, avg2) / min(avg1, avg2) if min(avg1, avg2) > 0 else 0
        
        if diff_ratio > 2:
            st.warning(f"""
            ⚠️ **Значительный дисбаланс**
            
            **{writes_more}** пишет в {diff_ratio:.1f} раз развёрнутее чем **{writes_less}**.
            
            Это может означать:
            - Разный уровень вовлечённости в общение
            - Разный стиль общения (не обязательно плохо)
            - **{writes_less}** отвечает формально, не развивает тему
            
            💡 Обратите внимание на паттерн односложных ответов
            """)
        elif diff_ratio > 1.5:
            st.info(f"📊 **{writes_more}** пишет немного развёрнутее. Не критично.")
        else:
            st.success("✅ Баланс развёрнутости сообщений хороший!")
    
    # Анализ односложных ответов
    st.markdown("### 🔤 Анализ коротких ответов")
    
    for user in users:
        stats = user_stats[user]
        msg_count = len(stats['message_lengths'])
        
        if msg_count > 0:
            one_word_ratio = stats['one_word_messages'] / msg_count * 100
            
            if one_word_ratio > 40:
                st.error(f"""
                🚨 **{user}**: {one_word_ratio:.0f}% односложных ответов
                
                Слишком много коротких ответов типа "ок", "да", "хорошо", "ага".
                Это может восприниматься как:
                - Незаинтересованность в разговоре
                - Формальные ответы "для галочки"
                - Нежелание общаться
                """)
            elif one_word_ratio > 25:
                st.warning(f"⚠️ **{user}**: {one_word_ratio:.0f}% односложных ответов — много")
            elif one_word_ratio > 15:
                st.info(f"📊 **{user}**: {one_word_ratio:.0f}% односложных ответов — нормально")
            else:
                st.success(f"✅ **{user}**: {one_word_ratio:.0f}% односложных — хорошо развивает темы")
    
    # Динамика по месяцам
    if len(monthly_stats) > 1:
        st.markdown("### 📈 Динамика средней длины по месяцам")
        
        months = sorted(monthly_stats.keys())
        
        fig2, ax = plt.subplots(figsize=(12, 5))
        
        for user in users:
            avg_lens = []
            for month in months:
                data = monthly_stats[month].get(user, {'chars': 0, 'count': 0})
                avg = data['chars'] / data['count'] if data['count'] > 0 else None
                avg_lens.append(avg)
            
            ax.plot(months, avg_lens, marker='o', label=user, linewidth=2)
        
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Средняя длина сообщения')
        ax.set_title('Как меняется развёрнутость сообщений')
        ax.legend()
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)
        
        # Анализ трендов
        st.markdown("#### 📉 Тренды")
        for user in users:
            avg_lens = []
            for month in months:
                data = monthly_stats[month].get(user, {'chars': 0, 'count': 0})
                if data['count'] > 0:
                    avg_lens.append(data['chars'] / data['count'])
            
            if len(avg_lens) >= 4:
                first_half = np.mean(avg_lens[:len(avg_lens)//2])
                second_half = np.mean(avg_lens[len(avg_lens)//2:])
                
                if first_half > 0:
                    change = (second_half - first_half) / first_half * 100
                    if change < -20:
                        st.warning(f"📉 **{user}**: сообщения становятся короче ({change:.0f}%) — может быть потеря интереса")
                    elif change > 20:
                        st.success(f"📈 **{user}**: сообщения становятся развёрнутее (+{change:.0f}%)")
                    else:
                        st.info(f"➡️ **{user}**: длина сообщений стабильна")
    
    # Итоговый вывод
    st.markdown("### 💡 Что это значит")
    
    st.markdown("""
    **Здоровые паттерны:**
    - Оба пишут примерно одинаково развёрнуто
    - Мало односложных ответов
    - Длина сообщений не падает со временем
    
    **Тревожные признаки:**
    - Один постоянно пишет развёрнуто, другой отвечает коротко
    - Много "ок", "ага", "да" — формальные ответы
    - Сообщения становятся короче со временем (угасание интереса)
    
    **Важно помнить:**
    - У людей разные стили общения
    - Кто-то предпочитает голосовые сообщения (проверьте статистику выше)
    - Смотрите на тренды, а не только на абсолютные значения
    """)
