#!/usr/bin/env python3

from typing import Optional, List, Tuple
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from nav_msgs.msg import OccupancyGrid, MapMetaData


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
            merged = self.clone_map_with_common_frame(self.map1)
            self.pub_merged.publish(merged)
            self.get_logger().debug('Published /common/global_map from robot_1 map only.')
            return

        if self.map1 is None and self.map2 is not None:
            merged = self.clone_map_with_common_frame(self.map2)
            self.pub_merged.publish(merged)
            self.get_logger().debug('Published /common/global_map from robot_2 map only.')
            return

        merged = self.merge_two_maps(self.map1, self.map2)
        self.pub_merged.publish(merged)
        self.get_logger().info('Published merged /common/global_map from robot_1 and robot_2.')

    def clone_map_with_common_frame(self, src: OccupancyGrid) -> OccupancyGrid:
        out = OccupancyGrid()
        out.header = src.header
        out.header.frame_id = 'common_map'
        out.info = src.info
        out.data = list(src.data)
        return out

    def merge_two_maps(self, map1: OccupancyGrid, map2: OccupancyGrid) -> OccupancyGrid:
        res1 = map1.info.resolution
        res2 = map2.info.resolution

        if not math.isclose(res1, res2, rel_tol=1e-6, abs_tol=1e-6):
            self.get_logger().warn(
                f'Resolution mismatch: robot_1={res1}, robot_2={res2}. '
                'Falling back to robot_1 map only.'
            )
            return self.clone_map_with_common_frame(map1)

        resolution = res1

        min_x = min(map1.info.origin.position.x, map2.info.origin.position.x)
        min_y = min(map1.info.origin.position.y, map2.info.origin.position.y)

        max_x = max(
            map1.info.origin.position.x + map1.info.width * resolution,
            map2.info.origin.position.x + map2.info.width * resolution
        )
        max_y = max(
            map1.info.origin.position.y + map1.info.height * resolution,
            map2.info.origin.position.y + map2.info.height * resolution
        )

        merged_width = int(math.ceil((max_x - min_x) / resolution))
        merged_height = int(math.ceil((max_y - min_y) / resolution))

        merged_data = [-1] * (merged_width * merged_height)

        self.blit_map_into_merged(map1, merged_data, merged_width, merged_height, min_x, min_y, resolution)
        self.blit_map_into_merged(map2, merged_data, merged_width, merged_height, min_x, min_y, resolution)

        merged = OccupancyGrid()
        merged.header.stamp = self.get_clock().now().to_msg()
        merged.header.frame_id = 'common_map'

        merged.info = MapMetaData()
        merged.info.map_load_time = self.get_clock().now().to_msg()
        merged.info.resolution = resolution
        merged.info.width = merged_width
        merged.info.height = merged_height
        merged.info.origin.position.x = min_x
        merged.info.origin.position.y = min_y
        merged.info.origin.position.z = 0.0
        merged.info.origin.orientation.x = 0.0
        merged.info.origin.orientation.y = 0.0
        merged.info.origin.orientation.z = 0.0
        merged.info.origin.orientation.w = 1.0

        merged.data = merged_data
        return merged

    def blit_map_into_merged(
        self,
        src_map: OccupancyGrid,
        merged_data: List[int],
        merged_width: int,
        merged_height: int,
        merged_origin_x: float,
        merged_origin_y: float,
        resolution: float
    ) -> None:
        offset_x = int(round((src_map.info.origin.position.x - merged_origin_x) / resolution))
        offset_y = int(round((src_map.info.origin.position.y - merged_origin_y) / resolution))

        src_width = src_map.info.width
        src_height = src_map.info.height

        for y in range(src_height):
            for x in range(src_width):
                src_idx = y * src_width + x
                src_val = src_map.data[src_idx]

                dst_x = x + offset_x
                dst_y = y + offset_y

                if dst_x < 0 or dst_x >= merged_width or dst_y < 0 or dst_y >= merged_height:
                    continue

                dst_idx = dst_y * merged_width + dst_x
                dst_val = merged_data[dst_idx]

                merged_data[dst_idx] = self.merge_cell_values(dst_val, src_val)

    def merge_cell_values(self, old_val: int, new_val: int) -> int:
        # Unknown handling
        if old_val == -1:
            return new_val
        if new_val == -1:
            return old_val

        # Conservative occupancy merge:
        # occupied wins over free, otherwise take higher confidence.
        occupied_threshold = 50

        old_occ = old_val >= occupied_threshold
        new_occ = new_val >= occupied_threshold

        if old_occ or new_occ:
            return max(old_val, new_val)

        return min(old_val, new_val)


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