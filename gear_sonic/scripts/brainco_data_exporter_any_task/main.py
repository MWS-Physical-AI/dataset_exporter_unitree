"""Composition root for ego-view-only BrainCo dataset collection."""

from gear_sonic.data.features_sonic_vla import get_g1_robot_model
from gear_sonic.utils.data_collection.text_to_speech import TextToSpeech
from gear_sonic.utils.data_collection.zmq_state_subscriber import poll_robot_config_zmq

from .collector import BraincoGrootDataCollector
from .config import BraincoDataExporterConfig
from .constants import (
    BRAINCO_MOTOR_NAMES,
    BRAINCO_NUM_MOTORS,
    DEPTH_CAMERA_RGB_FEATURE,
)
from .dds import BraincoHandDDSSubscriber
from .exporter import BraincoDataExporter
from .schema import (
    BraincoSchema,
    configure_camera_schema,
    get_brainco_features,
    get_brainco_modality_config,
)
from .session_profile import collect_session_profile


def main(config: BraincoDataExporterConfig) -> None:
    session_profile = collect_session_profile()
    config.task_prompt = session_profile.task
    config.dataset_name = session_profile.dataset_name()
    print(f"Dataset name: {config.dataset_name}")

    if config.record_wrist_cameras:
        raise ValueError("This collector records only ego_view; wrist cameras are disabled")

    robot_model = get_g1_robot_model()
    schema = BraincoSchema(robot_model)
    features = get_brainco_features(robot_model, schema)
    modality_config = get_brainco_modality_config(robot_model, schema)
    configure_camera_schema(features, modality_config, config)

    print("config.brainco_network_interface", config.brainco_network_interface)
    brainco_subscriber = BraincoHandDDSSubscriber(
        domain_id=config.brainco_dds_domain_id,
        network_interface=config.brainco_network_interface,
    )
    try:
        brainco_subscriber.wait_until_ready(config.brainco_message_timeout)
        robot_config = poll_robot_config_zmq(
            config.state_zmq_host,
            config.state_zmq_port,
            config.robot_config_timeout,
        )
    except Exception:
        brainco_subscriber.close()
        raise

    data_exporter = BraincoDataExporter.create(
        save_root=f"{config.root_output_dir}/{config.dataset_name}",
        fps=config.data_collection_frequency,
        features=features,
        modality_config=modality_config,
        task=config.task_prompt,
        script_config={
            **robot_config,
            "session_profile": session_profile.to_dict(),
            "interaction_metadata_path": "meta/interaction_metadata.jsonl",
            "record_wrist_cameras": False,
            "enabled_camera_streams": ["ego_view"],
            "depth_camera_rgb_image_key": config.depth_camera_rgb_image_key,
            "depth_camera_image_key": config.depth_camera_image_key,
            "depth_camera_resolution": [
                config.depth_camera_width,
                config.depth_camera_height,
            ],
            "depth_stream_resolution": [
                config.depth_stream_width,
                config.depth_stream_height,
            ],
            "record_depth_video": config.record_depth_video,
            "record_raw_depth": config.record_raw_depth,
            "depth_video_encoding": "grayscale_rgb8_preview",
            "depth_video_max_meters": config.depth_video_max_meters,
            "raw_depth_encoding": "uint16_mm_png",
            "raw_depth_root": {"ego_view": "depth"},
            "raw_depth_unit_meters": 0.001,
            "raw_depth_invalid_value": 0,
            "raw_depth_aligned_to": {
                "ego_view": DEPTH_CAMERA_RGB_FEATURE,
            },
            "episode_grip_timestamps_key": BraincoDataExporter.GRIP_TIMESTAMPS_KEY,
            "episode_trigger_timestamp_keys": list(
                BraincoDataExporter.TRIGGER_TIMESTAMP_KEYS.values()
            ),
            "hand_type": "brainco_revo2",
            "hand_dof": BRAINCO_NUM_MOTORS,
            "hand_coordinates": "normalized_0_to_1",
            "hand_motor_order": list(BRAINCO_MOTOR_NAMES),
            "brainco_state_source": "dds_feedback",
            "brainco_tau_est_source": "MotorStates_.states[].tau_est",
            "brainco_action_source": "dds_command",
        },
    )
    data_exporter.record_raw_depth = config.record_raw_depth
    data_exporter.enabled_camera_streams = ("ego_view",)
    data_exporter.session_profile = session_profile.to_dict()

    text_to_speech = TextToSpeech() if config.text_to_speech else None
    collector = BraincoGrootDataCollector(
        frequency=config.data_collection_frequency,
        data_exporter=data_exporter,
        robot_model=robot_model,
        camera_host=config.camera_host,
        camera_port=config.camera_port,
        text_to_speech=text_to_speech,
        sonic_data_zmq_host=config.sonic_zmq_host,
        sonic_data_zmq_port=config.sonic_zmq_port,
        state_zmq_host=config.state_zmq_host,
        state_zmq_port=config.state_zmq_port,
        episode_status_zmq_port=config.episode_status_zmq_port,
        episode_status_publish_hz=config.episode_status_publish_hz,
        brainco_subscriber=brainco_subscriber,
        brainco_schema=schema,
        depth_camera_rgb_image_key=config.depth_camera_rgb_image_key,
        depth_camera_image_key=config.depth_camera_image_key,
        depth_video_max_meters=config.depth_video_max_meters,
        record_raw_depth=config.record_raw_depth,
    )
    collector.run()
