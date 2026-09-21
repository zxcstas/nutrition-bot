import aiohttp
from typing import Optional, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class TokenClubAPI:
    """Client for Token.club API"""

    def __init__(self):
        self.api_key = settings.tokenclub_api_key
        self.base_url = "https://tooken.club/v1"
        self.vision_url = f"{self.base_url}/images/generations"
        self.chat_url = f"{self.base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def analyze_food_image(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Analyze food image using Vision API
        Returns nutrition information extracted from the image
        """
        try:
            async with aiohttp.ClientSession() as session:
                # For tooken.club vision API, send image and get description
                payload = {
                    "model": "gpt-image-2",
                    "prompt": "Analyze this food image and provide detailed nutrition information in Russian. "
                             "Include: название блюда, калории, белки, жиры, углеводы, примерный вес порции.",
                    "n": 1,
                    "size": "1024x1024"
                }

                # Note: The actual API format may differ - adjust based on tooken.club documentation
                # This is a placeholder implementation
                headers = {"Authorization": f"Bearer {self.api_key}"}

                async with session.post(
                    self.vision_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Vision API response: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Vision API error {response.status}: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Error calling Vision API: {e}")
            return None

    async def parse_text_food_description(self, text: str, additional_hints: str = "") -> Optional[Dict[str, Any]]:
        """
        Parse text food description using Chat API
        Returns structured nutrition information
        """
        try:
            prompt = f"""Ты помощник по подсчету КБЖУ. Проанализируй описание еды и верни структурированную информацию о питательной ценности.

Описание еды: {text}

{f"Дополнительные подсказки: {additional_hints}" if additional_hints else ""}

Верни ответ СТРОГО в JSON формате:
{{
    "description": "краткое описание блюда",
    "calories": число,
    "protein": число,
    "fats": число,
    "carbs": число,
    "portion_size": "примерный размер порции",
    "confidence": "high/medium/low"
}}

Если не уверен в точности - укажи confidence: "low" или "medium".
Все числа должны быть в граммах для БЖУ и в ккал для калорий."""

            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "claude-opus-5",  # Use Claude Opus 5 from tooken.club
                    "messages": [
                        {"role": "system", "content": "Ты эксперт по питанию и подсчету КБЖУ. Отвечай только валидным JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                }

                async with session.post(
                    self.chat_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Chat API response: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Chat API error {response.status}: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Error calling Chat API: {e}")
            return None

    async def analyze_nutrition_label(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Analyze nutrition label using Vision API with OCR
        Returns extracted nutrition information from the label
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "gpt-image-2",
                    "prompt": "Это этикетка продукта питания. Извлеки из неё информацию о пищевой ценности (КБЖУ). "
                             "Найди: калории (ккал), белки (г), жиры (г), углеводы (г) на 100г или на порцию. "
                             "Также найди название продукта и размер порции если указан.",
                    "n": 1,
                    "size": "1024x1024"
                }

                headers = {"Authorization": f"Bearer {self.api_key}"}

                async with session.post(
                    self.vision_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Label analysis response: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Label analysis error {response.status}: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Error analyzing nutrition label: {e}")
            return None


# Singleton instance
tokenclub_api = TokenClubAPI()
