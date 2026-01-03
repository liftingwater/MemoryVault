from typing import Literal, Optional
from enum import Enum


class ContentType(str, Enum):
    """Enum for content types"""
    TEXT = "text"
    IMAGE = "image"


class CardContent:
    """Represents the content of one side of a flashcard (front or back)"""
    
    def __init__(
        self,
        content_type: ContentType,
        value: str,
        alt_text: Optional[str] = None
    ):
        """
        Initialize card content.
        
        Args:
            content_type: Type of content (text or image)
            value: The actual content (text string or image URL/path)
            alt_text: Alternative text for images (for accessibility)
        """
        self.content_type = content_type
        self.value = value
        self.alt_text = alt_text
    
    def to_dict(self) -> dict:
        """Convert content to dictionary representation"""
        result = {
            'type': self.content_type.value,
            'value': self.value
        }
        if self.alt_text:
            result['alt_text'] = self.alt_text
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CardContent':
        """Create CardContent instance from dictionary"""
        return cls(
            content_type=ContentType(data['type']),
            value=data['value'],
            alt_text=data.get('alt_text')
        )
    
    @classmethod
    def text(cls, text: str) -> 'CardContent':
        """Create text content"""
        return cls(ContentType.TEXT, text)
    
    @classmethod
    def image(cls, image_url: str, alt_text: Optional[str] = None) -> 'CardContent':
        """Create image content"""
        return cls(ContentType.IMAGE, image_url, alt_text)
    
    def is_text(self) -> bool:
        """Check if content is text"""
        return self.content_type == ContentType.TEXT
    
    def is_image(self) -> bool:
        """Check if content is an image"""
        return self.content_type == ContentType.IMAGE
    
    def __repr__(self) -> str:
        if self.is_text():
            preview = self.value[:30] + '...' if len(self.value) > 30 else self.value
            return f"CardContent(type=TEXT, value='{preview}')"
        else:
            return f"CardContent(type=IMAGE, url='{self.value}')"

