import sys
import time
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_

def LowStateHandler(msg: LowState_):
    print(f"[G1] IMU gyroscope: {msg.imu_state.gyroscope}")
    print(f"[G1] motor[0] q: {msg.motor_state[0].q:.4f}")

if __name__ == "__main__":
    interface  = sys.argv[1] if len(sys.argv) > 1 else "lo"
    domain_id  = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    ChannelFactoryInitialize(domain_id, interface)

    sub = ChannelSubscriber("rt/lowstate", LowState_)
    sub.Init(LowStateHandler, 10)

    print(f"G1 통신 테스트 시작 (interface={interface}, domain_id={domain_id})")
    print("데이터 수신 대기 중... (Ctrl+C로 종료)")
    while True:
        time.sleep(1)
