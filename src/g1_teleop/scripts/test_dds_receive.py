import sys
sys.path.insert(0, '/home/rokey/g1_workspace/third_party/unitree_sdk2_python')

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
import time

ChannelFactoryInitialize(1, "lo")

received = []
def cb(msg): received.append(msg)

sub = ChannelSubscriber("rt/lowstate", LowState_)
sub.Init(cb, 10)

time.sleep(3)
print(f"수신된 메시지: {len(received)}개")
