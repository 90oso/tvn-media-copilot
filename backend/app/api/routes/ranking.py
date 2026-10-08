from fastapi import APIRouter
from app.schemas.api import AttentionScoreRequest
from app.services.ranking import AttentionComponents
router=APIRouter(prefix='/ranking',tags=['ranking'])
@router.post('/score')
def score(b:AttentionScoreRequest):
    c=AttentionComponents(b.relevance,b.impact,b.urgency,b.novelty,b.evidence)
    return {'score':c.total,'band':c.band,'formula':'P = 30R + 25I + 20U + 15N + 10E','warning':'El puntaje de atención no representa verdad, pérdida ni habilitación de publicación.'}
