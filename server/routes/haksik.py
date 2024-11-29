from fastapi import APIRouter, HTTPException, Depends, Response, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
# from server.db import get_haksik_db_connection
from server.db import get_db
from server.models import CafeteriaMenu, Cafeteria, HaksikMenu, MealType
from server.schemas import CafeteriaMenuSchema, CafeteriaSchema
from collections import defaultdict


haksik_router = APIRouter(
  prefix="/v1/haksik"
)


@haksik_router.get('')
async def get_haksik(db: Session = Depends(get_db)):
  menus = db.query(CafeteriaMenu).options(
    joinedload(CafeteriaMenu.cafeteria),
    joinedload(CafeteriaMenu.day_of_week),
    joinedload(CafeteriaMenu.meal),
    joinedload(CafeteriaMenu.menu)
  ).all()
  
  haksik_data = defaultdict(lambda: {"menu": {"breakfast": defaultdict(list), "lunch": defaultdict(list)}})
  
  day_map = {1: "MON", 2: "TUE", 3: "WED", 4: "THU", 5: "FRI"}

  # 데이터를 그룹화
  for menu in menus:
      cafeteria_id = menu.cafeteria_id
      meal_type = menu.meal.type  # 'breakfast' 또는 'lunch'
      day_name = day_map[menu.day_id]  # 'MON', 'TUE' 등
      menu_name = menu.menu.name  # 실제 메뉴 이름

      # 데이터 구조에 추가
      haksik_data[cafeteria_id]["menu"][meal_type][day_name].append(menu_name)

  haksik_data = dict(haksik_data)  # defaultdict를 일반 dict로 변환
  return haksik_data

@haksik_router.put('')
async def update_haksik(data: dict = Body(...), db: Session = Depends(get_db)):
    # Fix : 그냥 들어오는 순서대로 덮어쓰게 되어있으므로 추후 수정해야함
    
    # 데이터 수정
    all_menu_names = []

    # 메뉴 데이터를 하나의 리스트로 결합
    for cafeteria_id, cafeteria_data in data.items():
        for meal_type, meal_data in cafeteria_data["menu"].items():
            for day, menu_list in meal_data.items():
                # 각 메뉴 리스트를 모두 합침
                all_menu_names.extend(menu_list)

    # 합쳐진 all_menu_names 리스트의 값들을 순차적으로 업데이트
    for idx, menu_name in enumerate(all_menu_names):
      # haksik_menu의 id를 idx에 맞게 찾아서 name을 덮어씀
      haksik_menu = db.query(HaksikMenu).filter(HaksikMenu.id == idx + 1).first()

      if haksik_menu:
        haksik_menu.name = menu_name  
        db.commit()
      else:
        print(f"HaksikMenu with id {idx + 1} not found")

    return JSONResponse(status_code=200, content={'success': True, 'message': "학식 메뉴가 업데이트 되었습니다!"})
