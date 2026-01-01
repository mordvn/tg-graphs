"""
Relationship Summary
Итоговый дашборд со всеми ключевыми метриками отношений.
Помогает принять решение о продолжении отношений.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Импортируем маркеры из других модулей (упрощённые версии)
POSITIVE_MARKERS = {
    'люблю', 'обожаю', 'счастлив', 'рад', 'прекрасн', 'спасибо',
    'молодец', 'умница', 'горжусь', 'целую', 'обнимаю', 'скучаю',
    '😊', '😍', '🥰', '❤️', '💕', '😘', '🤗'
}

NEGATIVE_MARKERS = {
    'ненавижу', 'бесит', 'достал', 'устал', 'надоело', 'плохо',
    'грустно', 'обидно', 'злюсь', '😢', '😭', '😤', '😠', '😡'
}

TOXIC_MARKERS = {
    'идиот', 'дура', 'тупой', 'заткнись', 'отвали', 'пошёл',
    'ненавижу тебя', 'ты виноват', 'из-за тебя'
}

SUPPORT_MARKERS = {
    'всё будет хорошо', 'я рядом', 'верю в тебя', 'ты справишься',
    'могу помочь', 'как ты', 'что случилось'
}

CONTROL_MARKERS = {
    'где ты', 'с кем ты', 'почему не отвечаешь', 'покажи переписку'
}

INSECURITY_MARKERS = {
    'я не достойн', 'ты меня бросишь', 'ты найдёшь лучше',
    'я тебе надоела', 'ты меня любишь'
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
    return sum(1 for m in markers if m in text_lower)


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"📋 Итоговый Анализ Отношений — {chat_name}")
    st.markdown("""
    Комплексная оценка здоровья отношений на основе всех метрик.
    
    ⚠️ **Важно**: Это алгоритмический анализ, а не психологическая экспертиза.
    Используйте как дополнительный инструмент, а не как окончательный вердикт.
    """)
    
    # Собираем все метрики
    user_stats = defaultdict(lambda: {
        'total_messages': 0,
        'total_chars': 0,
        'positive': 0,
        'negative': 0,
        'toxic': 0,
        'support': 0,
        'control': 0,
        'insecurity': 0,
        'questions': 0,
        'conversation_starts': 0,
    })
    
    # Для анализа инициативы
    messages_sorted = []
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
        
        text = get_text(msg)
        user_stats[sender]['total_messages'] += 1
        user_stats[sender]['total_chars'] += len(text)
        
        user_stats[sender]['positive'] += count_markers(text, POSITIVE_MARKERS)
        user_stats[sender]['negative'] += count_markers(text, NEGATIVE_MARKERS)
        user_stats[sender]['toxic'] += count_markers(text, TOXIC_MARKERS)
        user_stats[sender]['support'] += count_markers(text, SUPPORT_MARKERS)
        user_stats[sender]['control'] += count_markers(text, CONTROL_MARKERS)
        user_stats[sender]['insecurity'] += count_markers(text, INSECURITY_MARKERS)
        user_stats[sender]['questions'] += text.count('?')
        
        try:
            dt = parse_date(msg['date'])
            messages_sorted.append({'datetime': dt, 'sender': sender})
        except:
            pass
    
    # Анализ инициативы (кто начинает разговоры)
    messages_sorted.sort(key=lambda x: x['datetime'])
    if len(messages_sorted) > 1:
        from datetime import timedelta
        pause_threshold = timedelta(hours=4)
        prev = messages_sorted[0]
        user_stats[prev['sender']]['conversation_starts'] += 1
        
        for msg in messages_sorted[1:]:
            if msg['datetime'] - prev['datetime'] >= pause_threshold:
                user_stats[msg['sender']]['conversation_starts'] += 1
            prev = msg
    
    users = list(user_stats.keys())
    if len(users) < 2:
        st.warning("Нужно минимум 2 участника чата для анализа.")
        return
    
    user1, user2 = users[0], users[1]
    
    # Вычисляем индексы для каждого пользователя
    def calculate_health_index(stats):
        """Вычисляет индекс здоровья от -100 до 100"""
        if stats['total_messages'] == 0:
            return 0
        
        msg_count = stats['total_messages']
        
        # Позитивные факторы
        positive_score = (stats['positive'] / msg_count * 10) if msg_count else 0
        support_score = (stats['support'] / msg_count * 15) if msg_count else 0
        interest_score = (stats['questions'] / msg_count * 5) if msg_count else 0
        
        # Негативные факторы
        negative_score = (stats['negative'] / msg_count * 10) if msg_count else 0
        toxic_score = (stats['toxic'] / msg_count * 30) if msg_count else 0
        control_score = (stats['control'] / msg_count * 20) if msg_count else 0
        insecurity_score = (stats['insecurity'] / msg_count * 15) if msg_count else 0
        
        # Общий индекс
        index = positive_score + support_score + interest_score - negative_score - toxic_score - control_score - insecurity_score
        
        # Нормализуем к -100..100
        return max(-100, min(100, index * 10))
    
    index1 = calculate_health_index(user_stats[user1])
    index2 = calculate_health_index(user_stats[user2])
    
    # Основные метрики
    st.markdown("### 📊 Ключевые метрики")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            f"🏥 Индекс здоровья: {user1}", 
            f"{index1:.0f}",
            help="От -100 (токсично) до 100 (здорово)"
        )
    
    with col2:
        st.metric(
            f"🏥 Индекс здоровья: {user2}", 
            f"{index2:.0f}",
            help="От -100 (токсично) до 100 (здорово)"
        )
    
    with col3:
        avg_index = (index1 + index2) / 2
        st.metric(
            "💑 Общий индекс отношений",
            f"{avg_index:.0f}",
            help="Среднее здоровье отношений"
        )
    
    # Детальная таблица
    st.markdown("### 📋 Детальная статистика")
    
    comparison_data = []
    metrics = [
        ('Сообщений', 'total_messages'),
        ('😊 Позитив', 'positive'),
        ('😢 Негатив', 'negative'),
        ('☢️ Токсичность', 'toxic'),
        ('🤝 Поддержка', 'support'),
        ('🎯 Контроль', 'control'),
        ('😰 Неуверенность', 'insecurity'),
        ('❓ Вопросов', 'questions'),
        ('💬 Начал разговоров', 'conversation_starts'),
    ]
    
    for label, key in metrics:
        val1 = user_stats[user1][key]
        val2 = user_stats[user2][key]
        comparison_data.append({
            'Метрика': label,
            user1: val1,
            user2: val2,
            'Баланс': '✅' if abs(val1 - val2) / max(val1, val2, 1) < 0.3 else '⚠️'
        })
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, hide_index=True)
    
    # Визуализация баланса
    st.markdown("### ⚖️ Баланс отношений")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Нормализуем значения для сравнения
    categories = ['Позитив', 'Негатив', 'Поддержка', 'Контроль', 'Неуверен.', 'Вопросы']
    keys = ['positive', 'negative', 'support', 'control', 'insecurity', 'questions']
    
    def normalize(user, key):
        val = user_stats[user][key]
        total = user_stats[user]['total_messages']
        return val / total * 100 if total > 0 else 0
    
    values1 = [normalize(user1, k) for k in keys]
    values2 = [normalize(user2, k) for k in keys]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, values1, width, label=user1, color='steelblue')
    bars2 = ax.bar(x + width/2, values2, width, label=user2, color='coral')
    
    ax.set_ylabel('% от всех сообщений')
    ax.set_title('Сравнение ключевых показателей')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Красные флаги
    st.markdown("### 🚩 Красные флаги")
    
    red_flags = []
    
    # Проверяем токсичность
    for user in users:
        stats = user_stats[user]
        toxic_ratio = stats['toxic'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        if toxic_ratio > 0.5:
            red_flags.append(f"☢️ **{user}**: обнаружена токсичность ({stats['toxic']} случаев)")
    
    # Проверяем контроль
    for user in users:
        stats = user_stats[user]
        control_ratio = stats['control'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        if control_ratio > 1:
            red_flags.append(f"🎯 **{user}**: признаки контролирующего поведения")
    
    # Проверяем неуверенность
    for user in users:
        stats = user_stats[user]
        ins_ratio = stats['insecurity'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        if ins_ratio > 2:
            red_flags.append(f"😰 **{user}**: высокий уровень неуверенности в себе")
    
    # Дисбаланс инициативы
    starts1 = user_stats[user1]['conversation_starts']
    starts2 = user_stats[user2]['conversation_starts']
    if min(starts1, starts2) > 0:
        init_ratio = max(starts1, starts2) / min(starts1, starts2)
        if init_ratio > 3:
            more_active = user1 if starts1 > starts2 else user2
            red_flags.append(f"💬 Дисбаланс инициативы: **{more_active}** начинает разговоры в {init_ratio:.1f} раз чаще")
    
    # Дисбаланс поддержки
    support1 = user_stats[user1]['support']
    support2 = user_stats[user2]['support']
    if min(support1, support2) > 0:
        sup_ratio = max(support1, support2) / min(support1, support2)
        if sup_ratio > 3:
            more_supportive = user1 if support1 > support2 else user2
            red_flags.append(f"🤝 Дисбаланс поддержки: **{more_supportive}** поддерживает значительно чаще")
    
    # Негативный перевес
    for user in users:
        stats = user_stats[user]
        if stats['negative'] > stats['positive'] * 1.5 and stats['negative'] > 10:
            red_flags.append(f"😢 **{user}**: негатив преобладает над позитивом")
    
    if red_flags:
        for flag in red_flags:
            st.warning(flag)
    else:
        st.success("✅ Серьёзных красных флагов не обнаружено!")
    
    # Зелёные флаги
    st.markdown("### 💚 Зелёные флаги")
    
    green_flags = []
    
    # Взаимная поддержка
    if support1 > 5 and support2 > 5:
        sup_balance = min(support1, support2) / max(support1, support2)
        if sup_balance > 0.5:
            green_flags.append("🤝 Взаимная поддержка — оба партнёра поддерживают друг друга")
    
    # Баланс инициативы
    if starts1 > 0 and starts2 > 0:
        init_balance = min(starts1, starts2) / max(starts1, starts2)
        if init_balance > 0.5:
            green_flags.append("💬 Сбалансированная инициатива — оба начинают разговоры")
    
    # Позитивный фон
    for user in users:
        stats = user_stats[user]
        if stats['positive'] > stats['negative'] * 2 and stats['positive'] > 20:
            green_flags.append(f"😊 **{user}**: позитивный эмоциональный фон")
    
    # Интерес к партнёру
    for user in users:
        stats = user_stats[user]
        q_ratio = stats['questions'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        if q_ratio > 5:
            green_flags.append(f"❓ **{user}**: высокий интерес к партнёру (много вопросов)")
    
    # Отсутствие токсичности
    total_toxic = sum(user_stats[u]['toxic'] for u in users)
    if total_toxic == 0:
        green_flags.append("💚 Токсичных паттернов не обнаружено")
    
    if green_flags:
        for flag in green_flags:
            st.success(flag)
    else:
        st.info("📊 Зелёные флаги не выявлены (возможно, недостаточно данных)")
    
    # Итоговый вердикт
    st.markdown("### 🎯 Итоговая оценка")
    
    # Взвешенная оценка
    total_red = len(red_flags)
    total_green = len(green_flags)
    
    # Считаем серьёзность красных флагов
    serious_red = sum(1 for f in red_flags if '☢️' in f or '🎯' in f)
    
    if serious_red > 0:
        st.error(f"""
        ## ⛔ Есть серьёзные проблемы
        
        Обнаружено **{serious_red}** серьёзных красных флагов (токсичность, контроль).
        
        **Рекомендация**: Необходимо серьёзно задуматься о продолжении отношений.
        Рекомендуется консультация с психологом.
        """)
    elif total_red > total_green + 2:
        st.warning(f"""
        ## ⚠️ Есть проблемы
        
        Красных флагов ({total_red}) больше чем зелёных ({total_green}).
        
        **Рекомендация**: Обсудите проблемы с партнёром. 
        Обратите внимание на выявленные дисбалансы.
        """)
    elif total_green > total_red + 2:
        st.success(f"""
        ## ✅ Отношения выглядят здоровыми
        
        Зелёных флагов ({total_green}) больше чем красных ({total_red}).
        Общий индекс здоровья: **{avg_index:.0f}**
        
        **Рекомендация**: Продолжайте строить отношения!
        """)
    else:
        st.info(f"""
        ## 📊 Смешанная картина
        
        Красных флагов: {total_red}, Зелёных: {total_green}
        Общий индекс: **{avg_index:.0f}**
        
        **Рекомендация**: Изучите детальные плагины для более глубокого анализа.
        Обратите внимание на конкретные проблемные области.
        """)
    
    st.markdown("---")
    st.caption("""
    **Дисклеймер**: Этот анализ основан только на текстовых паттернах и не может заменить 
    профессиональную психологическую оценку. Используйте результаты как отправную точку 
    для размышлений, а не как окончательный диагноз ваших отношений.
    """)

