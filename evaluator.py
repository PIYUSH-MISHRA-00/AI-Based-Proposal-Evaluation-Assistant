import json
import re
import fitz  # PyMuPDF
import logging
from typing import Dict, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_weights(path: str = "weights_config.json") -> Dict[str, float]:
    """Load scoring weights from JSON file."""
    try:
        with open(path, "r") as f:
            weights = json.load(f)
        return weights
    except Exception as e:
        logger.error(f"Failed to load weights config: {e}")
        # Return default weights if file missing or error
        return {"cost": 0.3, "technical_merit": 0.4, "past_performance": 0.3}

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return ""

def extract_sections(text: str) -> Dict[str, str]:
    """
    Extract Cost, Technical Approach, and Past Performance sections from text.
    Uses regex to find sections by headings.
    """
    sections = {"cost": "", "technical_merit": "", "past_performance": ""}
    # Regex patterns for sections - case insensitive, allow some flexibility
    patterns = {
        "cost": r"(?:Cost|Pricing|Budget)[\s\S]*?(?=(?:Technical Approach|Past Performance|$))",
        "technical_merit": r"(?:Technical Approach|Technical Proposal|Approach)[\s\S]*?(?=(?:Cost|Past Performance|$))",
        "past_performance": r"(?:Past Performance|Experience|References)[\s\S]*?(?=(?:Cost|Technical Approach|$))",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            sections[key] = match.group(0).strip()
    return sections

def score_cost_section(cost_text: str, all_costs: list = None) -> float:
    """
    Extract numeric cost from cost_text and return a normalized score (lower cost = higher score).
    If no cost found, return 0.
    If all_costs provided, normalize cost relative to all costs.
    """
    # Extract all numbers that look like costs (e.g., $12345, 12345)
    numbers = re.findall(r"\$?([\d,]+(?:\.\d+)?)", cost_text.replace(",", ""))
    costs = []
    for num in numbers:
        try:
            costs.append(float(num))
        except ValueError:
            continue
    if not costs:
        return 0.0
    cost_value = min(costs)  # Use minimum cost found in text
    if all_costs and len(all_costs) > 1:
        min_cost = min(all_costs)
        max_cost = max(all_costs)
        if max_cost == min_cost:
            return 100.0
        # Normalize: lower cost -> higher score
        score = 100 * (max_cost - cost_value) / (max_cost - min_cost)
        return score
    else:
        # Without normalization, return 100 for lowest cost found
        return 100.0

def heuristic_score_section(text: str) -> float:
    """
    Simple heuristic scoring based on word count and keyword density.
    Returns a score between 0 and 100.
    """
    if not text:
        return 0.0
    word_count = len(text.split())
    # Simple keyword density for demonstration
    keywords = ["experience", "quality", "performance", "reliable", "efficient"]
    keyword_count = sum(text.lower().count(k) for k in keywords)
    # Score formula: weighted sum of normalized word count and keyword density
    score = min(100.0, word_count * 0.5 + keyword_count * 10)
    return score

def score_sections(sections: Dict[str, str], weights: Dict[str, float]) -> Dict[str, float]:
    """
    Score each section using heuristics and calculate weighted final score.
    Returns dict with individual scores and final score.
    """
    cost_score = score_cost_section(sections.get("cost", ""))
    tech_score = heuristic_score_section(sections.get("technical_merit", ""))
    past_score = heuristic_score_section(sections.get("past_performance", ""))
    final_score = (
        cost_score * weights.get("cost", 0) +
        tech_score * weights.get("technical_merit", 0) +
        past_score * weights.get("past_performance", 0)
    )
    return {
        "cost_score": cost_score,
        "technical_merit_score": tech_score,
        "past_performance_score": past_score,
        "final_score": final_score
    }

def score_with_gemini(text: str, category: str, api_key: str) -> Optional[float]:
    """
    Use Google Gemini API to score a text section.
    Returns a numeric score (0-100) or None on failure.
    """
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": api_key
        }
        prompt_text = f"Rate the following {category.upper()} section (0–100). Respond with only a number.\n\n{text}"
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt_text
                        }
                    ]
                }
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_json = response.json()
        # Extract the text response
        content = ""
        try:
            content = response_json["candidates"][0]["content"].strip()
        except (KeyError, IndexError):
            logger.error("Unexpected Gemini API response format.")
            return None
        score_match = re.findall(r"\d+\.?\d*", content)
        if not score_match:
            logger.error("No numeric score found in Gemini response.")
            return None
        score = float(score_match[0])
        if 0 <= score <= 100:
            return score
        else:
            logger.warning(f"Gemini returned out-of-range score: {score}")
            return None
    except Exception as e:
        logger.error(f"Gemini scoring error: {e}")
        return None

def score_sections_with_optional_gemini(sections: Dict[str, str], weights: Dict[str, float], api_key: Optional[str] = None) -> Dict[str, float]:
    """
    Score sections using Gemini if api_key provided, else heuristics.
    Cost always scored heuristically.
    """
    cost_score = score_cost_section(sections.get("cost", ""))
    if api_key:
        tech_score = score_with_gemini(sections.get("technical_merit", ""), "TECHNICAL APPROACH", api_key)
        past_score = score_with_gemini(sections.get("past_performance", ""), "PAST PERFORMANCE", api_key)
        # Fallback to heuristic if Gemini fails
        if tech_score is None:
            tech_score = heuristic_score_section(sections.get("technical_merit", ""))
        if past_score is None:
            past_score = heuristic_score_section(sections.get("past_performance", ""))
    else:
        tech_score = heuristic_score_section(sections.get("technical_merit", ""))
        past_score = heuristic_score_section(sections.get("past_performance", ""))
    final_score = (
        cost_score * weights.get("cost", 0) +
        tech_score * weights.get("technical_merit", 0) +
        past_score * weights.get("past_performance", 0)
    )
    return {
        "cost_score": cost_score,
        "technical_merit_score": tech_score,
        "past_performance_score": past_score,
        "final_score": final_score
    }
