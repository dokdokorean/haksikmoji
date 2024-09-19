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
          'MON': ['카페테리아 현(아침)', '된장찌개', '돈가스카레', '새우볶음밥', '치킨마요', '비빔국수'],
          'TUE': ['카페테리아 현(아침)', '순두부찌개', '닭갈비덮밥', '해물파전', '돼지불고기', '닭고기커리'],
          'WED': ['카페테리아 현(아침)', '갈비탕', '콩나물국밥', '치즈돈가스', '김치라면', '제육쌈밥'],
          'THU': ['카페테리아 현(아침)', '냉모밀', '미트볼스파게티', '불닭볶음면', '', '차돌박이된장찌개'],
          'FRI': ['카페테리아 현(아침)', '', '초밥', '', '짜장면', '김밥']
        },
        'lunch' : {
          'MON' : ['카페테리아 현(점심)', '사골우거지해장국', '청국장찌개', '소불고기덮밥', '가츠동', '마제소바', '제육덮밥'],
          'TUE' : ['카페테리아 현(점심)', '비지찌개', '소고기무국', '고추참치마요덮밥', '후랑크갈릭볶음밥', '낙불새덮밥 *(낙지, 불고기, 새우)', '닭개장'],
          'WED' : ['카페테리아 현(점심)', '돼지고기김치찌개', '우삼겹된장찌개', '', '', '소고기유부볶음밥', ''],
          'THU' : ['카페테리아 현(점심)', '짬뽕', '해물우동', '돼지순두부찌개', '일식카레*가라아게', '갈비찜', ''],
          'FRI': ['카페테리아 현(점심)', '진우덮밥', '오꼬노미야끼+미니소바', '사케동', '명란마요덮밥', '', ''],
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
