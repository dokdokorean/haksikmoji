from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
# from server.db import get_haksik_db_connection


haksik_router = APIRouter(
  prefix="/haksik"
)


@haksik_router.get('')
async def get_haksik():
  haksikData = {
    1: {
      'menu' : {
        'breakfast' : {
          'MON': ['김치볶음밥', '된장찌개', '돈가스카레', '새우볶음밥', '치킨마요', '비빔국수'],
          'TUE': ['우동', '순두부찌개', '닭갈비덮밥', '해물파전', '돼지불고기', '닭고기커리'],
          'WED': ['비빔밥', '갈비탕', '콩나물국밥', '치즈돈가스', '김치라면', '제육쌈밥'],
          'THU': ['해물볶음우동', '냉모밀', '미트볼스파게티', '불닭볶음면', '', '차돌박이된장찌개'],
          'FRI': ['소고기국밥', '', '초밥', '', '짜장면', '김밥']
        },
        'lunch' : {
          'MON' : ['참치마요', '사골우거지해장국', '청국장찌개', '소불고기덮밥', '가츠동', '마제소바', '제육덮밥'],
          'TUE' : ['참치마요', '비지찌개', '소고기무국', '고추참치마요덮밥', '후랑크갈릭볶음밥', '낙불새덮밥 *(낙지, 불고기, 새우)', '닭개장'],
          'WED' : ['참치마요', '돼지고기김치찌개', '우삼겹된장찌개', '', '', '소고기유부볶음밥', ''],
          'THU' : ['', '짬뽕', '해물우동', '돼지순두부찌개', '일식카레*가라아게', '갈비찜', ''],
          'FRI': ['', '진우덮밥', '오꼬노미야끼+미니소바', '사케동', '명란마요덮밥', '', ''],
        }
      }
    },
    2: {
      'menu' : {
        'breakfast' : {
          'MON': ['김치볶음밥', '제육볶음', '된장찌개', '해물볶음밥', '불고기', '비빔냉면'],
          'TUE': ['초계국수', '순두부찌개', '돈가스', '카레라이스', '비빔밥', '쫄면'],
          'WED': ['우삼겹덮밥', '콩나물국밥', '김치찜', '차돌박이된장찌개', '해물파전', '냉모밀'],
          'THU': ['짜장면', '짬뽕', '라멘', '스팸김치볶음밥', '치킨가스', '비빔국수'],
          'FRI': ['소불고기덮밥', '사골곰탕', '비빔밥', '닭갈비', '떡국', '김밥']
        },
        'lunch' : {
          'MON': ['김치찌개', '참치마요덮밥', '감자탕', '오므라이스', '돈가스', '우동', '제육볶음'],
          'TUE': ['칼국수', '된장찌개', '불고기덮밥', '새우볶음밥', '치킨마요', '', '미트볼'],
          'WED': ['소고기무국', '카레라이스', '', '치즈돈가스', '순두부찌개', '콩나물국밥', '라면'],
          'THU': ['비빔국수', '해물파전', '매운갈비찜', '라멘', '', '차돌박이된장찌개', '김밥'],
          'FRI': ['갈비탕', '삼계탕', '부대찌개', '', '', '제육덮밥', '만두국']
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
