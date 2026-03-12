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
        self.fps: int = 5
        self.jpeg_quality: int = 70
        self.frame_size: tuple = (480, 360)

        self.ros_bridge: Optional[RosBridgeConnection] = None
        self.isaac_bridge: Optional[RosBridgeConnection] = None
        self.client_id: Optional[str] = None

        self._front_queue: asyncio.Queue = asyncio.Queue(maxsize=2)
        self._rear_queue: asyncio.Queue = asyncio.Queue(maxsize=2)

        # topic 메타 (set_front/rear_topic 에서 저장, 실제 구독은 stream 시작 시)
        self._front_topic_name: Optional[str] = None
        self._front_topic_type: Optional[str] = None
        self._front_is_isaac: bool = False
        self._front_subscribed: bool = False
        self._front_consumers: int = 0

        self._rear_topic_name: Optional[str] = None
        self._rear_topic_type: Optional[str] = None
        self._rear_is_isaac: bool = False
        self._rear_subscribed: bool = False
        self._rear_consumers: int = 0

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
            if self._front_subscribed and self._front_topic_name and self.ros_bridge:
                bridge = self._get_bridge(self._front_is_isaac)
                await bridge.unsubscribe(self._front_topic_name, self._on_front_image)
                self._front_subscribed = False
            if self._rear_subscribed and self._rear_topic_name and self.ros_bridge:
                bridge = self._get_bridge(self._rear_is_isaac)
                await bridge.unsubscribe(self._rear_topic_name, self._on_rear_image)
                self._rear_subscribed = False

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
            encoding = message.get('encoding', '') or message.get('format', '')
            raw_data = message.get('data', '')

            if not raw_data:
                logger.warning(f"[camera] empty data field, keys={list(message.keys())}")
                return None

            if isinstance(raw_data, list):
                image_bytes = bytes(raw_data)
            else:
                image_bytes = base64.b64decode(raw_data)

            np_arr = np.frombuffer(image_bytes, np.uint8)

            is_compressed = (
                'compressed' in encoding.lower()
                or 'jpeg' in encoding.lower()
                or 'jpg' in encoding.lower()
                or 'png' in encoding.lower()
                or encoding == ''
            )

            if is_compressed:
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            elif encoding in ('rgb8', 'bgr8'):
                w = message.get('width', 0)
                h = message.get('height', 0)
                if w and h and len(np_arr) == w * h * 3:
                    frame = np_arr.reshape(h, w, 3)
                    if encoding == 'rgb8':
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                else:
                    logger.warning(f"[camera] raw image size mismatch: w={w} h={h} len={len(np_arr)}")
                    return None
            else:
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is not None and frame.size > 0:
                return cv2.resize(frame, self.frame_size)

            logger.warning(f"[camera] imdecode returned None, encoding={encoding!r}, data_len={len(image_bytes)}")
            return None
        except Exception as e:
            logger.warning(f"[camera] Image decode error: {e}")
            return None

    def _on_front_image(self, message: dict) -> None:
        logger.debug(f"[camera seq={self.seq}] front msg received, keys={list(message.keys())}")
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
        else:
            logger.warning(f"[camera seq={self.seq}] front decode returned None")

    def _on_rear_image(self, message: dict) -> None:
        logger.debug(f"[camera seq={self.seq}] rear msg received, keys={list(message.keys())}")
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
        else:
            logger.warning(f"[camera seq={self.seq}] rear decode returned None")

    async def set_front_topic(self, topic_name: str, topic_type: str, is_isaac: bool = False) -> None:
        """토픽 정보만 저장 – 실제 구독은 stream_front() 첫 소비자 진입 시 수행"""
        if self._front_subscribed and self._front_topic_name != topic_name:
            bridge = self._get_bridge(self._front_is_isaac)
            await bridge.unsubscribe(self._front_topic_name, self._on_front_image)
            self._front_subscribed = False
        self._front_topic_name = topic_name
        self._front_topic_type = topic_type
        self._front_is_isaac = is_isaac

    async def set_rear_topic(self, topic_name: str, topic_type: str, is_isaac: bool = False) -> None:
        """토픽 정보만 저장 – 실제 구독은 stream_rear() 첫 소비자 진입 시 수행"""
        if self._rear_subscribed and self._rear_topic_name != topic_name:
            bridge = self._get_bridge(self._rear_is_isaac)
            await bridge.unsubscribe(self._rear_topic_name, self._on_rear_image)
            self._rear_subscribed = False
        self._rear_topic_name = topic_name
        self._rear_topic_type = topic_type
        self._rear_is_isaac = is_isaac

    async def stream_front(self):
        """MJPEG 전면 카메라 스트림 (소비자 수 기반 구독/해제)"""
        # 첫 소비자 진입 시 구독
        if not self._front_subscribed and self._front_topic_name:
            bridge = self._get_bridge(self._front_is_isaac)
            await bridge.subscribe(self._front_topic_name, self._front_topic_type, self._on_front_image)
            self._front_subscribed = True
            logger.info(f"[camera seq={self.seq}] front subscribed: {self._front_topic_name}")

        self._front_consumers += 1
        logger.info(f"[camera seq={self.seq}] front consumer connected (total={self._front_consumers})")

        interval = 1.0 / self.fps
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        try:
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
        finally:
            self._front_consumers = max(0, self._front_consumers - 1)
            logger.info(f"[camera seq={self.seq}] front consumer disconnected (remaining={self._front_consumers})")
            if self._front_consumers == 0 and self._front_subscribed and self._front_topic_name:
                try:
                    bridge = self._get_bridge(self._front_is_isaac)
                    await bridge.unsubscribe(self._front_topic_name, self._on_front_image)
                    self._front_subscribed = False
                    logger.info(f"[camera seq={self.seq}] front unsubscribed: {self._front_topic_name}")
                except Exception as e:
                    logger.error(f"[camera seq={self.seq}] front unsubscribe error: {e}")

    async def stream_rear(self):
        """MJPEG 후면 카메라 스트림 (소비자 수 기반 구독/해제)"""
        if not self._rear_subscribed and self._rear_topic_name:
            bridge = self._get_bridge(self._rear_is_isaac)
            await bridge.subscribe(self._rear_topic_name, self._rear_topic_type, self._on_rear_image)
            self._rear_subscribed = True
            logger.info(f"[camera seq={self.seq}] rear subscribed: {self._rear_topic_name}")

        self._rear_consumers += 1
        logger.info(f"[camera seq={self.seq}] rear consumer connected (total={self._rear_consumers})")

        interval = 1.0 / self.fps
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        try:
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
        finally:
            self._rear_consumers = max(0, self._rear_consumers - 1)
            logger.info(f"[camera seq={self.seq}] rear consumer disconnected (remaining={self._rear_consumers})")
            if self._rear_consumers == 0 and self._rear_subscribed and self._rear_topic_name:
                try:
                    bridge = self._get_bridge(self._rear_is_isaac)
                    await bridge.unsubscribe(self._rear_topic_name, self._on_rear_image)
                    self._rear_subscribed = False
                    logger.info(f"[camera seq={self.seq}] rear unsubscribed: {self._rear_topic_name}")
                except Exception as e:
                    logger.error(f"[camera seq={self.seq}] rear unsubscribe error: {e}")

    def get_front_frame(self):
        return self.stream_front()

    def get_rear_frame(self):
        return self.stream_rear()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
