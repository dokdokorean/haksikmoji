import uvicorn
from typing import Annotated
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from server.routes.__init__ import router
from server.scheduler.update_store_status_scheduler import start_scheduler
from dotenv import load_dotenv
import threading
import os
from server.util.custom_exception import CustomHTTPException

from datetime import datetime, time
import pytz

load_dotenv()

SWAGGER_USERNAME = os.getenv('SWAGGER_USERNAME')
SWAGGER_PASSWORD = os.getenv('SWAGGER_PASSWORD')


# TODO : 시간대가 한국과 일부 차이가 존재.. 수정해야함
def get_skt_time():
  kst = pytz.timezone('Asia/Seoul')
  return datetime.now(kst)

app = FastAPI(
  docs_url=None, 
  redoc_url=None,
  openapi_url=None,
  openapi_tags=[
    {
      "name": "학식 API",
      "description": ""
    },
    {
      "name": "로그인/회원가입 API",
      "description": ""
    },
    {
      "name" : "매장 API",
      "description" : ""
    }
  ]
)

security = HTTPBasic()

def authenticate_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
  if (
    credentials.username != SWAGGER_USERNAME
    or credentials.password != SWAGGER_PASSWORD
  ):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Incorrect Credentials",
      headers={"WWW-Authenticate_user": "Basic"},
    )

@app.get("/docs", include_in_schema=False)
async def get_docs(credentials: Annotated[HTTPBasicCredentials, Depends(authenticate_user)],):
  return get_swagger_ui_html(openapi_url="/openapi.json", title="Swagger UI")

@app.get("/redoc", include_in_schema=False)
async def get_redocs(credentials: Annotated[HTTPBasicCredentials, Depends(authenticate_user)],):
  return get_redoc_html(openapi_url="/openapi.json", title="ReDoc")

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(credentials: Annotated[HTTPBasicCredentials, Depends(authenticate_user)],):
  return get_openapi(
      title="FastAPI with Private Swagger",
      version="0.1.0",
      routes=app.routes,
  )

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서의 요청 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

app.mount("/images", StaticFiles(directory="server/images", html=True), name="images")
app.mount("/static", StaticFiles(directory="server/static", html=True), name="static")

app.include_router(router, prefix="/api")

@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
  return JSONResponse(
    status_code=exc.status_code,
    content={
      "status": exc.status_code,
      "isSuccess": False,
      "message": exc.message,
      "result": None
    }
  )

@app.on_event('startup')
def start_background_scheduler():
  print(f"매장 상태 스케쥴러 실행 {get_skt_time().now().time()}")
  scheduler_thread = threading.Thread(target=start_scheduler)
  scheduler_thread.daemon = True
  scheduler_thread.start()
  
if __name__ == '__main__':
  start_background_scheduler()
  
  uvicorn.run(app, host="0.0.0.0", port=8080, reload=True, proxy_headers=True)