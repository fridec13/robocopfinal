import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def fix():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["robocop"]

    indexes = await db.robots.index_information()
    for name in ["robotId_1", "name_1"]:
        if name in indexes:
            await db.robots.drop_index(name)
            print(f"\uc778\ub371\uc2a4 {name} \uc81c\uac70")

    await db.robots.create_index("robotId", unique=True, sparse=True)
    await db.robots.create_index("name", unique=True, sparse=True)
    print("sparse \uc778\ub371\uc2a4 \uc7ac\uc131\uc131 \uc644\ub8cc")

    map_count = await db.map.count_documents({})
    print(f"map \ucf5c\ub809\uc158 \ubb38\uc11c \uc218: {map_count}")
    if map_count > 0:
        doc = await db.map.find_one({}, {"directed": 1, "nodes": 1, "links": 1})
        nodes = len(doc.get("nodes", []))
        links = len(doc.get("links", []))
        directed = doc.get("directed")
        print(f"  directed={directed}, nodes={nodes}, links={links}")
    else:
        print("  map \ub370\uc774\ud130 \uc5c6\uc74c \uc2dc\ub4dc \ud544\uc694")

    client.close()

asyncio.run(fix())
