from langdetect import detect
from deep_translator import GoogleTranslator

def translator(text: str, language: str):
    """
    Translate text to the specified language using Google Translate.
    
    Args:
        text (str): The text to be translated.
        language (str): The target language for translation. Supported values:
            - 'Deutsch': German
            - 'English': English
            - 'Chinese': Chinese (Simplified)
            - 'Türkçe': Turkish
            - 'Original': No translation (returns original text)
    
    Returns:
        str: The translated text, or the original text if translation fails or is not needed.
    """
    language_map = {
        'Deutsch': 'de',
        'English': 'en',
        'Chinese': 'zh-CN',
        'Türkçe': 'tr',
        'Original': None  # Add Original option, means no translation
    }
    
    try:
        target_lang = language_map.get(language)
        
        # If Original is selected or mapping does not exist, return the original text
        if target_lang is None:
            return text
            
        detected_lang = detect(text)
        
        # If the detected language is the same as the target language, return the original text
        if detected_lang == target_lang:
            return text
        else:
            # Perform translation
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            return translated if translated else text
            
    except Exception as e:
        # Return the original text if translation fails
        print(f"Translation error: {e}")
        return text