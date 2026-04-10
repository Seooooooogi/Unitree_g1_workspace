# g1_workspace

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Hard Rules (never bend)
See [~/.claude/rules/ai-constitution.md](~/.claude/rules/ai-constitution.md) for global rules.

Project-specific additions:
- **no fabricated sensor data**: DDS 토픽 또는 MuJoCo 상태 누락 시 null/unknown 반환 — 값 생성 금지
- **no hardcoded joint limits**: G1 관절 속도/토크 한계는 YAML 설정에서만 로드 — 소스코드 하드코딩 금지
- **input validation**: DDS 토픽 데이터, Xbox 컨트롤러 입력 등 모든 시스템 경계에서 유효성 검증
- **sim-only gate**: 실물 로봇 미보유 — 모든 컨트롤 로직은 시뮬레이터에서 먼저 검증

## Secrets Policy
- Robot IP, API 키는 환경변수로만 — `.env`에 보관, 코드에 하드코딩 금지
- `.env` 커밋 금지 — `.env.example`이 템플릿 (실제 값 없음)

## Quick Ref

### C++ Simulator
```bash
cd unitree_mujoco/simulate/build && ./unitree_mujoco
# Config: unitree_mujoco/simulate/config.yaml
```

### Python Simulator
```bash
python3 unitree_mujoco/simulate_python/unitree_mujoco.py
# Config: unitree_mujoco/simulate_python/config.py
```

### Control Scripts (ROS2)
```bash
source install/setup.bash
ros2 run g1_teleop joystick_controller
ros2 launch g1_mujoco_bridge bridge.launch.py dof_mode:=29
```

### Build (ROS2)
```bash
colcon build --packages-select g1_mujoco_bridge g1_teleop
source install/setup.bash
```

### Build (C++ Simulator)
```bash
cd external/unitree_mujoco/simulate && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release && cmake --build . -j4
```

### Tests
```bash
python3 -m pytest unitree_mujoco/simulate_python/test/ -q
```

## Project Overview

**Goal**: Xbox 컨트롤러로 G1 humanoid robot 보행 제어 (MuJoCo 시뮬레이터). 이후 티칭 데이터 수집 및 강화학습 배포 가능성 검토.

Supported robots: G1 (humanoid, 29/35 DOF), Go2, B2, B2w, H1, H1-2.

## Architecture

```
Xbox Controller Input
        │  pygame joystick events
Control Script (Python)
        │  reads LowState, writes LowCmd via DDS
Unitree SDK2-Python (ChannelPublisher/Subscriber)
        │  DDS topics: rt/lowcmd, rt/lowstate, rt/sportmodestate
CycloneDDS 0.10.2 (pub/sub, loopback for sim)
        │
UnitreeSdk2Bridge (simulator-side DDS adapter)
        │  maps MuJoCo motor state ↔ DDS messages
MuJoCo 3.3.6 (physics, sensors, MJCF models)
        │
Robot MJCF models (unitree_robots/g1/)
```

### Key Source Files
- `src/g1_mujoco_bridge/` — DDS LowState → /joint_states, /imu ROS2 브리지
- `src/g1_teleop/` — Xbox 컨트롤러 → G1 제어 ROS2 패키지
- `src/g1_teleop/g1_teleop/g1_joystick_controller.py` — 조이스틱 제어 (DDS 직접, ROS2 노드로 전환 예정)
- `external/unitree_mujoco/simulate/src/unitree_sdk2_bridge.h` — MuJoCo ↔ DDS 변환
- `external/unitree_mujoco/simulate_python/unitree_mujoco.py` — Python 시뮬레이터

### DDS Message Types
- **unitree_hg IDL**: G1, H1-2 — 35 motor indices (29 active DOF on G1)
- **unitree_go IDL**: Go2, B2, H1, B2w — 20 motors

### Domain ID Convention
- `domain_id=1`, `interface=lo` → simulation
- `domain_id=0`, `interface=enp*` → real robot (미보유, 추후)

## Configuration

### C++ Simulator — `unitree_mujoco/simulate/config.yaml`
```yaml
robot: "g1"
robot_scene: "scene.xml"
domain_id: 1          # 1=simulation
interface: "lo"
use_joystick: 0
```

### Python Simulator — `unitree_mujoco/simulate_python/config.py`
```python
ROBOT = "g1"
DOMAIN_ID = 1
INTERFACE = "lo"
SIMULATE_DT = 0.005   # Physics timestep (5ms)
```

## G1 Motor Index Reference
`unitree_mujoco/unitree_robots/g1/g1_joint_index_dds.md`:
- Indices 0–13: legs
- Indices 14–27: arms
- Indices 28–34: head/torso

## Dependencies
- **MuJoCo 3.3.6** — symlinked at `unitree_mujoco/simulate/mujoco-3.3.6/`
- **unitree_sdk2** — `/opt/unitree_robotics/`
- **CycloneDDS 0.10.2** — `cyclonedds/`, Python: `third_party/unitree_sdk2_python/`
- **Python**: mujoco, pygame, numpy, opencv-python, cyclonedds==0.10.2

## Dev Conventions
- 시뮬레이터 검증 먼저 — 실물 로봇 테스트 전 MuJoCo에서 확인
- 관절 파라미터는 YAML만 — 소스코드 하드코딩 금지
- 커밋은 명시적 요청 시에만
- **패키지 설치는 `uv pip install`** — `pip install` 사용 금지

## Compact Instructions
Preserve on compaction:
1. Hard Rules (project-specific + ai-constitution.md reference)
2. Current active branch / uncommitted file list
3. Pending tasks and their status
4. Active errors or bugs being investigated
5. Dev Conventions
6. File paths modified in this session
