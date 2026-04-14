#!/usr/bin/env python3

from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from nav_msgs.msg import OccupancyGrid


class MapMerger(Node):
    def __init__(self) -> None:
        super().__init__('map_merger')

        self.declare_parameter('map_topic_1', '/robot_1/map')
        self.declare_parameter('map_topic_2', '/robot_2/map')
        self.declare_parameter('output_topic', '/common/global_map')

        map_topic_1 = self.get_parameter('map_topic_1').get_parameter_value().string_value
        map_topic_2 = self.get_parameter('map_topic_2').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value

        self.map1: Optional[OccupancyGrid] = None
        self.map2: Optional[OccupancyGrid] = None

        map_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        self.sub_map1 = self.create_subscription(
            OccupancyGrid,
            map_topic_1,
            self.map1_callback,
            map_qos
        )
        self.sub_map2 = self.create_subscription(
            OccupancyGrid,
            map_topic_2,
            self.map2_callback,
            map_qos
        )

        self.pub_merged = self.create_publisher(
            OccupancyGrid,
            output_topic,
            10
        )

        self.timer = self.create_timer(1.0, self.publish_merged_map)

        self.get_logger().info(
            f'Map merger started. Subscribing to "{map_topic_1}" and "{map_topic_2}", '
            f'publishing merged map to "{output_topic}".'
        )

    def map1_callback(self, msg: OccupancyGrid) -> None:
        self.map1 = msg
        self.get_logger().info('Received map from robot_1.')

    def map2_callback(self, msg: OccupancyGrid) -> None:
        self.map2 = msg
        self.get_logger().info('Received map from robot_2.')

    def publish_merged_map(self) -> None:
        if self.map1 is None and self.map2 is None:
            self.get_logger().warn('No maps received yet.')
            return

        if self.map1 is not None and self.map2 is None:
            merged = OccupancyGrid()
            merged.header = self.map1.header
            merged.header.frame_id = 'common_map'
            merged.info = self.map1.info
            merged.data = list(self.map1.data)
            self.pub_merged.publish(merged)
            self.get_logger().debug('Published temporary /common/global_map from robot_1 map only.')
            return

        if self.map1 is None and self.map2 is not None:
            merged = OccupancyGrid()
            merged.header = self.map2.header
            merged.header.frame_id = 'common_map'
            merged.info = self.map2.info
            merged.data = list(self.map2.data)
            self.pub_merged.publish(merged)
            self.get_logger().debug('Published temporary /common/global_map from robot_2 map only.')
            return

        # Temporary milestone version:
        # publish robot_1 map as the current common map.
        merged = OccupancyGrid()
        merged.header = self.map1.header
        merged.header.frame_id = 'common_map'
        merged.info = self.map1.info
        merged.data = list(self.map1.data)

        self.pub_merged.publish(merged)
        self.get_logger().debug('Published temporary /common/global_map from robot_1 map.')

def main(args=None) -> None:
    rclpy.init(args=args)
    node = MapMerger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()