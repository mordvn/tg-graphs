"""
Topic Analysis
Анализирует основные темы обсуждений в группе.
Использует частотный анализ слов и фраз.
"""
from collections import defaultdict, Counter
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

# Стоп-слова для русского и английского
STOP_WORDS = {
    # Русские
    'и', 'в', 'на', 'с', 'по', 'для', 'к', 'от', 'из', 'за', 'о', 'об', 'у', 'до',
    'что', 'как', 'это', 'так', 'но', 'а', 'или', 'если', 'то', 'же', 'ты', 'я',
    'он', 'она', 'мы', 'вы', 'они', 'его', 'её', 'их', 'мой', 'твой', 'наш', 'ваш',
    'не', 'да', 'нет', 'ну', 'вот', 'бы', 'ли', 'уже', 'ещё', 'еще', 'тоже', 'очень',
    'там', 'тут', 'здесь', 'где', 'когда', 'потом', 'сейчас', 'всё', 'все', 'этот',
    'эта', 'эти', 'тот', 'та', 'те', 'какой', 'какая', 'какие', 'такой', 'такая',
    'быть', 'есть', 'было', 'будет', 'был', 'была', 'были', 'могу', 'можно', 'надо',
    'только', 'просто', 'даже', 'чтобы', 'хотя', 'через', 'после', 'перед', 'между',
    # Английские
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these', 'those',
    'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how',
    'and', 'or', 'but', 'if', 'then', 'so', 'than', 'too', 'very', 'just',
    'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'about', 'from',
    'not', 'no', 'yes', 'ok', 'okay',
}

