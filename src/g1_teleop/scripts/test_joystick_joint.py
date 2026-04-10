"""
G1 조이스틱 → 관절 매핑 테스트
================================
버튼을 누르면 해당 관절이 움직이며, 꾹 누르면 연속으로 동작합니다.
시뮬레이터(unitree_mujoco.py)가 먼저 실행 중이어야 합니다.

[ 아날로그 스틱 — 연속 ]
    좌스틱 X   → 허리 좌우 회전     (WAIST_YAW)
    좌스틱 Y   → 허리 앞뒤 기울기   (WAIST_PITCH)
    우스틱 X   → 양팔 어깨 좌우     (L/R SHOULDER_ROLL, 반대방향)
    우스틱 Y   → 양팔 어깨 앞뒤     (L/R SHOULDER_PITCH)

[ 페이스 버튼 — 팔꿈치 ]
    A          → 왼쪽 팔꿈치 굽힘   (L_ELBOW +)
    X          → 왼쪽 팔꿈치 펴기   (L_ELBOW -)
    B          → 오른쪽 팔꿈치 굽힘  (R_ELBOW +)
    Y          → 오른쪽 팔꿈치 펴기  (R_ELBOW -)

[ 숄더 버튼 — 다리 ]
    L1         → 양쪽 무릎 굽힘 (쪼그리기)
    R1         → 양쪽 무릎 펴기 (일어서기)
    L2         → 왼쪽 엉덩이 앞뒤   (L_HIP_PITCH +)
    R2         → 오른쪽 엉덩이 앞뒤  (R_HIP_PITCH +)

[ D패드 — 허리 롤 / 엉덩이 롤 ]
    위         → 허리 오른쪽 기울기  (WAIST_ROLL +)
    아래       → 허리 왼쪽 기울기    (WAIST_ROLL -)
    왼쪽       → 왼쪽 엉덩이 좌우    (L_HIP_ROLL +)
    오른쪽     → 오른쪽 엉덩이 좌우  (R_HIP_ROLL +)
"""

import time
import sys
sys.path.insert(0, '/home/rokey/g1_workspace/external/third_party/unitree_sdk2_python')

import numpy as np
from unitree_sdk2py.core.channel import (
    ChannelPublisher,
    ChannelSubscriber,
    ChannelFactoryInitialize,
)
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import WirelessController_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.utils.crc import CRC

# ── 상수 ─────────────────────────────────────────────
NUM_ACTIVE    = 29
DT            = 0.002   # 500Hz
STEP          = 0.03    # 1회 이동량 (rad)
AXIS_SCALE    = 1.5     # 스틱 스케일 (rad/s 단위, DT 곱해서 적용)

HOLD_DELAY    = 0.3     # 꾹 누르기 시작까지 대기 시간 (초)
HOLD_INTERVAL = 0.05    # 꾹 누를 때 스텝 간격 (초)
AXIS_PRINT_INTERVAL = 0.2  # 스틱 출력 간격 (초, 너무 많이 찍히지 않도록)

# key_map 비트 위치 (unitree_sdk2py_bridge.py 기준)
KEY_R1     = (1 << 0)
KEY_L1     = (1 << 1)
KEY_SELECT = (1 << 3)
KEY_R2     = (1 << 4)
KEY_L2     = (1 << 5)
KEY_A      = (1 << 8)
KEY_B      = (1 << 9)
KEY_X      = (1 << 10)
KEY_Y      = (1 << 11)
KEY_UP     = (1 << 12)
KEY_RIGHT  = (1 << 13)
KEY_DOWN   = (1 << 14)
KEY_LEFT   = (1 << 15)

# PD 게인 (공중 매달린 상태 기준)
KP_LEG    = 500.0; KD_LEG    = 20.0
KP_ANKLE  = 100.0; KD_ANKLE  = 40.0   # 발목: Kp 낮추고 Kd 높여 떨림 억제
KP_WAIST  = 100.0; KD_WAIST  = 6.0
KP_ARM    = 100.0; KD_ARM    = 5.0

# 발목 관절 인덱스: L_ANKLE_PITCH(4), L_ANKLE_ROLL(5), R_ANKLE_PITCH(10), R_ANKLE_ROLL(11)
ANKLE_IDX = {4, 5, 10, 11}

