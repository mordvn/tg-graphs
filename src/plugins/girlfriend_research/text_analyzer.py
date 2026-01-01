"""
Text Analyzer - общий модуль для улучшенного анализа текста.
Используется другими плагинами girlfriend_research.

Улучшения по сравнению с простым поиском маркеров:
1. N-граммы (фразы из 2-3 слов)
2. Контекстный анализ (что перед/после ключевого слова)
3. Нормализация текста
4. Учёт отрицаний ("не люблю" vs "люблю")
5. Эмодзи-анализ
"""
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Set, Optional


def normalize_text(text: str) -> str:
    """Нормализует текст: нижний регистр, убирает лишние пробелы"""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_words(text: str) -> List[str]:
    """Извлекает слова из текста"""
    # Разделяем по не-буквам, но сохраняем эмодзи
    words = re.findall(r'[\w]+|[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text.lower())
    return words


def get_ngrams(words: List[str], n: int) -> List[str]:
    """Создаёт n-граммы из списка слов"""
    if len(words) < n:
        return []
    return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]


def check_negation(text: str, keyword: str, window: int = 3) -> bool:
    """Проверяет, есть ли отрицание перед ключевым словом"""
    negations = {'не', 'нет', 'ни', 'никогда', 'без', 'never', 'not', "don't", "doesn't", "didn't"}
    
    words = extract_words(text)
    try:
        idx = words.index(keyword)
        # Проверяем слова перед ключевым
        start = max(0, idx - window)
        context = words[start:idx]
        return any(neg in context for neg in negations)
    except ValueError:
        return False


class SentimentAnalyzer:
    """Анализатор настроения текста"""
    
    # Расширенные словари с весами
    POSITIVE_WORDS = {
        # Сильный позитив (вес 2)
        'люблю': 2, 'обожаю': 2, 'счастлив': 2, 'счастлива': 2, 'восхитительно': 2,
        'потрясающе': 2, 'прекрасно': 2, 'идеально': 2, 'невероятно': 2,
        'love': 2, 'amazing': 2, 'wonderful': 2, 'perfect': 2, 'incredible': 2,
        
        # Средний позитив (вес 1)
        'хорошо': 1, 'отлично': 1, 'круто': 1, 'классно': 1, 'здорово': 1,
        'нравится': 1, 'рад': 1, 'рада': 1, 'доволен': 1, 'довольна': 1,
        'спасибо': 1, 'благодарю': 1, 'молодец': 1, 'умница': 1,
        'great': 1, 'good': 1, 'nice': 1, 'happy': 1, 'glad': 1, 'thanks': 1,
        
        # Слабый позитив (вес 0.5)
        'норм': 0.5, 'ок': 0.5, 'окей': 0.5, 'неплохо': 0.5, 'сойдёт': 0.5,
        'okay': 0.5, 'fine': 0.5, 'alright': 0.5,
    }
    
    NEGATIVE_WORDS = {
        # Сильный негатив (вес 2)
        'ненавижу': 2, 'отвратительно': 2, 'ужасно': 2, 'кошмар': 2,
        'hate': 2, 'terrible': 2, 'horrible': 2, 'awful': 2,
        
        # Средний негатив (вес 1)
        'плохо': 1, 'грустно': 1, 'обидно': 1, 'расстроен': 1, 'расстроена': 1,
        'злюсь': 1, 'бесит': 1, 'раздражает': 1, 'достало': 1, 'надоело': 1,
        'устал': 1, 'устала': 1, 'разочарован': 1, 'разочарована': 1,
        'sad': 1, 'angry': 1, 'upset': 1, 'annoyed': 1, 'tired': 1, 'bad': 1,
        
        # Слабый негатив (вес 0.5)
        'не очень': 0.5, 'так себе': 0.5, 'могло быть лучше': 0.5,
        'not great': 0.5, 'meh': 0.5,
    }
    
    POSITIVE_EMOJIS = {
        '😊': 1, '😄': 1, '😃': 1, '😁': 1, '🙂': 0.5, '😍': 2, '🥰': 2,
        '❤️': 1.5, '💕': 1.5, '💖': 1.5, '💗': 1, '💓': 1, '💘': 1.5,
        '😘': 1.5, '😚': 1, '😻': 1.5, '🤗': 1, '🥳': 1.5, '🎉': 1,
        '👍': 0.5, '👏': 1, '🙏': 0.5, '✨': 0.5, '🌟': 0.5, '💪': 0.5,
    }
    
    NEGATIVE_EMOJIS = {
        '😢': 1, '😭': 1.5, '😞': 1, '😔': 1, '😟': 1, '😕': 0.5,
        '😤': 1, '😠': 1.5, '😡': 2, '🤬': 2, '💔': 1.5, '😒': 1,
        '🙄': 0.5, '😑': 0.5, '😩': 1, '😫': 1, '😣': 1, '😖': 1,
    }
    
    def analyze(self, text: str) -> Dict:
        """
        Анализирует текст и возвращает оценку настроения.
        
        Returns:
            Dict с ключами:
            - score: float от -1 до 1 (-1 = очень негативно, 1 = очень позитивно)
            - positive_words: list найденных позитивных слов
            - negative_words: list найденных негативных слов
            - confidence: float от 0 до 1 (уверенность в оценке)
        """
        text_lower = normalize_text(text)
        words = extract_words(text)
        
        positive_score = 0.0
        negative_score = 0.0
        positive_found = []
        negative_found = []
        
        # Анализ слов
        for word in words:
            if word in self.POSITIVE_WORDS:
                # Проверяем отрицание
                if check_negation(text_lower, word):
                    negative_score += self.POSITIVE_WORDS[word]
                    negative_found.append(f"не {word}")
                else:
                    positive_score += self.POSITIVE_WORDS[word]
                    positive_found.append(word)
            
            if word in self.NEGATIVE_WORDS:
                if check_negation(text_lower, word):
                    positive_score += self.NEGATIVE_WORDS[word] * 0.5  # Двойное отрицание слабее
                    positive_found.append(f"не {word}")
                else:
                    negative_score += self.NEGATIVE_WORDS[word]
                    negative_found.append(word)
        
        # Анализ эмодзи
        for char in text:
            if char in self.POSITIVE_EMOJIS:
                positive_score += self.POSITIVE_EMOJIS[char]
                positive_found.append(char)
            if char in self.NEGATIVE_EMOJIS:
                negative_score += self.NEGATIVE_EMOJIS[char]
                negative_found.append(char)
        
        # Вычисляем итоговый score
        total = positive_score + negative_score
        if total == 0:
            score = 0.0
            confidence = 0.0
        else:
            score = (positive_score - negative_score) / total
            # Уверенность зависит от количества найденных маркеров
            confidence = min(1.0, total / 5)
        
        return {
            'score': score,
            'positive_words': positive_found,
            'negative_words': negative_found,
            'positive_score': positive_score,
            'negative_score': negative_score,
            'confidence': confidence,
        }


