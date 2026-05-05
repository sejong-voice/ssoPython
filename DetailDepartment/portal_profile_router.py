import requests
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from DetailDepartment.portal_department_parser import SejongPortalClient

router = APIRouter(prefix="/auth", tags=["Auth"])


class PortalProfileRequest(BaseModel):
    student_id: str
    password: str

class SSOResult(BaseModel):
    success: bool
    is_auth: bool
    code: Optional[Any] = None
    body: Dict[str, Any] = {}

class DetailDepartmentResponse(BaseModel):
    success: bool
    user: Dict[str, Any]    
    sso: Optional[SSOResult] = None


@router.post("/detail-department", response_model=DetailDepartmentResponse, status_code=200)
async def get_detail_department(req: PortalProfileRequest):
    client = SejongPortalClient()

    try:
        client.login(student_id=req.student_id, password=req.password)
        html = client.fetch_main_html()
        info = client.parse_student_affiliation(html)
    except requests.exceptions.SSLError as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "SSL_ERROR", "message": str(e)},
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "UPSTREAM_ERROR", "message": str(e)},
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=401,
            detail={"code": "AUTH_FAILED", "message": str(e)},
        )

    # print(info.major)
    # print(info.student_id)
    detail_department = info.major or info.affiliation_raw
    sid = info.student_id or req.student_id
    user = {
        "id": f"u_{sid}",
        "student_id": sid ,
        "role": "student",
#        "password": req.password,
        "name": info.name,
        "major":  detail_department,         #전공 반환값을 수정하고 싶으면 해당 부분을 조율해주면 됨
    }

    sso_data = SSOResult(
        success=True,
        is_auth=True,
        code="success",
        body={
            "name": info.name,
            "major": detail_department,
        }
    ) 

    

    return DetailDepartmentResponse(success=True, user=user, sso=sso_data)
    # return {
    #     "student_id": info.student_id or req.student_id,
    #     "password": req.password,
    #     "role" : "student",
    #     "name": info.name,
    #     "DetailDepartment": info.major or info.affiliation_raw,#전공 반환값을 수정하고 싶으면 해당 부분을 조율해주면 됨
    # }
