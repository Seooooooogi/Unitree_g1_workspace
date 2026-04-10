"""
Unit tests for G1 joint name definitions.
No ROS2 or DDS required.
"""
import pytest
from g1_mujoco_bridge.joint_names import G1_29DOF_JOINT_NAMES, G1_23DOF_JOINT_NAMES


def test_29dof_count():
    assert len(G1_29DOF_JOINT_NAMES) == 29


def test_23dof_count():
    assert len(G1_23DOF_JOINT_NAMES) == 23


def test_29dof_no_duplicates():
    assert len(G1_29DOF_JOINT_NAMES) == len(set(G1_29DOF_JOINT_NAMES))


def test_23dof_no_duplicates():
    assert len(G1_23DOF_JOINT_NAMES) == len(set(G1_23DOF_JOINT_NAMES))


def test_29dof_leg_indices():
    # Legs: indices 0-11
    assert G1_29DOF_JOINT_NAMES[0] == 'L_LEG_HIP_PITCH'
    assert G1_29DOF_JOINT_NAMES[6] == 'R_LEG_HIP_PITCH'
    assert G1_29DOF_JOINT_NAMES[11] == 'R_LEG_ANKLE_ROLL'


def test_29dof_waist_indices():
    # Waist: indices 12-14
    assert G1_29DOF_JOINT_NAMES[12] == 'WAIST_YAW'
    assert G1_29DOF_JOINT_NAMES[13] == 'WAIST_ROLL'
    assert G1_29DOF_JOINT_NAMES[14] == 'WAIST_PITCH'


def test_29dof_arm_indices():
    # Left arm starts at 15, right arm at 22
    assert G1_29DOF_JOINT_NAMES[15] == 'L_SHOULDER_PITCH'
    assert G1_29DOF_JOINT_NAMES[22] == 'R_SHOULDER_PITCH'
    assert G1_29DOF_JOINT_NAMES[28] == 'R_WRIST_YAW'


def test_29dof_all_strings():
    for name in G1_29DOF_JOINT_NAMES:
        assert isinstance(name, str) and len(name) > 0
