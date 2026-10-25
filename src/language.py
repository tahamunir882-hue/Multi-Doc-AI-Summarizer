from langdetect import DetectorFactory, detect

DetectorFactory.seed = 0

# code -> name used in prompts / dropdowns
LANGUAGES = {
    "en": "English", "ur": "Urdu", "roman-ur": "Roman Urdu (Urdu in English letters)",
    "ar": "Arabic", "fa": "Persian", "hi": "Hindi", "zh-cn": "Chinese", "ja": "Japanese",
    "ko": "Korean", "fr": "French", "de": "German", "es": "Spanish", "it": "Italian",
    "pt": "Portuguese", "ru": "Russian", "tr": "Turkish", "ms": "Malay", "id": "Indonesian",
}


def detect_language(text: str) -> str:
    try:
        return detect(text.replace("\f", " ")[:3000])
    except Exception:
        return "en"


def language_name(code: str) -> str:
    return LANGUAGES.get(code, code)
