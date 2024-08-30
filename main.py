# Author: ZK-Jackie
# Time: 2024/08/09
# Title: CampusQA
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

from api.chat import api_chat
from auth import verify_host, verify_token
import uvicorn

app = FastAPI(dependencies=[Depends(verify_host), Depends(verify_token)])

app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
)

@app.middleware("http")
async def intercept_all_requests(request: Request, call_next):
    # 在这里处理所有请求
    try:
        verify_host(request)
        verify_token(request, request.headers.get("Token"))
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    response = await call_next(request)
    return response

app.include_router(api_chat)
app.mount("/static", StaticFiles(directory="static"), name="static")



if __name__ == "__main__":
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=54823,
                reload=True)
