from fastapi import APIRouter

router = APIRouter(tags=["Coming Soon"])

COMING_SOON = {"message": "🚧 This feature is coming soon!", "status": "planned", "phase": 2}


@router.get("/courses")
def courses():
    return COMING_SOON


@router.get("/courses/{course_id}")
def course_detail(course_id: str):
    return COMING_SOON


@router.get("/materials")
def materials():
    return COMING_SOON


@router.get("/recommendations")
def recommendations():
    return COMING_SOON


@router.get("/webcam-emotions")
def webcam_full():
    return {"message": "Basic webcam emotion logging is active. Advanced webcam features coming in Phase 3.", "status": "partial"}
