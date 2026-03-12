import asyncio
import logging
from .ros_bridge_connection import RosBridgeConnection

logger = logging.getLogger(__name__)


class RosPublisherService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.ros_connection = RosBridgeConnection()
        return cls._instance

    async def publish_cmd_vel(self, seq: str, direction: str):
        """로봇 이동 명령 발행"""
        try:
            self.ros_connection.ensure_connected()
            topic_name = f"/robot_{seq}/key_input"
            message = {'data': direction.upper()}
            await self.ros_connection.publish(topic_name, 'std_msgs/String', message)
            logger.info(f"Published cmd_vel: {direction}")
        except Exception as e:
            logger.error(f"Failed to publish cmd_vel: {e}")
            raise

    async def call_homing_service(self, seq: str):
        return await self.ros_connection.call_service(f'/robot_{seq}/homing')

    async def call_navigate_service(self, seq: str, goal: dict):
        return await self.ros_connection.call_service(f'/robot_{seq}/navigate', goal)

    async def call_patrol_service(self, seq: str, goals: dict):
        return await self.ros_connection.call_service(f'/robot_{seq}/patrol', goals)

    async def call_estop_service(self, seq: str):
        return await self.ros_connection.call_service(f'/robot_{seq}/stop')

    async def call_temp_stop_service(self, seq: str):
        return await self.ros_connection.call_service(f'/robot_{seq}/temp_stop')

    async def call_resume_service(self, seq: str):
        return await self.ros_connection.call_service(f'/robot_{seq}/resume')

    async def call_waiting_service(self, seq: str):
        return await self.ros_connection.call_service(f'/robot_{seq}/waiting')

    async def call_manual_service(self, seq: str):
        return await self.ros_connection.call_service(f'/robot_{seq}/manual')
