#!/usr/bin/env python3

from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectoryPoint


class JointSequenceController(Node):
    """Envía al controlador físico la secuencia de diez poses del brazo."""

    JOINT_NAMES = ['joint1', 'joint2', 'joint3']
    WAYPOINTS = [
        [0.0, 0.0, 0.0],
        [0.2, 0.7, 0.9],
        [0.3, 0.8, 0.2],
        [0.5, 0.4, -0.3],
        [0.7, -0.2, 0.5],
        [0.3, 0.6, 0.6],
        [-0.2, 0.4, 0.9],
        [-0.5, -0.3, 0.4],
        [0.2, -0.7, -0.6],
        [0.0, 0.0, 0.0],
    ]

    def __init__(self):
        super().__init__('joint_sequence_controller')

        self.declare_parameter('seconds_per_point', 2.0)
        self.declare_parameter('repeat', True)
        self.declare_parameter('repeat_delay', 2.0)

        self.seconds_per_point = float(
            self.get_parameter('seconds_per_point').value)
        self.repeat = bool(self.get_parameter('repeat').value)
        self.repeat_delay = float(self.get_parameter('repeat_delay').value)

        if self.seconds_per_point <= 0.0:
            raise ValueError('seconds_per_point debe ser mayor que cero')
        if self.repeat_delay <= 0.0:
            raise ValueError('repeat_delay debe ser mayor que cero')

        self.action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/arm_controller/follow_joint_trajectory',
        )
        self.start_timer = self.create_timer(1.0, self._wait_for_controller)
        self.repeat_timer = None
        self.get_logger().info(
            'Esperando el action server de arm_controller...')

    def _wait_for_controller(self):
        if not self.action_client.server_is_ready():
            self.get_logger().info('arm_controller todavía no está disponible')
            return

        self.start_timer.cancel()
        self.get_logger().info('arm_controller disponible. Enviando trayectoria.')
        self._send_trajectory()

    def _build_goal(self):
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = self.JOINT_NAMES

        for index, positions in enumerate(self.WAYPOINTS, start=1):
            point = JointTrajectoryPoint()
            point.positions = [float(value) for value in positions]

            total_seconds = index * self.seconds_per_point
            seconds = int(total_seconds)
            nanoseconds = int((total_seconds - seconds) * 1_000_000_000)
            point.time_from_start = Duration(
                sec=seconds,
                nanosec=nanoseconds,
            )
            goal.trajectory.points.append(point)

        goal.goal_time_tolerance = Duration(sec=1)
        return goal

    def _send_trajectory(self):
        send_goal_future = self.action_client.send_goal_async(self._build_goal())
        send_goal_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        try:
            goal_handle = future.result()
        except Exception as error:  # rclpy conserva la excepción en Future.
            self.get_logger().error(f'No se pudo enviar la trayectoria: {error}')
            return

        if not goal_handle.accepted:
            self.get_logger().error('El controlador rechazó la trayectoria')
            return

        self.get_logger().info('Trayectoria aceptada')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _result_callback(self, future):
        try:
            wrapped_result = future.result()
        except Exception as error:
            self.get_logger().error(f'No se recibió resultado: {error}')
            return

        error_code = wrapped_result.result.error_code
        if error_code != FollowJointTrajectory.Result.SUCCESSFUL:
            self.get_logger().error(
                f'La secuencia terminó con error_code={error_code}')
            return

        self.get_logger().info('Secuencia terminada correctamente')
        if self.repeat:
            self.get_logger().info(
                f'Repitiendo en {self.repeat_delay:.1f} segundos')
            self.repeat_timer = self.create_timer(
                self.repeat_delay,
                self._repeat_once,
            )

    def _repeat_once(self):
        self.repeat_timer.cancel()
        self.repeat_timer = None
        self._send_trajectory()


def main(args=None):
    rclpy.init(args=args)
    node = JointSequenceController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.destroy_node()
        except KeyboardInterrupt:
            pass
        finally:
            if rclpy.ok():
                try:
                    rclpy.shutdown()
                except KeyboardInterrupt:
                    pass


if __name__ == '__main__':
    main()