# 스탠딩 자세
STAND_POSE = np.zeros(NUM_ACTIVE)
STAND_POSE[0]  = -0.05  # L_HIP_PITCH
STAND_POSE[6]  = -0.05  # R_HIP_PITCH
STAND_POSE[3]  =  0.15  # L_KNEE
STAND_POSE[9]  =  0.15  # R_KNEE
STAND_POSE[4]  = -0.10  # L_ANKLE_PITCH
STAND_POSE[10] = -0.10  # R_ANKLE_PITCH

crc = CRC()
g_lowstate: LowState_ = None
g_joystick: WirelessController_ = None


def on_lowstate(msg: LowState_):
    global g_lowstate
    g_lowstate = msg


def on_wireless(msg: WirelessController_):
    global g_joystick
    g_joystick = msg


def make_cmd(target_q: np.ndarray) -> LowCmd_:
    cmd = unitree_hg_msg_dds__LowCmd_()
    for i in range(NUM_ACTIVE):
        mc = cmd.motor_cmd[i]
        mc.mode = 1
        mc.q    = float(target_q[i])
        mc.dq   = 0.0
        mc.tau  = 0.0
        if i in ANKLE_IDX:
            mc.kp = KP_ANKLE; mc.kd = KD_ANKLE
        elif i < 12:
            mc.kp = KP_LEG;   mc.kd = KD_LEG
        elif i < 15:
            mc.kp = KP_WAIST; mc.kd = KD_WAIST
        else:
            mc.kp = KP_ARM;   mc.kd = KD_ARM
    cmd.crc = crc.Crc(cmd)
    return cmd


def log(button: str, part: str, joint: str, idx: int, val: float):
    arrow = "▲" if val >= 0 else "▼"
    print(f"  [{button:<5}]  {arrow} {part:<20} ({joint}, 관절 {idx:2d})  →  {val:+.3f} rad", flush=True)


