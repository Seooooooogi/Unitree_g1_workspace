import time
from unitree_sdk2py.core.channel import (
    ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
)
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_ as hg_LowCmd
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_ as hg_LowState
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.utils.crc import CRC

TOPIC_LOW_CMD   = "rt/lowcmd"
TOPIC_LOW_STATE = "rt/lowstate"

G1_NUM_MOTORS = 29

class ArmIdx:
    L_SHOULDER_PITCH = 15
    L_SHOULDER_ROLL  = 16
    L_SHOULDER_YAW   = 17
    L_ELBOW          = 18
    
    R_SHOULDER_PITCH = 22
    R_SHOULDER_ROLL  = 23
    R_SHOULDER_YAW   = 24
    R_ELBOW          = 25

current_state = None
crc = CRC()
init_q = []  # 자연스러운 초기 자세를 저장할 리스트

def low_state_callback(msg: hg_LowState):
    global current_state
    current_state = msg

def send_pose(pub, joint_targets: dict):
    global init_q
    cmd = unitree_hg_msg_dds__LowCmd_()
    cmd.mode_pr = 0
    cmd.mode_machine = 0
    # send_pose 함수 내부 수정 예시
    for i in range(29):
	    cmd.motor_cmd[i].mode = 0x01
	    cmd.motor_cmd[i].dq = 0.0
	    cmd.motor_cmd[i].tau = 0.0
		
		# 허리 관절 (12, 13, 14번)은 무조건 0으로 펴기
	    if 12 <= i <= 14:
		    cmd.motor_cmd[i].q = 0.0
		    cmd.motor_cmd[i].kp = 250.0  # 허리를 펴는 힘을 강하게
		    cmd.motor_cmd[i].kd = 10.0
	    else:
		    cmd.motor_cmd[i].q = init_q[i]
		    cmd.motor_cmd[i].kp = 100.0
		    cmd.motor_cmd[i].kd = 5.0

    # 2. 움직일 팔 관절만 목표 각도로 덮어쓰기
    for idx, q in joint_targets.items():
        cmd.motor_cmd[idx].q  = q
        
    cmd.crc = crc.Crc(cmd)
    pub.Write(cmd)

def move_to_pose(pub, target_joints: dict, duration=2.0, dt=0.002):
    global current_state
    start_q = {idx: current_state.motor_state[idx].q for idx in target_joints}
    steps = int(duration / dt)

    for i in range(steps):
        alpha = i / steps
        interp = {idx: start_q[idx] + alpha * (target_joints[idx] - start_q[idx])
                  for idx in target_joints}
        send_pose(pub, interp)
        time.sleep(dt)

def hold_pose(pub, target_joints: dict, duration=1.0, dt=0.002):
    steps = int(duration / dt)
    for _ in range(steps):
        send_pose(pub, target_joints)
        time.sleep(dt)

def main():
    global init_q
    ChannelFactoryInitialize(0, "lo")

    pub = ChannelPublisher(TOPIC_LOW_CMD, hg_LowCmd)
    pub.Init()

    sub = ChannelSubscriber(TOPIC_LOW_STATE, hg_LowState)
    sub.Init(low_state_callback, 10)

    print("초기화 완료. lowstate 수신 대기 중...")
    time.sleep(1.0)

    if current_state is None:
        print("[오류] lowstate를 받지 못했습니다.")
        return

    # ✅ 핵심: 시뮬레이터가 켜졌을 때의 자연스러운 관절값을 초기값으로 저장!
    init_q = [current_state.motor_state[i].q for i in range(G1_NUM_MOTORS)]

    # ── 동작 0: 현재 자세 안정화 (1초 대기) ──
    print("\n[0] 초기 자세 안정화 (떨림 방지)...")
    hold_pose(pub, {}, duration=1.0)

    # ── 동작 1: 양팔 앞으로 뻗기 ──
    print("\n[1] 양팔 앞으로 쭉 뻗기...")
    pose1 = {
        ArmIdx.L_SHOULDER_PITCH: -1.5,
        ArmIdx.R_SHOULDER_PITCH: -1.5,
        ArmIdx.L_ELBOW:          0.0,
        ArmIdx.R_ELBOW:          0.0,
    }
    move_to_pose(pub, pose1, duration=2.0)
    hold_pose(pub, pose1, duration=2.0)

    # ── 동작 1.5: 팔이 꼬이지 않게 차려 자세 거치기 ──
    print("\n[복귀] 차려 자세로 돌아오기...")
    pose_home = {
        ArmIdx.L_SHOULDER_PITCH: 0.0,
        ArmIdx.R_SHOULDER_PITCH: 0.0,
        ArmIdx.L_SHOULDER_ROLL:  0.0,
        ArmIdx.R_SHOULDER_ROLL:  0.0,
        ArmIdx.L_ELBOW:          0.0,
        ArmIdx.R_ELBOW:          0.0,
    }
    move_to_pose(pub, pose_home, duration=1.5)

    # ── 동작 2: 양팔 옆으로 벌리기 (T포즈) ──
    print("\n[2] 양팔 옆으로 벌리기 (T포즈)...")
    pose2 = {
        ArmIdx.L_SHOULDER_PITCH: 0.0,
        ArmIdx.R_SHOULDER_PITCH: 0.0,
        ArmIdx.L_SHOULDER_ROLL:  1.5,
        ArmIdx.R_SHOULDER_ROLL: -1.5,
        ArmIdx.L_ELBOW:          0.0,
        ArmIdx.R_ELBOW:          0.0,
    }
    move_to_pose(pub, pose2, duration=2.0)
    hold_pose(pub, pose2, duration=2.0)

    # ── 동작 3: 최종 차려 자세 ──
    print("\n[3] 최종 차려 자세 복귀...")
    move_to_pose(pub, pose_home, duration=2.0)
    hold_pose(pub, pose_home, duration=1.0)

    print("\n✅ T자 자세 완벽 제어 성공!")

if __name__ == "__main__":
    main()
