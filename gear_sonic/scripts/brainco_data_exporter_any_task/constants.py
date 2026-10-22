"""Dataset feature names and BrainCo hand metadata."""

BRAINCO_MOTOR_NAMES = ("thumb", "thumb_aux", "index", "middle", "ring", "pinky")
BRAINCO_NUM_MOTORS = len(BRAINCO_MOTOR_NAMES)
BRAINCO_MAX_AGE_SEC = 0.25

DEPTH_CAMERA_RGB_FEATURE = "observation.images.depth_camera_rgb"
DEPTH_CAMERA_FEATURE = "observation.images.depth_camera"
