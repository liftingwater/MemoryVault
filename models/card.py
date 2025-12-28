from datetime import datetime
from typing import Optional


class Card:
    """Represents a flashcard in the Leitner box system"""
    
    def __init__(
        self,
        front: str,
        back: str,
        card_id: Optional[int] = None,
        box: int = 1,
        created_at: Optional[str] = None,
        last_reviewed: Optional[str] = None,
        review_count: int = 0
    ):
        self.id = card_id
        self.front = front
        self.back = back
        self.box = box
        self.created_at = created_at or datetime.now().isoformat()
        self.last_reviewed = last_reviewed
        self.review_count = review_count
    
    def to_dict(self) -> dict:
        """Convert card to dictionary representation"""
        return {
            'id': self.id,
            'front': self.front,
            'back': self.back,
            'box': self.box,
            'created_at': self.created_at,
            'last_reviewed': self.last_reviewed,
            'review_count': self.review_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Card':
        """Create a Card instance from a dictionary"""
        return cls(
            card_id=data.get('id'),
            front=data['front'],
            back=data['back'],
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
    
    def update(self, front: Optional[str] = None, back: Optional[str] = None):
        """Update card content"""
        if front is not None:
            self.front = front
        if back is not None:
            self.back = back
    
    def __repr__(self) -> str:
        return f"Card(id={self.id}, front='{self.front[:20]}...', box={self.box})"

