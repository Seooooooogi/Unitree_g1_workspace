"""
Unit tests for bridge node message conversion logic.
Uses mock objects — no ROS2 spin or DDS connection required.
"""
import pytest
from unittest.mock import MagicMock, patch
from g1_mujoco_bridge.joint_names import G1_29DOF_JOINT_NAMES


def _make_motor_state(q, dq, tau_est):
    m = MagicMock()
    m.q = q
    m.dq = dq
    m.tau_est = tau_est
    return m


def _make_imu_state(quaternion, gyroscope, accelerometer):
    imu = MagicMock()
    imu.quaternion = quaternion
    imu.gyroscope = gyroscope
    imu.accelerometer = accelerometer
    return imu


def _make_low_state(n_motors=29):
    msg = MagicMock()
    msg.motor_state = [
        _make_motor_state(q=float(i) * 0.01, dq=float(i) * 0.001, tau_est=0.0)
        for i in range(35)
    ]
    msg.imu_state = _make_imu_state(
        quaternion=[1.0, 0.0, 0.0, 0.0],
        gyroscope=[0.1, 0.2, 0.3],
        accelerometer=[0.0, 0.0, 9.81],
    )
    return msg


class TestJointStateConversion:
    """Test the joint state extraction logic."""

    def test_position_order_matches_joint_names(self):
        msg = _make_low_state()
        n = len(G1_29DOF_JOINT_NAMES)
        positions = [msg.motor_state[i].q for i in range(n)]
        assert len(positions) == 29
        assert positions[0] == pytest.approx(0.0)
        assert positions[1] == pytest.approx(0.01)

    def test_velocity_extracted_correctly(self):
        msg = _make_low_state()
        n = len(G1_29DOF_JOINT_NAMES)
        velocities = [msg.motor_state[i].dq for i in range(n)]
        assert velocities[0] == pytest.approx(0.0)
        assert velocities[1] == pytest.approx(0.001)

    def test_effort_extracted_correctly(self):
        msg = _make_low_state()
        n = len(G1_29DOF_JOINT_NAMES)
        efforts = [msg.motor_state[i].tau_est for i in range(n)]
        assert all(e == pytest.approx(0.0) for e in efforts)

    def test_joint_names_length_matches_motor_count(self):
        assert len(G1_29DOF_JOINT_NAMES) == 29


class TestImuConversion:
    """Test IMU data extraction logic."""

    def test_quaternion_extracted(self):
        msg = _make_low_state()
        q = msg.imu_state.quaternion
        assert float(q[0]) == pytest.approx(1.0)  # w
        assert float(q[1]) == pytest.approx(0.0)  # x
        assert float(q[2]) == pytest.approx(0.0)  # y
        assert float(q[3]) == pytest.approx(0.0)  # z

    def test_gyroscope_extracted(self):
        msg = _make_low_state()
        g = msg.imu_state.gyroscope
        assert float(g[0]) == pytest.approx(0.1)
        assert float(g[1]) == pytest.approx(0.2)
        assert float(g[2]) == pytest.approx(0.3)

    def test_accelerometer_extracted(self):
        msg = _make_low_state()
        a = msg.imu_state.accelerometer
        assert float(a[2]) == pytest.approx(9.81)
