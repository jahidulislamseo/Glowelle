"""
Multi-Language Support for Al Barakah Mart Chatbot
Handles language detection and translation.
"""

import re
from deep_translator import GoogleTranslator


class LanguageDetector:
    """
    Detect language from user input.
    """
    
    @staticmethod
    def detect(text):
        """
        Detect language: bengali, english, or banglish.
        """
        if not text:
            return 'banglish'
        
        # Check for Bengali Unicode characters
        bengali_chars = re.findall(r'[\u0980-\u09FF]', text)
        if len(bengali_chars) > len(text) * 0.3:  # 30% Bengali chars
            return 'bengali'
        
        # Check if mostly ASCII (English or Banglish)
        if text.isascii():
            # Check for common Banglish patterns
            banglish_patterns = [
                'apni', 'tumi', 'ami', 'kemon', 'achen', 'aso', 'koro',
                'lagbe', 'hobe', 'ase', 'nai', 'ki', 'koto', 'dam',
                'delivery', 'order', 'korbo', 'nibo', 'dibo'
            ]
            
            text_lower = text.lower()
            if any(pattern in text_lower for pattern in banglish_patterns):
                return 'banglish'
            
            return 'english'
        
        # Mixed content - default to Banglish
        return 'banglish'
    
    @staticmethod
    def get_language_name(code):
        """
        Get human-readable language name.
        """
        names = {
            'bengali': 'বাংলা',
            'english': 'English',
            'banglish': 'Banglish'
        }
        return names.get(code, 'Unknown')


class MultiLanguageSupport:
    """
    Provide multi-language support for chatbot.
    """
    
    def __init__(self):
        self.detector = LanguageDetector()
        self.translator = None
    
    def translate_to_bengali(self, text):
        """
        Translate English text to Bengali.
        """
        try:
            if not self.translator:
                self.translator = GoogleTranslator(source='en', target='bn')
            return self.translator.translate(text)
        except Exception as e:
            return text
    
    def translate_to_english(self, text):
        """
        Translate Bengali text to English.
        """
        try:
            translator = GoogleTranslator(source='bn', target='en')
            return translator.translate(text)
        except Exception as e:
            return text
    
    def get_response_language(self, user_message):
        """
        Determine which language to respond in based on user's message.
        """
        detected = self.detector.detect(user_message)
        
        # Respond in same language as user
        return detected
    
    def format_response(self, response, target_language):
        """
        Format response according to target language preferences.
        """
        if target_language == 'english':
            # Remove Bangla-specific emojis and formatting
            response = response.replace('✅', '✓')
            response = response.replace('❌', '✗')
        
        return response


# Singleton instance
_language_support = None

def get_language_support():
    """
    Get or create language support instance.
    """
    global _language_support
    if _language_support is None:
        _language_support = MultiLanguageSupport()
    return _language_support


def detect_language(text):
    """
    Helper function to detect language.
    """
    detector = LanguageDetector()
    return detector.detect(text)


def get_system_prompt_by_language(language):
    """
    Get language-specific system prompt.
    """
    prompts = {
        'bengali': """তুমি 'Al Barakah Mart' এর একজন সহায়ক সহকারী। তুমি গ্রাহকদের পণ্য খুঁজে পেতে, অর্ডার করতে এবং প্রশ্নের উত্তর দিতে সাহায্য কর।

নিয়ম:
- সংক্ষিপ্ত এবং স্পষ্ট বাক্য ব্যবহার কর (সর্বোচ্চ ২-৩ লাইন)
- প্রতি বার্তায় ১-২টি ইমোজি ব্যবহার কর
- "আমি একটি AI" বলবে না
- প্রাকৃতিক কথোপকথন বজায় রাখ
""",
        
        'english': """You are a helpful assistant for 'Al Barakah Mart'. You help customers find products, place orders, and answer questions.

Rules:
- Use short and clear sentences (max 2-3 lines)
- Use 1-2 emojis per message
- Don't say "I am an AI"
- Maintain natural conversation
""",
        
        'banglish': """Tumi 'Al Barakah Mart' er ekjon helpful assistant. Tumi customers ke product khuje pete, order korte ebong questions er answer dite help koro.

Rules:
- Choto ebong clear sentences use koro (max 2-3 lines)
- Proti message e 1-2 emoji use koro
- "Ami ekta AI" bolbe na
- Natural conversation maintain koro
"""
    }
    
    return prompts.get(language, prompts['banglish'])
