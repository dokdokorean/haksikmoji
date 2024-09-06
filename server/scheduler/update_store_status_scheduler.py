from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker
from server.db import engine
from server.models import Store
from datetime import datetime
import time
import pytz

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_skt_time():
  kst = pytz.timezone('Asia/Seoul')
  return datetime.now(kst)

def update_store_statuses():
  db_session = SessionLocal()
  try:
    stores = db_session.query(Store).all()
    for store in stores:
      store.update_is_open(db_session)
    db_session.commit()
    print(f"매장 업데이트 {get_skt_time()}")
  except Exception as e:
    db_session.rollback()
    print(f"업데이트 중 오류 발생 - {get_skt_time} : {e}")
  finally:
    db_session.close()

def start_scheduler():
  scheduler = BackgroundScheduler()
  
  # 10분 마다 update_store_statuses 함수 호출
  scheduler.add_job(update_store_statuses, 'cron', minute='1,11,21,31,41,51')
  
  scheduler.start()
  
  # 스케쥴려가 백그라운드에서 계속 반복 실행될 수 있도록 유지하기 위한 코드
  try:
    # 루프가 1분 동안 멈춘 후 다시 돌아가면서 스케쥴러의 작업을 계속 유지
    # 1분 간격으로 스케쥴러가 잘 동작하고 있는지 확인하며, 백그라운드에서 다른 일이 없을 때는 CPU를 낭비하지 않도록 휴식시간(sleep)
    while True:
      time.sleep(60)
  except (KeyboardInterrupt, SystemExit):
    # 스케쥴러가 실행 중일 때 예외가 발생하면 안전하게 종료하기 위한 shutdown메서드 호출
    scheduler.shutdown()