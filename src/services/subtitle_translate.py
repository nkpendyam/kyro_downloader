"""Subtitle translation service."""
from pathlib import Path

import requests
from src.utils.logger import get_logger
logger = get_logger(__name__)

TRANSLATION_API = "https://api.mymemory.translated.net/get"

def translate_subtitle(text: str, source_lang: str = "en", target_lang: str = "es") -> str:
    """Translate subtitle text using MyMemory API (free, no key required).

    Args:
        text: Subtitle text to translate
        source_lang: Source language code (default: en)
        target_lang: Target language code (default: es)

    Returns:
        Translated text or original text on failure
    """
    if not text or not text.strip():
        return text
    try:
        params = {"q": text[:500], "langpair": f"{source_lang}|{target_lang}"}
        response = requests.get(TRANSLATION_API, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get("responseData", {}).get("translatedText", text)
    except Exception as e:
        logger.warning(f"Subtitle translation failed: {e}")
        return text

def translate_srt_file(input_path: str | Path, output_path: str | Path, source_lang: str = "en", target_lang: str = "es") -> bool:
    """Translate an SRT subtitle file.

    Args:
        input_path: Path to input SRT file
        output_path: Path to output translated SRT file
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        translated = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.isdigit() and "-->" not in stripped:
                translated_line = translate_subtitle(stripped, source_lang, target_lang)
                translated.append(translated_line + "\n")
            else:
                translated.append(line)

        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(translated)

        logger.info(f"Translated subtitle: {input_path} -> {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to translate subtitle file: {e}")
        return False
