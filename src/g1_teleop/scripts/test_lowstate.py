# check_lowstate.py — DDS 통신 진단용
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_ as hg_LowState
import time

def cb(msg):
    print(f"수신 ✅  관절0: {msg.motor_state[0].q:.4f} | 관절14: {msg.motor_state[14].q:.4f}")

ChannelFactoryInitialize(0, "lo")
sub = ChannelSubscriber("rt/lowstate", hg_LowState)
sub.Init(cb, 10)

print("lowstate 수신 대기 중... (Ctrl+C로 종료)")
while True:
    time.sleep(1)