def main():
    ChannelFactoryInitialize(1, "lo")

    pub = ChannelPublisher("rt/lowcmd", LowCmd_)
    pub.Init()

    sub_state = ChannelSubscriber("rt/lowstate", LowState_)
    sub_state.Init(on_lowstate, 10)

    sub_js = ChannelSubscriber("rt/wirelesscontroller", WirelessController_)
    sub_js.Init(on_wireless, 10)

    print("상태 수신 대기 중...")
    t0 = time.time()
    while g_lowstate is None and time.time() - t0 < 5.0:
        time.sleep(0.05)
    if g_lowstate is None:
        print("[오류] lowstate 수신 실패. 시뮬레이터가 실행 중인지 확인하세요.")
        return

    target_q = STAND_POSE.copy()
    print("조이스틱으로 조작하세요. Ctrl+C로 종료.\n")

    # 꾹 누르기 상태 추적: key_mask → (처음 누른 시각, 마지막 스텝 시각)
    hold_state: dict[int, tuple[float, float]] = {}
    prev_keys = 0
    last_axis_print = 0.0

    # 버튼 → (관절 인덱스, 변화량, 표시 이름, 관절명)
    BUTTON_MAP = [
        (KEY_A,     18,  +STEP, "A    ", "왼쪽 팔꿈치 굽힘 ",  "L_ELBOW"),
        (KEY_X,     18,  -STEP, "X    ", "왼쪽 팔꿈치 펴기 ",  "L_ELBOW"),
        (KEY_B,     25,  +STEP, "B    ", "오른쪽 팔꿈치 굽힘", "R_ELBOW"),
        (KEY_Y,     25,  -STEP, "Y    ", "오른쪽 팔꿈치 펴기", "R_ELBOW"),
        (KEY_L1,    [3, 9],  +STEP, "L1   ", "양쪽 무릎 굽힘  ",  "L/R_KNEE"),
        (KEY_R1,    [3, 9],  -STEP, "R1   ", "양쪽 무릎 펴기  ",  "L/R_KNEE"),
        (KEY_L2,    0,   +STEP, "L2   ", "왼쪽 엉덩이 앞뒤 ", "L_HIP_PITCH"),
        (KEY_R2,    6,   +STEP, "R2   ", "오른쪽 엉덩이 앞뒤", "R_HIP_PITCH"),
        (KEY_UP,    13,  +STEP, "↑    ", "허리 오른쪽 기울기", "WAIST_ROLL"),
        (KEY_DOWN,  13,  -STEP, "↓    ", "허리 왼쪽 기울기 ", "WAIST_ROLL"),
        (KEY_LEFT,  1,   +STEP, "←    ", "왼쪽 엉덩이 롤  ",  "L_HIP_ROLL"),
        (KEY_RIGHT, 7,   +STEP, "→    ", "오른쪽 엉덩이 롤",  "R_HIP_ROLL"),
    ]

    try:
        while True:
            t_start = time.perf_counter()
            now = t_start

            js = g_joystick
            if js is not None:
                keys = js.keys
                lx = float(js.lx)
                ly = float(js.ly)
                rx = float(js.rx)
                ry = float(js.ry)

                # ── 버튼 처리 (첫 누름 + 꾹 누르기) ──────────────
                for entry in BUTTON_MAP:
                    key_mask, idx, delta, btn, part, joint = entry
                    if keys & key_mask:
                        if key_mask not in hold_state:
                            # 첫 누름: 즉시 1회 동작
                            hold_state[key_mask] = (now, now)
                            if isinstance(idx, list):
                                for i in idx:
                                    target_q[i] += delta
                                log(btn, part, joint, idx[0], target_q[idx[0]])
                            else:
                                target_q[idx] += delta
                                log(btn, part, joint, idx, target_q[idx])
                        else:
                            first_t, last_t = hold_state[key_mask]
                            # HOLD_DELAY 이후 HOLD_INTERVAL마다 연속 동작
                            if (now - first_t > HOLD_DELAY and
                                    now - last_t > HOLD_INTERVAL):
                                hold_state[key_mask] = (first_t, now)
                                if isinstance(idx, list):
                                    for i in idx:
                                        target_q[i] += delta
                                else:
                                    target_q[idx] += delta
                    else:
                        hold_state.pop(key_mask, None)

                # ── SELECT: 스탠딩 자세로 리셋 ───────────────────
                if (keys & KEY_SELECT) and not (prev_keys & KEY_SELECT):
                    target_q = STAND_POSE.copy()
                    hold_state.clear()
                    print("  [SELECT] ↺ 스탠딩 자세로 리셋", flush=True)

                # ── 스틱 (연속) ───────────────────────────────────
                stick_active = []
                if abs(lx) > 0.1:
                    target_q[12] += lx * AXIS_SCALE * DT
                    stick_active.append(f"좌X({lx:+.2f})→허리 좌우={target_q[12]:+.3f}")
                if abs(ly) > 0.1:
                    target_q[14] += ly * AXIS_SCALE * DT
                    stick_active.append(f"좌Y({ly:+.2f})→허리 앞뒤={target_q[14]:+.3f}")
                if abs(rx) > 0.1:
                    target_q[16] -= rx * AXIS_SCALE * DT
                    target_q[23] += rx * AXIS_SCALE * DT
                    stick_active.append(f"우X({rx:+.2f})→어깨 롤 L={target_q[16]:+.3f} R={target_q[23]:+.3f}")
                if abs(ry) > 0.1:
                    target_q[15] += ry * AXIS_SCALE * DT
                    target_q[22] += ry * AXIS_SCALE * DT
                    stick_active.append(f"우Y({ry:+.2f})→어깨 앞뒤 L={target_q[15]:+.3f} R={target_q[22]:+.3f}")

                if stick_active and now - last_axis_print > AXIS_PRINT_INTERVAL:
                    print("  [스틱] " + "  |  ".join(stick_active), flush=True)
                    last_axis_print = now

                prev_keys = keys
                pub.Write(make_cmd(target_q))

            elapsed = time.perf_counter() - t_start
            remaining = DT - elapsed
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        print("\n종료.")
        cmd = unitree_hg_msg_dds__LowCmd_()
        cmd.crc = crc.Crc(cmd)
        pub.Write(cmd)


if __name__ == "__main__":
    main()
