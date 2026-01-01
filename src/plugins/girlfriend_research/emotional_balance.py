"""
Emotional Balance Analyzer
Анализирует эмоциональный баланс сообщений: позитив vs негатив
Помогает понять общий эмоциональный фон общения
"""
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Расширенные словари для русского и английского
POSITIVE_MARKERS = {
    # Русские
    'люблю', 'обожаю', 'счастлив', 'счастлива', 'рад', 'рада', 'радость',
    'прекрасн', 'замечательн', 'отличн', 'супер', 'класс', 'круто', 'кайф',
    'здорово', 'молодец', 'умница', 'горжусь', 'благодар', 'спасибо',
    'ура', 'йей', 'вау', 'ого', 'офигенн', 'потрясающ', 'восхитительн',
    'нежн', 'милый', 'милая', 'солнц', 'котик', 'зая', 'малыш', 'родн',
    'скучаю', 'целую', 'обнимаю', 'хочу к тебе', 'жду', 'мечтаю',
    'верю в тебя', 'поддержив', 'всё получится', 'ты лучш', 'ты супер',
    'красив', 'умный', 'умная', 'талантлив', 'интересн', 'весел', 'смешн',
    'хаха', 'хехе', 'лол', '😊', '😍', '🥰', '❤️', '💕', '💖', '🥺', '😘', '💋',
    '🤗', '✨', '🎉', '😂', '🤣', '😁', '😃', '😄', '💪', '👍', '🙏',
    # Английские
    'love', 'happy', 'great', 'amazing', 'wonderful', 'beautiful', 'awesome',
    'perfect', 'best', 'thank', 'proud', 'excited', 'glad', 'joy', 'miss you',
    'hug', 'kiss', 'sweet', 'cute', 'lovely', 'adore', 'appreciate', 'grateful',
}

NEGATIVE_MARKERS = {
    # Русские - жалобы, нытьё, негатив
    'устал', 'устала', 'достало', 'надоело', 'задолбал', 'бесит', 'бешу',
    'раздража', 'злюсь', 'злит', 'ненавижу', 'не могу больше', 'сил нет',
    'плохо', 'ужасн', 'кошмар', 'отвратительн', 'мерзк', 'противн',
    'грустно', 'грущу', 'печаль', 'тоска', 'одинок', 'несчастн', 'плачу',
    'обидел', 'обидно', 'обижен', 'обижена', 'разочарован', 'расстроен',
    'боюсь', 'страшно', 'тревожн', 'переживаю', 'нервнича', 'стресс',
    'болит', 'заболе', 'плохо себя чувствую', 'тошнит', 'голова раскалывается',
    'не хочу', 'не буду', 'отстань', 'надоел', 'достал', 'заткнись',
    'тупой', 'тупая', 'идиот', 'дурак', 'дура', 'ненормальн',
    'всё плохо', 'ничего не получается', 'не справляюсь', 'провал',
    'никогда', 'вечно ты', 'опять ты', 'всегда так', 'постоянно',
    '😢', '😭', '😞', '😔', '😕', '😟', '😣', '😖', '😫', '😩',
    '😤', '😠', '😡', '🤬', '💔', '😒', '🙄', '😑',
    # Английские
    'hate', 'angry', 'sad', 'tired', 'annoyed', 'frustrated', 'upset',
    'disappointed', 'hurt', 'scared', 'worried', 'stressed', 'sick',
    'awful', 'terrible', 'horrible', 'worst', 'stupid', 'idiot', 'shut up',
    'never', 'always you', 'again you', 'cant', "can't", 'dont', "don't want",
}

# Маркеры неуверенности в себе
INSECURITY_MARKERS = {
    # Русские
    'я не достойн', 'не заслужива', 'я плох', 'я хуже', 'ты лучше меня',
    'я некрасив', 'я толст', 'я глуп', 'я тупая', 'я тупой',
    'меня никто не любит', 'я никому не нужн', 'ты меня бросишь',
    'ты найдёшь лучше', 'я тебе надоела', 'я тебе надоел', 
    'ты устанешь от меня', 'зачем я тебе', 'почему ты со мной',
    'ты точно меня любишь', 'ты меня ещё любишь', 'я не интересн',
    'я скучная', 'я скучный', 'со мной скучно', 'я ничего не умею',
    'у меня ничего не получается', 'я неудачник', 'я неудачница',
    'я всё порчу', 'это моя вина', 'прости что я такая', 'прости что я такой',
    'ты разлюбишь', 'ты уйдёшь', 'ты меня обманыва', 'ты врёшь',
    'ты изменяешь', 'ты с кем-то', 'кто она', 'кто он',
    # Манипуляции через неуверенность
    'тебе на меня плевать', 'тебе всё равно', 'ты меня не любишь',
    'ты меня не понимаешь', 'никто меня не понимает',
    # Английские
    'im not good enough', "i'm not worthy", 'you deserve better',
    'you will leave', 'youll find someone better', 'am i boring',
    'do you still love me', 'you dont love me', "you don't care",
    'nobody loves me', 'i ruin everything', 'its my fault', "it's my fault",
}

