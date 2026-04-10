from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    dof_mode_arg = DeclareLaunchArgument(
        'dof_mode',
        default_value='29',
        description='G1 DOF mode: 23 or 29',
    )
    lowstate_topic_arg = DeclareLaunchArgument(
        'lowstate_topic',
        default_value='lowstate',
        description='unitree_hg LowState topic name',
    )

    bridge_node = Node(
        package='g1_mujoco_bridge',
        executable='bridge_node',
        name='g1_mujoco_bridge',
        parameters=[{
            'dof_mode': LaunchConfiguration('dof_mode'),
            'lowstate_topic': LaunchConfiguration('lowstate_topic'),
        }],
        output='screen',
    )

    return LaunchDescription([
        dof_mode_arg,
        lowstate_topic_arg,
        bridge_node,
    ])
