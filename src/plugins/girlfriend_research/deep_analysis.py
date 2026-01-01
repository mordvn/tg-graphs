"""
Deep Relationship Analysis
Глубокий анализ отношений с использованием улучшенного NLP.
Учитывает контекст, отрицания, n-граммы.
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(__file__))

try:
    from text_analyzer import RelationshipAnalyzer, SentimentAnalyzer
except ImportError:
    # Fallback если импорт не работает
    RelationshipAnalyzer = None
    SentimentAnalyzer = None


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
    
    st.subheader(f"🔬 Глубокий Анализ — {chat_name}")
    st.markdown("""
    Улучшенный анализ с учётом контекста и n-грамм.
    Более точное определение настроения и паттернов.
    """)
    
    if RelationshipAnalyzer is None:
        st.error("Модуль text_analyzer не загружен. Используйте базовые плагины.")
        return
    
    analyzer = RelationshipAnalyzer()
    
    # Анализируем все сообщения
    user_analysis = defaultdict(lambda: {
        'messages': 0,
        'chars': 0,
        'sentiment_scores': [],
        'insecurity': defaultdict(list),  # Сохраняем примеры
        'control': defaultdict(list),
        'support': defaultdict(list),
    })
    
    monthly_sentiment = defaultdict(lambda: defaultdict(list))
    
    with st.spinner("Анализируем сообщения..."):
        for msg in messages:
            sender = msg.get('from')
            if not sender:
                continue
            
            text = get_text(msg)
            if not text or len(text) < 3:
                continue
            
            user_analysis[sender]['messages'] += 1
            user_analysis[sender]['chars'] += len(text)
            
            # Анализируем сообщение
            result = analyzer.analyze_message(text)
            
            # Sentiment
            if result['sentiment']['confidence'] > 0.2:
                user_analysis[sender]['sentiment_scores'].append(result['sentiment']['score'])
                
                try:
                    dt = parse_date(msg['date'])
                    month = dt.strftime('%Y-%m')
                    monthly_sentiment[month][sender].append(result['sentiment']['score'])
                except:
                    pass
            
            # Собираем примеры с контекстом
            for category, matches in result['insecurity'].items():
                for pattern, context in matches:
                    if len(user_analysis[sender]['insecurity'][category]) < 5:
                        user_analysis[sender]['insecurity'][category].append({
                            'pattern': pattern,
                            'context': context,
                            'text': text[:100]
                        })
            
            for category, matches in result['control'].items():
                for pattern, context in matches:
                    if len(user_analysis[sender]['control'][category]) < 5:
                        user_analysis[sender]['control'][category].append({
                            'pattern': pattern,
                            'context': context,
                            'text': text[:100]
                        })
            
            for category, matches in result['support'].items():
                for pattern, context in matches:
                    if len(user_analysis[sender]['support'][category]) < 5:
                        user_analysis[sender]['support'][category].append({
                            'pattern': pattern,
                            'context': context,
                            'text': text[:100]
                        })
    
    users = list(user_analysis.keys())
    
    if not users:
        st.warning("Не удалось проанализировать сообщения.")
        return
    
    # Основная статистика
    st.markdown("### 📊 Эмоциональный профиль")
    
    table_data = []
    for user in users:
        stats = user_analysis[user]
        scores = stats['sentiment_scores']
        
        if scores:
            avg_sentiment = sum(scores) / len(scores)
            positive_pct = sum(1 for s in scores if s > 0.2) / len(scores) * 100
            negative_pct = sum(1 for s in scores if s < -0.2) / len(scores) * 100
            neutral_pct = 100 - positive_pct - negative_pct
        else:
            avg_sentiment = 0
            positive_pct = negative_pct = neutral_pct = 0
        
        # Считаем паттерны
        total_insecurity = sum(len(v) for v in stats['insecurity'].values())
        total_control = sum(len(v) for v in stats['control'].values())
        total_support = sum(len(v) for v in stats['support'].values())
        
        table_data.append({
            'Участник': user,
            'Сообщений': stats['messages'],
            '😊 Позитивных': f"{positive_pct:.0f}%",
            '😐 Нейтральных': f"{neutral_pct:.0f}%",
            '😢 Негативных': f"{negative_pct:.0f}%",
            'Ср. настроение': f"{avg_sentiment:+.2f}",
            '😰 Неуверенность': total_insecurity,
            '🎯 Контроль': total_control,
            '🤝 Поддержка': total_support,
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # Визуализация настроения
    st.markdown("### 📈 Настроение по месяцам")
    
    if len(monthly_sentiment) > 1:
        months = sorted(monthly_sentiment.keys())
        
        fig, ax = plt.subplots(figsize=(12, 5))
        
        for user in users:
            avg_by_month = []
            for month in months:
                scores = monthly_sentiment[month].get(user, [])
                avg = sum(scores) / len(scores) if scores else None
                avg_by_month.append(avg)
            
            ax.plot(months, avg_by_month, marker='o', label=user, linewidth=2)
        
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Среднее настроение (-1 до +1)')
        ax.set_title('Динамика эмоционального фона')
        ax.legend()
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylim(-1, 1)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    # Детальный анализ паттернов
    st.markdown("### 🔍 Детальный анализ паттернов")
    
    for user in users:
        stats = user_analysis[user]
        
        with st.expander(f"👤 {user}"):
            # Неуверенность
            if any(stats['insecurity'].values()):
                st.markdown("#### 😰 Неуверенность в себе")
                for category, examples in stats['insecurity'].items():
                    if examples:
                        st.markdown(f"**{category.replace('_', ' ').title()}** ({len(examples)} случаев)")
                        for ex in examples[:3]:
                            st.caption(f"«_{ex['text']}..._» — паттерн: **{ex['pattern']}**")
            else:
                st.success("✅ Признаков неуверенности не обнаружено")
            
            st.divider()
            
            # Контроль
            if any(stats['control'].values()):
                st.markdown("#### 🎯 Контролирующее поведение")
                for category, examples in stats['control'].items():
                    if examples:
                        st.markdown(f"**{category.replace('_', ' ').title()}** ({len(examples)} случаев)")
                        for ex in examples[:3]:
                            st.caption(f"«_{ex['text']}..._» — паттерн: **{ex['pattern']}**")
            else:
                st.success("✅ Контролирующих паттернов не обнаружено")
            
            st.divider()
            
            # Поддержка
            if any(stats['support'].values()):
                st.markdown("#### 🤝 Поддержка")
                for category, examples in stats['support'].items():
                    if examples:
                        st.markdown(f"**{category.replace('_', ' ').title()}** ({len(examples)} случаев)")
                        for ex in examples[:3]:
                            st.caption(f"«_{ex['text']}..._»")
            else:
                st.info("📝 Паттернов поддержки не обнаружено")
    
    # Сравнительный анализ
    if len(users) >= 2:
        st.markdown("### ⚖️ Сравнительный анализ")
        
        user1, user2 = users[0], users[1]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{user1}**")
            stats1 = user_analysis[user1]
            avg1 = sum(stats1['sentiment_scores']) / len(stats1['sentiment_scores']) if stats1['sentiment_scores'] else 0
            
            st.metric("Среднее настроение", f"{avg1:+.2f}")
            st.metric("Неуверенность", sum(len(v) for v in stats1['insecurity'].values()))
            st.metric("Контроль", sum(len(v) for v in stats1['control'].values()))
            st.metric("Поддержка", sum(len(v) for v in stats1['support'].values()))
        
        with col2:
            st.markdown(f"**{user2}**")
            stats2 = user_analysis[user2]
            avg2 = sum(stats2['sentiment_scores']) / len(stats2['sentiment_scores']) if stats2['sentiment_scores'] else 0
            
            st.metric("Среднее настроение", f"{avg2:+.2f}")
            st.metric("Неуверенность", sum(len(v) for v in stats2['insecurity'].values()))
            st.metric("Контроль", sum(len(v) for v in stats2['control'].values()))
            st.metric("Поддержка", sum(len(v) for v in stats2['support'].values()))
    
    # Итоговые выводы
    st.markdown("### 💡 Выводы")
    
    for user in users:
        stats = user_analysis[user]
        avg_sentiment = sum(stats['sentiment_scores']) / len(stats['sentiment_scores']) if stats['sentiment_scores'] else 0
        
        total_insecurity = sum(len(v) for v in stats['insecurity'].values())
        total_control = sum(len(v) for v in stats['control'].values())
        total_support = sum(len(v) for v in stats['support'].values())
        
        # Нормализуем на 100 сообщений
        msg_count = stats['messages']
        ins_per_100 = total_insecurity / msg_count * 100 if msg_count > 0 else 0
        ctrl_per_100 = total_control / msg_count * 100 if msg_count > 0 else 0
        sup_per_100 = total_support / msg_count * 100 if msg_count > 0 else 0
        
        issues = []
        
        if avg_sentiment < -0.2:
            issues.append("преобладает негативное настроение")
        if ins_per_100 > 2:
            issues.append("повышенная неуверенность в себе")
        if ctrl_per_100 > 1:
            issues.append("признаки контролирующего поведения")
        
        positives = []
        if avg_sentiment > 0.2:
            positives.append("позитивный эмоциональный фон")
        if sup_per_100 > 3:
            positives.append("высокий уровень поддержки")
        
        if issues:
            st.warning(f"**{user}**: ⚠️ {', '.join(issues)}")
        
        if positives:
            st.success(f"**{user}**: ✅ {', '.join(positives)}")
        
        if not issues and not positives:
            st.info(f"**{user}**: 📊 Нейтральный профиль")
    
    st.markdown("---")
    st.caption("""
    **Методология**: Анализ использует взвешенные маркеры настроения, 
    учёт отрицаний ("не люблю" = негатив), контекстный анализ фраз.
    Точность выше простого поиска ключевых слов, но всё ещё не заменяет 
    профессиональную психологическую оценку.
    """)