class PatternMatcher:
    """Улучшенный поиск паттернов с контекстом"""
    
    def __init__(self, patterns: Dict[str, Set[str]]):
        """
        patterns: Dict категория -> набор паттернов
        """
        self.patterns = patterns
        # Разделяем на одиночные слова и фразы
        self.single_words = {}
        self.phrases = {}
        
        for category, pattern_set in patterns.items():
            self.single_words[category] = set()
            self.phrases[category] = set()
            
            for p in pattern_set:
                if ' ' in p:
                    self.phrases[category].add(p.lower())
                else:
                    self.single_words[category].add(p.lower())
    
    def find_all(self, text: str) -> Dict[str, List[Tuple[str, str]]]:
        """
        Находит все паттерны в тексте.
        
        Returns:
            Dict категория -> List[(найденный_паттерн, контекст)]
        """
        text_lower = normalize_text(text)
        words = extract_words(text)
        
        results = defaultdict(list)
        
        for category in self.patterns:
            # Проверяем фразы
            for phrase in self.phrases[category]:
                if phrase in text_lower:
                    # Извлекаем контекст
                    idx = text_lower.find(phrase)
                    start = max(0, idx - 30)
                    end = min(len(text_lower), idx + len(phrase) + 30)
                    context = text_lower[start:end]
                    results[category].append((phrase, context))
            
            # Проверяем одиночные слова
            for word in words:
                if word in self.single_words[category]:
                    # Проверяем отрицание
                    negated = check_negation(text_lower, word)
                    pattern = f"не {word}" if negated else word
                    
                    # Извлекаем контекст
                    try:
                        idx = words.index(word)
                        start = max(0, idx - 3)
                        end = min(len(words), idx + 4)
                        context = ' '.join(words[start:end])
                    except:
                        context = word
                    
                    results[category].append((pattern, context))
        
        return dict(results)
    
    def count_by_category(self, text: str) -> Dict[str, int]:
        """Считает количество совпадений по категориям"""
        matches = self.find_all(text)
        return {cat: len(matches) for cat, matches in matches.items()}


