#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List, Optional, Tuple
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from nav_msgs.msg import OccupancyGrid, MapMetaData
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


@dataclass
class MapTransform2D:
    x: float
    y: float
    yaw: float
    frame_id: str


class MapMerger(Node):
    def __init__(self) -> None:
        super().__init__('map_merger')

        self.declare_parameter('map_topic_1', '/robot_1/map')
        self.declare_parameter('map_topic_2', '/robot_2/map')
        self.declare_parameter('output_topic', '/common/global_map')
        self.declare_parameter('global_frame', 'common_map')

        # Manual transform from each robot map frame into common_map.
        # These are the first prototype values. Later ArUco can estimate/update them.
        self.declare_parameter('map1_offset_x', 0.0)
        self.declare_parameter('map1_offset_y', 0.0)
        self.declare_parameter('map1_yaw', 0.0)

        self.declare_parameter('map2_offset_x', 0.0)
        self.declare_parameter('map2_offset_y', 0.0)
        self.declare_parameter('map2_yaw', 0.0)

        # Optional override. If empty, the incoming OccupancyGrid header.frame_id is used.
        self.declare_parameter('map1_frame', '')
        self.declare_parameter('map2_frame', '')

        self.declare_parameter('occupied_threshold', 50)

        self.tf_broadcaster = TransformBroadcaster(self)

        self.map_topic_1 = self.get_parameter('map_topic_1').value
        self.map_topic_2 = self.get_parameter('map_topic_2').value
        self.output_topic = self.get_parameter('output_topic').value
        self.global_frame = self.get_parameter('global_frame').value

        self.map1: Optional[OccupancyGrid] = None
        self.map2: Optional[OccupancyGrid] = None

        self.publish_count = 0
        self.no_map_warn_count = 0

        map_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        self.sub_map1 = self.create_subscription(
            OccupancyGrid,
            self.map_topic_1,
            self.map1_callback,
            map_qos
        )

        self.sub_map2 = self.create_subscription(
            OccupancyGrid,
            self.map_topic_2,
            self.map2_callback,
            map_qos
        )

        # Important: merged map also uses TRANSIENT_LOCAL QoS.
        # This allows RViz and `ros2 topic echo --once` to receive the latest map even if they start late.
        self.pub_merged = self.create_publisher(
            OccupancyGrid,
            self.output_topic,
            map_qos
        )

        self.timer = self.create_timer(1.0, self.publish_merged_map)

        self.get_logger().info(
            f'Map merger started. Subscribing to "{self.map_topic_1}" and "{self.map_topic_2}", '
            f'publishing merged map to "{self.output_topic}" in frame "{self.global_frame}".'
        )

    def map1_callback(self, msg: OccupancyGrid) -> None:
        first_receive = self.map1 is None
        self.map1 = msg

        if first_receive:
            self.get_logger().info(
                f'Received first map from source 1: frame={msg.header.frame_id}, '
                f'size={msg.info.width}x{msg.info.height}, resolution={msg.info.resolution:.3f}'
            )

    def map2_callback(self, msg: OccupancyGrid) -> None:
        first_receive = self.map2 is None
        self.map2 = msg

        if first_receive:
            self.get_logger().info(
                f'Received first map from source 2: frame={msg.header.frame_id}, '
                f'size={msg.info.width}x{msg.info.height}, resolution={msg.info.resolution:.3f}'
            )

    def publish_merged_map(self) -> None:
        maps_and_transforms = self.get_available_maps_and_transforms()

        if not maps_and_transforms:
            self.no_map_warn_count += 1
            if self.no_map_warn_count == 1 or self.no_map_warn_count % 5 == 0:
                self.get_logger().warn('No maps received yet.')
            return

        merged = self.merge_maps(maps_and_transforms)
        self.pub_merged.publish(merged)

        for _, map_transform in maps_and_transforms:
            self.publish_map_transform(map_transform)

        self.publish_count += 1
        if self.publish_count == 1 or self.publish_count % 10 == 0:
            self.get_logger().info(
                f'Published merged map #{self.publish_count}: '
                f'frame={merged.header.frame_id}, '
                f'size={merged.info.width}x{merged.info.height}, '
                f'origin=({merged.info.origin.position.x:.2f}, {merged.info.origin.position.y:.2f})'
            )

    def get_available_maps_and_transforms(self) -> List[Tuple[OccupancyGrid, MapTransform2D]]:
        result: List[Tuple[OccupancyGrid, MapTransform2D]] = []

        if self.map1 is not None:
            frame_override = self.get_parameter('map1_frame').value
            frame_id = frame_override if frame_override else self.map1.header.frame_id

            result.append((
                self.map1,
                MapTransform2D(
                    x=float(self.get_parameter('map1_offset_x').value),
                    y=float(self.get_parameter('map1_offset_y').value),
                    yaw=float(self.get_parameter('map1_yaw').value),
                    frame_id=frame_id
                )
            ))

        if self.map2 is not None:
            frame_override = self.get_parameter('map2_frame').value
            frame_id = frame_override if frame_override else self.map2.header.frame_id

            result.append((
                self.map2,
                MapTransform2D(
                    x=float(self.get_parameter('map2_offset_x').value),
                    y=float(self.get_parameter('map2_offset_y').value),
                    yaw=float(self.get_parameter('map2_yaw').value),
                    frame_id=frame_id
                )
            ))

        return result

    def merge_maps(
        self,
        maps_and_transforms: List[Tuple[OccupancyGrid, MapTransform2D]]
    ) -> OccupancyGrid:
        reference_resolution = maps_and_transforms[0][0].info.resolution

        compatible_maps: List[Tuple[OccupancyGrid, MapTransform2D]] = []
        for map_msg, map_transform in maps_and_transforms:
            if math.isclose(
                map_msg.info.resolution,
                reference_resolution,
                rel_tol=1e-6,
                abs_tol=1e-6
            ):
                compatible_maps.append((map_msg, map_transform))
            else:
                self.get_logger().warn(
                    f'Ignoring map "{map_msg.header.frame_id}" because resolution '
                    f'{map_msg.info.resolution} does not match reference resolution '
                    f'{reference_resolution}.'
                )

        if not compatible_maps:
            raise RuntimeError('No compatible maps available for merging.')

        resolution = reference_resolution

        min_x, min_y, max_x, max_y = self.compute_global_bounds(compatible_maps)

        merged_width = max(1, int(math.ceil((max_x - min_x) / resolution)))
        merged_height = max(1, int(math.ceil((max_y - min_y) / resolution)))

        merged_data = [-1] * (merged_width * merged_height)

        for map_msg, map_transform in compatible_maps:
            self.blit_transformed_map_into_merged(
                src_map=map_msg,
                src_to_global=map_transform,
                merged_data=merged_data,
                merged_width=merged_width,
                merged_height=merged_height,
                merged_origin_x=min_x,
                merged_origin_y=min_y,
                resolution=resolution
            )

        merged = OccupancyGrid()
        merged.header.stamp = self.get_clock().now().to_msg()
        merged.header.frame_id = self.global_frame

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

    def compute_global_bounds(
        self,
        maps_and_transforms: List[Tuple[OccupancyGrid, MapTransform2D]]
    ) -> Tuple[float, float, float, float]:
        all_points: List[Tuple[float, float]] = []

        for map_msg, map_transform in maps_and_transforms:
            all_points.extend(self.get_transformed_map_corners(map_msg, map_transform))

        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]

        return min(xs), min(ys), max(xs), max(ys)

    def get_transformed_map_corners(
        self,
        map_msg: OccupancyGrid,
        src_to_global: MapTransform2D
    ) -> List[Tuple[float, float]]:
        resolution = map_msg.info.resolution
        width_m = map_msg.info.width * resolution
        height_m = map_msg.info.height * resolution

        local_corners = [
            (0.0, 0.0),
            (width_m, 0.0),
            (0.0, height_m),
            (width_m, height_m),
        ]

        transformed_corners: List[Tuple[float, float]] = []

        for local_x, local_y in local_corners:
            map_x, map_y = self.local_grid_point_to_map_frame(map_msg, local_x, local_y)
            global_x, global_y = self.transform_point_2d(map_x, map_y, src_to_global)
            transformed_corners.append((global_x, global_y))

        return transformed_corners

    def blit_transformed_map_into_merged(
        self,
        src_map: OccupancyGrid,
        src_to_global: MapTransform2D,
        merged_data: List[int],
        merged_width: int,
        merged_height: int,
        merged_origin_x: float,
        merged_origin_y: float,
        resolution: float
    ) -> None:
        src_width = src_map.info.width
        src_height = src_map.info.height

        for y in range(src_height):
            for x in range(src_width):
                src_idx = y * src_width + x
                src_val = int(src_map.data[src_idx])

                map_x, map_y = self.cell_center_to_map_frame(src_map, x, y)
                global_x, global_y = self.transform_point_2d(map_x, map_y, src_to_global)

                dst_x = int(math.floor((global_x - merged_origin_x) / resolution))
                dst_y = int(math.floor((global_y - merged_origin_y) / resolution))

                if dst_x < 0 or dst_x >= merged_width or dst_y < 0 or dst_y >= merged_height:
                    continue

                dst_idx = dst_y * merged_width + dst_x
                old_val = merged_data[dst_idx]

                merged_data[dst_idx] = self.merge_cell_values(old_val, src_val)

    def cell_center_to_map_frame(
        self,
        map_msg: OccupancyGrid,
        cell_x: int,
        cell_y: int
    ) -> Tuple[float, float]:
        resolution = map_msg.info.resolution

        local_x = (cell_x + 0.5) * resolution
        local_y = (cell_y + 0.5) * resolution

        return self.local_grid_point_to_map_frame(map_msg, local_x, local_y)

    def local_grid_point_to_map_frame(
        self,
        map_msg: OccupancyGrid,
        local_x: float,
        local_y: float
    ) -> Tuple[float, float]:
        origin = map_msg.info.origin
        origin_yaw = self.quaternion_to_yaw(
            origin.orientation.x,
            origin.orientation.y,
            origin.orientation.z,
            origin.orientation.w
        )

        c = math.cos(origin_yaw)
        s = math.sin(origin_yaw)

        map_x = origin.position.x + c * local_x - s * local_y
        map_y = origin.position.y + s * local_x + c * local_y

        return map_x, map_y

    def transform_point_2d(
        self,
        x: float,
        y: float,
        transform: MapTransform2D
    ) -> Tuple[float, float]:
        c = math.cos(transform.yaw)
        s = math.sin(transform.yaw)

        out_x = transform.x + c * x - s * y
        out_y = transform.y + s * x + c * y

        return out_x, out_y

    def merge_cell_values(self, old_val: int, new_val: int) -> int:
        # OccupancyGrid values:
        # -1 = unknown
        #  0 = free
        # 100 = occupied
        #
        # PGM image maps may use 0/205/254/255 style values, but the ROS topic
        # nav_msgs/msg/OccupancyGrid uses -1..100.
        if old_val == -1:
            return new_val

        if new_val == -1:
            return old_val

        occupied_threshold = int(self.get_parameter('occupied_threshold').value)

        old_occupied = old_val >= occupied_threshold
        new_occupied = new_val >= occupied_threshold

        # Conservative merge: obstacle wins over free.
        if old_occupied or new_occupied:
            return max(old_val, new_val)

        # If both are free-ish, keep the freer value.
        return min(old_val, new_val)

    def publish_map_transform(self, map_transform: MapTransform2D) -> None:
        if not map_transform.frame_id:
            return

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = self.global_frame
        t.child_frame_id = map_transform.frame_id

        t.transform.translation.x = float(map_transform.x)
        t.transform.translation.y = float(map_transform.y)
        t.transform.translation.z = 0.0

        qx, qy, qz, qw = self.yaw_to_quaternion(map_transform.yaw)
        t.transform.rotation.x = qx
        t.transform.rotation.y = qy
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw

        self.tf_broadcaster.sendTransform(t)

    def quaternion_to_yaw(self, x: float, y: float, z: float, w: float) -> float:
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        return math.atan2(siny_cosp, cosy_cosp)

    def yaw_to_quaternion(self, yaw: float) -> Tuple[float, float, float, float]:
        half_yaw = yaw * 0.5
        return 0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MapMerger()

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
