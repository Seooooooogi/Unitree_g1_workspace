"""
G1 Joystick Controller
======================
- 조이스틱으로 G1 허리/팔을 조작합니다.
- unitree_mujoco 시뮬레이터가 먼저 실행 중이어야 합니다.

실행:
    python3 g1_joystick_controller.py

조이스틱 매핑 (Xbox):
    왼쪽 스틱 Y  → 허리 Pitch (앞/뒤 기울기)
    왼쪽 스틱 X  → 허리 Yaw (좌/우 회전)
    오른쪽 스틱 Y → 양팔 Shoulder Pitch (앞으로/뒤로)
    오른쪽 스틱 X → 양팔 Shoulder Roll (벌리기/모으기)
    START 버튼   → 컨트롤 활성화/비활성화 토글
"""

import time
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
NUM_ACTIVE = 29          # G1 29DoF 활성 모터
DT = 0.002               # 제어 주기 500Hz

# 관절 인덱스 (29DoF 기준)
IDX_WAIST_YAW    = 12
IDX_WAIST_PITCH  = 14
IDX_L_SHO_PITCH  = 15
IDX_L_SHO_ROLL   = 16
IDX_R_SHO_PITCH  = 22
IDX_R_SHO_ROLL   = 23

# PD 게인
KP_LEG   = 60.0;  KD_LEG   = 12.0
KP_WAIST = 50.0;  KD_WAIST = 8.0
KP_ARM   = 25.0;  KD_ARM   = 5.0

# 조이스틱 스케일
JS_WAIST_SCALE = 0.30
JS_ARM_SCALE   = 0.50

# ── 전역 상태 ─────────────────────────────────────────
g_lowstate: LowState_ = None
g_joystick: WirelessController_ = None
g_active = True

crc = CRC()

KEY_START = (1 << 7)


def on_lowstate(msg: LowState_):
    global g_lowstate
    g_lowstate = msg


def on_wireless(msg: WirelessController_):
    global g_joystick, g_active
    prev = g_joystick
    g_joystick = msg
    if prev is not None:
        was_pressed = bool(prev.keys & KEY_START)
        now_pressed = bool(msg.keys & KEY_START)
        if now_pressed and not was_pressed:
            g_active = not g_active
            print(f"[조이스틱] 컨트롤 {'활성화' if g_active else '비활성화'}")


def make_cmd(target_q: np.ndarray) -> LowCmd_:
    cmd = unitree_hg_msg_dds__LowCmd_()
    for i in range(NUM_ACTIVE):
        mc = cmd.motor_cmd[i]
        mc.mode = 1
        mc.q    = float(target_q[i])
        mc.dq   = 0.0
        mc.tau  = 0.0
        if i < 12:
            mc.kp = KP_LEG;   mc.kd = KD_LEG
        elif i < 15:
            mc.kp = KP_WAIST; mc.kd = KD_WAIST
        else:
            mc.kp = KP_ARM;   mc.kd = KD_ARM
    cmd.crc = crc.Crc(cmd)
    return cmd


def main():
    ChannelFactoryInitialize(1, "lo")

    pub = ChannelPublisher("rt/lowcmd", LowCmd_)
    pub.Init()

    sub_state = ChannelSubscriber("rt/lowstate", LowState_)
    sub_state.Init(on_lowstate, 10)

    sub_js = ChannelSubscriber("rt/wirelesscontroller", WirelessController_)
    sub_js.Init(on_wireless, 10)

    print("상태 수신 대기 중...")
    timeout = 5.0
    t0 = time.time()
    while g_lowstate is None and time.time() - t0 < timeout:
        time.sleep(0.05)
    if g_lowstate is None:
        print("[오류] lowstate 수신 실패. 시뮬레이터가 실행 중인지 확인하세요.")
        return

    print("수신 완료. 조이스틱으로 허리/팔을 조작하세요. Ctrl+C로 종료.")

    base_q = np.array([g_lowstate.motor_state[i].q for i in range(NUM_ACTIVE)])

    try:
        while True:
            t_start = time.perf_counter()

            if g_active:
                lx = ly = rx = ry = 0.0
                if g_joystick is not None:
                    lx = float(g_joystick.lx)
                    ly = float(g_joystick.ly)
                    rx = float(g_joystick.rx)
                    ry = float(g_joystick.ry)

                target = base_q.copy()
                target[IDX_WAIST_YAW]   += lx * JS_WAIST_SCALE
                target[IDX_WAIST_PITCH] += ly * JS_WAIST_SCALE
                target[IDX_L_SHO_PITCH] += ry * JS_ARM_SCALE
                target[IDX_R_SHO_PITCH] += ry * JS_ARM_SCALE
                target[IDX_L_SHO_ROLL]  += rx * JS_ARM_SCALE * 0.5
                target[IDX_R_SHO_ROLL]  -= rx * JS_ARM_SCALE * 0.5

                pub.Write(make_cmd(target))

            elapsed = time.perf_counter() - t_start
            remaining = DT - elapsed
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        print("\n종료 중...")
        cmd = unitree_hg_msg_dds__LowCmd_()
        cmd.crc = crc.Crc(cmd)
        pub.Write(cmd)
        print("완료.")


if __name__ == "__main__":
    main()
