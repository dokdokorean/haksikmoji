import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경변수 가져오기
KAKAO_ACCESS_TOKEN = os.getenv('KAKAO_ACCESS_TOKEN')
YONSEI_AUTH_URL = os.getenv('YONSEI_AUTH_URL')

INFO_BANK_URL = os.getenv('INFO_BANK_URL')
INFO_BANK_TEMPLATE_CODE = os.getenv('INFO_BANK_TEMPLATE_CODE')
INFO_BANK_SENDER_KEY = os.getenv('INFO_BANK_SENDER_KEY')

INFO_BANK_IB_ID = os.getenv('INFO_BANK_IB_ID')
INFO_BANK_IB_PW = os.getenv('INFO_BANK_IB_PW')

UNIVCERT_API_KEY = os.getenv('UNIVCERT_API_KEY')

UNIVCERT_URL = os.getenv('UNIVCERT_URL')