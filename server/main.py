from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes.__init__ import router


app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서의 요청 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, 등)
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

app.include_router(router, prefix="/api")

if __name__ == '__main__':
  import uvicorn
  uvicorn.run(app, host="0.0.0.0", port=8080)