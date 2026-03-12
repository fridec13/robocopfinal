import asyncio
import json
import logging
import uuid
from typing import Callable, Dict, List, Optional

import websockets

logger = logging.getLogger(__name__)


class RosBridgeConnection:
    """
    Pure asyncio WebSocket client for rosbridge v2 protocol.
    Replaces roslibpy (Twisted) to eliminate CPU spin in the asyncio event loop.
    """
    _instances: Dict[int, 'RosBridgeConnection'] = {}

    def __new__(cls, port: int = 10000):
        if port not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[port] = instance
        return cls._instances[port]

    def __init__(self, port: int = 10000):
        if self._initialized:
            return
        self._initialized = True

        from app.common.config.manager import get_settings
        settings = get_settings()

        self.host: str = settings.ros2.ROS_BRIDGE_HOST
        self.port: int = port
        self.url: str = f"ws://{self.host}:{self.port}"

        self._ws = None
        self._connected: bool = False
        self._subscribers: Dict[str, List[Callable]] = {}
        self._pending_services: Dict[str, asyncio.Future] = {}
        self._receive_task: Optional[asyncio.Task] = None
        self.connected_clients: set = set()

    @property
    def is_connected(self) -> bool:
        return self._connected and self._ws is not None

    async def connect(self) -> bool:
        try:
            logger.info(f"ROS Bridge 연결 시도 중... ({self.url})")
            self._ws = await websockets.connect(
                self.url,
                ping_interval=20,
                ping_timeout=10,
                max_size=10 * 1024 * 1024,  # 10 MB (raw 이미지 대응)
            )
            self._connected = True
            self._receive_task = asyncio.create_task(self._receive_loop())
            logger.info(f"ROS Bridge connected: {self.url}")
            return True
        except Exception as e:
            logger.error(f"ROS Bridge connection failed: {e}")
            self._connected = False
            return False

    async def _receive_loop(self):
        try:
            async for raw_msg in self._ws:
                try:
                    msg = json.loads(raw_msg)
                    op = msg.get('op')

                    if op == 'publish':
                        topic = msg.get('topic')
                        if topic in self._subscribers:
                            for cb in list(self._subscribers[topic]):
                                try:
                                    if asyncio.iscoroutinefunction(cb):
                                        asyncio.create_task(cb(msg.get('msg', {})))
                                    else:
                                        cb(msg.get('msg', {}))
                                except Exception as e:
                                    logger.error(f"Subscriber callback error on {topic}: {e}")

                    elif op == 'service_response':
                        sid = msg.get('id')
                        if sid in self._pending_services:
                            future = self._pending_services.pop(sid)
                            if not future.done():
                                future.set_result(msg.get('values', {}))

                except Exception as e:
                    logger.error(f"Message processing error: {e}")

        except Exception as e:
            logger.warning(f"ROS Bridge receive loop ended: {e}")
            self._connected = False

    async def publish(self, topic: str, msg_type: str, message: dict) -> bool:
        if not self.is_connected:
            logger.warning("ROS Bridge not connected, skipping publish")
            return False
        try:
            payload = json.dumps({"op": "publish", "topic": topic, "msg": message})
            await self._ws.send(payload)
            return True
        except Exception as e:
            logger.error(f"Publish failed on {topic}: {e}")
            self._connected = False
            return False

    async def subscribe(self, topic: str, msg_type: str, callback: Callable) -> None:
        if topic not in self._subscribers:
            self._subscribers[topic] = []
            if self.is_connected:
                payload = json.dumps({"op": "subscribe", "topic": topic, "type": msg_type})
                await self._ws.send(payload)
        if callback not in self._subscribers[topic]:
            self._subscribers[topic].append(callback)

    async def unsubscribe(self, topic: str, callback: Callable = None) -> None:
        if topic not in self._subscribers:
            return
        if callback:
            try:
                self._subscribers[topic].remove(callback)
            except ValueError:
                pass
        else:
            self._subscribers[topic].clear()

        if not self._subscribers[topic]:
            del self._subscribers[topic]
            if self.is_connected:
                payload = json.dumps({"op": "unsubscribe", "topic": topic})
                await self._ws.send(payload)

    async def call_service(self, service: str, args: dict = None, timeout: float = 10.0) -> dict:
        if not self.is_connected:
            raise ConnectionError("ROS Bridge not connected")

        sid = f"service:{service}:{uuid.uuid4().hex[:8]}"
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._pending_services[sid] = future

        try:
            payload = json.dumps({
                "op": "call_service",
                "id": sid,
                "service": service,
                "args": args or {}
            })
            await self._ws.send(payload)
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending_services.pop(sid, None)
            raise TimeoutError(f"Service call timed out: {service}")
        except Exception as e:
            self._pending_services.pop(sid, None)
            raise

    def register_client(self, client_id: str):
        self.connected_clients.add(client_id)

    def unregister_client(self, client_id: str):
        self.connected_clients.discard(client_id)

    def ensure_connected(self):
        """Compatibility shim: schedules async connect if not connected."""
        if not self.is_connected:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.connect())
            except Exception:
                pass

    async def close(self):
        self._connected = False
        if self._receive_task:
            self._receive_task.cancel()
        if self._ws:
            await self._ws.close()
        self.__class__._instances.pop(self.port, None)
