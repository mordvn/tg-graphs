"""
Flirt Style Analyzer 😏
Анализ стиля флирта и соблазнения.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# Стили флирта
FLIRT_STYLES = {
    'прямой': {
        # Прямые заявления
        'хочу тебя', 'хочу к тебе', 'хочу секс',
        'давай встретимся', 'приезжай', 'приходи',
        'жду тебя', 'жду ночи', 'не могу ждать',
    },
    'игривый': {
        # Шутки и подколы
        'хаха', 'ахах', 'ржу', 'лол',
        'шутишь', 'прикол', 'смешно',
        '😂', '🤣', '😆', '😜', '😝', '😛',
        'дурачок', 'дурочка', 'глупенький',
    },
    'романтичный': {
        # Романтика
        'люблю тебя', 'обожаю', 'любимый', 'любимая',
        'ты самый', 'ты самая', 'ты лучший', 'ты лучшая',
        'моё счастье', 'моя радость', 'солнышко',
        '❤️', '💕', '💖', '💗', '💓', '💘', '💝',
        'красивый', 'красивая', 'прекрасный', 'прекрасная',
    },
    'провокативный': {
        # Провокации
        'а что если', 'а что будет', 'представь',
        'интересно', 'любопытно',
        'хочешь узнать', 'покажу', 'расскажу',
        '😏', '😈', '🔥', '👀',
    },
    'комплименты': {
        # Комплименты
        'красотка', 'красавчик', 'секси', 'горячий', 'горячая',
        'сексуальный', 'сексуальная', 'милый', 'милая',
        'обалденный', 'обалденная', 'шикарный', 'шикарная',
        'симпатичный', 'симпатичная', 'привлекательный',
    },
    'физический': {
        # Описание физического контакта
        'обнять', 'обнимаю', 'целовать', 'целую',
        'прижаться', 'прикоснуться', 'гладить',
        'губы', 'руки', 'тело', 'шея',
        '💋', '🤗', '😘',
    },
    'таинственный': {
        # Интрига
        'сюрприз', 'тайна', 'секрет',
        'узнаешь', 'потом скажу', 'не скажу',
        'угадай', 'подумай',
        '🤫', '🤭', '👀',
    },
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
    
    st.subheader(f"😏 Стиль Флирта — {chat_name}")
    st.markdown("""
    Анализ стилей флирта каждого участника.
    
    **Стили:**
    - 🎯 **Прямой** — говорит что хочет напрямую
    - 😜 **Игривый** — шутки и подколы  
    - 💕 **Романтичный** — нежность и любовь
    - 😈 **Провокативный** — интриги и провокации
    - 💋 **Комплименты** — хвалит внешность
    - 🤗 **Физический** — описывает прикосновения
    - 🤫 **Таинственный** — загадки и секреты
    """)
    
    # Статистика
    user_stats = defaultdict(lambda: {
        'messages': 0,
        'styles': {style: 0 for style in FLIRT_STYLES},
        'examples': {style: [] for style in FLIRT_STYLES},
    })
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        text = get_text(msg)
        if not text:
            continue
        
        user_stats[sender]['messages'] += 1
        
        for style, markers in FLIRT_STYLES.items():
            count, found = count_markers(text, markers)
            if count > 0:
                user_stats[sender]['styles'][style] += count
                if len(user_stats[sender]['examples'][style]) < 5:
                    user_stats[sender]['examples'][style].append({
                        'text': text[:100],
                        'found': found
                    })
    
    users = list(user_stats.keys())
    
    if not users:
        st.warning("Не удалось проанализировать.")
        return
    
    # Таблица стилей
    st.markdown("### 📊 Стили флирта")
    
    style_icons = {
        'прямой': '🎯',
        'игривый': '😜',
        'романтичный': '💕',
        'провокативный': '😈',
        'комплименты': '💋',
        'физический': '🤗',
        'таинственный': '🤫',
    }
    
    table_data = []
    for user in users:
        row = {'Участник': user}
        for style in FLIRT_STYLES:
            row[f"{style_icons[style]} {style.title()}"] = user_stats[user]['styles'][style]
        
        # Основной стиль
        styles = user_stats[user]['styles']
        if max(styles.values()) > 0:
            main_style = max(styles.items(), key=lambda x: x[1])
            row['Основной'] = f"{style_icons[main_style[0]]} {main_style[0].title()}"
        else:
            row['Основной'] = '—'
        
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # Визуализация профилей
    st.markdown("### 📈 Профили флирта")
    
    col1, col2 = st.columns(2)
    
    for idx, user in enumerate(users[:2]):
        with [col1, col2][idx]:
            st.markdown(f"**{user}**")
            
            styles = user_stats[user]['styles']
            labels = [f"{style_icons[s]} {s[:6]}" for s in FLIRT_STYLES]
            values = [styles[s] for s in FLIRT_STYLES]
            
            if sum(values) > 0:
                fig, ax = plt.subplots(figsize=(6, 6))
                
                # Radar chart (упрощённый как bar)
                ax.bar(labels, values, color='coral')
                ax.tick_params(axis='x', rotation=45)
                ax.set_ylabel('Количество')
                ax.set_title(f'Профиль: {user}')
                
                plt.tight_layout()
                st.pyplot(fig)
    
    # Сравнение
    st.markdown("### ⚖️ Сравнение стилей")
    
    if len(users) >= 2:
        user1, user2 = users[0], users[1]
        
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        
        styles_list = list(FLIRT_STYLES.keys())
        x = np.arange(len(styles_list))
        width = 0.35
        
        values1 = [user_stats[user1]['styles'][s] for s in styles_list]
        values2 = [user_stats[user2]['styles'][s] for s in styles_list]
        
        ax2.bar(x - width/2, values1, width, label=user1, color='coral')
        ax2.bar(x + width/2, values2, width, label=user2, color='steelblue')
        
        ax2.set_xticks(x)
        ax2.set_xticklabels([f"{style_icons[s]} {s}" for s in styles_list], rotation=45, ha='right')
        ax2.legend()
        ax2.set_ylabel('Количество')
        ax2.set_title('Сравнение стилей флирта')
        
        plt.tight_layout()
        st.pyplot(fig2)
    
    # Примеры
    st.markdown("### 🔍 Примеры по стилям")
    
    for user in users:
        with st.expander(f"👤 {user}"):
            for style in FLIRT_STYLES:
                examples = user_stats[user]['examples'][style]
                if examples:
                    st.markdown(f"**{style_icons[style]} {style.title()}:**")
                    for ex in examples[:2]:
                        st.caption(f"«_{ex['text']}..._»")
    
    # Совместимость стилей
    st.markdown("### 💘 Совместимость стилей")
    
    if len(users) >= 2:
        user1, user2 = users[0], users[1]
        
        # Находим основные стили
        styles1 = user_stats[user1]['styles']
        styles2 = user_stats[user2]['styles']
        
        if max(styles1.values()) > 0 and max(styles2.values()) > 0:
            main1 = max(styles1.items(), key=lambda x: x[1])[0]
            main2 = max(styles2.items(), key=lambda x: x[1])[0]
            
            # Матрица совместимости (упрощённая)
            compatible = {
                ('прямой', 'прямой'): ('✅', 'Оба прямолинейны — понимают друг друга'),
                ('прямой', 'игривый'): ('👍', 'Хорошо! Прямота + юмор'),
                ('романтичный', 'романтичный'): ('❤️', 'Идеально! Романтика с обеих сторон'),
                ('провокативный', 'провокативный'): ('🔥', 'Огонь! Оба любят интригу'),
                ('игривый', 'игривый'): ('😄', 'Весело! Оба любят шутить'),
            }
            
            pair = (main1, main2)
            pair_rev = (main2, main1)
            
            if pair in compatible:
                emoji, desc = compatible[pair]
                st.success(f"{emoji} **{main1.title()}** + **{main2.title()}**: {desc}")
            elif pair_rev in compatible:
                emoji, desc = compatible[pair_rev]
                st.success(f"{emoji} **{main2.title()}** + **{main1.title()}**: {desc}")
            else:
                st.info(f"📊 **{user1}**: {style_icons[main1]} {main1} | **{user2}**: {style_icons[main2]} {main2}")
                st.caption("Разные стили могут дополнять друг друга!")
    
    # Выводы
    st.markdown("### 💡 Выводы")
    
    for user in users:
        styles = user_stats[user]['styles']
        total = sum(styles.values())
        
        if total > 0:
            # Топ-2 стиля
            sorted_styles = sorted(styles.items(), key=lambda x: x[1], reverse=True)[:2]
            styles_str = ' + '.join(f"{style_icons[s[0]]} {s[0]}" for s in sorted_styles if s[1] > 0)
            st.info(f"**{user}** предпочитает: {styles_str}")

