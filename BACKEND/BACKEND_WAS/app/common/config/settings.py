from pydantic_settings import BaseSettings

class ROS2Settings(BaseSettings):
    BRIDGE_URL: str = "ws://127.0.0.1:10000"
    ROS_BRIDGE_HOST: str = "127.0.0.1"
    ROS_BRIDGE_PORT: int = 10000
    RETRY_INTERVAL: int = 5
    MAX_RETRIES: int = 3

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

class Settings(BaseSettings):
    # ... 기존 설정들 ...
    ros2: ROS2Settings = ROS2Settings() 