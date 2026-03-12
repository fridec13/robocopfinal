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

@router.get("/sse/{seq}")
async def lidar_scan_sse(seq: int, request: Request):
    """LaserScan 토픽을 SSE로 스트리밍 (seq=1→ssafy, seq=2→samsung)"""
    ns = "samsung" if seq == 2 else "ssafy"
    topic = f"/{ns}/scan"
    topic_type = "sensor_msgs/LaserScan"

    queue: asyncio.Queue = asyncio.Queue(maxsize=2)

    _debug_logged = [False]

    def on_scan(message: dict):
        try:
            if not _debug_logged[0]:
                sample_ranges = message.get("ranges", [])[:5]
                logger.info(f"[lidar] first scan msg keys={list(message.keys())}, angle_min={message.get('angle_min')}, angle_increment={message.get('angle_increment')}, ranges[:5]={sample_ranges}")
                _debug_logged[0] = True
            ranges = message.get("ranges") or []
            angle_min = float(message.get("angle_min") or 0.0)
            angle_increment = float(message.get("angle_increment") or 0.0)
            range_min = float(message.get("range_min") or 0.1)
            range_max = float(message.get("range_max") or 10.0)
            intensities = message.get("intensities", [])

            positions = []
            out_intensities = []

            for i, r in enumerate(ranges):
                if r is None:
                    continue
                try:
                    r = float(r)
                except (TypeError, ValueError):
                    continue
                if math.isnan(r) or math.isinf(r):
                    continue
                if r < range_min or r > range_max:
                    continue
                angle = angle_min + i * angle_increment
                positions.extend([
                    r * math.cos(angle),   # x
                    r * math.sin(angle),   # y
                    0.0                    # z (2D scan)
                ])
                out_intensities.append(float(intensities[i]) if i < len(intensities) else 1.0)

            try:
                queue.put_nowait({"positions": positions, "intensities": out_intensities})
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.put_nowait({"positions": positions, "intensities": out_intensities})
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"[lidar] scan parse error (seq={seq}): {e}")

    bridge = RosBridgeConnection(port=10000)
    client_id = f"lidar_sse_{seq}_{id(queue)}"
    bridge.register_client(client_id)
    await bridge.subscribe(topic, topic_type, on_scan)
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
            await bridge.unsubscribe(topic, on_scan)
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