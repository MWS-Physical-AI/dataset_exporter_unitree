"""CLI configuration for ego-view BrainCo dataset collection."""

from dataclasses import dataclass

from gear_sonic.scripts.run_data_exporter import SonicDataExporterConfig


@dataclass
class BraincoDataExporterConfig(SonicDataExporterConfig):
    """CLI configuration for native 6-DOF BrainCo dataset collection."""

    brainco_dds_domain_id: int = 0
    """DDS domain used by brainco_hand_service."""

    brainco_network_interface: str | None = "wlp128s20f3"
    """DDS network interface, for example eth0. None enables auto-selection."""

    brainco_message_timeout: float = 10.0
    """Seconds to wait for both hand state messages (0 = forever)."""

    depth_camera_rgb_image_key: str = "ego_view"
    """RGB image key published by the depth camera."""

    depth_camera_image_key: str = "ego_view_depth"
    """Depth image key published by the depth camera."""

    depth_camera_width: int = 1280
    """Width of the recorded ego-view RGB stream."""

    depth_camera_height: int = 720
    """Height of the recorded ego-view RGB stream."""

    depth_stream_width: int = 640
    """Width of the recorded ego-view depth stream."""

    depth_stream_height: int = 480
    """Height of the recorded ego-view depth stream."""

    depth_video_max_meters: float = 5.0
    """Depth mapped to white in the 8-bit depth visualization video."""

    record_depth_video: bool = False
    """Record enabled depth streams as 8-bit grayscale preview videos."""

    record_raw_depth: bool = False
    """Record enabled metric depth streams as uint16 millimetre PNG sequences."""
