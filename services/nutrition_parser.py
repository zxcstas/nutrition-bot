import json
import re
from typing import Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class NutritionInfo:
    """Structured nutrition information"""
    description: str
    calories: float
    protein: float
    fats: float
    carbs: float
    confidence: str = "medium"
    portion_size: Optional[str] = None


class NutritionParser:
    """Parse and normalize nutrition data from various sources"""

    @staticmethod
    def parse_llm_response(response: Dict) -> Optional[NutritionInfo]:
        """Parse LLM API response and extract nutrition info"""
        try:
            # Extract content from response
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
            else:
                logger.error("Invalid LLM response structure")
                return None

            # Try to extract JSON from content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in LLM response")
                return None

            data = json.loads(json_match.group())

            return NutritionInfo(
                description=data.get("description", "Неизвестно"),
                calories=float(data.get("calories", 0)),
                protein=float(data.get("protein", 0)),
                fats=float(data.get("fats", 0)),
                carbs=float(data.get("carbs", 0)),
                confidence=data.get("confidence", "medium"),
                portion_size=data.get("portion_size"),
            )

        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None

    @staticmethod
    def parse_vision_response(response: Dict) -> Optional[NutritionInfo]:
        """Parse Claude Vision API response and extract nutrition info"""
        try:
            # Claude Messages API returns content in specific format
            if "content" in response and len(response["content"]) > 0:
                text = response["content"][0].get("text", "")
            else:
                logger.error("Unknown Claude Vision response format")
                return None

            # Extract JSON from text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in Claude Vision response")
                return None

            data = json.loads(json_match.group())

            return NutritionInfo(
                description=data.get("description", "Неизвестно"),
                calories=float(data.get("calories", 0)),
                protein=float(data.get("protein", 0)),
                fats=float(data.get("fats", 0)),
                carbs=float(data.get("carbs", 0)),
                confidence=data.get("confidence", "medium"),
                portion_size=data.get("portion_size"),
            )

        except Exception as e:
            logger.error(f"Error parsing Claude Vision response: {e}")
            return None

    @staticmethod
    def parse_label_response(response: Dict) -> Optional[NutritionInfo]:
        """Parse nutrition label OCR response"""
        try:
            # Similar to vision parsing but expect more structured data from labels
            if "text" in response:
                text = response["text"]
            elif "description" in response:
                text = response["description"]
            else:
                logger.error("Unknown label response format")
                return None

            # Extract product name
            product_match = re.search(r'(?:название|продукт)[:\s]+(.+?)(?:\n|$)', text, re.IGNORECASE)
            product_name = product_match.group(1).strip() if product_match else "Продукт с этикетки"

            # Extract nutrition values (more precise for labels)
            calories = NutritionParser._extract_number(text, r'энергетическая ценность[:\s]+(\d+\.?\d*)|калорийность[:\s]+(\d+\.?\d*)')
            protein = NutritionParser._extract_number(text, r'белки?[:\s]+(\d+\.?\d*)')
            fats = NutritionParser._extract_number(text, r'жиры?[:\s]+(\d+\.?\d*)')
            carbs = NutritionParser._extract_number(text, r'углеводы?[:\s]+(\d+\.?\d*)')

            if not calories:
                logger.warning("Could not extract nutrition values from label")
                return None

            return NutritionInfo(
                description=product_name,
                calories=calories,
                protein=protein or 0,
                fats=fats or 0,
                carbs=carbs or 0,
                confidence="high",  # Labels are typically more accurate
            )

        except Exception as e:
            logger.error(f"Error parsing label response: {e}")
            return None

    @staticmethod
    def _extract_number(text: str, pattern: str) -> Optional[float]:
        """Extract number using regex pattern"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Find first non-None group
            for group in match.groups():
                if group:
                    try:
                        return float(group.replace(',', '.'))
                    except ValueError:
                        continue
        return None
