# ROBOCOP — Windows 로컬 개발 환경 실행 가이드

> OS: Windows 11 + WSL2 (Ubuntu 22.04)  
> 최종 확인: 2026-03-10

---

## 전체 구조

```
[Windows 11]
  ├── Docker Desktop
  │     ├── MongoDB (localhost:27017)   ← docker-compose 또는 docker run
  │     └── Redis   (localhost:6379)   ← docker-compose 또는 docker run
  ├── Python FastAPI 백엔드 (localhost:8080)
  └── Vue.js + Vite 프론트엔드 (localhost:5173)

[WSL2 — Ubuntu 22.04]
  ├── ROS2 Humble
  ├── Gazebo 11 (시뮬레이터)
  ├── rosbridge_server (ws://WSL_IP:10000)
  └── ssafy_ws (robot_status_publisher, robot_patrol, global_path_planner, ...)
```

백엔드는 WSL2 IP(`.env`의 `ROS_BRIDGE_HOST`)를 통해 rosbridge에 접속한다.  
WSL2 IP는 재부팅마다 바뀔 수 있으므로 매번 확인이 필요하다.

> **MongoDB · Redis 설치 방법**: Windows에 직접 설치하거나, **Docker Desktop으로 컨테이너로 실행**하는 두 가지 방법이 있다. Docker를 권장한다.

---

## 사전 요구 사항 (최초 1회 설치)

### Windows

