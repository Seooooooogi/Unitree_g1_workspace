import sys
sys.path.insert(0, '/home/rokey/g1_workspace/third_party/unitree_sdk2_python')

from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
from unitree_sdk2py.idl.unitree_go.msg.dds_ import WirelessController_, SportModeState_
import time

DOMAIN_ID = 1
INTERFACE = "lo"

ChannelFactoryInitialize(DOMAIN_ID, INTERFACE)

topics = {
    "rt/lowstate": {"sub": None, "count": 0},
    "rt/wirelesscontroller": {"sub": None, "count": 0},
    "rt/sportmodestate": {"sub": None, "count": 0},
}

def make_cb(name):
    def cb(msg):
        topics[name]["count"] += 1
    return cb

sub_lowstate = ChannelSubscriber("rt/lowstate", LowState_)
sub_lowstate.Init(make_cb("rt/lowstate"), 10)

sub_js = ChannelSubscriber("rt/wirelesscontroller", WirelessController_)
sub_js.Init(make_cb("rt/wirelesscontroller"), 10)

sub_sport = ChannelSubscriber("rt/sportmodestate", SportModeState_)
sub_sport.Init(make_cb("rt/sportmodestate"), 10)

print(f"3초간 수신 중... (domain_id={DOMAIN_ID}, interface={INTERFACE})")
time.sleep(3)

print("\n[결과]")
for topic, info in topics.items():
    status = "O" if info["count"] > 0 else "X"
    print(f"  [{status}] {topic}: {info['count']}개")
