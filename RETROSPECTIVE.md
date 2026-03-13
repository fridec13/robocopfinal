# 프로젝트 기술 회고록

작성일: 2026-03-12

---

## 1. 기술 스택 선택 회고

### 백엔드 — FastAPI 선택

초기에 Django vs FastAPI를 두고 고민했다.

**Django를 선택하지 않은 이유:**
- Django는 기본이 동기(sync) 방식으로 설계된 프레임워크
- async 지원은 후에 추가된 기능이라 어색함
- ROS 토픽 → SSE → 프론트 실시간 스트리밍이 핵심인 이 프로젝트와 맞지 않음

**FastAPI를 선택한 이유:**
- 처음부터 asyncio 기반으로 설계된 프레임워크
- SSE, WebSocket 연동이 자연스러움
- Swagger 자동 API 문서 제공
- 실시간 데이터 파이프라인 구조에 최적화

→ **결론: FastAPI 선택은 올바른 판단이었다.**

---

## 2. roslibpy의 한계와 교훈

### 문제 발생

개발 초기 ROS2 토픽을 Python 백엔드에서 구독하기 위해 **roslibpy**를 사용했다.  
운영 중 CPU 사용률이 지속적으로 높게 측정되었다.

```powershell
# PowerShell로 Python 프로세스 CPU 누적 시간 측정
while ($true) {
    $proc = Get-Process python
    $cpu  = ($proc | Measure-Object CPU -Sum).Sum
    Write-Host "$(Get-Date -Format 'HH:mm:ss') | CPU: ${cpu}s"
    Start-Sleep 2
}

# 측정 결과
# 16:46:57 | CPU: 13.2s
# 16:46:59 | CPU: 14.7s   ← 2초에 1.5s 증가 = CPU 75% 점유
# 16:47:01 | CPU: 16.2s
# 16:47:03 | CPU: 17.7s
```

> CPU 사용률 공식: `Δcpu_time / Δwall_time × 100`  
> 2초 동안 1.5s 증가 → `1.5 / 2.0 × 100 = 75%`

### 원인 분석

**가설 1 — WSL2 리소스 경합**: 배제됨. Windows Python 프로세스 단독 수치를 측정했기 때문.

**가설 2 — 카메라 토픽 고대역 데이터**: 확인됨.

```bash
# 카메라 토픽 실측 대역폭
average rate: 4.931 Hz
4.89 MB/s from 4 messages
Message size mean: 0.92 MB
```

초당 5프레임 × 0.92MB = 약 4.6MB/s의 이미지 데이터가 지속 유입.

### roslibpy가 근본 문제인 이유

roslibpy는 내부적으로 **Twisted 이벤트루프를 별도 스레드**에서 운영한다.

```
ROS 메시지 (바이너리)
  → rosbridge가 base64 + JSON 직렬화  → 0.92MB → 1.2MB로 증가
  → WebSocket 전송
  → roslibpy 스레드에서 json.loads() 역직렬화  ← GIL 점유
  → base64 디코딩                              ← GIL 점유
  → 콜백 실행
```

**Python GIL(Global Interpreter Lock) 문제:**

Python은 멀티스레드를 지원하더라도, GIL로 인해 한 번에 하나의 스레드만 Python 코드를 실행할 수 있다.

```
스레드A (asyncio):  [기다림][기다림][겨우실행][기다림]
스레드B (roslibpy): [json파싱━━━━][json파싱━━━━][json파싱━━━━]
                        ↑
                    GIL을 오래 점유 → asyncio가 끼어들 틈 없음
```

멀티코어 환경이어도:
```
코어1: roslibpy 스레드 (json 파싱 중)
코어2: 비어있음  ← asyncio가 GIL 없어서 실행 불가
```

### 카메라와 roslibpy의 조합이 치명적인 이유

카메라 단독이었다면 부하가 있어도 견딜 수 있는 수준이었을 것이다.  
roslibpy가 큰 데이터를 처리하는 동안 GIL을 오래 점유하면서 asyncio 루프 전체가 멈추는 현상이 발생했다.

> **비유**: 카메라는 방아쇠, roslibpy는 총이었다.

### 해결 방법

**1. 카메라 토픽 구독 제거** — 대용량 데이터 원천 차단

**2. roslibpy → pure asyncio WebSocket으로 교체**

