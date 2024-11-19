from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
# from server.db import get_haksik_db_connection
from server.db import get_db
# from server.models import Cafeteria


haksik_router = APIRouter(
  prefix="/v1/haksik"
)


@haksik_router.get('')
async def get_haksik(db: Session = Depends(get_db)):
  # haksikEnt = db.query(Cafeteria).all()
  # for cafeteria in haksikEnt:
  #   print(cafeteria.id)
  #   print(cafeteria.name)
  #   print(cafeteria.school_id)
  
  haksikData = {
    1: {
      'menu' : {
        'breakfast' : {
          'MON': ['야채짬뽕국', '백미밥', '꿔바로우(5p)', '감자콘샐러드', '배추김치', '셀프계란후라이'],
          'TUE': ['건새우아욱된장국', '백미밥', '칼집비엔나메알어묵볶음', '참치마카로니샐러드', '배추김치/요구르트', '셀프계란후라이'],
          'WED': ['무채국', '카레라이스', '멘치까스(1p) & 칠리소스(셀프)', '숙주맛살냉채', '배추김치', '셀프계란후라이'],
          'THU': ['미역미소국', '백미밥', '돈육김치볶음&연두부', '씨앗멸치볶음', '배추김치', '셀프계란후라이'],
          'FRI': ['된장찌개', '백미밥', '갈릭너비아니무침(3p)', '들깨무나물', '배추김치/떠먹는요거트', '셀프계란후라이']
        },
        'lunch' : {
          'MON' : ['비지찌개', '돼지김치찌개', '참치마요덮밥', '규동', '해물짜장면', '', ''],
          'TUE' : ['콩나물황태해장국', '닭개장', '스팸김치덮밥', '시오야끼덮밥', '샤브야채국수&비빔야채만두', '', ''],
          'WED' : ['소고기미역국', '애호박고추장찌개', '돈까스김치나베', '비프하이라이스&함박', '날치알볶음밥&후라이', '', ''],
          'THU' : ['소고기무국', '햄치즈순두부찌개', '오야꼬동', '깻잎제육덮밥', '튀김우동', '', ''],
          'FRI': ['도시락 및 상차림 예약으로 인한 일반식 운영X', '', '', '', '', '', ''],
        }
      }
    },
    2: {
      'menu' : {
        'breakfast': {
          'MON' : ['', '', '', '', '', ''],
          'TUE' : ['', '', '', '', '', ''],
          'WED' : ['', '', '', '', '', ''],
          'THU' : ['', '', '', '', '', ''],
          'FRI': ['', '', '', '', '', ''],
        },
        'lunch' : {
          'MON' : ['BNC백반(점심)', '사골우거지해장국', '청국장찌개', '소불고기덮밥', '가츠동', '마제소바', '제육덮밥'],
          'TUE' : ['BNC백반(점심)', '비지찌개', '소고기무국', '고추참치마요덮밥', '후랑크갈릭볶음밥', '낙불새덮밥 *(낙지, 불고기, 새우)', '닭개장'],
          'WED' : ['BNC백반(점심)', '돼지고기김치찌개', '우삼겹된장찌개', '', '', '소고기유부볶음밥', ''],
          'THU' : ['BNC백반(점심)', '짬뽕', '해물우동', '돼지순두부찌개', '일식카레*가라아게', '갈비찜', ''],
          'FRI': ['BNC백반(점심)', '진우덮밥', '오꼬노미야끼+미니소바', '사케동', '명란마요덮밥', '', ''],
        }
      }
    }
  }
  # connection = get_haksik_db_connection()
  # try:
  #   with connection.cursor() as cursor:
  #     haksikData = {'menu': {}}
  #     weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI']
  #     cafeteria_id = 1

  #     for day in weekdays:
  #       sql = """
  #       SELECT cm.name
  #       FROM cafeteriaMenu cm
  #       JOIN cafeteriaMiddle cmid ON cm.id = cmid.menu_id
  #       JOIN dayOfWeek dow ON cmid.day_id = dow.id
  #       WHERE cmid.cafeteria_id = %s AND dow.name = %s;
  #       """
  #       cursor.execute(sql, (cafeteria_id, day))
  #       dayData = [row['name'] for row in cursor.fetchall()]
  #       haksikData['menu'][day] = dayData
  return JSONResponse(status_code=200, content={'success' : True, 'body' : haksikData})
  # finally:
  #   connection.close()
