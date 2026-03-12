from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import logging
from ..service.camera_service import CameraService

logger = logging.getLogger(__name__)
router = APIRouter()

# ROS 토픽 정보 상수 정의
CAMERA_TOPICS = [
    {
        "name_pattern": "/ssafy/tb3_{direction}_camera/image_raw",
        "type": "sensor_msgs/Image",
        "description": "로봇 카메라 raw 이미지 스트림"
    }
]

# Isaac 로봇 관련 토픽 정의
ISAAC_TOPICS = [
    {
        "name": "/Isaacbot/front/img_compressed",
        "type": "sensor_msgs/msg/Image",
        "description": "Isaac 로봇 전면 카메라 이미지"
    },
    {
        "name": "/Isaacbot/rear/img_compressed",
        "type": "sensor_msgs/msg/Image",
        "description": "Isaac 로봇 후면 카메라 이미지"
    },
    {
        "name": "/Isaacbot/velodyne_points",
        "type": "sensor_msgs/PointCloud2",
        "description": "Velodyne LiDAR 포인트 클라우드 데이터"
    },
    {
        "name": "/Isaacbot/cmd_vel",
        "type": "geometry_msgs/Twist",
        "description": "로봇 속도 명령"
    },
    {
        "name": "/Isaacbot/imu",
        "type": "sensor_msgs/Imu",
        "description": "IMU 센서 데이터"
    }
]

@router.get("/video_feed/{seq}/front")
async def front_video_feed(seq: int):
    try:
        camera_service = await CameraService.get_instance(seq)
        if camera_service is None:
            raise HTTPException(status_code=500, detail="카메라 서비스 초기화 실패")
        
        if seq == 11:
            topic_info = next(
                (topic for topic in ISAAC_TOPICS 
                 if topic["name"] == "/Isaacbot/front/img_compressed"),
                None
            )
            
            if not topic_info:
                raise HTTPException(status_code=400, detail="해당하는 카메라 토픽을 찾을 수 없습니다")
            
            logger.info(f"Isaac 로봇 전면 카메라 토픽 설정: {topic_info['name']}, {topic_info['type']}")
            await camera_service.set_front_topic(
                topic_info["name"],
                topic_info["type"],
                is_isaac=True
            )
        else:
            topic_pattern = CAMERA_TOPICS[0]["name_pattern"]
            robot_ns = "samsung" if seq == 2 else "ssafy"
            topic_name = topic_pattern.format(direction="front").replace("ssafy", robot_ns)
            topic_type = CAMERA_TOPICS[0]["type"]

            logger.info(f"일반 로봇 전면 카메라 토픽 설정: {topic_name}, {topic_type}")
            await camera_service.set_front_topic(topic_name, topic_type, is_isaac=False)

        return StreamingResponse(
            camera_service.stream_front(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
        
        
    except Exception as e:
        logger.error(f"전면 카메라 스트리밍 에러: {str(e)}")
        logger.error(f"Request seq: {seq}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video_feed/{seq}/rear")
async def rear_video_feed(seq: int):
    try:
        # get_instance를 명시적으로 await
        camera_service = await CameraService.get_instance(seq)
        if camera_service is None:
            raise HTTPException(status_code=500, detail="카메라 서비스 초기화 실패")
        
        if seq == 11:
            topic_info = next(
                (topic for topic in ISAAC_TOPICS 
                 if topic["name"] == "/Isaacbot/rear/img_compressed"),
                None
            )
            
            if not topic_info:
                raise HTTPException(status_code=400, detail="해당하는 카메라 토픽을 찾을 수 없습니다")
            
            logger.info(f"Isaac 로봇 후면 카메라 토픽 설정: {topic_info['name']}, {topic_info['type']}")
            await camera_service.set_rear_topic(
                topic_info["name"],
                topic_info["type"],
                is_isaac=True
            )
        else:
            topic_pattern = CAMERA_TOPICS[0]["name_pattern"]
            robot_ns = "samsung" if seq == 2 else "ssafy"
            topic_name = topic_pattern.format(direction="rear").replace("ssafy", robot_ns)
            topic_type = CAMERA_TOPICS[0]["type"]

            logger.info(f"일반 로봇 후면 카메라 토픽 설정: {topic_name}, {topic_type}")
            await camera_service.set_rear_topic(topic_name, topic_type, is_isaac=False)

        return StreamingResponse(
            camera_service.stream_rear(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
            
    except Exception as e:
        logger.error(f"후면 카메라 스트리밍 에러: {str(e)}")
        logger.error(f"Request seq: {seq}")
        raise HTTPException(status_code=500, detail=str(e))

# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     """WebSocket 연결을 처리하는 엔드포인트"""
#     try:
#         await websocket.accept()
#         while True:
#             data = await websocket.receive_text()
#             await websocket.send_text(f"Message received: {data}")
#     except Exception as e:
#         logger.error(f"WebSocket 에러: {str(e)}")
#     finally:
#         try:
#             await websocket.close()
#         except:
#             pass
