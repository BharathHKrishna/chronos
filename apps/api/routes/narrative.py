from fastapi import APIRouter
from pydantic import BaseModel
from apps.api.services.llm import write_narrative

router = APIRouter()


class NarrativeRequest(BaseModel):
    lat: float
    lon: float
    scenario: str = "bau"
    history: dict
    forecast: dict


@router.post("")
async def post_narrative(req: NarrativeRequest):
    """Generate a 4–6 sentence LLM diary entry grounded in the actual numbers."""
    text = await write_narrative(
        lat=req.lat,
        lon=req.lon,
        scenario=req.scenario,
        history=req.history,
        forecast=req.forecast,
    )
    return {"narrative": text}
