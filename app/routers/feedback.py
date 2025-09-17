from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.feedback import Feedback
from app.models.users import User
from app.schemas.feedback import FeedbackCreationRequest

router = APIRouter(
    prefix='/api/feedbacks',
    tags=['feedback']
)


@router.post('')
async def created_feedback(request: FeedbackCreationRequest,
                           user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    feedback = Feedback(content=request.content,
                        user_id=user.id)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback.id
