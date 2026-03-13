import logging
from ..models.map_models import PointsData
from ....infrastructure.database.connection import DatabaseConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PointService:
    @staticmethod
    async def get_points():
        try:
            db = await DatabaseConnection.get_db()
            if db is None:
                raise Exception("데이터베이스 연결 실패")

            map_data = await db.map.find_one()
            if map_data is None:
                logger.error("맵 데이터를 찾을 수 없습니다.")
                return PointsData(directed=False, multigraph=False, graph={}, nodes=[], links=[])

            return PointsData(**map_data)
        except Exception as e:
            logger.error(f"맵 데이터 읽기 오류: {str(e)}")
            return PointsData(directed=False, multigraph=False, graph={}, nodes=[], links=[])

    @staticmethod
    async def update_points(data: PointsData):
        try:
            db = await DatabaseConnection.get_db()
            if db is None:
                raise Exception("데이터베이스 연결 실패")

            await db.map.drop()
            await db.map.insert_one(data.model_dump())
            logger.info(f"맵 갱신 완료 — 노드 {len(data.nodes)}개, 링크 {len(data.links)}개")
            return {"ok": True, "nodes": len(data.nodes), "links": len(data.links)}
        except Exception as e:
            logger.error(f"맵 데이터 쓰기 오류: {str(e)}")
            raise