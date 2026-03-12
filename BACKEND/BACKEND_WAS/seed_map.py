import asyncio
import json
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "robocop"

async def seed_map():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    map_json_path = Path(__file__).parent / "app" / "domain" / "map" / "global_map.json"
    with open(map_json_path, "r", encoding="utf-8") as f:
        map_data = json.load(f)

    existing = await db.map.find_one()
    if existing:
        print("맵 데이터가 이미 존재합니다. 업데이트합니다.")
        await db.map.replace_one({}, map_data)
    else:
        await db.map.insert_one(map_data)
        print("맵 데이터를 삽입했습니다.")

    count = await db.map.count_documents({})
    print(f"map 컬렉션 문서 수: {count}")
    client.close()

asyncio.run(seed_map())
