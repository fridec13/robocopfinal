from fastapi import APIRouter
from ..models.ros_publisher_models import PublishRequest, NavigateRequest, PatrolRequest
from ..service.ros_publisher_service import RosPublisherService
import logging
from app.common.middleware.socket_service import broadcast_to_clients, send_people_images
import json

router = APIRouter()
logger = logging.getLogger(__name__)

ros_publisher = RosPublisherService()


@router.post("/{seq}/start")
async def start_robot(seq: str):
    try:
        response = await ros_publisher.call_resume_service(seq)
        await send_people_images()
        return {"status": "success", "message": "Robot start service called successfully", "response": response}
    except Exception as e:
        logger.error(f"Failed to start robot: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/cmd_vel")
async def publish_cmd_vel(seq: str, direction: str):
    try:
        await ros_publisher.publish_cmd_vel(seq, direction)
        return {"status": "success", "message": f"Published direction: {direction}"}
    except Exception as e:
        logger.error(f"Failed to publish direction: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/call-service/homing")
async def call_homing_endpoint(seq: str):
    try:
        estop_response = await ros_publisher.call_estop_service(seq)
        waiting_response = await ros_publisher.call_waiting_service(seq)
        response = await ros_publisher.call_homing_service(seq)
        return {"status": "success", "mode": "homing", "message": "Homing service called successfully", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/call-service/navigate")
async def call_navigate_endpoint(seq: str, request: NavigateRequest):
    try:
        goal = {"goal": {"x": request.goal.x, "y": request.goal.y, "theta": request.goal.theta}}
        response = await ros_publisher.call_navigate_service(seq, goal)
        return {"status": "success", "message": "Navigation service called successfully", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/call-service/patrol")
async def call_patrol_endpoint(seq: str, request: PatrolRequest):
    try:
        goals = {
            "goals": [
                {"x": goal.x, "y": goal.y, "theta": goal.theta}
                for goal in request.goals
            ]
        }
        response = await ros_publisher.call_patrol_service(seq, goals)
        return {"status": "success", "mode": "patrol", "message": "Patrol service called successfully", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/call-service/estop")
async def call_estop_endpoint(seq: str):
    try:
        response = await ros_publisher.call_estop_service(seq)
        return {"status": "success", "mode": "emergency_stop", "message": "E-stop service called successfully", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/call-service/temp-stop")
async def call_temp_stop_endpoint(seq: str):
    try:
        response = await ros_publisher.call_temp_stop_service(seq)
        return {"status": "success", "mode": "temp_stop", "message": "Temporary stop service called successfully", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/call-service/resume")
async def call_resume_endpoint(seq: str):
    try:
        response = await ros_publisher.call_resume_service(seq)
        return {"status": "success", "message": "Resume service called successfully", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/call-service/waiting")
async def call_waiting_endpoint(seq: str):
    try:
        response = await ros_publisher.call_waiting_service(seq)
        return {"status": "success", "mode": "waiting", "message": "Waiting service called successfully", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/call-service/manual")
async def call_manual_endpoint(seq: str):
    try:
        estop_response = await ros_publisher.call_estop_service(seq)
        waiting_response = await ros_publisher.call_waiting_service(seq)
        response = await ros_publisher.call_manual_service(seq)
        return {"status": "success", "message": "Manual mode service called successfully", "response": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/{seq}/reset")
async def reset_robot(seq: str):
    try:
        estop_response = await ros_publisher.call_estop_service(seq)
        waiting_response = await ros_publisher.call_waiting_service(seq)
        return {
            "status": "success",
            "message": "Robot reset successfully",
            "responses": {"estop": estop_response, "waiting": waiting_response}
        }
    except Exception as e:
        logger.error(f"Failed to reset robot: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.post("/alert-off")
async def alert_off():
    try:
        await broadcast_to_clients(json.dumps({"response_type": "MODE_ALERT_STOP"}))
        return {"status": "success", "message": "Alert off message sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send alert off message: {str(e)}")
        return {"status": "error", "message": str(e)}


@router.post("/ai-init")
async def ai_init():
    try:
        await broadcast_to_clients(json.dumps({"response_type": "MODE_INIT"}))
        return {"status": "success", "message": "AI init message sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send ai init message: {str(e)}")
        return {"status": "error", "message": str(e)}
