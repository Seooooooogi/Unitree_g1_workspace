# g1_workspace

Unitree G1 humanoid robot simulation and control — MuJoCo physics + ROS2 Humble.

**목표**: Xbox 컨트롤러로 G1 시뮬레이터 보행 제어 → 티칭 데이터 수집 → 강화학습 배포 검토

> 실물 로봇 미보유. 모든 테스트는 MuJoCo 시뮬레이터 기준.

---

## Architecture

```
Xbox Controller (USB)
        │  pygame joystick events
        ▼
┌─────────────────────┐
│   g1_teleop (ROS2)  │  ← src/g1_teleop/
│  joystick_controller│
└────────┬────────────┘
         │  unitree_hg/msg/LowCmd  (DDS rt/lowcmd)
         ▼
┌─────────────────────────────────┐
│  MuJoCo Simulator               │  ← external/unitree_mujoco/
│  (Python or C++)                │
│  UnitreeSdk2Bridge              │
└────────┬────────────────────────┘
         │  unitree_hg/msg/LowState  (DDS rt/lowstate)
         ▼
┌──────────────────────────┐
│  g1_mujoco_bridge (ROS2) │  ← src/g1_mujoco_bridge/
└──────┬───────────────────┘
       │
       ├─▶  /joint_states  (sensor_msgs/JointState)
       └─▶  /imu           (sensor_msgs/Imu)
```

**DDS Domain**: `domain_id=1`, `interface=lo` (loopback, 시뮬레이터 전용)

---

## Directory Structure

```
g1_workspace/
├── src/
│   ├── g1_mujoco_bridge/        # DDS LowState → ROS2 /joint_states, /imu
│   │   ├── g1_mujoco_bridge/
│   │   │   ├── bridge_node.py
│   │   │   └── joint_names.py   # G1 23/29DOF 관절 이름 매핑
│   │   └── launch/bridge.launch.py
│   └── g1_teleop/               # Xbox 컨트롤러 → G1 제어
│       ├── g1_teleop/
│       │   ├── g1_joystick_controller.py  # DDS 직접 제어 (ROS2 노드 전환 예정)
│       │   └── arm_low_basic.py
│       └── scripts/             # 수동 진단 스크립트 (DDS 연결 필요)
│           ├── test_g1_connection.py
│           ├── test_dds_topics.py
│           └── test_lowstate.py
├── external/                    # 비-ROS2 소스 (수정 금지)
│   ├── unitree_mujoco/          # MuJoCo 시뮬레이터
│   ├── cyclonedds/              # CycloneDDS 0.10.2 소스
│   └── third_party/             # unitree_sdk2_python
├── envs/                        # Python 가상환경 (unitree_g1)
├── build/ install/ log/         # colcon 빌드 산출물
├── docs/
│   └── DEVELOPMENT_ROADMAP.md
└── memory/                      # 세션 간 컨텍스트
```

---

## Prerequisites

| 항목 | 버전 |
|------|------|
| Ubuntu | 22.04 |
| ROS2 | Humble |
| MuJoCo | 3.3.6 (symlinked) |
| CycloneDDS | 0.10.2 |
| Python | 3.10 |
| unitree_ros2 | `~/unitree_ros2/` |

---

## Setup

### 0. 외부 패키지 클론 (최초 1회)

이 저장소는 아래 외부 패키지를 포함하지 않습니다. 직접 클론하세요.

```bash
cd ~/g1_workspace

# MuJoCo 시뮬레이터 (Unitree)
git clone https://github.com/unitreerobotics/unitree_mujoco external/unitree_mujoco

# CycloneDDS 0.10.2
git clone -b 0.10.2 https://github.com/eclipse-cyclonedds/cyclonedds.git external/cyclonedds

# unitree_sdk2_python
mkdir -p external/third_party
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git external/third_party/unitree_sdk2_python
```

### 1. unitree_ros2 메시지 패키지 빌드 (최초 1회)

```bash
sudo apt install ros-humble-rmw-cyclonedds-cpp ros-humble-rosidl-generator-dds-idl libyaml-cpp-dev

git clone https://github.com/unitreerobotics/unitree_ros2 ~/unitree_ros2
cd ~/unitree_ros2/cyclonedds_ws
bash -c "source /opt/ros/humble/setup.bash && colcon build --packages-select unitree_go unitree_hg unitree_api"
```

