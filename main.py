import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Set

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from auth import hash_password, verify_password
from database import Base, SessionLocal, engine, get_db
from models import Advice, CheckIn, Progress, Resource, User
from schemas import (
    AdviceRequest,
    CheckInRequest,
    LoginRequest,
    SignupRequest,
    StatusUpdateRequest,
)

BASE_DIR = Path(__file__).resolve().parent

ALLOWED_ROLES = {
    "child",
    "parent",
    "teacher",
    "counsellor",
}


def seed_database(database: Session) -> None:
    demo_users = [
        ("Demo Child", "child@mindbridge.test", "child"),
        ("Demo Parent", "parent@mindbridge.test", "parent"),
        ("Demo Teacher", "teacher@mindbridge.test", "teacher"),
        ("Demo Counsellor", "counsellor@mindbridge.test", "counsellor"),
    ]

    for full_name, email, role in demo_users:
        existing_user = (
            database.query(User)
            .filter(User.email == email)
            .first()
        )

        if not existing_user:
            database.add(
                User(
                    full_name=full_name,
                    email=email,
                    password_hash=hash_password("1234"),
                    role=role,
                    is_active=True,
                )
            )

    if database.query(Resource).count() == 0:
        database.add_all(
            [
                Resource(
                    title="Understanding Emotions",
                    description=(
                        "Watch a short video about recognising and "
                        "expressing emotions."
                    ),
                    resource_type="video",
                    file_url="/static/videos/viiii.mp4",
                ),
                Resource(
                    title="My Feelings Booklet",
                    description=(
                        "Read a child-friendly booklet about feelings "
                        "and asking for help."
                    ),
                    resource_type="booklet",
                    file_url="/static/booklets/emotions-booklet.pdf",
                ),
            ]
        )

    database.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as database:
        seed_database(database)

    yield


app = FastAPI(
    title="MindBridge",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SECRET_KEY",
        "change-this-local-development-secret",
    ),
    same_site="lax",
    https_only=False,
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


def role_page(role: str) -> str:
    if role == "child":
        return "/home"

    if role in {"parent", "teacher"}:
        return "/monitor-dashboard"

    if role == "counsellor":
        return "/counsellor-dashboard"

    return "/"


def session_user(
    request: Request,
    database: Session,
):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    user = database.get(User, user_id)

    if not user or not user.is_active:
        request.session.clear()
        return None

    return user


def current_user(
    request: Request,
    database: Session = Depends(get_db),
):
    user = session_user(request, database)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please log in.",
        )

    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to use this page.",
            )

        return user

    return checker


def html_page(
    request: Request,
    database: Session,
    template_name: str,
    roles: Optional[Set[str]] = None,
):
    user = session_user(request, database)

    if not user:
        return RedirectResponse(
            url="/",
            status_code=303,
        )

    if roles and user.role not in roles:
        return RedirectResponse(
            url=role_page(user.role),
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={},
    )


@app.get("/", response_class=HTMLResponse)
def login_page(
    request: Request,
    database: Session = Depends(get_db),
):
    user = session_user(request, database)

    if user:
        return RedirectResponse(
            url=role_page(user.role),
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="signup.html",
        context={},
    )


@app.get("/home", response_class=HTMLResponse)
def child_page(
    request: Request,
    database: Session = Depends(get_db),
):
    return html_page(
        request,
        database,
        "home.html",
        {"child"},
    )


@app.get("/monitor-dashboard", response_class=HTMLResponse)
def monitor_page(
    request: Request,
    database: Session = Depends(get_db),
):
    return html_page(
        request,
        database,
        "monitor-dashboard.html",
        {"parent", "teacher"},
    )


@app.get("/counsellor-dashboard", response_class=HTMLResponse)
def counsellor_page(
    request: Request,
    database: Session = Depends(get_db),
):
    return html_page(
        request,
        database,
        "counsellor-dashboard.html",
        {"counsellor"},
    )


@app.post("/api/signup")
def signup(
    data: SignupRequest,
    database: Session = Depends(get_db),
):
    email = data.email.lower()

    existing_user = (
        database.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    if data.role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Invalid role.",
        )

    user = User(
        full_name=data.full_name.strip(),
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
    )

    database.add(user)
    database.commit()

    return {
        "message": "Account created successfully.",
    }


@app.post("/api/login")
def login(
    data: LoginRequest,
    request: Request,
    database: Session = Depends(get_db),
):
    email = data.email.lower()

    user = (
        database.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="This account is inactive.",
        )

    request.session.clear()
    request.session["user_id"] = user.id

    return {
        "message": "Login successful.",
        "redirect": role_page(user.role),
    }


@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()

    return {
        "message": "Logged out.",
    }


