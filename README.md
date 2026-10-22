# Any-Task BrainCo Data Collection — Host

This folder is a separate, minimal copy of the part of `Teleop-Data-Collection`. It records the state of the G1 robot, BrainCo hands, and the `ego_view` RGB camera. The exporter asks for `Task to record:` and saves the dataset to `outputs/<task>-<timestamp>/` relative to this folder.

## Folder contents

- `launch_brainco_any_task_host_tmux.sh` — starts the exporter and the camera viewer on the host in tmux.
- `gear_sonic/scripts/brainco_data_exporter_any_task/` — data collection code, BrainCo DDS support, and the dataset schema.
- `gear_sonic/scripts/run_data_exporter.py`, `gear_sonic/data/`, `gear_sonic/utils/data_collection/` — required shared exporter components.
- `gear_sonic/scripts/run_camera_viewer.py`, `gear_sonic/camera/` — the `ego_view` viewer and the ZMQ camera client.
- `gear_sonic/data/robot_model/model_data/g1/g1_29dof_with_hand.urdf` — the model used for forward kinematics (FK). Visual geometry was removed, so mesh files are not required.


## Host setup

You need `uv`, `tmux`, network access to the robot, and a local `unitree_sdk2_python` installation. The commands in this guide are for Linux hosts.

Unless stated otherwise, run host-side commands from the root directory of this repository.

### Install Unitree SDK2 Python

Clone `unitree_sdk2_python` and Cyclone DDS into the home directory of the host user. The SDK requires Cyclone DDS 0.10.x. The following commands install both projects under `$HOME`:

```bash
sudo apt update
sudo apt install -y git cmake build-essential

cd "$HOME"
git clone --branch releases/0.10.x https://github.com/eclipse-cyclonedds/cyclonedds.git
cmake -S cyclonedds -B cyclonedds/build \
  -DCMAKE_INSTALL_PREFIX="$HOME/cyclonedds/install"
cmake --build cyclonedds/build --target install -j"$(nproc)"

git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
```

If either directory already exists, do not clone it again; update it with `git -C <directory> pull` if needed. Before installing the SDK into the project environment, set `CYCLONEDDS_HOME` to the Cyclone DDS installation directory:

```bash
export CYCLONEDDS_HOME="$HOME/cyclonedds/install"
```

Create the project virtual environment with Python 3.10 once, activate it, and install the dependencies:

```bash
uv python install 3.10
uv venv .venv_data_collection --python 3.10
source .venv_data_collection/bin/activate
GIT_LFS_SKIP_SMUDGE=1 uv pip install -r requirements.txt
uv pip install -e "$HOME/unitree_sdk2_python"
uv pip install --reinstall --no-deps opencv-python==4.11.0.86
```

`uv pip install -e "$HOME/unitree_sdk2_python"` installs the local SDK in editable mode. Keep `CYCLONEDDS_HOME` set in every terminal where you install or rebuild the SDK. If the installation reports `Could not locate cyclonedds`, check that the path exists and set `CYCLONEDDS_HOME` again.


```bash
source .venv_data_collection/bin/activate
```



### Optional: voice prompts

Voice prompts require the system `espeak` package. Install it on Ubuntu or Debian with:

```bash
sudo apt update
sudo apt install -y espeak
```

Data collection starts without it, but voice prompts may not work. If a ready environment from the original project already exists, pass it to the launcher with `DATA_COLLECTION_VENV=<path-to-original-project>/.venv_data_collection`.


The `wlp128s20f3` interface in the examples is the **host** network interface for BrainCo DDS. It must be the adapter connected to the robot network, not a VPN, Docker, or loopback interface. If your interface has a different name, replace `PICO_INTERFACE`/`--brainco-network-interface` with yours. The address `192.168.50.132` is the robot address that provides the ZMQ streams.

To find the interface used to reach the robot, replace `192.168.50.132` with your robot IP if necessary:

| Operating system | Command | Use this value |
| --- | --- | --- |
| Linux | `ip route get 192.168.50.132` | The name after `dev`, for example `enp3s0` or `wlp128s20f3`. To list all interfaces, run `ip -br link`. |
| macOS | `route -n get 192.168.50.132` | The value after `interface:`, for example `en0`. To see adapter names, run `networksetup -listallhardwareports`. |
| Windows (PowerShell) | <code>Get-NetRoute -DestinationPrefix 192.168.50.132/32 &#124; Sort-Object RouteMetric &#124; Select-Object -First 1 -ExpandProperty InterfaceAlias</code> | The returned adapter name, for example `Ethernet` or `Wi-Fi`. You can also list adapters with `Get-NetAdapter`. |

