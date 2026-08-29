import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_name = 'bajana_description'
    package_share = get_package_share_directory(package_name)
    ros_gz_share = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(
        package_share,
        'urdf',
        'bajana_description.urdf.xacro',
    )
    world_file = os.path.join(
        package_share,
        'worlds',
        'bajana_world.sdf',
    )
    bridge_config = os.path.join(
        package_share,
        'config',
        'ros_gz_bridge.yaml',
    )

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_share, 'launch', 'gz_sim.launch.py'),
        ),
        launch_arguments={
            'gz_args': f'-r {world_file}',
            'on_exit_shutdown': 'true',
        }.items(),
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        parameters=[{'config_file': bridge_config}],
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_bajana_arm',
        output='screen',
        arguments=[
            '-world', 'bajana_world',
            '-name', 'bajana_arm',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.0',
            '-allow_renaming', 'false',
        ],
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='joint_state_broadcaster_spawner',
        output='screen',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '120',
        ],
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='arm_controller_spawner',
        output='screen',
        arguments=[
            'arm_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '120',
        ],
    )

    sequence_node = Node(
        package=package_name,
        executable='joint_sequence_controller.py',
        name='joint_sequence_controller',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'seconds_per_point': 2.0,
            'repeat': True,
            'repeat_delay': 2.0,
        }],
    )

    delayed_spawn = TimerAction(period=5.0, actions=[spawn_robot])

    start_joint_state_broadcaster = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_robot,
            on_exit=[joint_state_broadcaster_spawner],
        ),
    )
    start_arm_controller = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[arm_controller_spawner],
        ),
    )
    start_sequence = RegisterEventHandler(
        OnProcessExit(
            target_action=arm_controller_spawner,
            on_exit=[sequence_node],
        ),
    )

    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        clock_bridge,
        delayed_spawn,
        start_joint_state_broadcaster,
        start_arm_controller,
        start_sequence,
    ])