class RelationshipAnalyzer:
    """Комплексный анализатор отношений"""
    
    # Паттерны для разных аспектов отношений
    INSECURITY_PATTERNS = {
        'самокритика': {
            'я не достойна', 'я не достоин', 'я плохая', 'я плохой',
            'я хуже', 'я некрасивая', 'я некрасивый', 'я толстая', 'я толстый',
            'я глупая', 'я глупый', 'я тупая', 'я тупой',
        },
        'страх_отвержения': {
            'ты меня бросишь', 'ты уйдёшь', 'ты найдёшь лучше',
            'я тебе надоела', 'я тебе надоел', 'ты устанешь от меня',
            'зачем я тебе', 'почему ты со мной',
        },
        'проверки': {
            'ты меня любишь', 'ты ещё любишь', 'ты точно любишь',
            'ты соскучился', 'ты скучал', 'ты рад меня видеть',
        },
    }
    
    CONTROL_PATTERNS = {
        'слежка': {
            'где ты', 'ты где', 'с кем ты', 'кто там', 'что делаешь',
            'почему не отвечаешь', 'почему долго', 'когда вернёшься',
        },
        'запреты': {
            'не ходи', 'не общайся', 'не разговаривай', 'я запрещаю',
            'нельзя', 'не разрешаю', 'не позволяю',
        },
        'требования': {
            'ты должен', 'ты должна', 'ты обязан', 'ты обязана',
            'покажи переписку', 'дай телефон', 'открой локацию',
        },
    }
    
    SUPPORT_PATTERNS = {
        'эмоциональная': {
            'я рядом', 'я с тобой', 'всё будет хорошо', 'ты справишься',
            'верю в тебя', 'горжусь тобой', 'ты молодец',
        },
        'практическая': {
            'могу помочь', 'чем помочь', 'давай помогу', 'сделаю для тебя',
            'решу', 'разберусь', 'не беспокойся',
        },
        'интерес': {
            'как дела', 'как ты', 'что случилось', 'расскажи',
            'как прошёл день', 'как себя чувствуешь',
        },
    }
    
    def __init__(self):
        self.sentiment = SentimentAnalyzer()
        self.insecurity_matcher = PatternMatcher(self.INSECURITY_PATTERNS)
        self.control_matcher = PatternMatcher(self.CONTROL_PATTERNS)
        self.support_matcher = PatternMatcher(self.SUPPORT_PATTERNS)
    
    def analyze_message(self, text: str) -> Dict:
        """Комплексный анализ одного сообщения"""
        sentiment = self.sentiment.analyze(text)
        
        return {
            'sentiment': sentiment,
            'insecurity': self.insecurity_matcher.find_all(text),
            'control': self.control_matcher.find_all(text),
            'support': self.support_matcher.find_all(text),
        }
    
    def analyze_conversation(self, messages: List[Dict]) -> Dict:
        """Анализ всей переписки"""
        user_stats = defaultdict(lambda: {
            'messages': 0,
            'sentiment_sum': 0.0,
            'sentiment_count': 0,
            'insecurity': defaultdict(int),
            'control': defaultdict(int),
            'support': defaultdict(int),
        })
        
        for msg in messages:
            sender = msg.get('from')
            if not sender:
                continue
            
            text = msg.get('text', '')
            if isinstance(text, list):
                text = ' '.join(
                    p if isinstance(p, str) else p.get('text', '')
                    for p in text
                )
            
            if not text:
                continue
            
            analysis = self.analyze_message(text)
            
            user_stats[sender]['messages'] += 1
            
            if analysis['sentiment']['confidence'] > 0.3:
                user_stats[sender]['sentiment_sum'] += analysis['sentiment']['score']
                user_stats[sender]['sentiment_count'] += 1
            
            for category, matches in analysis['insecurity'].items():
                user_stats[sender]['insecurity'][category] += len(matches)
            
            for category, matches in analysis['control'].items():
                user_stats[sender]['control'][category] += len(matches)
            
            for category, matches in analysis['support'].items():
                user_stats[sender]['support'][category] += len(matches)
        
        # Вычисляем средние значения
        for user, stats in user_stats.items():
            if stats['sentiment_count'] > 0:
                stats['avg_sentiment'] = stats['sentiment_sum'] / stats['sentiment_count']
            else:
                stats['avg_sentiment'] = 0.0
        
        return dict(user_stats)