The launcher and setup commands in this repository require Linux. The macOS and Windows commands above are useful for identifying the adapter name when configuring a machine or checking network connectivity; run the exporter on a supported Linux host.

## Start with tmux

First, start the processes on the robot (see below). Then, on the host:

```bash
ROBOT_HOST=192.168.50.132 \
PICO_INTERFACE=wlp128s20f3 \
bash launch_brainco_any_task_host_tmux.sh
tmux attach -t brainco_any_task_host
```

Enter the task name in the `exporter` window. The `viewer` window shows `ego_view`. To switch tmux windows, press `Ctrl-b`, then `n` or `p`. To detach, press `Ctrl-b`, then `d`.

To restart an existing session:

```bash
ROBOT_HOST=192.168.50.132 bash launch_brainco_any_task_host_tmux.sh --replace
```


## Host: start processes separately

After starting the robot processes, open two terminals.

### Terminal 1 — data exporter

```bash
source .venv_data_collection/bin/activate

python -m gear_sonic.scripts.brainco_data_exporter_any_task \
  --camera-host 192.168.50.132 \
  --camera-port 5555 \
  --sonic-zmq-host 192.168.50.132 \
  --sonic-zmq-port 5556 \
  --state-zmq-host 192.168.50.132 \
  --state-zmq-port 5557 \
  --brainco-network-interface wlp128s20f3 \
  --depth-camera-width 1280 \
  --depth-camera-height 720
```

Enter a task name when prompted with `Task to record:`. The data will be saved to `outputs/<task>-<timestamp>/`.

### Terminal 2 — ego-view viewer

```bash
source .venv_data_collection/bin/activate

python -m gear_sonic.scripts.run_camera_viewer \
  --camera-host 192.168.50.132 \
  --camera-port 5555 \
  --camera-streams ego_view \
  --no-depth \
  --grid-columns 1 \
  --no-motor-states
```

## Robot: start with tmux

The robot uses the **original** project and its original launcher:

```bash
cd /home/unitree/teleop-ws/Teleop-Data-Collection
bash gear_sonic/scripts/launch_brainco_any_task_robot_tmux.sh
tmux attach -t brainco_any_task_robot
```

To restart an existing session:

```bash
bash gear_sonic/scripts/launch_brainco_any_task_robot_tmux.sh --replace
```

As noted in the original instructions: if the robot starts moving strangely at a high frequency, stop the deploy process and the daemon container:

```bash
sudo docker stop 15f8798287b672dac5192885794060781cde1df1a969f78ff4ec77cb6e94f56c
```

## Robot: start processes separately

Run each block in a separate terminal on the robot, in the following order.

### Terminal 1 — BrainCo service

```bash
cd /home/unitree/teleop-ws/Teleop-Data-Collection
bash gear_sonic/scripts/start_brainco_and_check.sh \
  --container g1-brainco-hand-server \
  --attempts 10 \
  --interface wlxfc23cd997021
```

### Terminal 2 — ego-view camera

```bash
source /home/unitree/GR00T-WholeBodyControl/.venv_camera/bin/activate
cd /home/unitree/teleop-ws/Teleop-Data-Collection

python -m gear_sonic.camera.composed_camera \
  --ego-view-camera realsense \
  --ego-view-device-id 243422071979 \
  --realsense-width 1280 \
  --realsense-height 720 \
  --no-realsense-depth \
  --fps 15 \
  --port 5555
```

### Terminal 3 — Pico manager

```bash
source /home/unitree/GR00T-WholeBodyControl/.venv_teleop/bin/activate
cd /home/unitree/teleop-ws/Teleop-Data-Collection

python -m gear_sonic.scripts.pico_manager_brainco_dexterous \
  --manager \
  --port 5556 \
  --target_fps 50 \
  --brainco_network_interface wlxfc23cd997021
```

### Terminal 4 — Gear Sonic deploy

```bash
export TensorRT_ROOT="$HOME/TensorRT"
cd /home/unitree/GR00T-WholeBodyControl/gear_sonic_deploy
source scripts/setup_env.sh
./deploy.sh --input-type zmq_manager real
```

## Episode controls

- Left grip + `A`: start or finish an episode.
- Left grip + `B`: save the current episode as discarded.
- Right grip: add a timestamp marker.

## Robot control with Pico

- `A` + `B` + `X` + `Y`: start body-tracking calibration; press again to stop streaming (emergency stop).
- `A` + `B`: enable and switch the walking mode.
- `A` + `X`: toggle Pose mode (pause/resume pose streaming); the robot holds its last pose while paused.

