import asyncio
import base64
import logging
from typing import Dict, Optional

import cv2
import numpy as np

from ...ros_publisher.service.ros_bridge_connection import RosBridgeConnection

logger = logging.getLogger(__name__)


class CameraService:
    _instances: Dict[int, 'CameraService'] = {}

    @classmethod
    async def get_instance(cls, seq: int) -> 'CameraService':
        if seq not in cls._instances:
            instance = cls()
            await instance.initialize(seq)
            cls._instances[seq] = instance
        return cls._instances[seq]

    def __init__(self):
        self.seq: Optional[int] = None
        self.fps: int = 10
        self.jpeg_quality: int = 75
        self.frame_size: tuple = (640, 480)

        self.ros_bridge: Optional[RosBridgeConnection] = None
        self.isaac_bridge: Optional[RosBridgeConnection] = None
        self.client_id: Optional[str] = None

        self._front_queue: asyncio.Queue = asyncio.Queue(maxsize=2)
        self._rear_queue: asyncio.Queue = asyncio.Queue(maxsize=2)

        self._front_topic_name: Optional[str] = None
        self._rear_topic_name: Optional[str] = None

    async def initialize(self, seq: int) -> None:
        try:
            self.seq = seq
            self.client_id = f"camera_service_{seq}"

            self.ros_bridge = RosBridgeConnection(port=10000)
            self.ros_bridge.register_client(self.client_id)

            if seq == 11:
                self.isaac_bridge = RosBridgeConnection(port=10001)
                self.isaac_bridge.register_client(self.client_id)
                logger.info(f"Isaac Bridge client registered (seq: {seq})")
            else:
                self.isaac_bridge = None

            logger.info(f"CameraService initialized (seq: {seq})")
        except Exception as e:
            logger.error(f"Camera service initialization failed: {e}")
            raise

    async def cleanup(self) -> None:
        try:
            if self._front_topic_name and self.ros_bridge:
                await self.ros_bridge.unsubscribe(self._front_topic_name, self._on_front_image)
            if self._rear_topic_name and self.ros_bridge:
                await self.ros_bridge.unsubscribe(self._rear_topic_name, self._on_rear_image)

            if self.ros_bridge:
                self.ros_bridge.unregister_client(self.client_id)
            if self.isaac_bridge:
                self.isaac_bridge.unregister_client(self.client_id)
        except Exception as e:
            logger.error(f"Cleanup error for camera service {self.seq}: {e}")

    @classmethod
    async def remove_instance(cls, seq: int) -> None:
        if seq in cls._instances:
            instance = cls._instances[seq]
            await instance.cleanup()
            del cls._instances[seq]

    def _get_bridge(self, is_isaac: bool = False) -> RosBridgeConnection:
        return self.isaac_bridge if is_isaac else self.ros_bridge

    def _decode_image(self, message: dict) -> Optional[np.ndarray]:
        try:
            encoding = message.get('encoding', '')
            raw_data = message.get('data', '')

            if not raw_data:
                return None

            image_bytes = base64.b64decode(raw_data)
            np_arr = np.frombuffer(image_bytes, np.uint8)

            if 'compressed' in encoding.lower() or 'jpeg' in encoding.lower() or 'png' in encoding.lower():
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            elif encoding in ('rgb8', 'bgr8'):
                w = message.get('width', 0)
                h = message.get('height', 0)
                if w and h and len(np_arr) == w * h * 3:
                    frame = np_arr.reshape(h, w, 3)
                    if encoding == 'rgb8':
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    return None
            else:
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None and frame.size > 0:
                return cv2.resize(frame, self.frame_size)
            return None
        except Exception as e:
            logger.debug(f"Image decode error: {e}")
            return None

    def _on_front_image(self, message: dict) -> None:
        frame = self._decode_image(message)
        if frame is not None:
            try:
                self._front_queue.put_nowait(frame)
            except asyncio.QueueFull:
                try:
                    self._front_queue.get_nowait()
                    self._front_queue.put_nowait(frame)
                except Exception:
                    pass

    def _on_rear_image(self, message: dict) -> None:
        frame = self._decode_image(message)
        if frame is not None:
            try:
                self._rear_queue.put_nowait(frame)
            except asyncio.QueueFull:
                try:
                    self._rear_queue.get_nowait()
                    self._rear_queue.put_nowait(frame)
                except Exception:
                    pass

    async def set_front_topic(self, topic_name: str, topic_type: str, is_isaac: bool = False) -> None:
        bridge = self._get_bridge(is_isaac)
        if self._front_topic_name and self._front_topic_name != topic_name:
            await bridge.unsubscribe(self._front_topic_name, self._on_front_image)
        self._front_topic_name = topic_name
        await bridge.subscribe(topic_name, topic_type, self._on_front_image)

    async def set_rear_topic(self, topic_name: str, topic_type: str, is_isaac: bool = False) -> None:
        bridge = self._get_bridge(is_isaac)
        if self._rear_topic_name and self._rear_topic_name != topic_name:
            await bridge.unsubscribe(self._rear_topic_name, self._on_rear_image)
        self._rear_topic_name = topic_name
        await bridge.subscribe(topic_name, topic_type, self._on_rear_image)

    async def stream_front(self):
        """Async generator for MJPEG front camera stream."""
        interval = 1.0 / self.fps
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        while True:
            try:
                frame = await asyncio.wait_for(self._front_queue.get(), timeout=interval * 3)
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                await asyncio.sleep(interval)
            except asyncio.TimeoutError:
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Front stream error: {e}")
                await asyncio.sleep(0.5)

    async def stream_rear(self):
        """Async generator for MJPEG rear camera stream."""
        interval = 1.0 / self.fps
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        while True:
            try:
                frame = await asyncio.wait_for(self._rear_queue.get(), timeout=interval * 3)
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                await asyncio.sleep(interval)
            except asyncio.TimeoutError:
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Rear stream error: {e}")
                await asyncio.sleep(0.5)

    # Backwards-compatible sync generator aliases (used by older controller code)
    def get_front_frame(self):
        """Legacy sync wrapper - use stream_front() for new code."""
        loop = asyncio.get_event_loop()
        return self.stream_front()

    def get_rear_frame(self):
        """Legacy sync wrapper - use stream_rear() for new code."""
        return self.stream_rear()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
