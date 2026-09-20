from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
import os

router = APIRouter()

# تنظیم پوشه تمپلیت‌ها (فرض بر این است که فایل‌های HTML در پوشه static هستند)
templates = Jinja2Templates(directory="static")

@router.get("/")
async def read_root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Welcome to Map to 3D API. Visit /docs for documentation."}

@router.get("/project/{project_id}")
async def project_plan_page(request: Request, project_id: int):
    templates = Jinja2Templates(directory="static/plan")
    return templates.TemplateResponse(
        name="index.html", 
        request= request, 
        context={
            "project_id": project_id,
            "project_name":project_id
        }
    )    

@router.get("/project/{project_id}/objects/{object_id}/cost")
async def object_cost_page(project_id: int, object_id: int):
    """
    نمایش صفحه مدیریت هزینه برای یک Object خاص (دیوار، کف یا سقف)
    """
    path = "static/plan/cost/index.html"
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Cost page not found"}

@router.get("/project/{project_id}/report")
async def wall_cost_page(project_id: int):
    # ما پارامترها را در URL نگه می‌داریم تا JS بتواند آن‌ها را بخواند
    # اما چون FileResponse مستقیماً فایل را برمی‌گرداند، باید مطمئن شویم
    # که فایل index.html در پوشه cost وجود دارد.
    path = "static/report/index.html"
    if os.path.exists(path):
        return FileResponse(path)
    return {"error": "Report page not found"}
