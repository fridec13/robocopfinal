from fastapi import APIRouter, WebSocket, HTTPException, Request
from fastapi.responses import StreamingResponse
from ..service.lidar_service import LidarService
from ..models.lidar_models import LidarConfig, LidarStatus
from ....common.models.responses import BaseResponse
from ....common.config.manager import get_settings
from ....domain.ros_publisher.service.ros_bridge_connection import RosBridgeConnection
import asyncio
import json
import math
import time
import logging
import base64
import struct

logger = logging.getLogger(__name__)
router = APIRouter()
lidar_service = LidarService()
settings = get_settings()

# 기본 라이다 설정
DEFAULT_LIDAR_CONFIG = LidarConfig(
    ros_bridge_host="127.0.0.1",
    ros_bridge_port=10000,
    #ros_bridge_port=9090,
    topic_name="/ssafy/velodyne_points",
    message_type="sensor_msgs/PointCloud2",
    update_interval=0.1,
    max_points=4500
)

MAX_POINTS = 3000  # 프레임당 최대 포인트 수 (성능)

@router.get("/sse/{seq}")
async def lidar_scan_sse(seq: int, request: Request):
    """PointCloud2 토픽을 SSE로 스트리밍 (seq=1→ssafy, seq=2→samsung)"""
    ns = "samsung" if seq == 2 else "ssafy"
    topic = f"/{ns}/velodyne_points"
    topic_type = "sensor_msgs/PointCloud2"

    queue: asyncio.Queue = asyncio.Queue(maxsize=2)
    _debug_logged = [False]

    def on_pointcloud(message: dict):
        try:
            raw_data = message.get("data")
            if not raw_data:
                return

            # rosbridge는 uint8[] 를 base64 문자열로 전송
            if isinstance(raw_data, str):
                data_bytes = base64.b64decode(raw_data)
            else:
                data_bytes = bytes(raw_data)

            point_step = int(message.get("point_step") or 32)
            width  = int(message.get("width")  or 0)
            height = int(message.get("height") or 1)
            n_points = width * height

            if n_points == 0 or len(data_bytes) < n_points * point_step:
                return

            # 필드 오프셋 파악 (fields 배열에서 name→offset 매핑)
            fields = {f["name"]: int(f["offset"]) for f in message.get("fields", [])}
            x_off = fields.get("x", 0)
            y_off = fields.get("y", 4)
            z_off = fields.get("z", 8)
            i_off = fields.get("intensity", 16)

            if not _debug_logged[0]:
                logger.info(
                    f"[lidar] first PC2: topic={topic}, n_points={n_points}, "
                    f"point_step={point_step}, fields={list(fields.keys())}"
                )
                _debug_logged[0] = True

            positions = []
            intensities = []
            step = max(1, n_points // MAX_POINTS)  # 다운샘플링

            for i in range(0, n_points, step):
                off = i * point_step
                try:
                    x = struct.unpack_from('<f', data_bytes, off + x_off)[0]
                    y = struct.unpack_from('<f', data_bytes, off + y_off)[0]
                    z = struct.unpack_from('<f', data_bytes, off + z_off)[0]
                except struct.error:
                    continue
                if math.isnan(x) or math.isnan(y) or math.isnan(z):
                    continue
                if math.isinf(x) or math.isinf(y) or math.isinf(z):
                    continue
                # ROS 좌표계 → Three.js z-up 맵뷰 변환
                # ROS: x=전방, y=좌, z=상
                # Three.js 카메라가 -y 방향에서 바라보므로:
                #   three_x = -ros_y  (ROS 좌 → Three.js 오른쪽)
                #   three_y =  ros_x  (ROS 전방 → Three.js y = 화면 위쪽)
                #   three_z =  ros_z  (높이는 그대로)
                positions.extend([-y, x, z])
                try:
                    intensity = struct.unpack_from('<f', data_bytes, off + i_off)[0]
                    intensities.append(float(intensity) if not math.isnan(intensity) else 1.0)
                except (struct.error, ValueError):
                    intensities.append(1.0)

            try:
                queue.put_nowait({"positions": positions, "intensities": intensities})
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.put_nowait({"positions": positions, "intensities": intensities})
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"[lidar] PC2 parse error (seq={seq}): {e}")

    bridge = RosBridgeConnection(port=10000)
    client_id = f"lidar_sse_{seq}_{id(queue)}"
    bridge.register_client(client_id)
    await bridge.subscribe(topic, topic_type, on_pointcloud)
    logger.info(f"[lidar] SSE started: seq={seq}, topic={topic}")

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    pcd = await asyncio.wait_for(queue.get(), timeout=2.0)
                    payload = json.dumps({"pcd": pcd, "timestamp": time.time()})
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await bridge.unsubscribe(topic, on_pointcloud)
            bridge.unregister_client(client_id)
            logger.info(f"[lidar] SSE ended: seq={seq}, topic={topic}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.websocket("/ws")
async def lidar_websocket(websocket: WebSocket):
    """라이다 데이터 웹소켓 엔드포인트"""
    if not lidar_service.is_connected:
        await websocket.close(code=1000, reason="라이다가 연결되지 않았습니다")
        return
        
    await lidar_service.register_client(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        await lidar_service.unregister_client(websocket)

@router.get("/status", response_model=BaseResponse)
async def get_lidar_status():
    """라이다 상태를 조회합니다."""
    status = lidar_service.get_status()
    
    if not lidar_service.is_connected:
        return BaseResponse(
            success=False,
            message="라이다가 연결되지 않았습니다",
            data={"status": "disconnected"}
        )
    
    return BaseResponse(
        success=True,
        message="라이다 상태 조회 성공",
        data={"status": status}
    )

@router.post("/config", response_model=BaseResponse)
async def update_lidar_config(config: LidarConfig):
    """라이다 설정을 업데이트합니다."""
    if not lidar_service.is_connected:
        return BaseResponse(
            success=False,
            message="라이다가 연결되지 않았습니다",
            data={"status": "disconnected"}
        )
        
    try:
        lidar_service.config = config
        return BaseResponse(
            success=True,
            message="라이다 설정 업데이트 성공",
            data={"status": lidar_service.get_status()}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reconnect", response_model=BaseResponse)
async def reconnect_lidar():
    """라이다 연결을 재시도합니다."""
    try:
        # 기존 연결 종료
        if lidar_service.is_connected:
            await lidar_service.disconnect()
        
        # 연결 재시도
        connected = await lidar_service.connect(
            host=settings.ros.ROS_BRIDGE_HOST,
            port=settings.ros.ROS_BRIDGE_PORT
        )
        
        if not connected:
            return BaseResponse(
                success=False,
                message="라이다 연결 실패",
                data={"status": "disconnected"}
            )
            
        # 구독 시작
        asyncio.create_task(lidar_service.subscribe())
        
        return BaseResponse(
            success=True,
            message="라이다 재연결 성공",
            data={"status": "connected"}
        )
        
    except AttributeError:
        return BaseResponse(
            success=False,
            message="ROS 브릿지 설정을 찾을 수 없습니다",
            data={"status": "error"}
        )
    except Exception as e:
        logger.error(f"라이다 재연결 실패: {str(e)}")
        return BaseResponse(
            success=False,
            message=f"라이다 재연결 실패: {str(e)}",
            data={"status": "error"}
        )

async def start_lidar_subscriber():
    """라이다 구독자를 시작합니다."""
    try:
        # 기본 설정 적용
        lidar_service.config = DEFAULT_LIDAR_CONFIG
        
        # 연결 시도
        try:
            connected = await lidar_service.connect(
                host=lidar_service.config.ros_bridge_host,
                port=lidar_service.config.ros_bridge_port
            )
            
            if not connected:
                logger.warning("라이다 기능이 비활성화되었습니다")
                return
                
            logger.info("라이다 서비스가 시작되었습니다")
            await lidar_service.subscribe()
            
        except AttributeError:
            logger.warning("ROS 브릿지 설정을 찾을 수 없습니다. 라이다 기능이 비활성화됩니다.")
        except Exception as e:
            logger.warning(f"라이다 서비스 오류: {str(e)}")
            
    except asyncio.CancelledError:
        logger.info("라이다 서비스가 중단되었습니다")
    except Exception as e:
        logger.error(f"라이다 서비스 오류: {str(e)}")