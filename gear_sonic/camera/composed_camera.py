"""Camera ZMQ client extracted from gear_sonic.camera.composed_camera."""

from collections import deque
import time
from typing import Any

import numpy as np

from gear_sonic.camera.sensor import Sensor
from gear_sonic.camera.sensor_server import ImageMessageSchema, SensorClient


class ComposedCameraClientSensor(Sensor, SensorClient):
    """ZMQ client that deserializes merged camera frames from the server."""

    def __init__(self, server_ip: str = "localhost", port: int = 5555):
        self.start_client(server_ip, port)

        self._latest_message = None
        self._avg_time_per_frame: deque = deque(maxlen=20)
        self._msg_received_time = 0
        self._start_time = 0.0
        self.idx = 0

        self._last_new_message_time = None
        self._last_staleness_warning_time = 0.0
        self._staleness_warning_interval = 2.0

        print("Initialized composed camera client sensor")

    def read(self, blocking: bool = False, **kwargs) -> dict[str, Any] | None:
        self._start_time = time.time()
        current_time = time.time()

        if blocking:
            message = self.receive_message()
            if not message:
                return None
        else:
            message = self.receive_message_nonblocking(timeout_ms=0)

        if message is not None:
            self.idx += 1
            self._latest_message = ImageMessageSchema.deserialize(message).asdict()
            self._last_new_message_time = current_time

            if self.idx % 10 == 0:
                for image_key, image_time in self._latest_message["timestamps"].items():
                    image_latency = (time.time() - image_time) * 1000
                    print(f"Image latency for {image_key}: {image_latency:.2f} ms")

            self._msg_received_time = time.time()
            self._avg_time_per_frame.append(self._msg_received_time - self._start_time)
        elif not blocking and self._latest_message is not None:
            if self._last_new_message_time is not None:
                time_since_last_message = current_time - self._last_new_message_time
                if time_since_last_message > 0.1:
                    if (
                        current_time - self._last_staleness_warning_time
                        >= self._staleness_warning_interval
                    ):
                        print(
                            f"[WARNING] No new image message received for "
                            f"{time_since_last_message*1000:.1f}ms. "
                            f"Reusing stale image. Check camera server connection."
                        )
                        self._last_staleness_warning_time = current_time

        return self._latest_message

    def serialize(self, data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Client does not serialize")

    def close(self):
        self.stop_client()

    def fps(self) -> float:
        if len(self._avg_time_per_frame) == 0:
            return 0.0
        return float(1 / np.mean(self._avg_time_per_frame))


