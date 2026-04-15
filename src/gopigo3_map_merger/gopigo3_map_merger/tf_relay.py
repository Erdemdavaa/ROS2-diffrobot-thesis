#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from tf2_msgs.msg import TFMessage


class TfRelay(Node):
    def __init__(self) -> None:
        super().__init__('tf_relay')

        self.declare_parameter('tf_topics', ['/robot_1/tf', '/robot_2/tf'])
        self.declare_parameter('tf_static_topics', ['/robot_1/tf_static', '/robot_2/tf_static'])

        tf_topics = self.get_parameter('tf_topics').get_parameter_value().string_array_value
        tf_static_topics = self.get_parameter('tf_static_topics').get_parameter_value().string_array_value

        # Subscribe to robot-local dynamic TF with BEST_EFFORT
        dynamic_sub_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        # Publish relayed dynamic TF with RELIABLE
        dynamic_pub_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )

        static_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        self.tf_pub = self.create_publisher(TFMessage, '/tf', dynamic_pub_qos)
        self.tf_static_pub = self.create_publisher(TFMessage, '/tf_static', static_qos)

        self.tf_subs = []
        self.tf_static_subs = []

        for topic in tf_topics:
            sub = self.create_subscription(
                TFMessage,
                topic,
                self.tf_callback,
                dynamic_sub_qos
            )
            self.tf_subs.append(sub)
            self.get_logger().info(f'Relaying dynamic TF from {topic} -> /tf')

        for topic in tf_static_topics:
            sub = self.create_subscription(
                TFMessage,
                topic,
                self.tf_static_callback,
                static_qos
            )
            self.tf_static_subs.append(sub)
            self.get_logger().info(f'Relaying static TF from {topic} -> /tf_static')

    def tf_callback(self, msg: TFMessage) -> None:
        self.tf_pub.publish(msg)

    def tf_static_callback(self, msg: TFMessage) -> None:
        self.tf_static_pub.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TfRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()