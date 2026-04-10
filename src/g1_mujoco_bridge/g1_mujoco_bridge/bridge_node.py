"""
G1 MuJoCo Bridge Node

Subscribes to unitree_hg/msg/LowState (from MuJoCo via CycloneDDS)
and publishes:
  - /joint_states  (sensor_msgs/JointState)
  - /imu           (sensor_msgs/Imu)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import JointState, Imu
from std_msgs.msg import Header
from unitree_hg.msg import LowState

from .joint_names import G1_29DOF_JOINT_NAMES, G1_23DOF_JOINT_NAMES


class G1MuJoCoBridge(Node):
    def __init__(self):
        super().__init__('g1_mujoco_bridge')

        self.declare_parameter('dof_mode', 29)
        self.declare_parameter('lowstate_topic', 'lowstate')

        dof_mode = self.get_parameter('dof_mode').value
        lowstate_topic = self.get_parameter('lowstate_topic').value

        if dof_mode == 29:
            self.joint_names = G1_29DOF_JOINT_NAMES
        elif dof_mode == 23:
            self.joint_names = G1_23DOF_JOINT_NAMES
        else:
            self.get_logger().error(f'Unsupported dof_mode: {dof_mode}. Use 23 or 29.')
            raise ValueError(f'Invalid dof_mode: {dof_mode}')

        self.get_logger().info(
            f'G1 bridge starting — dof_mode={dof_mode}, topic={lowstate_topic}'
        )

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self.sub_lowstate = self.create_subscription(
            LowState,
            lowstate_topic,
            self._lowstate_callback,
            qos,
        )

        self.pub_joint_states = self.create_publisher(JointState, '/joint_states', 10)
        self.pub_imu = self.create_publisher(Imu, '/imu', 10)

    def _lowstate_callback(self, msg: LowState) -> None:
        now = self.get_clock().now().to_msg()
        self._publish_joint_states(msg, now)
        self._publish_imu(msg, now)

    def _publish_joint_states(self, msg: LowState, stamp) -> None:
        js = JointState()
        js.header = Header()
        js.header.stamp = stamp
        js.header.frame_id = 'base_link'

        n = len(self.joint_names)
        js.name = self.joint_names
        js.position = [msg.motor_state[i].q for i in range(n)]
        js.velocity = [msg.motor_state[i].dq for i in range(n)]
        js.effort = [msg.motor_state[i].tau_est for i in range(n)]

        self.pub_joint_states.publish(js)

    def _publish_imu(self, msg: LowState, stamp) -> None:
        imu = Imu()
        imu.header = Header()
        imu.header.stamp = stamp
        imu.header.frame_id = 'imu_link'

        q = msg.imu_state.quaternion
        imu.orientation.w = float(q[0])
        imu.orientation.x = float(q[1])
        imu.orientation.y = float(q[2])
        imu.orientation.z = float(q[3])

        g = msg.imu_state.gyroscope
        imu.angular_velocity.x = float(g[0])
        imu.angular_velocity.y = float(g[1])
        imu.angular_velocity.z = float(g[2])

        a = msg.imu_state.accelerometer
        imu.linear_acceleration.x = float(a[0])
        imu.linear_acceleration.y = float(a[1])
        imu.linear_acceleration.z = float(a[2])

        self.pub_imu.publish(imu)


def main(args=None):
    rclpy.init(args=args)
    node = G1MuJoCoBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
