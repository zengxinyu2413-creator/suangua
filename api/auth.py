"""
api/auth.py
===========
User authentication and saved charts API.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from models.common import ApiResponse

router = APIRouter(prefix="/user", tags=["用户系统"])

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=30)
    password: str = Field(..., min_length=4, max_length=100)
    display_name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class SaveChartRequest(BaseModel):
    module: str = "bazi"
    title: str = ""
    summary: str = ""
    birth_info: dict = {}
    chart_data: dict = {}
    notes: str = ""
    tags: str = ""

class UpdateNotesRequest(BaseModel):
    notes: str = ""

def _get_user(request: Request):
    """Extract user from X-User-Token header."""
    from core.user_db import get_user_by_token
    token = request.headers.get("X-User-Token", "")
    if not token:
        return None
    return get_user_by_token(token)

def _require_user(request: Request):
    user = _get_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user

# ── Auth endpoints ──

@router.post("/register", summary="注册")
async def user_register(req: RegisterRequest):
    from core.user_db import register
    result = register(req.username, req.password, req.display_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return ApiResponse(success=True, data=result["user"])

@router.post("/login", summary="登录")
async def user_login(req: LoginRequest):
    from core.user_db import login
    result = login(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return ApiResponse(success=True, data=result["user"])

@router.get("/me", summary="当前用户信息")
async def user_me(request: Request):
    user = _require_user(request)
    return ApiResponse(success=True, data=user)

# ── Saved charts endpoints ──

@router.post("/charts", summary="保存命盘")
async def save_user_chart(req: SaveChartRequest, request: Request):
    user = _require_user(request)
    from core.user_db import save_chart
    result = save_chart(user["id"], req.module, req.title, req.summary,
                        req.birth_info, req.chart_data, req.notes, req.tags)
    return ApiResponse(success=True, data=result)

@router.get("/charts", summary="我的命盘列表")
async def list_user_charts(request: Request, module: Optional[str] = None):
    user = _require_user(request)
    from core.user_db import list_charts
    charts = list_charts(user["id"], module)
    return ApiResponse(success=True, data=charts)

@router.get("/charts/{chart_id}", summary="命盘详情")
async def get_user_chart(chart_id: int, request: Request):
    user = _require_user(request)
    from core.user_db import get_chart
    chart = get_chart(user["id"], chart_id)
    if not chart:
        raise HTTPException(status_code=404, detail="命盘不存在")
    return ApiResponse(success=True, data=chart)

@router.put("/charts/{chart_id}/notes", summary="更新断事笔记")
async def update_chart_notes(chart_id: int, req: UpdateNotesRequest, request: Request):
    user = _require_user(request)
    from core.user_db import update_notes
    ok = update_notes(user["id"], chart_id, req.notes)
    if not ok:
        raise HTTPException(status_code=404, detail="命盘不存在")
    return ApiResponse(success=True, data={"updated": True})

@router.delete("/charts/{chart_id}", summary="删除命盘")
async def delete_user_chart(chart_id: int, request: Request):
    user = _require_user(request)
    from core.user_db import delete_chart
    ok = delete_chart(user["id"], chart_id)
    return ApiResponse(success=True, data={"deleted": ok})

# ── Birth info endpoints ──

class BirthInfoRequest(BaseModel):
    year: int = 1990
    month: int = 5
    day: int = 22
    hour: int = 8
    minute: int = 0
    gender: str = "male"
    is_lunar: bool = True
    is_leap_month: bool = False
    province: Optional[str] = None
    city: Optional[str] = None

@router.get("/birth-info", summary="获取保存的生辰信息")
async def get_birth_info(request: Request):
    user = _require_user(request)
    from core.user_db import get_birth_info
    info = get_birth_info(user["id"])
    return ApiResponse(success=True, data=info)

@router.post("/birth-info", summary="保存生辰信息")
async def save_birth_info(req: BirthInfoRequest, request: Request):
    user = _require_user(request)
    from core.user_db import save_birth_info
    ok = save_birth_info(user["id"], req.dict())
    if not ok:
        raise HTTPException(status_code=400, detail="保存失败")
    return ApiResponse(success=True, data=req.dict())