```python
# 교체 후 코드 (ros_bridge_connection.py)
"""
Pure asyncio WebSocket client for rosbridge v2 protocol.
Replaces roslibpy (Twisted) to eliminate CPU spin in the asyncio event loop.
"""

async def _receive_loop(self):
    async for raw_msg in self._ws:       # asyncio가 직접 수신 (별도 스레드 없음)
        msg = json.loads(raw_msg)
        asyncio.create_task(cb(msg))     # 콜백도 asyncio task로 처리
```

| | roslibpy | pure asyncio |
|--|---------|--------------|
| 스레드 | Twisted 별도 스레드 | 없음 (asyncio만) |
| GIL 경합 | 있음 | 없음 |
| 콜백 실행 | 스레드에서 동기 실행 | asyncio task (비동기) |
| 대기 방식 | 스레드 블로킹 | `async for` 논블로킹 |

---

## 3. 언어/프레임워크 선택 비교

### roslibpy를 쓸 수밖에 없었던 이유

**rclpy(ROS2 네이티브 Python 라이브러리)는 Linux 전용**이다.

```
이 프로젝트 구조:
  FastAPI 백엔드 → Windows (또는 Docker on Windows)
  ROS2 / Gazebo  → WSL2 (Linux)
```

백엔드가 Windows 환경에서 동작하므로 rosbridge를 중간에 둘 수밖에 없었고, roslibpy는 그 제약 안에서의 최선이었다.

### 다른 언어를 썼다면?

| 언어 | GIL | JSON 파싱 | ROS 연동 | 현실 가능성 |
|------|-----|-----------|----------|-------------|
| **Python (현재)** | 있음 | 보통 | roslibpy → asyncio 전환으로 해결 | 사용 |
| **Node.js** | 없음 | V8 네이티브(빠름) | roslibjs (구조 동일하나 파싱 빠름) | 가능했음 |
| **Java** | 없음 | 빠름 | roslibj | 팀 인력 없음 |
| **C++** | 없음 | 매우 빠름 | rclcpp 네이티브 | 개발 생산성 너무 낮음 |

**Node.js가 이 프로젝트에서 더 유리했을 수 있다.**  
단, AI 모델 서빙(YOLO 등)은 Python이 필수이므로 어느 방식이든 Python은 어딘가에 필요했다. 백엔드를 Python으로 통일한 것은 관리 측면에서 합리적인 선택이었다.

### 최종 판단

- Django 대신 FastAPI → **올바른 선택** (실시간 스트리밍 구조에 최적)
- roslibpy 사용 → **아키텍처 제약 내 최선**, 이후 asyncio로 개선
- Python 백엔드 → **AI 통합 고려 시 합리적**, 틀린 선택이 아님

---

## 4. 핵심 개념 정리

### CPU 사용률 측정 원리

```
CPU% = (Δcpu_time / Δwall_time) × 100

- cpu_time: 프로세스가 실제로 CPU를 사용한 누적 시간 (초)
- wall_time: 실제 경과 시간 (벽시계 시간)

예: 1초 동안 CPU를 0.6초 사용 → 60%
```

PowerShell에서 Python 프로세스 측정:
```powershell
while ($true) {
    $t1 = (Get-Process python | Measure-Object CPU -Sum).Sum
    Start-Sleep 1
    $t2 = (Get-Process python | Measure-Object CPU -Sum).Sum
    $pct = [math]::Round(($t2 - $t1) * 100, 1)
    Write-Host "$(Get-Date -Format 'HH:mm:ss') | CPU: $pct%"
}
```

### Python GIL 요약

> Python은 멀티스레드를 지원하지만 GIL로 인해 한 번에 하나의 스레드만 Python 코드를 실행한다.  
> 따라서 CPU 집중 작업을 하는 스레드가 GIL을 오래 점유하면 다른 스레드는 실행 기회를 얻지 못한다.  
> asyncio는 단일 스레드 비동기 방식으로 GIL 경합 자체를 없앤다.

### 직렬화 / 역직렬화

```
직렬화:   바이너리 이미지 → base64 인코딩 → JSON 문자열  (0.92MB → 1.2MB)
역직렬화: JSON 문자열 → json.loads() → base64 디코딩 → Python 객체
```

rclpy(네이티브 DDS)를 쓰면 이 변환 단계 없이 바이너리를 직접 처리한다.

---

*이 회고록은 프로젝트 마무리 단계에서 팀원 간 기술적 논의를 정리한 것입니다.*