@app.get("/api/child/dashboard")
def child_dashboard(
    user: User = Depends(require_roles("child")),
    database: Session = Depends(get_db),
):
    resources = (
        database.query(Resource)
        .order_by(Resource.id)
        .all()
    )

    completed_records = (
        database.query(Progress)
        .filter(Progress.child_id == user.id)
        .all()
    )

    completed_resource_ids = {
        record.resource_id
        for record in completed_records
    }

    latest_check_in = (
        database.query(CheckIn)
        .filter(CheckIn.child_id == user.id)
        .order_by(CheckIn.created_at.desc())
        .first()
    )

    advice_records = (
        database.query(Advice)
        .filter(Advice.child_id == user.id)
        .order_by(Advice.created_at.desc())
        .limit(10)
        .all()
    )

    advice = []

    for record in advice_records:
        counsellor = database.get(
            User,
            record.counsellor_id,
        )

        advice.append(
            {
                "message": record.message,
                "counsellor": (
                    counsellor.full_name
                    if counsellor
                    else "Counsellor"
                ),
                "created_at": record.created_at.isoformat(),
            }
        )

    return {
        "user": {
            "full_name": user.full_name,
            "role": user.role,
        },
        "resources": [
            {
                "id": resource.id,
                "title": resource.title,
                "description": resource.description,
                "resource_type": resource.resource_type,
                "file_url": resource.file_url,
                "completed": (
                    resource.id in completed_resource_ids
                ),
            }
            for resource in resources
        ],
        "completed_count": len(completed_resource_ids),
        "total_resources": len(resources),
        "latest_check_in": (
            {
                "feeling": latest_check_in.feeling,
                "reason": latest_check_in.reason,
                "support_requested": (
                    latest_check_in.support_requested
                ),
                "created_at": (
                    latest_check_in.created_at.isoformat()
                ),
            }
            if latest_check_in
            else None
        ),
        "advice": advice,
    }


@app.post("/api/progress/{resource_id}")
def complete_resource(
    resource_id: int,
    user: User = Depends(require_roles("child")),
    database: Session = Depends(get_db),
):
    resource = database.get(Resource, resource_id)

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Resource not found.",
        )

    existing_progress = (
        database.query(Progress)
        .filter(
            Progress.child_id == user.id,
            Progress.resource_id == resource_id,
        )
        .first()
    )

    if not existing_progress:
        database.add(
            Progress(
                child_id=user.id,
                resource_id=resource_id,
                status="Completed",
            )
        )
        database.commit()

    return {
        "message": "Resource completed.",
    }


@app.post("/api/check-ins")
def create_check_in(
    data: CheckInRequest,
    user: User = Depends(require_roles("child")),
    database: Session = Depends(get_db),
):
    database.add(
        CheckIn(
            child_id=user.id,
            feeling=data.feeling.strip(),
            reason=data.reason.strip(),
            support_requested=data.support_requested,
        )
    )

    database.commit()

    return {
        "message": "Check-in saved.",
    }


@app.get("/api/monitor/children")
def monitor_children(
    user: User = Depends(
        require_roles("parent", "teacher")
    ),
    database: Session = Depends(get_db),
):
    children = (
        database.query(User)
        .filter(User.role == "child")
        .order_by(User.full_name)
        .all()
    )

    total_resources = database.query(Resource).count()
    result = []

    for child in children:
        completed_count = (
            database.query(Progress)
            .filter(Progress.child_id == child.id)
            .count()
        )

        latest_check_in = (
            database.query(CheckIn)
            .filter(CheckIn.child_id == child.id)
            .order_by(CheckIn.created_at.desc())
            .first()
        )

        result.append(
            {
                "id": child.id,
                "full_name": child.full_name,
                "email": child.email,
                "completed_count": completed_count,
                "total_resources": total_resources,
                "latest_feeling": (
                    latest_check_in.feeling
                    if latest_check_in
                    else "No check-in"
                ),
                "support_requested": (
                    latest_check_in.support_requested
                    if latest_check_in
                    else False
                ),
                "is_active": child.is_active,
            }
        )

    return {
        "viewer": user.full_name,
        "children": result,
    }


@app.patch("/api/monitor/children/{child_id}/status")
def update_child_status(
    child_id: int,
    data: StatusUpdateRequest,
    user: User = Depends(
        require_roles("parent", "teacher")
    ),
    database: Session = Depends(get_db),
):
    child = database.get(User, child_id)

    if not child or child.role != "child":
        raise HTTPException(
            status_code=404,
            detail="Child not found.",
        )

    child.is_active = data.is_active
    database.commit()

    return {
        "message": "Account status updated.",
        "is_active": child.is_active,
    }


@app.get("/api/counsellor/children")
def counsellor_children(
    user: User = Depends(
        require_roles("counsellor")
    ),
    database: Session = Depends(get_db),
):
    children = (
        database.query(User)
        .filter(User.role == "child")
        .order_by(User.full_name)
        .all()
    )

    result = []

    for child in children:
        latest_check_in = (
            database.query(CheckIn)
            .filter(CheckIn.child_id == child.id)
            .order_by(CheckIn.created_at.desc())
            .first()
        )

        result.append(
            {
                "id": child.id,
                "full_name": child.full_name,
                "latest_feeling": (
                    latest_check_in.feeling
                    if latest_check_in
                    else "No check-in"
                ),
                "reason": (
                    latest_check_in.reason
                    if latest_check_in
                    else "No check-in submitted."
                ),
                "support_requested": (
                    latest_check_in.support_requested
                    if latest_check_in
                    else False
                ),
            }
        )

    return {
        "viewer": user.full_name,
        "children": result,
    }


@app.post("/api/counsellor/advice")
def create_advice(
    data: AdviceRequest,
    counsellor: User = Depends(
        require_roles("counsellor")
    ),
    database: Session = Depends(get_db),
):
    child = database.get(User, data.child_id)

    if not child or child.role != "child":
        raise HTTPException(
            status_code=404,
            detail="Child not found.",
        )

    database.add(
        Advice(
            child_id=child.id,
            counsellor_id=counsellor.id,
            message=data.message.strip(),
        )
    )

    database.commit()

    return {
        "message": "Advice shared successfully.",
    }


@app.exception_handler(HTTPException)
async def http_error_handler(
    request: Request,
    error: HTTPException,
):
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail},
    )
