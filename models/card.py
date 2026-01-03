from datetime import datetime
from typing import Optional, Union
from .content import CardContent, ContentType


class Card:
    """Represents a flashcard in the Leitner box system"""

    def __init__(
        self,
        front: Union[str, CardContent],
        back: Union[str, CardContent],
        card_id: Optional[int] = None,
        box: int = 1,
        created_at: Optional[str] = None,
        last_reviewed: Optional[str] = None,
        review_count: int = 0
    ):
        self.id = card_id
        # Convert strings to CardContent objects for backward compatibility
        self.front = front if isinstance(front, CardContent) else CardContent.text(front)
        self.back = back if isinstance(back, CardContent) else CardContent.text(back)
        self.box = box
        self.created_at = created_at or datetime.now().isoformat()
        self.last_reviewed = last_reviewed
        self.review_count = review_count
    
    def to_dict(self) -> dict:
        """Convert card to dictionary representation"""
        return {
            'id': self.id,
            'front': self.front.to_dict(),
            'back': self.back.to_dict(),
            'box': self.box,
            'created_at': self.created_at,
            'last_reviewed': self.last_reviewed,
            'review_count': self.review_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Card':
        """Create a Card instance from a dictionary"""
        # Handle both old format (string) and new format (dict with type)
        front_data = data['front']
        back_data = data['back']

        front = CardContent.from_dict(front_data) if isinstance(front_data, dict) else CardContent.text(front_data)
        back = CardContent.from_dict(back_data) if isinstance(back_data, dict) else CardContent.text(back_data)

        return cls(
            card_id=data.get('id'),
            front=front,
            back=back,
            box=data.get('box', 1),
            created_at=data.get('created_at'),
            last_reviewed=data.get('last_reviewed'),
            review_count=data.get('review_count', 0)
        )
    
    def review(self, correct: bool) -> int:
        """
        Review the card and update its box position.
        
        Args:
            correct: Whether the user answered correctly
            
        Returns:
            The new box number
        """
        old_box = self.box
        
        if correct:
            # Move to next box (max box 5)
            self.box = min(self.box + 1, 5)
        else:
            # Move back to box 1
            self.box = 1
        
        self.last_reviewed = datetime.now().isoformat()
        self.review_count += 1
        
        return self.box
    
    def update(
        self,
        front: Optional[Union[str, CardContent]] = None,
        back: Optional[Union[str, CardContent]] = None
    ):
        """Update card content"""
        if front is not None:
            self.front = front if isinstance(front, CardContent) else CardContent.text(front)
        if back is not None:
            self.back = back if isinstance(back, CardContent) else CardContent.text(back)
    
    def __repr__(self) -> str:
        front_preview = str(self.front)[:40] + '...' if len(str(self.front)) > 40 else str(self.front)
        return f"Card(id={self.id}, front={front_preview}, box={self.box})"