| 소프트웨어 | 버전 | 설치 링크 |
|-----------|------|----------|
| Python | 3.10 이상 | [python.org](https://www.python.org/downloads/) |
| Node.js | 18 LTS 이상 | [nodejs.org](https://nodejs.org/) |
| Docker Desktop | 최신 | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| WSL2 | — | 아래 참고 |

> MongoDB Community를 Windows 서비스로 직접 설치한 경우에도 동작하지만, **Docker 사용을 권장**한다. (데이터 볼륨 관리가 편리하고 포트 충돌 위험이 낮음)

### WSL2 — Ubuntu 22.04 최초 설치

```powershell
# PowerShell (관리자)
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2
```

---

## 0단계 — MongoDB · Redis Docker 설치 (최초 1회)

> Docker Desktop이 실행 중인 상태에서 진행한다.

### 방법 A — docker-compose 사용 (권장)

프로젝트에 포함된 `docker-compose.yml`에서 MongoDB · Redis 서비스만 분리해서 실행하는 방법이다.

```powershell
cd BACKEND\BACKEND_WAS

# MongoDB + Redis 컨테이너만 백그라운드 실행
docker compose up -d mongodb redis
```

정상 실행 확인:

```powershell
docker ps
# CONTAINER ID   IMAGE   COMMAND    PORTS     NAMES
# xxxxxxxxxxxx   mongo   ...        ...       mongodb
# xxxxxxxxxxxx   redis   ...        ...       redis
```

데이터는 Docker named volume(`mongodb_data`, `redis_data`)에 영구 저장된다.  
컨테이너를 내렸다 올려도 데이터가 유지된다.

```powershell
# 중지 (데이터 유지)
docker compose stop mongodb redis

# 재시작
docker compose start mongodb redis
```

---

### 방법 B — docker run 개별 실행

docker-compose 없이 각각 실행하는 방법이다.

```powershell
# MongoDB
docker run -d `
  --name mongodb `
  -p 27017:27017 `
  -v mongodb_data:/data/db `
  -e TZ=Asia/Seoul `
  --restart unless-stopped `
  mongo

# Redis
docker run -d `
  --name redis `
  -p 6379:6379 `
  -v redis_data:/data `
  -e TZ=Asia/Seoul `
  --restart unless-stopped `
  redis redis-server --save 60 1
```

---

### 연결 확인

```powershell
# MongoDB 접속 테스트
docker exec -it mongodb mongosh --eval "db.runCommand({ ping: 1 })"
# 출력: { ok: 1 }

# Redis 접속 테스트
docker exec -it redis redis-cli ping
# 출력: PONG
```

### .env 설정값 (Docker 사용 시 그대로 사용)

```dotenv
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=robocop

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
```

Docker 컨테이너가 `--network host` (Linux) 또는 포트 바인딩(`-p`)으로 실행되므로 `localhost`로 접근 가능하다.

---

## 1단계 — WSL2 IP 확인

```powershell
# PowerShell (매 세션 시작 시 확인 권장)
wsl hostname -I
# 예: 172.25.52.95
```

또는 WSL2 터미널에서:
```bash
ip addr show eth0 | grep 'inet '
```

확인한 IP를 백엔드 `.env`에 반영한다 (아래 2단계 참고).

---

## 2단계 — 백엔드 (FastAPI) 설정 및 실행

### 2-1. `.env` 파일 편집

```
BACKEND/BACKEND_WAS/.env
```

```dotenv
ROS_BRIDGE_HOST=172.25.52.95   # ← WSL2 IP로 변경
ROS_BRIDGE_PORT=10000
BRIDGE_URL=ws://172.25.52.95:10000

MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=robocop
```

### 2-2. 가상환경 생성 (최초 1회)

```powershell
cd BACKEND\BACKEND_WAS
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> PowerShell 실행 정책 오류 발생 시:
> ```powershell
> Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 2-3. 백엔드 실행

```powershell
cd BACKEND\BACKEND_WAS
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

백엔드 접속 확인: http://localhost:8080/docs

---

## 3단계 — 프론트엔드 (Vue.js) 실행

```powershell
cd FRONTEND_WEB
npm install          # 최초 1회
npm run dev
```

프론트엔드 접속: http://localhost:5173

---

## 4단계 — WSL2 ROS2 환경 구성 (최초 1회)

WSL2 터미널을 열고:

```bash
wsl -d Ubuntu-22.04
```

### 4-1. ROS2 Humble 설치

```bash
sudo apt update && sudo apt upgrade -y

# locale 설정
sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

# ROS2 저장소 추가
sudo apt install software-properties-common curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install ros-humble-desktop ros-humble-ros-base -y
```

### 4-2. 필수 패키지 설치

```bash
# Gazebo
sudo apt install ros-humble-gazebo-ros-pkgs -y

# rosbridge
sudo apt install ros-humble-rosbridge-suite -y

# 경로 계획 / 좌표 변환
sudo apt install libgeographic-dev ros-humble-geographic-msgs -y

# 벨로다인
sudo apt install ros-humble-velodyne ros-humble-velodyne-simulator -y

# 기타
sudo apt install libeigen3-dev ros-humble-pcl-conversions -y
pip3 install networkx numpy scikit-learn matplotlib
```

### 4-3. `.bashrc` 환경 변수 등록

```bash
nano ~/.bashrc
```

파일 끝에 추가:

```bash
source /opt/ros/humble/setup.bash

# ssafy_ws 경로 (자신의 경로로 수정)
export SSAFY_WS=~/ssafy_ws
source $SSAFY_WS/install/setup.bash

# Gazebo 모델 경로
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:\
$SSAFY_WS/src/turtlebot3_simulations/turtlebot3_gazebo/models

# TurtleBot3 모델
export TURTLEBOT3_MODEL=burger

source /usr/share/gazebo/setup.sh
```

```bash
source ~/.bashrc
```

### 4-4. ssafy_ws 빌드

```bash
cd ~/ssafy_ws
colcon build --symlink-install
source install/setup.bash
```

> 빌드 에러 발생 시 `colcon build --packages-select <패키지명>` 으로 개별 빌드.

---

## 5단계 — WSL2 ROS2 시뮬레이션 실행

> 각 명령은 **별도 WSL2 터미널 탭**에서 실행한다.  
> 매 탭 시작 시 `source ~/ssafy_ws/install/setup.bash` 실행.

### 터미널 1 — rosbridge (백엔드 연결용)

```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=10000
```

출력에 `Rosbridge WebSocket server started on port 10000` 가 나오면 정상.

### 터미널 2 — Gazebo (ssafy_office C101 월드)

```bash
cd ~/ssafy_ws
ros2 launch turtlebot3_gazebo ssafy_office.launch.py
```

> 최초 실행 시 모델 로딩에 수 분 소요. 창이 열리고 사무실 월드가 보이면 정상.  
> `Address already in use` 오류 시: `killall -9 gzserver gzclient`

### 터미널 3 — 로봇 1번 (ssafy, seq=1)

```bash
cd ~/ssafy_ws
ros2 launch total_launch_pkg ssafy_robot_launch.py robot_name:=ssafy robot_number:=1
```

### 터미널 4 — 로봇 2번 (samsung, seq=2)

```bash
cd ~/ssafy_ws
ros2 launch total_launch_pkg ssafy_robot_launch.py robot_name:=samsung robot_number:=2
```

---

## 6단계 — MongoDB 데이터 초기화 (최초 1회)

백엔드 venv 활성화 상태에서:

```powershell
cd BACKEND\BACKEND_WAS
.\venv\Scripts\Activate.ps1

# 맵 데이터 시드
python seed_map.py

# DB 인덱스 수정 (robotId_1 DuplicateKey 방지)
python fix_indexes.py

# 로봇 덤프 임포트 (exec/ 폴더의 robocop_db.robots.json)
python import_robots_dump.py
```

정상 임포트 후 MongoDB에 로봇 문서가 존재하는지 확인:

```bash
# mongosh (Windows)
mongosh
use robocop
db.robots.countDocuments()   # > 0 이면 정상
```

---

## 실행 순서 요약

```
[매 개발 세션 시작 시]

0. Docker Desktop 실행 후 MongoDB · Redis 시작
   docker compose up -d mongodb redis   (BACKEND/BACKEND_WAS 디렉터리)

1. WSL2 IP 확인 → .env ROS_BRIDGE_HOST 업데이트 (IP 바뀐 경우)

2. WSL2 터미널 1: rosbridge 실행
   ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=10000

3. WSL2 터미널 2: Gazebo 실행
   ros2 launch turtlebot3_gazebo ssafy_office.launch.py

4. WSL2 터미널 3: 로봇 1번
   ros2 launch total_launch_pkg ssafy_robot_launch.py robot_name:=ssafy robot_number:=1

5. WSL2 터미널 4: 로봇 2번
   ros2 launch total_launch_pkg ssafy_robot_launch.py robot_name:=samsung robot_number:=2

6. PowerShell: 백엔드 실행
   cd BACKEND\BACKEND_WAS && .\venv\Scripts\Activate.ps1
   uvicorn app.main:app --host 0.0.0.0 --port 8080

7. PowerShell: 프론트엔드 실행
   cd FRONTEND_WEB && npm run dev
```

---

## 트러블슈팅

### rosbridge에 연결이 안 됨

```
ConnectionRefusedError / WebSocket connection failed
```

- WSL2 IP가 바뀌었는지 확인 → `.env` 업데이트
- rosbridge가 실행 중인지 확인: `ros2 topic list` 로 `/rosout` 등 토픽이 보이면 정상
- Windows 방화벽에서 10000 포트 허용 여부 확인

```powershell
# 방화벽 규칙 추가 (최초 1회, 관리자 PowerShell)
New-NetFirewallRule -DisplayName "ROS Bridge 10000" `
    -Direction Inbound -Protocol TCP -LocalPort 10000 -Action Allow
```

### Gazebo 실행 시 월드가 텅 빔

`GAZEBO_MODEL_PATH`가 설정되지 않은 경우. `.bashrc` 에 경로 등록 후:

```bash
source ~/.bashrc
killall -9 gzserver gzclient   # 기존 프로세스 제거
ros2 launch turtlebot3_gazebo ssafy_office.launch.py
```

### `/ssafy/velodyne_points` 토픽이 없음

`ssafy_office.launch.py` 가 아닌 다른 launch 파일을 실행한 경우.  
반드시 `ssafy_office.launch.py` (c101.world 사용)로 실행해야 Velodyne 토픽이 발행된다.

```bash
ros2 topic list | grep velodyne
# /samsung/velodyne_points
# /ssafy/velodyne_points
```

### MongoDB · Redis 컨테이너가 뜨지 않음

```powershell
# 로그 확인
docker logs mongodb
docker logs redis

# 포트 충돌 확인 (27017이 이미 사용 중인 경우)
netstat -ano | findstr :27017
# Windows MongoDB 서비스가 실행 중이면 중지
Stop-Service MongoDB
```

Windows에 MongoDB Community가 서비스로 설치되어 있으면 Docker 컨테이너와 포트가 충돌한다.  
둘 중 하나만 사용한다.

### MongoDB `E11000 duplicate key error`

```powershell
cd BACKEND\BACKEND_WAS
.\venv\Scripts\Activate.ps1
python fix_indexes.py
```

`robotId_1`, `name_1` 인덱스를 `sparse=True` 로 재생성한다.

### 로봇 상태가 "비활성(inactive)"으로 표시됨

MongoDB의 해당 로봇 문서에 `isActive: true` 필드가 없거나 `false`인 경우.

```bash
# mongosh
use robocop
db.robots.updateMany(
  { manufactureName: { $in: ["ssafy", "samsung"] } },
  { $set: { isActive: true } }
)
```

### 경로 완료 후 다음 명령이 무시됨 (waiting 즉시 복귀)

`robot_patrol.cpp`의 버그 — 2026-03-10 수정 완료.  
수정 후 재빌드가 필요하다:

```bash
cd ~/ssafy_ws
colcon build --packages-select robot_control_pkg
source install/setup.bash
```

---

## 포트 정리

| 서비스 | 호스트 | 포트 |
|--------|--------|------|
| MongoDB | localhost (Windows) | 27017 |
| FastAPI 백엔드 | localhost (Windows) | 8080 |
| Vue 프론트엔드 | localhost (Windows) | 5173 |
| rosbridge WebSocket | WSL2 IP | 10000 |
| Gazebo | WSL2 | — |