### 2. 워크스페이스 빌드

```bash
cd ~/g1_workspace
bash -c "
  source /opt/ros/humble/setup.bash &&
  source ~/unitree_ros2/cyclonedds_ws/install/setup.bash &&
  colcon build
"
```

### 3. 환경 변수 설정 (매 터미널마다)

```bash
source /opt/ros/humble/setup.bash
source ~/unitree_ros2/cyclonedds_ws/install/setup.bash
source ~/g1_workspace/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI='<CycloneDDS><Domain><General><Interfaces>
    <NetworkInterface name="lo" priority="default" multicast="default" />
</Interfaces></General></Domain></CycloneDDS>'
```

> **팁**: 위 내용을 `~/.bashrc`에 추가하거나 별도 `env.sh`로 저장해 `source env.sh`로 사용하세요.

---

## Running

### 터미널 구성 (3개)

**Terminal 1 — MuJoCo 시뮬레이터 실행**

```bash
# Python 시뮬레이터
cd ~/g1_workspace/external/unitree_mujoco/simulate_python
python3 unitree_mujoco.py

# 또는 C++ 시뮬레이터
~/g1_workspace/external/unitree_mujoco/simulate/build/unitree_mujoco
```

시뮬레이터 설정: `external/unitree_mujoco/simulate_python/config.py`
```python
ROBOT = "g1"
DOMAIN_ID = 1
INTERFACE = "lo"
USE_JOYSTICK = 1        # Xbox 컨트롤러 활성화
JOYSTICK_TYPE = "xbox"
```

**Terminal 2 — ROS2 Bridge 실행**

```bash
cd ~/g1_workspace
source install/setup.bash
ros2 launch g1_mujoco_bridge bridge.launch.py dof_mode:=29
```

`/joint_states`, `/imu` 토픽 확인:
```bash
ros2 topic echo /joint_states
ros2 topic echo /imu
```

**Terminal 3 — 조이스틱 컨트롤러 실행**

```bash
# ROS2 노드 (전환 완료 후)
ros2 run g1_teleop joystick_controller

# 또는 DDS 직접 (현재)
cd ~/g1_workspace/src/g1_teleop/g1_teleop
python3 g1_joystick_controller.py
```

---

## Xbox Controller Mapping

| 입력 | 동작 |
|------|------|
| 왼쪽 스틱 Y | 허리 Pitch (앞/뒤) |
| 왼쪽 스틱 X | 허리 Yaw (좌/우 회전) |
| 오른쪽 스틱 Y | 양팔 Shoulder Pitch |
| 오른쪽 스틱 X | 양팔 Shoulder Roll |
| START | 컨트롤 활성화/비활성화 토글 |

> 보행 제어 매핑은 구현 후 업데이트 예정 (ROADMAP 2-2)

---

## Tests

```bash
cd ~/g1_workspace
source install/setup.bash
python3 -m pytest src/g1_mujoco_bridge/test/ -v
```

수동 진단 스크립트 (시뮬레이터 실행 후):
```bash
cd src/g1_teleop/scripts
python3 test_g1_connection.py       # DDS 연결 확인
python3 test_dds_topics.py          # 토픽 목록 확인
python3 test_lowstate.py            # LowState 수신 확인
```

---

## G1 Motor Index (29DOF)

| 인덱스 | 관절 | 인덱스 | 관절 |
|--------|------|--------|------|
| 0–5 | 왼쪽 다리 (Hip×3, Knee, Ankle×2) | 6–11 | 오른쪽 다리 |
| 12–14 | 허리 (Yaw, Roll, Pitch) | 15–21 | 왼쪽 팔 |
| 22–28 | 오른쪽 팔 | | |

전체 매핑: `external/unitree_mujoco/unitree_robots/g1/g1_joint_index_dds.md`

---

## Dependencies

| 패키지 | 위치 | 용도 |
|--------|------|------|
| unitree_ros2 | `~/unitree_ros2/` | ROS2 메시지 (unitree_hg, unitree_go, unitree_api) |
| unitree_sdk2_python | `external/third_party/` | DDS Python 바인딩 |
| MuJoCo 3.3.6 | `external/unitree_mujoco/simulate/mujoco-3.3.6/` | 물리 시뮬레이터 |
| CycloneDDS 0.10.2 | `external/cyclonedds/` | DDS 미들웨어 소스 |
