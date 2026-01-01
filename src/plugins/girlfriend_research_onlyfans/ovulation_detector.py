"""
Ovulation Detector 🌡️
Детектор овуляции на основе паттернов общения.

Научная основа:
- Во время овуляции (примерно 14й день цикла) у женщин повышается:
  * Либидо и сексуальный интерес
  * Энергия и общительность
  * Эмоциональность
  * Использование флирта и игривых сообщений

- В ПМС (за 3-7 дней до месячных):
  * Повышенная раздражительность
  * Эмоциональные качели
  * Жалобы на самочувствие

Алгоритм ищет циклические паттерны за 28-35 дней периоды.
"""
from collections import defaultdict
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


# Маркеры повышенного либидо / овуляции (с весами)
HORNY_MARKERS = {
    # Высокий вес - прямые сексуальные намёки
    'хочу тебя': 3, 'хочу к тебе': 3, 'приезжай': 2, 'приходи': 2,
    'соскучилась': 2, 'соскучился': 2, 'жду встречи': 2,
    'хочу обнять': 2, 'хочу целовать': 2, 'хочу поцеловать': 2,
    
    # Средний вес - флирт
    'скучаю по тебе': 1.5, 'жду тебя': 1.5, 'когда увидимся': 1.5,
    'красавчик': 1, 'сексуальный': 2, 'горячий': 2,
    'мой хороший': 1, 'мой любимый': 1,
    
    # Физический контакт
    'обнимаю': 1, 'целую': 1, 'прижаться': 1.5,
    'лежать рядом': 1.5, 'засыпать вместе': 1.5,
    
    # Намёки
    'хочется': 2, 'мечтаю': 1.5, 'представляю': 1.5,
    
    # Эмодзи - высокий вес для сексуальных
    '😏': 2, '🥵': 3, '😈': 3, '💦': 3, '🍑': 3, '🍆': 3, '❤️‍🔥': 2,
    # Средний вес для романтических
    '😘': 1, '😍': 1.5, '🥰': 1.5, '💋': 1.5, '🔥': 1.5,
    '😻': 1, '💕': 0.5, '💖': 0.5, '💘': 0.5, '💗': 0.5, '💓': 0.5, '💞': 0.5,
}

# Маркеры ПМС / плохого самочувствия (с весами)
PMS_MARKERS = {
    # Физическое - высокий вес
    'болит живот': 3, 'болит голова': 2, 'тошнит': 2, 
    'плохо себя чувствую': 2, 'отекла': 2, 'вздулась': 2, 'ноет': 1,
    
    # Усталость
    'устала': 1.5, 'нет сил': 2, 'хочу лежать': 1, 'хочу спать': 1,
    
    # Эмоциональное
    'раздражает': 1.5, 'бесит': 2, 'всё бесит': 3, 'достало': 2, 'надоело': 1.5,
    'хочу плакать': 2, 'плачу': 2, 'грустно': 1, 'тоска': 1.5,
    'не хочу никого видеть': 2, 'оставьте меня': 2,
    
    # Еда (характерно для ПМС)
    'хочу шоколад': 2, 'хочу сладкое': 1.5, 'жру': 1, 'обожралась': 1,
    
    # Эмодзи
    '😭': 1.5, '😢': 1, '😩': 1.5, '😫': 1.5, '🥺': 0.5, '😤': 1, '😠': 1.5, '💔': 1,
}

