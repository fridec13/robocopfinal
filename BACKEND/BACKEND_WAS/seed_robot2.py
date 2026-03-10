import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "robocop"

async def fix():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    await db.robots.update_one(
        {"seq": 1},
        {"$set": {"robotId": "robot-001", "name": "ROBOCOP-001"}}
    )
    print("seq=1 robotId/name \uc5c5\ub370\uc774\ud2b8 \uc644\ub8cc")

    existing = await db.robots.find_one({"seq": 2})
    if existing:
        print("seq=2 \uc774\ubbf8 \uc874\uc7ac")
        client.close()
        return

    now = datetime.utcnow()
    robot2 = {
        "seq": 2,
        "robotId": "robot-002",
        "name": "ROBOCOP-002",
        "manufactureName": "ROBOCOP-002",
        "nickname": "\ub85c\ubd07 2\ud638",
        "sensorName": "lidar_01",
        "ipAddress": "192.168.1.101",
        "networkStatus": "connected",
        "status": "waiting",
        "networkHealth": 100.0,
        "position": {"x": 1.0, "y": 1.0, "z": 0.0, "orientation": 0.0},
        "motion": {"kph": 0.0, "mps": 0.0},
        "battery": {"level": 90.0, "isCharging": False, "lastCharged": None},
        "cpuTemp": 38.0,
        "image": None,
        "waypoints": [],
        "startAt": now,
        "IsActive": True,
        "IsDeleted": False,
        "DeletedAt": None,
        "lastActive": now,
        "createdAt": now,
        "updatedAt": None,
    }
    result = await db.robots.insert_one(robot2)
    print(f"seq=2 \uc0bd\uc785 \uc644\ub8cc: {result.inserted_id}")

    count = await db.robots.count_documents({})
    print(f"robots \ucd1d \ubb38\uc11c \uc218: {count}")
    client.close()

asyncio.run(fix())