# Маркеры эмоционального шантажа / манипуляций
MANIPULATION_MARKERS = {
    # Русские
    'если ты меня любишь', 'если бы ты меня любил', 'если бы ты меня любила',
    'докажи что любишь', 'ты должен', 'ты должна', 'ты обязан', 'ты обязана',
    'из-за тебя', 'это твоя вина', 'ты виноват', 'ты виновата',
    'ты меня довёл', 'ты меня довела', 'ты меня достал', 'ты меня достала',
    'мне плохо из-за тебя', 'я страдаю из-за тебя', 'ты меня убиваешь',
    'я умру', 'мне конец', 'я не могу без тебя жить', 'я покончу',
    'ты пожалеешь', 'ты ещё пожалеешь', 'будешь жалеть',
    'все так делают', 'нормальные парни', 'нормальные девушки',
    'мой бывший', 'моя бывшая', 'а вот он', 'а вот она',
    'я же для тебя', 'после всего что я', 'сколько я для тебя',
    # Английские
    'if you loved me', 'prove you love me', 'you have to', 'you must',
    'its your fault', "it's your fault", 'because of you', 'you made me',
    'i cant live without you', "i can't live without you", 'youll regret',
    'my ex', 'other guys', 'other girls', 'after all i did',
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


def count_markers(text, markers):
    """Считает количество маркеров в тексте"""
    text_lower = text.lower()
    count = 0
    found = []
    for marker in markers:
        if marker in text_lower:
            count += 1
            found.append(marker)
    return count, found


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")
    
    if not messages:
        st.warning("Нет сообщений для анализа.")
        return
    
    st.subheader(f"💚 Эмоциональный Баланс — {chat_name}")
    st.markdown("Анализ эмоционального фона общения: позитив, негатив, неуверенность, манипуляции")
    
    # Собираем статистику по пользователям
    user_stats = defaultdict(lambda: {
        'positive': 0, 'negative': 0, 'insecurity': 0, 'manipulation': 0,
        'total_messages': 0, 'positive_examples': [], 'negative_examples': [],
        'insecurity_examples': [], 'manipulation_examples': []
    })
    
    # Статистика по месяцам для графика динамики
    monthly_stats = defaultdict(lambda: defaultdict(lambda: {'positive': 0, 'negative': 0}))
    
    for msg in messages:
        sender = msg.get('from')
        if not sender:
            continue
            
        text = get_text(msg)
        if not text or len(text) < 2:
            continue
        
        user_stats[sender]['total_messages'] += 1
        
        # Считаем маркеры
        pos_count, pos_found = count_markers(text, POSITIVE_MARKERS)
        neg_count, neg_found = count_markers(text, NEGATIVE_MARKERS)
        ins_count, ins_found = count_markers(text, INSECURITY_MARKERS)
        man_count, man_found = count_markers(text, MANIPULATION_MARKERS)
        
        user_stats[sender]['positive'] += pos_count
        user_stats[sender]['negative'] += neg_count
        user_stats[sender]['insecurity'] += ins_count
        user_stats[sender]['manipulation'] += man_count
        
        # Сохраняем примеры (первые 10)
        if pos_found and len(user_stats[sender]['positive_examples']) < 10:
            user_stats[sender]['positive_examples'].append((text[:100], pos_found))
        if neg_found and len(user_stats[sender]['negative_examples']) < 10:
            user_stats[sender]['negative_examples'].append((text[:100], neg_found))
        if ins_found and len(user_stats[sender]['insecurity_examples']) < 10:
            user_stats[sender]['insecurity_examples'].append((text[:100], ins_found))
        if man_found and len(user_stats[sender]['manipulation_examples']) < 10:
            user_stats[sender]['manipulation_examples'].append((text[:100], man_found))
        
        # Статистика по месяцам
        try:
            dt = parse_date(msg['date'])
            month_key = dt.strftime('%Y-%m')
            monthly_stats[month_key][sender]['positive'] += pos_count
            monthly_stats[month_key][sender]['negative'] += neg_count
        except:
            pass
    
    if not user_stats:
        st.warning("Не удалось проанализировать сообщения.")
        return
    
    # Основная таблица
    st.markdown("### 📊 Общая статистика")
    
    table_data = []
    for user, stats in user_stats.items():
        total = stats['positive'] + stats['negative']
        if total > 0:
            pos_ratio = stats['positive'] / total * 100
            neg_ratio = stats['negative'] / total * 100
        else:
            pos_ratio = neg_ratio = 50
        
        # Индекс здоровья: (позитив - негатив - неуверенность*2 - манипуляции*3) / всего сообщений
        health_score = (stats['positive'] - stats['negative'] - stats['insecurity']*2 - stats['manipulation']*3)
        if stats['total_messages'] > 0:
            health_score = health_score / stats['total_messages'] * 100
        
        table_data.append({
            'Пользователь': user,
            'Сообщений': stats['total_messages'],
            '😊 Позитив': stats['positive'],
            '😢 Негатив': stats['negative'],
            '😰 Неуверенность': stats['insecurity'],
            '🎭 Манипуляции': stats['manipulation'],
            'Позитив %': f"{pos_ratio:.1f}%",
            '💚 Индекс здоровья': f"{health_score:.1f}"
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, hide_index=True)
    
    # Интерпретация
    st.markdown("### 🔍 Интерпретация")
    
    for user, stats in user_stats.items():
        with st.expander(f"📝 Анализ: {user}"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Позитив/Негатив баланс
                total = stats['positive'] + stats['negative']
                if total > 0:
                    pos_ratio = stats['positive'] / total * 100
                    if pos_ratio >= 70:
                        st.success(f"✅ Преобладает позитив ({pos_ratio:.0f}%)")
                    elif pos_ratio >= 50:
                        st.info(f"⚖️ Баланс примерно равный ({pos_ratio:.0f}% позитива)")
                    else:
                        st.warning(f"⚠️ Преобладает негатив ({100-pos_ratio:.0f}%)")
                
                # Неуверенность
                ins_per_100 = stats['insecurity'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
                if ins_per_100 > 5:
                    st.error(f"🚨 Высокий уровень неуверенности ({ins_per_100:.1f} на 100 сообщений)")
                elif ins_per_100 > 2:
                    st.warning(f"⚠️ Заметная неуверенность ({ins_per_100:.1f} на 100 сообщений)")
                elif ins_per_100 > 0:
                    st.info(f"📊 Небольшая неуверенность ({ins_per_100:.1f} на 100 сообщений)")
                else:
                    st.success("✅ Признаков неуверенности не обнаружено")
            
            with col2:
                # Манипуляции
                man_per_100 = stats['manipulation'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
                if man_per_100 > 3:
                    st.error(f"🚨 Высокий уровень манипулятивности ({man_per_100:.1f} на 100 сообщений)")
                elif man_per_100 > 1:
                    st.warning(f"⚠️ Есть признаки манипуляций ({man_per_100:.1f} на 100 сообщений)")
                elif man_per_100 > 0:
                    st.info(f"📊 Редкие манипулятивные паттерны ({man_per_100:.1f} на 100 сообщений)")
                else:
                    st.success("✅ Манипулятивных паттернов не обнаружено")
            
            # Примеры
            if stats['insecurity_examples']:
                st.markdown("**Примеры неуверенности:**")
                for text, markers in stats['insecurity_examples'][:3]:
                    st.caption(f"_{text}..._ → маркеры: {', '.join(markers)}")
            
            if stats['manipulation_examples']:
                st.markdown("**Примеры манипуляций:**")
                for text, markers in stats['manipulation_examples'][:3]:
                    st.caption(f"_{text}..._ → маркеры: {', '.join(markers)}")
    
    # График динамики
    if len(monthly_stats) > 1:
        st.markdown("### 📈 Динамика эмоционального фона по месяцам")
        
        months = sorted(monthly_stats.keys())
        users = list(user_stats.keys())
        
        fig, axes = plt.subplots(len(users), 1, figsize=(12, 4*len(users)))
        if len(users) == 1:
            axes = [axes]
        
        for idx, user in enumerate(users):
            pos_values = [monthly_stats[m][user]['positive'] for m in months]
            neg_values = [monthly_stats[m][user]['negative'] for m in months]
            
            axes[idx].bar(months, pos_values, label='Позитив', color='green', alpha=0.7)
            axes[idx].bar(months, [-n for n in neg_values], label='Негатив', color='red', alpha=0.7)
            axes[idx].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            axes[idx].set_title(f'{user}')
            axes[idx].legend()
            axes[idx].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    # Итоговый вывод
    st.markdown("### 💡 Выводы")
    
    for user, stats in user_stats.items():
        ins_per_100 = stats['insecurity'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        man_per_100 = stats['manipulation'] / stats['total_messages'] * 100 if stats['total_messages'] > 0 else 0
        total = stats['positive'] + stats['negative']
        pos_ratio = stats['positive'] / total * 100 if total > 0 else 50
        
        issues = []
        if pos_ratio < 50:
            issues.append("преобладание негатива")
        if ins_per_100 > 2:
            issues.append("неуверенность в себе")
        if man_per_100 > 1:
            issues.append("манипулятивные паттерны")
        
        if issues:
            st.warning(f"**{user}**: обнаружены потенциальные проблемы: {', '.join(issues)}")
        else:
            st.success(f"**{user}**: эмоциональный фон в норме")