# Категории тем
TOPIC_CATEGORIES = {
    '💼 Работа': ['работа', 'офис', 'начальник', 'проект', 'дедлайн', 'митинг', 'задача', 'коллега'],
    '🎮 Игры': ['игра', 'играть', 'steam', 'ps5', 'xbox', 'геймер', 'матч', 'рейд', 'гильдия'],
    '🎬 Кино/Сериалы': ['фильм', 'сериал', 'netflix', 'кино', 'смотреть', 'актёр', 'серия', 'сезон'],
    '🍕 Еда': ['еда', 'ресторан', 'кафе', 'пицца', 'суши', 'бургер', 'готовить', 'вкусно', 'доставка'],
    '🏋️ Спорт/Здоровье': ['спорт', 'тренировка', 'зал', 'бег', 'футбол', 'здоровье', 'врач', 'болеть'],
    '🎵 Музыка': ['музыка', 'песня', 'концерт', 'альбом', 'spotify', 'слушать', 'трек', 'группа'],
    '📱 Технологии': ['телефон', 'apple', 'android', 'приложение', 'обновление', 'баг', 'код', 'программа'],
    '✈️ Путешествия': ['путешествие', 'отпуск', 'билет', 'отель', 'поездка', 'страна', 'город', 'виза'],
    '💰 Деньги': ['деньги', 'зарплата', 'кредит', 'банк', 'инвестиции', 'крипта', 'курс', 'дорого'],
    '❤️ Отношения': ['девушка', 'парень', 'свидание', 'отношения', 'любовь', 'свадьба', 'расстались'],
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


def extract_words(text):
    """Извлекает слова из текста"""
    # Оставляем только буквы и цифры
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    # Фильтруем короткие и стоп-слова
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"💬 Анализ Тем — {chat_name}")
    st.markdown("О чём чаще всего говорят в группе")
    
    # Собираем все слова
    all_words = []
    user_words = defaultdict(list)
    monthly_words = defaultdict(list)
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        text = get_text(msg)
        words = extract_words(text)
        
        all_words.extend(words)
        user_words[sender].extend(words)
        
        try:
            dt = parse_date(msg['date'])
            month = dt.strftime('%Y-%m')
            monthly_words[month].extend(words)
        except:
            pass
    
    if not all_words:
        st.warning("Недостаточно текста для анализа.")
        return
    
    # Частота слов
    word_freq = Counter(all_words)
    
    # Топ слов
    st.markdown("### 🔤 Самые частые слова")
    
    top_words = word_freq.most_common(30)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Таблица
        df_words = pd.DataFrame(top_words, columns=['Слово', 'Частота'])
        st.dataframe(df_words, hide_index=True)
    
    with col2:
        # Облако слов (bar chart)
        fig1, ax1 = plt.subplots(figsize=(8, 8))
        
        words_20 = top_words[:20]
        words_list = [w[0] for w in words_20]
        counts_list = [w[1] for w in words_20]
        
        ax1.barh(words_list[::-1], counts_list[::-1], color='steelblue')
        ax1.set_xlabel('Частота')
        ax1.set_title('Топ-20 слов')
        
        plt.tight_layout()
        st.pyplot(fig1)
    
    # Анализ по категориям тем
    st.markdown("### 📊 Темы обсуждений")
    
    topic_counts = {}
    for topic, keywords in TOPIC_CATEGORIES.items():
        count = sum(word_freq.get(kw, 0) for kw in keywords)
        if count > 0:
            topic_counts[topic] = count
    
    if topic_counts:
        # Сортируем
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        
        topics = [t[0] for t in sorted_topics]
        counts = [t[1] for t in sorted_topics]
        
        bars = ax2.bar(topics, counts, color='coral')
        ax2.set_ylabel('Упоминаний')
        ax2.set_title('Популярность тем')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig2)
        
        # Описание
        st.markdown("**Топ-3 темы:**")
        for topic, count in sorted_topics[:3]:
            keywords = TOPIC_CATEGORIES[topic]
            found_keywords = [(kw, word_freq.get(kw, 0)) for kw in keywords if word_freq.get(kw, 0) > 0]
            found_keywords.sort(key=lambda x: x[1], reverse=True)
            kw_str = ', '.join(f"{kw} ({c})" for kw, c in found_keywords[:5])
            st.write(f"**{topic}**: {count} упоминаний — {kw_str}")
    else:
        st.info("Не удалось определить конкретные темы")
    
    # Уникальные слова по участникам
    st.markdown("### 👤 Характерные слова участников")
    
    users = list(user_words.keys())
    
    # Находим уникальные слова для каждого пользователя
    user_unique = {}
    for user in users:
        user_freq = Counter(user_words[user])
        
        # Вычисляем TF-IDF-like метрику
        unique_words = []
        for word, count in user_freq.most_common(50):
            # Сколько пользователей используют это слово
            users_with_word = sum(1 for u in users if word in user_words[u])
            # Уникальность = частота * (1 / количество пользователей со словом)
            uniqueness = count * (len(users) / users_with_word)
            unique_words.append((word, uniqueness, count))
        
        unique_words.sort(key=lambda x: x[1], reverse=True)
        user_unique[user] = unique_words[:10]
    
    # Показываем топ участников
    for user in sorted(users, key=lambda u: len(user_words[u]), reverse=True)[:10]:
        if user_unique[user]:
            words_str = ', '.join(f"**{w[0]}** ({w[2]})" for w in user_unique[user][:5])
            st.write(f"👤 **{user}**: {words_str}")
    
    # Динамика тем по месяцам
    if len(monthly_words) > 3:
        st.markdown("### 📈 Динамика тем по месяцам")
        
        months = sorted(monthly_words.keys())
        
        # Выбираем топ-5 тем для отслеживания
        top_topics = sorted_topics[:5] if topic_counts else []
        
        if top_topics:
            fig3, ax3 = plt.subplots(figsize=(12, 5))
            
            for topic, _ in top_topics:
                keywords = TOPIC_CATEGORIES[topic]
                values = []
                for month in months:
                    month_freq = Counter(monthly_words[month])
                    count = sum(month_freq.get(kw, 0) for kw in keywords)
                    values.append(count)
                
                ax3.plot(months, values, marker='o', label=topic, linewidth=2)
            
            ax3.set_xlabel('Месяц')
            ax3.set_ylabel('Упоминаний')
            ax3.set_title('Популярность тем по месяцам')
            ax3.legend()
            ax3.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            st.pyplot(fig3)
    
    # Интересные факты
    st.markdown("### 💡 Интересные факты")
    
    # Самое длинное частое слово
    long_words = [(w, c) for w, c in word_freq.items() if len(w) > 8 and c > 5]
    if long_words:
        longest = max(long_words, key=lambda x: len(x[0]))
        st.info(f"📝 Самое длинное популярное слово: **{longest[0]}** ({longest[1]} раз)")
    
    # Уникальный словарь группы
    unique_vocab = len(word_freq)
    total_words = sum(word_freq.values())
    st.info(f"📚 Словарный запас группы: **{unique_vocab}** уникальных слов из {total_words} общих")
    
    # Среднее количество слов на сообщение
    avg_words = total_words / len(messages) if messages else 0
    st.info(f"💬 Среднее слов на сообщение: **{avg_words:.1f}**")

