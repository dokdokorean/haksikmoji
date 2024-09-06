from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes.__init__ import router
from server.scheduler.update_store_status_scheduler import start_scheduler
import threading

from datetime import datetime, time
import pytz

def get_skt_time():
  kst = pytz.timezone('Asia/Seoul')
  return datetime.now(kst)


app = FastAPI(
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

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서의 요청 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

app.include_router(router, prefix="/api")

@app.on_event('startup')
def start_background_scheduler():
  print(f"매장 상태 스케쥴러 실행 {get_skt_time().now().time()}")
  scheduler_thread = threading.Thread(target=start_scheduler)
  scheduler_thread.daemon = True
  scheduler_thread.start()
  
if __name__ == '__main__':
  start_background_scheduler()
  
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)