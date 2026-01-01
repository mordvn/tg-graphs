"""
Complaint Meter
Анализирует частоту жалоб, нытья и негативных высказываний.
Помогает понять энергетический баланс в общении.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Жалобы на жизнь, усталость
LIFE_COMPLAINTS = {
    'устал', 'устала', 'задолбал', 'задолбала', 'достало', 'надоело',
    'не могу больше', 'сил нет', 'сил моих нет', 'нет сил',
    'хочу умереть', 'хочу сдохнуть', 'ненавижу свою жизнь',
    'всё плохо', 'всё ужасно', 'всё отстой', 'жизнь — говно',
    'когда это кончится', 'за что мне это', 'почему я',
    'невезучий', 'невезучая', 'не везёт', 'опять не повезло',
    'снова', 'опять', 'как всегда', 'вечно так',
    'день не задался', 'ужасный день', 'отвратительный день',
    'хочу домой', 'хочу спать', 'хочу отдохнуть',
}

# Жалобы на работу/учёбу
WORK_COMPLAINTS = {
    'ненавижу работу', 'ненавижу учёбу', 'ненавижу школу', 'ненавижу универ',
    'начальник', 'босс достал', 'коллеги бесят', 'препод',
    'много работы', 'завал', 'дедлайн', 'не успеваю',
    'не хочу работать', 'не хочу учиться', 'не хочу идти',
    'опять на работу', 'снова на работу', 'ещё один рабочий день',
    'увольняюсь', 'брошу всё', 'надоела работа', 'надоела учёба',
    'зарплата маленькая', 'мало платят', 'не ценят',
}

# Жалобы на здоровье
HEALTH_COMPLAINTS = {
    'болит', 'заболела', 'заболел', 'простыла', 'простыл',
    'плохо себя чувствую', 'тошнит', 'голова раскалывается',
    'мигрень', 'температура', 'горло болит', 'живот болит',
    'спина болит', 'голова болит', 'зубы болят',
    'не выспалась', 'не выспался', 'бессонница', 'кошмары',
    'аллергия', 'насморк', 'кашель', 'давление',
}

# Жалобы на людей
PEOPLE_COMPLAINTS = {
    'бесит', 'бесят', 'раздражает', 'раздражают', 'достали',
    'идиоты', 'дебилы', 'тупые', 'неадекваты',
    'родители достали', 'мама достала', 'папа достал',
    'друзья', 'подруга бесит', 'друг бесит',
    'соседи', 'люди в метро', 'люди в автобусе',
    'никто не понимает', 'все против меня', 'все идиоты',
    'ненавижу людей', 'устала от людей', 'устал от людей',
}

# Жалобы на погоду и внешние факторы
EXTERNAL_COMPLAINTS = {
    'погода отстой', 'холодно', 'жарко', 'дождь', 'снег',
    'пробки', 'опоздала', 'опоздал', 'автобус', 'метро',
    'сломалось', 'разбила', 'разбил', 'потеряла', 'потерял',
    'забыла', 'забыл', 'опять забыла', 'опять забыл',
    'интернет', 'телефон сел', 'батарея', 'зарядка',
}

# Общие нытьё-маркеры
WHINING_MARKERS = {
    'не хочууу', 'не хочу', 'не хочется', 'лень', 'влом',
    'неохота', 'не буду', 'не пойду', 'не могу',
    'скучно', 'нечего делать', 'некуда пойти',
    'ааа', 'аааа', 'ааааа', 'блин', 'блииин', 'блииииин',
    'ну почему', 'ну за что', 'ну как так', 'ну вот',
    'эх', 'ох', 'уф', 'фух', 'пф', 'пфф',
    '😩', '😫', '😤', '😒', '🙄', '😑', '😞', '😔', '😢', '😭',
    'помогите', 'спасите', 'убейте меня',
}


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


def count_markers(text, markers):
    """Считает маркеры в тексте"""
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
    
    st.subheader(f"😩 Метр Жалоб — {chat_name}")
    st.markdown("""
    Анализ частоты жалоб и нытья. 
    
    Жаловаться — нормально, но постоянное нытьё может истощать партнёра.
    """)
    
    categories = {
        '😫 Усталость/Жизнь': LIFE_COMPLAINTS,
        '💼 Работа/Учёба': WORK_COMPLAINTS,
        '🤒 Здоровье': HEALTH_COMPLAINTS,
        '👥 Люди': PEOPLE_COMPLAINTS,
        '🌧️ Внешние факторы': EXTERNAL_COMPLAINTS,
        '😭 Общее нытьё': WHINING_MARKERS,
    }
    
    # Собираем статистику
    user_stats = defaultdict(lambda: {
        'total_messages': 0,
        'complaint_messages': 0,
        'categories': {cat: {'count': 0, 'examples': []} for cat in categories}
    })
    
    monthly_stats = defaultdict(lambda: defaultdict(int))
    daily_stats = defaultdict(lambda: defaultdict(int))
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
            
        text = get_text(msg)
        if not text or len(text) < 2:
            continue
        
        user_stats[sender]['total_messages'] += 1
        
        is_complaint = False
        for cat_name, markers in categories.items():
            count, found = count_markers(text, markers)
            if count > 0:
                is_complaint = True
                user_stats[sender]['categories'][cat_name]['count'] += count
                if len(user_stats[sender]['categories'][cat_name]['examples']) < 5:
                    user_stats[sender]['categories'][cat_name]['examples'].append({
                        'text': text[:100],
                        'markers': found
                    })
        
        if is_complaint:
            user_stats[sender]['complaint_messages'] += 1
            
            try:
                dt = parse_date(msg['date'])
                monthly_stats[dt.strftime('%Y-%m')][sender] += 1
                daily_stats[dt.strftime('%Y-%m-%d')][sender] += 1
            except:
                pass
    
    if not user_stats:
        st.warning("Не удалось проанализировать сообщения.")
        return
    
    # Основная статистика
    st.markdown("### 📊 Общая статистика жалоб")
    
    table_data = []
    for user, stats in user_stats.items():
        total_complaints = sum(stats['categories'][cat]['count'] for cat in categories)
        complaint_ratio = stats['complaint_messages'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        
        row = {
            'Пользователь': user,
            'Всего сообщений': stats['total_messages'],
            'С жалобами': stats['complaint_messages'],
            'Доля жалоб': f"{complaint_ratio:.1f}%",
            'Маркеров': total_complaints,
        }
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # По категориям
    st.markdown("### 📋 По категориям")
    
    users = list(user_stats.keys())
    
    cat_table = []
    for cat_name in categories:
        row = {'Категория': cat_name}
        for user in users:
            row[user] = user_stats[user]['categories'][cat_name]['count']
        cat_table.append(row)
    
    df_cat = pd.DataFrame(cat_table)
    st.dataframe(df_cat, hide_index=True)
    
    # Визуализация
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Распределение жалоб")
        
        fig1, ax1 = plt.subplots(figsize=(6, 6))
        
        for user in users:
            cat_counts = [user_stats[user]['categories'][cat]['count'] for cat in categories]
            ax1.bar(range(len(categories)), cat_counts, label=user, alpha=0.7)
        
        ax1.set_xticks(range(len(categories)))
        ax1.set_xticklabels([c.split()[1] for c in categories], rotation=45, ha='right')
        ax1.legend()
        ax1.set_ylabel('Количество')
        plt.tight_layout()
        st.pyplot(fig1)
    
    with col2:
        st.markdown("#### 🥧 Соотношение жалоб")
        
        if len(users) >= 2:
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            
            user_totals = {user: sum(user_stats[user]['categories'][cat]['count'] for cat in categories) for user in users}
            
            ax2.pie(
                user_totals.values(), 
                labels=user_totals.keys(), 
                autopct='%1.1f%%',
                startangle=90
            )
            ax2.set_title('Кто жалуется чаще')
            st.pyplot(fig2)
    
    # Детали по пользователям
    st.markdown("### 🔍 Детальный анализ")
    
    for user, stats in user_stats.items():
        total_complaints = sum(stats['categories'][cat]['count'] for cat in categories)
        complaint_ratio = stats['complaint_messages'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        
        with st.expander(f"👤 {user} — {total_complaints} жалоб ({complaint_ratio:.1f}%)"):
            for cat_name in categories:
                cat_stats = stats['categories'][cat_name]
                if cat_stats['count'] > 0:
                    st.markdown(f"**{cat_name}** — {cat_stats['count']} раз")
                    for example in cat_stats['examples'][:3]:
                        st.caption(f"_{example['text']}..._ → {', '.join(example['markers'])}")
                    st.divider()
    
    # Динамика по месяцам
    if len(monthly_stats) > 1:
        st.markdown("### 📈 Динамика жалоб по месяцам")
        
        months = sorted(monthly_stats.keys())
        
        fig3, ax3 = plt.subplots(figsize=(12, 5))
        
        for user in users:
            values = [monthly_stats[m].get(user, 0) for m in months]
            ax3.plot(months, values, marker='o', label=user, linewidth=2)
        
        ax3.set_xlabel('Месяц')
        ax3.set_ylabel('Сообщений с жалобами')
        ax3.set_title('Как меняется частота жалоб')
        ax3.legend()
        ax3.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig3)
    
    # Интерпретация
    st.markdown("### 💡 Интерпретация")
    
    for user, stats in user_stats.items():
        total_complaints = sum(stats['categories'][cat]['count'] for cat in categories)
        complaint_ratio = stats['complaint_messages'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        
        if complaint_ratio > 30:
            st.error(f"""
            🚨 **{user}**: Очень высокий уровень жалоб ({complaint_ratio:.0f}% сообщений)
            
            Это может:
            - Истощать партнёра эмоционально
            - Создавать негативную атмосферу
            - Быть признаком депрессии или выгорания
            
            💡 Рекомендация: обсудить это, возможно нужна помощь специалиста
            """)
        elif complaint_ratio > 20:
            st.warning(f"""
            ⚠️ **{user}**: Заметный уровень жалоб ({complaint_ratio:.0f}%)
            
            Выше среднего, стоит обратить внимание.
            """)
        elif complaint_ratio > 10:
            st.info(f"""
            📊 **{user}**: Умеренный уровень жалоб ({complaint_ratio:.0f}%)
            
            В пределах нормы, все иногда жалуются.
            """)
        else:
            st.success(f"""
            ✅ **{user}**: Низкий уровень жалоб ({complaint_ratio:.0f}%)
            
            Позитивный настрой в общении.
            """)
    
    # Сравнение
    if len(users) == 2:
        st.markdown("### ⚖️ Баланс жалоб")
        
        user1, user2 = users
        ratio1 = user_stats[user1]['complaint_messages'] / user_stats[user1]['total_messages'] * 100 if user_stats[user1]['total_messages'] > 0 else 0
        ratio2 = user_stats[user2]['complaint_messages'] / user_stats[user2]['total_messages'] * 100 if user_stats[user2]['total_messages'] > 0 else 0
        
        diff = abs(ratio1 - ratio2)
        
        if diff > 15:
            more_complainer = user1 if ratio1 > ratio2 else user2
            st.warning(f"""
            ⚠️ **{more_complainer}** жалуется значительно чаще.
            
            Это создаёт дисбаланс: один партнёр постоянно "вытягивает" негатив,
            а другой вынужден его поддерживать.
            """)
        elif diff > 7:
            st.info("📊 Есть небольшой дисбаланс в жалобах, но не критичный.")
        else:
            st.success("✅ Баланс жалоб примерно одинаковый — это хорошо!")

