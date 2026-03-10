import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "robocop"

async def fix():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    r1 = await db.robots.update_one(
        {"seq": 1},
        {"$set": {"manufactureName": "ssafy"}}
    )
    print(f"seq=1 \uc5c5\ub370\uc774\ud2b8: {r1.modified_count}\uac74")

    r2 = await db.robots.update_one(
        {"seq": 2},
        {"$set": {"manufactureName": "samsung"}}
    )
    print(f"seq=2 \uc5c5\ub370\uc774\ud2b8: {r2.modified_count}\uac74")

    robots = await db.robots.find({}, {"seq": 1, "manufactureName": 1, "nickname": 1}).to_list(10)
    for r in robots:
        print(r)

    client.close()

asyncio.run(fix())