# Маркеры высокой энергии (характерно для овуляции)
HIGH_ENERGY_MARKERS = {
    'отлично': 1, 'супер': 1, 'круто': 1, 'класс': 1, 'ура': 1.5, 'йей': 1.5,
    'хочу': 0.5, 'давай': 0.5, 'погнали': 1, 'пойдём': 0.5, 'поехали': 0.5,
    'весело': 1, 'смешно': 0.5, 'ржу': 0.5, 'хаха': 0.3, 'ахах': 0.3,
    '😂': 0.3, '🤣': 0.3, '😆': 0.3, '🥳': 1, '🎉': 1, '💪': 1, '✨': 0.5, '🌟': 0.5,
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


def count_markers_weighted(text, markers_dict):
    """Считает маркеры с учётом весов"""
    text_lower = text.lower()
    total = 0
    for marker, weight in markers_dict.items():
        if marker in text_lower:
            total += weight
    return total


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"🌡️ Детектор Овуляции — {chat_name}")
    st.markdown("""
    Анализ циклических паттернов активности и настроения.
    
    **Научная основа:** Во время овуляции (~14й день цикла) наблюдается повышение 
    либидо, энергии и общительности. В ПМС — наоборот.
    
    ⚠️ Это статистический анализ, не медицинский диагноз!
    """)
    
    # Получаем список участников
    users = set()
    for msg in messages:
        sender = msg.get('from')
        if sender:
            users.add(sender)
    
    users = list(users)
    
    # Выбор пользователя для анализа
    target_user = st.selectbox("Выберите участника для анализа цикла", users)
    
    if not target_user:
        return
    
    # Настройки алгоритма
    with st.expander("⚙️ Настройки алгоритма"):
        smooth_window = st.slider("Окно сглаживания (дней)", 3, 14, 7, 
                                   help="Больше = меньше шума, но менее точные даты")
        min_cycle = st.slider("Минимальная длина цикла (дней)", 20, 30, 25)
        max_cycle = st.slider("Максимальная длина цикла (дней)", 30, 45, 38)
        peak_window = st.slider("Окно поиска пика (дней)", 5, 15, 10,
                                help="Пик должен быть максимумом в этом окне")
    
    # Собираем данные по дням
    daily_stats = defaultdict(lambda: {
        'messages': 0,
        'chars': 0,
        'horny': 0,
        'pms': 0,
        'energy': 0,
    })
    
    for msg in messages:
        sender = msg.get('from')
        if sender != target_user:
            continue
        
        try:
            dt = parse_date(msg['date'])
            date_key = dt.date()
        except:
            continue
        
        text = get_text(msg)
        
        daily_stats[date_key]['messages'] += 1
        daily_stats[date_key]['chars'] += len(text)
        daily_stats[date_key]['horny'] += count_markers_weighted(text, HORNY_MARKERS)
        daily_stats[date_key]['pms'] += count_markers_weighted(text, PMS_MARKERS)
        daily_stats[date_key]['energy'] += count_markers_weighted(text, HIGH_ENERGY_MARKERS)
    
    if len(daily_stats) < 28:
        st.warning("Нужно минимум 28 дней данных для анализа цикла.")
        return
    
    # Создаём DataFrame с непрерывным индексом дат
    dates = sorted(daily_stats.keys())
    all_dates = pd.date_range(start=dates[0], end=dates[-1], freq='D')
    
    df_data = []
    for date in all_dates:
        date_key = date.date()
        stats = daily_stats.get(date_key, {'messages': 0, 'chars': 0, 'horny': 0, 'pms': 0, 'energy': 0})
        
        # Нормализуем по количеству сообщений (избегаем деления на 0)
        msg_count = max(stats['messages'], 1)
        
        # Индекс либидо: horny + energy - pms, нормализованный
        raw_libido = stats['horny'] + stats['energy'] * 0.5 - stats['pms'] * 1.5
        
        df_data.append({
            'date': date,
            'messages': stats['messages'],
            'chars': stats['chars'],
            'horny': stats['horny'],
            'pms': stats['pms'],
            'energy': stats['energy'],
            'libido_raw': raw_libido,
            # Нормализованный индекс (для дней с сообщениями)
            'libido_norm': raw_libido / np.sqrt(msg_count) if stats['messages'] > 0 else np.nan,
        })
    
    df = pd.DataFrame(df_data)
    df = df.set_index('date')
    
    # Интерполяция пропусков
    df['libido_filled'] = df['libido_norm'].interpolate(method='linear', limit=3)
    
    # Сглаживание
    df['libido_smooth'] = df['libido_filled'].rolling(
        window=smooth_window, center=True, min_periods=smooth_window//2
    ).mean()
    
    # Заполняем NaN нулями для расчётов
    df['libido_smooth'] = df['libido_smooth'].fillna(0)
    
    # Находим пики либидо
    st.markdown("### 📈 График либидо")
    
    fig, ax = plt.subplots(figsize=(14, 5))
    
    # Показываем и сырые данные и сглаженные
    ax.bar(df.index, df['libido_raw'].fillna(0), alpha=0.3, color='pink', label='Сырые данные')
    ax.plot(df.index, df['libido_smooth'], color='red', linewidth=2, label='Сглаженное')
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_xlabel('Дата')
    ax.set_ylabel('Индекс либидо')
    ax.set_title(f'Динамика либидо: {target_user}')
    ax.legend()
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    
    # Анализ цикла
    st.markdown("### 🔄 Анализ цикла")
    
    def find_cycle_peaks(values, min_distance=25, window=10):
        """
        Улучшенный алгоритм поиска пиков цикла.
        
        Пик должен быть:
        1. Максимумом в окне ±window дней
        2. Выше 75-го перцентиля
        3. На расстоянии min_distance от предыдущего пика
        """
        values = np.array(values)
        n = len(values)
        
        # Порог - 75-й перцентиль положительных значений
        positive_values = values[values > 0]
        if len(positive_values) < 10:
            threshold = np.mean(values) if np.mean(values) > 0 else 0
        else:
            threshold = np.percentile(positive_values, 70)
        
        peaks = []
        
        for i in range(window, n - window):
            # Проверяем что это локальный максимум в окне
            left_max = np.max(values[max(0, i-window):i])
            right_max = np.max(values[i+1:min(n, i+window+1)])
            
            if values[i] >= left_max and values[i] >= right_max:
                # Проверяем порог
                if values[i] >= threshold:
                    # Проверяем расстояние от предыдущего пика
                    if not peaks or (i - peaks[-1]) >= min_distance:
                        peaks.append(i)
        
        return peaks, threshold
    
    # Находим пики
    libido_values = df['libido_smooth'].values
    peaks, threshold = find_cycle_peaks(libido_values, min_distance=min_cycle, window=peak_window)
    
    st.caption(f"Порог обнаружения пика: {threshold:.2f}")
    
    if peaks:
        peak_dates = df.index[peaks]
        
        # Отмечаем пики на графике
        fig2, ax2 = plt.subplots(figsize=(14, 5))
        ax2.plot(df.index, df['libido_smooth'], color='red', linewidth=2)
        ax2.axhline(y=threshold, color='orange', linestyle='--', alpha=0.7, label=f'Порог: {threshold:.2f}')
        
        for peak_idx in peaks:
            ax2.axvline(x=df.index[peak_idx], color='green', linestyle='-', alpha=0.7)
            ax2.scatter([df.index[peak_idx]], [libido_values[peak_idx]], 
                       color='green', s=100, zorder=5)
        
        ax2.set_xlabel('Дата')
        ax2.set_ylabel('Индекс либидо')
        ax2.set_title('Обнаруженные пики (предполагаемая овуляция)')
        ax2.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)
        
        if len(peak_dates) >= 2:
            # Вычисляем средний цикл
            cycle_lengths = []
            for i in range(1, len(peak_dates)):
                cycle = (peak_dates[i] - peak_dates[i-1]).days
                if min_cycle <= cycle <= max_cycle:
                    cycle_lengths.append(cycle)
            
            if cycle_lengths:
                avg_cycle = np.mean(cycle_lengths)
                std_cycle = np.std(cycle_lengths) if len(cycle_lengths) > 1 else 0
                median_cycle = np.median(cycle_lengths)
                
                # Предсказание следующей овуляции
                last_peak = peak_dates[-1]
                next_ovulation = last_peak + timedelta(days=int(median_cycle))
                
                st.success(f"""
                📊 **Найден цикл!**
                
                - Средняя длина цикла: **{avg_cycle:.0f} дней**
                - Медиана: **{median_cycle:.0f} дней**
                - Отклонение: ±{std_cycle:.1f} дней
                - Количество полных циклов: {len(cycle_lengths)}
                
                🎯 **Предполагаемая следующая овуляция: {next_ovulation.strftime('%d.%m.%Y')}**
                
                📅 Окно фертильности: {(next_ovulation - timedelta(days=5)).strftime('%d.%m')} — {(next_ovulation + timedelta(days=1)).strftime('%d.%m')}
                """)
                
                # Показываем все циклы
                st.markdown("**Обнаруженные циклы:**")
                for i in range(1, len(peak_dates)):
                    cycle = (peak_dates[i] - peak_dates[i-1]).days
                    status = "✅" if min_cycle <= cycle <= max_cycle else "⚠️"
                    st.write(f"{status} {peak_dates[i-1].strftime('%d.%m.%Y')} → {peak_dates[i].strftime('%d.%m.%Y')}: **{cycle} дней**")
                
                # Показываем даты пиков
                st.markdown("**Даты пиков либидо (предполагаемая овуляция):**")
                for pd_date in peak_dates:
                    st.write(f"- {pd_date.strftime('%d.%m.%Y (%A)')}")
            else:
                st.warning(f"Найдены пики, но расстояние между ними вне диапазона {min_cycle}-{max_cycle} дней")
                for pd_date in peak_dates:
                    st.write(f"- {pd_date.strftime('%d.%m.%Y')}")
        else:
            st.info("Найден только 1 пик — недостаточно для определения цикла.")
            st.write(f"Пик: {peak_dates[0].strftime('%d.%m.%Y')}")
    else:
        st.info("Пики либидо не обнаружены. Попробуйте уменьшить окно сглаживания или порог.")
    
    # Тепловая карта по дням месяца
    st.markdown("### 🗓️ Тепловая карта: день месяца vs месяц")
    
    months = sorted(set(d.strftime('%Y-%m') for d in df.index))
    
    if len(months) >= 2:
        heatmap_data = np.zeros((len(months), 31))
        heatmap_data[:] = np.nan
        
        for date, row in df.iterrows():
            month_idx = months.index(date.strftime('%Y-%m'))
            day = date.day - 1
            heatmap_data[month_idx, day] = row['libido_smooth']
        
        fig3, ax3 = plt.subplots(figsize=(14, max(4, len(months) * 0.5)))
        
        vmax = np.nanpercentile(heatmap_data, 95) if not np.all(np.isnan(heatmap_data)) else 3
        im = ax3.imshow(heatmap_data, aspect='auto', cmap='RdYlGn', 
                        vmin=-vmax/2, vmax=vmax)
        
        ax3.set_xticks(range(31))
        ax3.set_xticklabels(range(1, 32))
        ax3.set_yticks(range(len(months)))
        ax3.set_yticklabels(months)
        ax3.set_xlabel('День месяца')
        ax3.set_ylabel('Месяц')
        
        plt.colorbar(im, ax=ax3, label='Индекс либидо')
        plt.tight_layout()
        st.pyplot(fig3)
        
        # Находим "горячие" дни
        avg_by_day = np.nanmean(heatmap_data, axis=0)
        valid_days = ~np.isnan(avg_by_day)
        if np.any(valid_days):
            hot_days = np.argsort(avg_by_day)[-5:][::-1] + 1
            cold_days = np.argsort(avg_by_day)[:5] + 1
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("🔥 **Самые горячие дни месяца:**")
                for day in hot_days:
                    if day <= 31 and not np.isnan(avg_by_day[day-1]):
                        st.write(f"- {day} число ({avg_by_day[day-1]:.2f})")
            
            with col2:
                st.markdown("❄️ **Самые холодные дни месяца:**")
                for day in cold_days:
                    if day <= 31 and not np.isnan(avg_by_day[day-1]):
                        st.write(f"- {day} число ({avg_by_day[day-1]:.2f})")
    
    # Анализ по дням недели
    st.markdown("### 📅 Либидо по дням недели")
    
    df['weekday'] = df.index.dayofweek
    weekday_avg = df.groupby('weekday')['libido_smooth'].mean()
    
    days_ru = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    
    fig4, ax4 = plt.subplots(figsize=(10, 5))
    colors = ['coral' if v > 0 else 'steelblue' for v in weekday_avg.values]
    ax4.bar(days_ru, weekday_avg.values, color=colors)
    ax4.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax4.set_ylabel('Средний индекс либидо')
    ax4.set_title('Либидо по дням недели')
    
    plt.tight_layout()
    st.pyplot(fig4)
    
    if len(weekday_avg) > 0:
        hottest_day = days_ru[weekday_avg.values.argmax()]
        st.info(f"🔥 Самый горячий день недели: **{hottest_day}**")
    
    # Статистика
    st.markdown("### 📊 Общая статистика")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Дней данных", len(df))
        st.metric("Дней с сообщениями", (df['messages'] > 0).sum())
    
    with col2:
        st.metric("🔥 Horny маркеров", f"{df['horny'].sum():.0f}")
        st.metric("😤 PMS маркеров", f"{df['pms'].sum():.0f}")
    
    with col3:
        st.metric("⚡ Energy маркеров", f"{df['energy'].sum():.0f}")
        avg_libido = df['libido_smooth'].mean()
        st.metric("Средний индекс либидо", f"{avg_libido:.2f}")
