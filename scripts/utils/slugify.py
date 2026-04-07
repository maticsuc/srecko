"""
Slug generation utilities for categories and tags.
"""

import re
from typing import Dict
from unidecode import unidecode


# Slovenian character mappings
SLOVENIAN_CHAR_MAP = {
    'č': 'c',
    'ć': 'c',
    'š': 's',
    'ž': 'z',
    'đ': 'd',
    'Č': 'c',
    'Ć': 'c',
    'Š': 's',
    'Ž': 'z',
    'Đ': 'd',
}


def slugify(text: str, separator: str = '_') -> str:
    """
    Convert text to URL-friendly slug.
    
    Handles Slovenian characters and converts to lowercase with separators.
    
    Args:
        text: Input text to slugify
        separator: Character to use between words (default: underscore)
        
    Returns:
        Slugified text
        
    Examples:
        >>> slugify("Avantgardistična poezija")
        'avantgardisticna_poezija'
        >>> slugify("Članki in eseji")
        'clanki_in_eseji'
        >>> slugify("Pesmi v prozi", separator='-')
        'pesmi-v-prozi'
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace Slovenian characters
    for char, replacement in SLOVENIAN_CHAR_MAP.items():
        text = text.replace(char.lower(), replacement)
    
    # Use unidecode for any remaining special characters
    text = unidecode(text)
    
    # Replace spaces and special characters with separator
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', separator, text)
    
    # Remove leading/trailing separators
    text = text.strip(separator)
    
    return text


def generate_category_slugs(categories: list) -> Dict[str, str]:
    """
    Generate slugs for a list of category names.
    
    Args:
        categories: List of category names
        
    Returns:
        Dictionary mapping original names to slugs
    """
    return {name: slugify(name) for name in categories}


def generate_tag_slug(tag: str) -> str:
    """
    Generate slug for a tag.
    
    Args:
        tag: Tag name
        
    Returns:
        Slugified tag
    """
    return slugify(tag, separator='-')


# Predefined category slugs (based on kosovel_data_cleaned.json structure)
CATEGORY_SLUGS = {
    "lirika": "lirika",
    "avantgardisticna_poezija": "avantgardisticna_poezija",
    "pesmi_v_prozi": "pesmi_v_prozi",
    "clanki": "clanki",
    "eseji_o_umetnosti": "eseji_o_umetnosti",
    "literarne_kritike": "literarne_kritike",
    "crtice": "crtice",
    "precevanja": "precevanja",
}


def get_category_display_name(slug: str) -> str:
    """
    Convert category slug back to display name.
    
    Args:
        slug: Category slug
        
    Returns:
        Human-readable display name
    """
    display_names = {
        "lirika": "Lirika",
        "avantgardisticna_poezija": "Avantgardistična poezija",
        "pesmi_v_prozi": "Pesmi v prozi",
        "clanki": "Članki",
        "eseji_o_umetnosti": "Eseji o umetnosti",
        "literarne_kritike": "Literarne kritike",
        "crtice": "Črtice",
        "precevanja": "Prečevanja",
    }
    
    return display_names.get(slug, slug.replace('_', ' ').title())


if __name__ == "__main__":
    """Test slug generation."""
    
    print("Testing slug generation...")
    print()
    
    # Test cases
    test_cases = [
        "Avantgardistična poezija",
        "Pesmi v prozi",
        "Članki",
        "Eseji o umetnosti",
        "Literarne kritike",
        "Črtice",
        "Prečevanja",
        "Kras in burja",
        "Življenje in smrt",
    ]
    
    print("Category slugs:")
    for text in test_cases:
        slug = slugify(text)
        print(f"  {text:30} → {slug}")
    
    print()
    print("Tag slugs (with hyphens):")
    for text in test_cases:
        slug = generate_tag_slug(text)
        print(f"  {text:30} → {slug}")
    
    print()
    print("Reverse lookup:")
    for slug in CATEGORY_SLUGS.values():
        display = get_category_display_name(slug)
        print(f"  {slug:30} → {display}")
