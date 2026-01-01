"""
Initiative Ratio Analyzer
Анализирует кто чаще начинает разговор после пауз
Важный индикатор заинтересованности в общении
"""
from collections import defaultdict
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Порог паузы для определения "нового разговора" (в часах)
DEFAULT_PAUSE_THRESHOLD = 4


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"💬 Инициатива в Общении — {chat_name}")
    st.markdown("Кто чаще начинает разговор после пауз? Это показатель заинтересованности.")
    
    # Настройки
    pause_hours = st.slider(
        "Пауза для нового разговора (часы)", 
        min_value=1, max_value=24, value=DEFAULT_PAUSE_THRESHOLD,
        help="Если между сообщениями прошло больше этого времени — считаем что начался новый разговор"
    )
    pause_threshold = timedelta(hours=pause_hours)
    
    # Сортируем и парсим даты
    messages_sorted = []
    for msg in messages:
        try:
            dt = parse_date(msg["date"])
            sender = msg.get("from")
            if sender:
                messages_sorted.append({
                    'datetime': dt,
                    'sender': sender,
                    'date': dt.date()
                })
        except:
            continue
    
    messages_sorted.sort(key=lambda x: x['datetime'])
    
    if len(messages_sorted) < 2:
        st.warning("Недостаточно сообщений для анализа.")
        return
    
    # Анализируем кто начинает разговоры
    conversation_starters = defaultdict(int)
    morning_starters = defaultdict(int)  # Кто пишет первым утром (6-12)
    evening_starters = defaultdict(int)  # Кто пишет первым вечером (18-24)
    
    # Статистика по времени суток
    time_of_day_initiative = defaultdict(lambda: defaultdict(int))
    
    # Статистика по месяцам
    monthly_initiative = defaultdict(lambda: defaultdict(int))
    
    prev_msg = messages_sorted[0]
    conversation_starters[prev_msg['sender']] += 1  # Первое сообщение — начало разговора
    
    for msg in messages_sorted[1:]:
        time_diff = msg['datetime'] - prev_msg['datetime']
        
        if time_diff >= pause_threshold:
            # Новый разговор начался
            starter = msg['sender']
            conversation_starters[starter] += 1
            
            # Время суток
            hour = msg['datetime'].hour
            if 6 <= hour < 12:
                morning_starters[starter] += 1
                time_of_day_initiative['Утро (6-12)'][starter] += 1
            elif 12 <= hour < 18:
                time_of_day_initiative['День (12-18)'][starter] += 1
            elif 18 <= hour < 24:
                evening_starters[starter] += 1
                time_of_day_initiative['Вечер (18-24)'][starter] += 1
            else:
                time_of_day_initiative['Ночь (0-6)'][starter] += 1
            
            # По месяцам
            month_key = msg['datetime'].strftime('%Y-%m')
            monthly_initiative[month_key][starter] += 1
        
        prev_msg = msg
    
    if not conversation_starters:
        st.warning("Не удалось определить начала разговоров.")
        return
    
    # Основная статистика
    st.markdown("### 📊 Кто начинает разговоры")
    
    total_conversations = sum(conversation_starters.values())
    
    table_data = []
    for user, count in conversation_starters.items():
        percentage = count / total_conversations * 100 if total_conversations > 0 else 0
        table_data.append({
            'Пользователь': user,
            'Начал разговоров': count,
            'Доля': f"{percentage:.1f}%"
        })
    
    df = pd.DataFrame(table_data)
    df = df.sort_values('Начал разговоров', ascending=False)
    st.dataframe(df, hide_index=True)
    
    # Визуализация
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🥧 Распределение инициативы")
        fig1, ax1 = plt.subplots(figsize=(6, 6))
        colors = plt.cm.Pastel1.colors[:len(conversation_starters)]
        ax1.pie(
            conversation_starters.values(), 
            labels=conversation_starters.keys(), 
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )
        ax1.set_title(f'Кто начинает разговоры\n(пауза ≥{pause_hours}ч)')
        st.pyplot(fig1)
    
    with col2:
        st.markdown("#### ⏰ Инициатива по времени суток")
        if time_of_day_initiative:
            users = list(conversation_starters.keys())
            times = list(time_of_day_initiative.keys())
            
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            x = range(len(times))
            width = 0.8 / len(users)
            
            for i, user in enumerate(users):
                values = [time_of_day_initiative[t][user] for t in times]
                offset = (i - len(users)/2 + 0.5) * width
                ax2.bar([xi + offset for xi in x], values, width, label=user)
            
            ax2.set_xticks(x)
            ax2.set_xticklabels(times, rotation=45, ha='right')
            ax2.legend()
            ax2.set_ylabel('Количество')
            ax2.set_title('Кто пишет первым в разное время')
            plt.tight_layout()
            st.pyplot(fig2)
    
    # Динамика по месяцам
    if len(monthly_initiative) > 1:
        st.markdown("### 📈 Динамика инициативы по месяцам")
        
        months = sorted(monthly_initiative.keys())
        users = list(conversation_starters.keys())
        
        fig3, ax3 = plt.subplots(figsize=(12, 5))
        
        for user in users:
            values = [monthly_initiative[m][user] for m in months]
            ax3.plot(months, values, marker='o', label=user, linewidth=2)
        
        ax3.set_xlabel('Месяц')
        ax3.set_ylabel('Начато разговоров')
        ax3.set_title('Кто чаще пишет первым (по месяцам)')
        ax3.legend()
        ax3.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig3)
        
        # Анализ тренда
        st.markdown("#### 📉 Анализ трендов")
        for user in users:
            values = [monthly_initiative[m][user] for m in months]
            if len(values) >= 3:
                first_half = sum(values[:len(values)//2])
                second_half = sum(values[len(values)//2:])
                if second_half > first_half * 1.3:
                    st.success(f"📈 **{user}**: инициатива растёт со временем (+{((second_half/first_half)-1)*100:.0f}%)")
                elif second_half < first_half * 0.7:
                    st.warning(f"📉 **{user}**: инициатива падает со временем ({((second_half/first_half)-1)*100:.0f}%)")
                else:
                    st.info(f"➡️ **{user}**: инициатива стабильна")
    
    # Интерпретация
    st.markdown("### 💡 Интерпретация")
    
    users = list(conversation_starters.keys())
    if len(users) == 2:
        user1, user2 = users
        count1 = conversation_starters[user1]
        count2 = conversation_starters[user2]
        
        ratio = max(count1, count2) / min(count1, count2) if min(count1, count2) > 0 else float('inf')
        
        more_active = user1 if count1 > count2 else user2
        less_active = user2 if count1 > count2 else user1
        
        if ratio > 3:
            st.error(f"""
            🚨 **Критический дисбаланс инициативы**
            
            **{more_active}** начинает разговоры в {ratio:.1f} раз чаще чем **{less_active}**.
            
            Это может означать:
            - Разный уровень заинтересованности в общении
            - {less_active} принимает общение как должное
            - Односторонние отношения
            
            ⚠️ Рекомендация: обсудить это с партнёром
            """)
        elif ratio > 2:
            st.warning(f"""
            ⚠️ **Заметный дисбаланс**
            
            **{more_active}** чаще проявляет инициативу ({ratio:.1f}x).
            
            Стоит обратить внимание, но не критично.
            """)
        elif ratio > 1.5:
            st.info(f"""
            📊 **Небольшой перекос**
            
            **{more_active}** немного чаще начинает общение.
            В целом баланс приемлемый.
            """)
        else:
            st.success(f"""
            ✅ **Отличный баланс инициативы!**
            
            Оба партнёра примерно одинаково часто начинают разговоры.
            Это признак здоровых отношений с взаимным интересом.
            """)
    
    # Дополнительные метрики
    st.markdown("### 📋 Дополнительные метрики")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего разговоров", total_conversations)
    
    with col2:
        if len(messages_sorted) > 0:
            days = (messages_sorted[-1]['datetime'] - messages_sorted[0]['datetime']).days + 1
            avg_per_day = total_conversations / days if days > 0 else 0
            st.metric("Разговоров в день (среднее)", f"{avg_per_day:.1f}")
    
    with col3:
        if len(users) == 2:
            st.metric("Соотношение инициативы", f"{max(count1, count2)}:{min(count1, count2)}")
