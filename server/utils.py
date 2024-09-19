import pytz
from datetime import datetime

def get_skt_time():
  kst = pytz.timezone('Asia/Seoul')
  return datetime.now(kst)