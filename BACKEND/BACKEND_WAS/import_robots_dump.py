"""
robocop_db.robots.json 덤프 파일을 MongoDB에 임포트합니다.
- 기존 robots 컬렉션을 초기화하고 덤프 데이터로 교체
- seq=1 → manufactureName="ssafy", seq=2 → manufactureName="samsung" 유지
- robotId/name 유니크 인덱스 제거 (덤프에 해당 필드 없음)
"""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "robocop"
DUMP_PATH = Path(__file__).parent.parent.parent / "exec" / "robocop_db.robots.json"

def parse_extended_json(obj):
    """MongoDB Extended JSON ($oid, $date) 변환"""
    if isinstance(obj, dict):
        if "$oid" in obj:
            return obj["$oid"]
        if "$date" in obj:
            return datetime.fromisoformat(obj["$date"].replace("Z", "+00:00"))
        return {k: parse_extended_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [parse_extended_json(i) for i in obj]
    return obj

async def main():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    # 1. 기존 컬렉션 삭제 후 재생성
    await db.robots.drop()
    print("\ub85c\ubd07 \ucf5c\ub809\uc158 \ucd08\uae30\ud654 \uc644\ub8cc")

    # 2. 덤프 파일 로드
    with open(DUMP_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    robots = [parse_extended_json(r) for r in raw]

    # 3. seq=1,2 manufactureName 수정 (ROS 네임스페이스 매핑)
    ns_map = {1: "ssafy", 2: "samsung"}
    for r in robots:
        seq = r.get("seq")
        if seq in ns_map:
            r["manufactureName"] = ns_map[seq]

    # 4. _id 제거 (MongoDB가 자동 생성하도록)
    for r in robots:
        r.pop("_id", None)

    # 5. 삽입
    result = await db.robots.insert_many(robots)
    print(f"{len(result.inserted_ids)}\uac1c \ub85c\ubd07 \uc0bd\uc785 \uc644\ub8cc")

    # 6. 기존 문제 인덱스 제거 (robotId_1, name_1 - 덤프에 해당 필드 없음)
    indexes = await db.robots.index_information()
    for idx_name in ["robotId_1", "name_1"]:
        if idx_name in indexes:
            await db.robots.drop_index(idx_name)
            print(f"\uc778\ub371\uc2a4 '{idx_name}' \uc81c\uac70")

    # 7. 결과 확인
    count = await db.robots.count_documents({})
    print(f"\n\uc0bd\uc785 \ud6c4 \uc804\uccb4 \ub85c\ubd07 \uc218: {count}")

    active = await db.robots.find({"IsActive": True}, {"seq": 1, "manufactureName": 1, "nickname": 1}).to_list(20)
    print("\n[ \ud65c\uc131 \ub85c\ubd07 ]")
    for r in active:
        print(f"  seq={r['seq']} | manufactureName={r['manufactureName']} | nickname={r['nickname']}")

    client.close()

asyncio.run(main())
