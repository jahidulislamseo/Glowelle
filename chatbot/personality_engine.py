"""
Chatbot Personality Customization for GlowElle
Provides time-based greetings and festival-specific responses.
"""

import datetime
from django.utils import timezone


class PersonalityEngine:
    """
    Chatbot personality customization system.
    """
    
    @staticmethod
    def get_time_based_greeting():
        """
        Get greeting based on current time.
        """
        hour = datetime.datetime.now().hour
        
        if 5 <= hour < 12:
            return "সুপ্রভাত! 🌅 আজ কি নিতে চান?"
        elif 12 <= hour < 17:
            return "শুভ বিকাল! ☀️ কি সাহায্য করতে পারি?"
        elif 17 <= hour < 21:
            return "শুভ সন্ধ্যা! 🌆 অর্ডার করবেন?"
        else:
            return "শুভ রাত্রি! 🌙 কি লাগবে?"
    
    @staticmethod
    def get_festival_greeting():
        """
        Get festival-specific greeting if applicable.
        """
        today = datetime.date.today()
        month = today.month
        day = today.day
        
        # Eid-ul-Fitr (approximate - varies by lunar calendar)
        if month in [4, 5]:
            return "ঈদ মুবারক! 🌙 ঈদের বাজার করবেন? আমাদের কাছে সব কিছু আছে!"
        
        # Eid-ul-Adha (approximate)
        if month in [7, 8]:
            return "ঈদ মুবারক! 🐑 কোরবানির জন্য কি লাগবে?"
        
        # Pohela Boishakh (April 14)
        if month == 4 and day == 14:
            return "শুভ নববর্ষ! 🎊 নতুন বছরে আমাদের সাথে কেনাকাটা করুন!"
        
        # Independence Day (March 26)
        if month == 3 and day == 26:
            return "স্বাধীনতা দিবসের শুভেচ্ছা! 🇧🇩 আজ বিশেষ ছাড় পাবেন!"
        
        # Victory Day (December 16)
        if month == 12 and day == 16:
            return "বিজয় দিবসের শুভেচ্ছা! 🇧🇩 আজ ১৬% ছাড়!"
        
        # Durga Puja (September-October)
        if month in [9, 10]:
            return "শুভ দুর্গা পূজা! 🪔 পূজার জন্য সব কিছু পাবেন!"
        
        # Christmas (December 25)
        if month == 12 and day == 25:
            return "Merry Christmas! 🎄 আজ বিশেষ অফার!"
        
        # New Year (January 1)
        if month == 1 and day == 1:
            return "Happy New Year! 🎉 নতুন বছরে নতুন অফার!"
        
        return None
    
    @staticmethod
    def get_contextual_greeting(greeting_count=0):
        """
        Get greeting based on conversation context.
        """
        # Check for festival first
        festival_greeting = PersonalityEngine.get_festival_greeting()
        if festival_greeting:
            return festival_greeting
        
        # Then check greeting count
        if greeting_count == 0:
            time_greeting = PersonalityEngine.get_time_based_greeting()
            return f"Assalamualaikum! GlowElle এ স্বাগতম 😊\n{time_greeting}"
        elif greeting_count == 1:
            return "Alhamdulillah bhalo 😊 Apni ki nite chan?"
        else:
            return "Ki lagbe?"
    
    @staticmethod
    def get_persona_prompt(persona='friendly'):
        """
        Get system prompt for different personas.
        """
        personas = {
            'friendly': """তুমি একজন বন্ধুত্বপূর্ণ এবং সহায়ক সহকারী। তুমি:
- সংক্ষিপ্ত এবং স্পষ্ট বাক্য ব্যবহার কর
- ইমোজি ব্যবহার কর (১-২টি প্রতি বার্তায়)
- প্রাকৃতিক কথোপকথন বজায় রাখ
- গ্রাহকদের সাথে বন্ধুর মতো আচরণ কর
""",
            
            'formal': """আপনি একজন পেশাদার সহকারী। আপনি:
- আনুষ্ঠানিক ভাষা ব্যবহার করেন
- সংক্ষিপ্ত এবং সুস্পষ্ট তথ্য প্রদান করেন
- ইমোজি কম ব্যবহার করেন
- গ্রাহকদের সাথে সম্মানজনক আচরণ করেন
""",
            
            'casual': """Tumi ekjon casual ebong friendly assistant. Tumi:
- Banglish use koro naturally
- Emoji use koro freely
- Relaxed conversation maintain koro
- Customers er sathe friendly behave koro
"""
        }
        
        return personas.get(persona, personas['friendly'])
    
    @staticmethod
    def get_response_style(language='banglish', persona='friendly'):
        """
        Get response style based on language and persona.
        """
        styles = {
            ('bengali', 'friendly'): {
                'greeting': 'হ্যাঁ, বলুন! 😊',
                'thanks': 'আপনাকে ধন্যবাদ! 🙏',
                'bye': 'আসসালামু আলাইকুম! আবার আসবেন। 👋'
            },
            ('english', 'friendly'): {
                'greeting': 'Yes, how can I help? 😊',
                'thanks': 'You\'re welcome! 🙏',
                'bye': 'Goodbye! Come again. 👋'
            },
            ('banglish', 'friendly'): {
                'greeting': 'Ha, bolun! 😊',
                'thanks': 'Apnake dhonnobad! 🙏',
                'bye': 'Assalamualaikum! Abar asben. 👋'
            }
        }
        
        return styles.get((language, persona), styles[('banglish', 'friendly')])


# Singleton instance
_personality_engine = None

def get_personality_engine():
    """
    Get or create personality engine instance.
    """
    global _personality_engine
    if _personality_engine is None:
        _personality_engine = PersonalityEngine()
    return _personality_engine


def get_contextual_greeting(greeting_count=0):
    """
    Helper function to get contextual greeting.
    """
    return PersonalityEngine.get_contextual_greeting(greeting_count)


def get_time_based_greeting():
    """
    Helper function to get time-based greeting.
    """
    return PersonalityEngine.get_time_based_greeting()
