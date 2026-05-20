#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List, Optional, Tuple
import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

from nav_msgs.msg import OccupancyGrid, MapMetaData
from geometry_msgs.msg import TransformStamped
from tf2_ros import Buffer, TransformListener, TransformBroadcaster, TransformException


@dataclass
class PlanarTransform:
    x: float
    y: float
    yaw: float


@dataclass
class MapSource:
    name: str
    msg: OccupancyGrid
    transform: PlanarTransform


def yaw_from_quaternion(q) -> float:
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def transform_point(t: PlanarTransform, x: float, y: float) -> Tuple[float, float]:
    c = math.cos(t.yaw)
    s = math.sin(t.yaw)
    return (
        t.x + c * x - s * y,
        t.y + s * x + c * y,
    )


class MapMerger(Node):
    def __init__(self) -> None:
        super().__init__('map_merger')

        self.declare_parameter('map_topic_1', '/robot_1/map')
        self.declare_parameter('map_topic_2', '/robot_2/map')
        self.declare_parameter('output_topic', '/common/global_map')

        self.declare_parameter('global_frame', 'common_map')

        # If true, map positions are read from TF:
        # global_frame -> map1_frame and global_frame -> map2_frame.
        # If false, static manual offset parameters are used.
        self.declare_parameter('use_tf_alignment', False)
        self.declare_parameter('map1_frame', 'robot_1/map')
        self.declare_parameter('map2_frame', 'robot_2/map')

        # Manual fallback offsets.
        self.declare_parameter('map1_offset_x', 0.0)
        self.declare_parameter('map1_offset_y', 0.0)
        self.declare_parameter('map1_yaw', 0.0)
        self.declare_parameter('map2_offset_x', 1.0)
        self.declare_parameter('map2_offset_y', 0.5)
        self.declare_parameter('map2_yaw', 0.0)

        self.global_frame = self.get_parameter('global_frame').value
        self.use_tf_alignment = bool(self.get_parameter('use_tf_alignment').value)

        map_topic_1 = self.get_parameter('map_topic_1').value
        map_topic_2 = self.get_parameter('map_topic_2').value
        output_topic = self.get_parameter('output_topic').value

        self.map1: Optional[OccupancyGrid] = None
        self.map2: Optional[OccupancyGrid] = None
        self.publish_count = 0

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self, spin_thread=True)
        self.tf_broadcaster = TransformBroadcaster(self)

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
            map_qos,
        )
        self.sub_map2 = self.create_subscription(
            OccupancyGrid,
            map_topic_2,
            self.map2_callback,
            map_qos,
        )

        self.pub_merged = self.create_publisher(
            OccupancyGrid,
            output_topic,
            map_qos,
        )

        self.timer = self.create_timer(1.0, self.publish_merged_map)

        mode = 'TF/ArUco alignment' if self.use_tf_alignment else 'manual static offsets'
        self.get_logger().info(
            f'Map merger started in {mode} mode. '
            f'Subscribing to "{map_topic_1}" and "{map_topic_2}", '
            f'publishing "{output_topic}" in frame "{self.global_frame}".'
        )

    def map1_callback(self, msg: OccupancyGrid) -> None:
        first = self.map1 is None
        self.map1 = msg
        if first:
            self.get_logger().info(
                f'Received first map from source 1: frame={msg.header.frame_id}, '
                f'size={msg.info.width}x{msg.info.height}, resolution={msg.info.resolution:.3f}'
            )

    def map2_callback(self, msg: OccupancyGrid) -> None:
        first = self.map2 is None
        self.map2 = msg
        if first:
            self.get_logger().info(
                f'Received first map from source 2: frame={msg.header.frame_id}, '
                f'size={msg.info.width}x{msg.info.height}, resolution={msg.info.resolution:.3f}'
            )

    def get_manual_transform(self, idx: int) -> PlanarTransform:
        return PlanarTransform(
            x=float(self.get_parameter(f'map{idx}_offset_x').value),
            y=float(self.get_parameter(f'map{idx}_offset_y').value),
            yaw=float(self.get_parameter(f'map{idx}_yaw').value),
        )

    def get_tf_transform(self, frame: str) -> Optional[PlanarTransform]:
        try:
            ts = self.tf_buffer.lookup_transform(
                self.global_frame,
                frame,
                Time(),
            )
        except TransformException as exc:
            self.get_logger().warn(
                f'Waiting for TF {self.global_frame} -> {frame}: {exc}'
            )
            return None

        tr = ts.transform.translation
        rot = ts.transform.rotation
        return PlanarTransform(
            x=float(tr.x),
            y=float(tr.y),
            yaw=yaw_from_quaternion(rot),
        )

    def get_source_transform(self, idx: int, msg: OccupancyGrid) -> Optional[PlanarTransform]:
        if not self.use_tf_alignment:
            return self.get_manual_transform(idx)

        configured_frame = self.get_parameter(f'map{idx}_frame').value
        frame = configured_frame if configured_frame else msg.header.frame_id
        return self.get_tf_transform(frame)

    def publish_merged_map(self) -> None:
        sources: List[MapSource] = []

        if self.map1 is not None:
            t1 = self.get_source_transform(1, self.map1)
            if t1 is None:
                return
            sources.append(MapSource('robot_1', self.map1, t1))

        if self.map2 is not None:
            t2 = self.get_source_transform(2, self.map2)
            if t2 is None:
                return
            sources.append(MapSource('robot_2', self.map2, t2))

        if not sources:
            self.get_logger().warn('No maps received yet.')
            return

        merged = self.merge_maps(sources)
        self.pub_merged.publish(merged)

        if not self.use_tf_alignment:
            for i, source in enumerate(sources, start=1):
                frame = self.get_parameter(f'map{i}_frame').value
                self.publish_single_map_transform(self.global_frame, frame, source.transform)

        self.publish_count += 1
        if self.publish_count == 1 or self.publish_count % 10 == 0:
            self.get_logger().info(
                f'Published merged map #{self.publish_count}: '
                f'frame={merged.header.frame_id}, '
                f'size={merged.info.width}x{merged.info.height}, '
                f'origin=({merged.info.origin.position.x:.2f}, {merged.info.origin.position.y:.2f})'
            )

    def map_cell_to_global(
        self,
        source: MapSource,
        cell_x: float,
        cell_y: float,
    ) -> Tuple[float, float]:
        src = source.msg
        resolution = src.info.resolution

        # Cell coordinate in the OccupancyGrid local coordinate system.
        grid_x = cell_x * resolution
        grid_y = cell_y * resolution

        origin_yaw = yaw_from_quaternion(src.info.origin.orientation)
        origin_t = PlanarTransform(
            x=src.info.origin.position.x,
            y=src.info.origin.position.y,
            yaw=origin_yaw,
        )

        # Grid -> source map frame.
        map_x, map_y = transform_point(origin_t, grid_x, grid_y)

        # Source map frame -> global frame.
        return transform_point(source.transform, map_x, map_y)

    def compute_global_bounds(self, sources: List[MapSource]) -> Tuple[float, float, float, float]:
        xs = []
        ys = []

        for source in sources:
            width = source.msg.info.width
            height = source.msg.info.height

            corners = [
                (0.0, 0.0),
                (float(width), 0.0),
                (0.0, float(height)),
                (float(width), float(height)),
            ]

            for cx, cy in corners:
                gx, gy = self.map_cell_to_global(source, cx, cy)
                xs.append(gx)
                ys.append(gy)

        return min(xs), min(ys), max(xs), max(ys)

    def merge_maps(self, sources: List[MapSource]) -> OccupancyGrid:
        resolution = sources[0].msg.info.resolution

        for source in sources[1:]:
            if not math.isclose(source.msg.info.resolution, resolution, rel_tol=1e-6, abs_tol=1e-6):
                self.get_logger().warn(
                    f'Resolution mismatch. Using first map resolution={resolution}. '
                    f'Source {source.name} has resolution={source.msg.info.resolution}.'
                )

        min_x, min_y, max_x, max_y = self.compute_global_bounds(sources)

        merged_width = max(1, int(math.ceil((max_x - min_x) / resolution)) + 1)
        merged_height = max(1, int(math.ceil((max_y - min_y) / resolution)) + 1)

        merged_data = [-1] * (merged_width * merged_height)

        for source in sources:
            self.blit_source_map(source, merged_data, merged_width, merged_height, min_x, min_y, resolution)

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

    def blit_source_map(
        self,
        source: MapSource,
        merged_data: List[int],
        merged_width: int,
        merged_height: int,
        merged_origin_x: float,
        merged_origin_y: float,
        resolution: float,
    ) -> None:
        src = source.msg
        src_width = src.info.width
        src_height = src.info.height

        for y in range(src_height):
            for x in range(src_width):
                src_idx = y * src_width + x
                src_val = int(src.data[src_idx])

                if src_val == -1:
                    continue

                # Use cell center.
                gx, gy = self.map_cell_to_global(source, x + 0.5, y + 0.5)

                dst_x = int(math.floor((gx - merged_origin_x) / resolution))
                dst_y = int(math.floor((gy - merged_origin_y) / resolution))

                if dst_x < 0 or dst_x >= merged_width or dst_y < 0 or dst_y >= merged_height:
                    continue

                dst_idx = dst_y * merged_width + dst_x
                merged_data[dst_idx] = self.merge_cell_values(merged_data[dst_idx], src_val)

    def merge_cell_values(self, old_val: int, new_val: int) -> int:
        if old_val == -1:
            return new_val
        if new_val == -1:
            return old_val

        occupied_threshold = 50

        old_occ = old_val >= occupied_threshold
        new_occ = new_val >= occupied_threshold

        # Conservative rule: obstacle wins.
        if old_occ or new_occ:
            return max(old_val, new_val)

        # For free cells, keep the freer value.
        return min(old_val, new_val)

    def publish_single_map_transform(
        self,
        parent_frame: str,
        child_frame: str,
        t_planar: PlanarTransform,
    ) -> None:
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = parent_frame
        t.child_frame_id = child_frame

        t.transform.translation.x = float(t_planar.x)
        t.transform.translation.y = float(t_planar.y)
        t.transform.translation.z = 0.0

        half = t_planar.yaw / 2.0
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = math.sin(half)
        t.transform.rotation.w = math.cos(half)

        self.tf_broadcaster.sendTransform(t)


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