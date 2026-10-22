#!/usr/bin/env bash
# Start the host-side exporter and ego-view viewer for arbitrary tasks.

set -Eeuo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
SESSION="${TMUX_SESSION:-brainco_any_task_host}"
REPLACE_SESSION=0

if [[ "${1:-}" == "--replace" ]]; then
    REPLACE_SESSION=1
elif [[ $# -gt 0 ]]; then
    echo "Usage: $0 [--replace]" >&2
    exit 2
fi

command -v tmux >/dev/null || {
    echo "tmux is required. Install it with: sudo apt install tmux" >&2
    exit 1
}

if tmux has-session -t "$SESSION" 2>/dev/null; then
    if [[ $REPLACE_SESSION -eq 0 ]]; then
        echo "tmux session '$SESSION' already exists." >&2
        echo "Attach: tmux attach -t $SESSION" >&2
        echo "Replace: $0 --replace" >&2
        exit 1
    fi
    tmux kill-session -t "$SESSION"
fi

DATA_COLLECTION_VENV="${DATA_COLLECTION_VENV:-$PROJECT_DIR/.venv_data_collection}"
if [[ ! -f "$DATA_COLLECTION_VENV/bin/activate" ]]; then
    echo "Python environment not found: $DATA_COLLECTION_VENV" >&2
    echo "Create it using the instructions in README.md, or set DATA_COLLECTION_VENV." >&2
    exit 1
fi
ROBOT_HOST="${ROBOT_HOST:-192.168.50.132}"
CAMERA_HOST="${CAMERA_HOST:-$ROBOT_HOST}"
SONIC_HOST="${SONIC_HOST:-$ROBOT_HOST}"
STATE_HOST="${STATE_HOST:-$ROBOT_HOST}"
CAMERA_PORT="${CAMERA_PORT:-5555}"
SONIC_PORT="${SONIC_PORT:-5556}"
STATE_PORT="${STATE_PORT:-5557}"
PICO_INTERFACE="${PICO_INTERFACE:-wlp128s20f3}"
ENABLE_CAMERA_VIEWER="${ENABLE_CAMERA_VIEWER:-1}"
EXPORTER_EXTRA_ARGS="${EXPORTER_EXTRA_ARGS:-}"
if [[ "$ENABLE_CAMERA_VIEWER" != "0" && "$ENABLE_CAMERA_VIEWER" != "1" ]]; then
    echo "ENABLE_CAMERA_VIEWER must be 0 or 1" >&2
    exit 2
fi

tmux new-session -d -s "$SESSION" -n exporter
tmux set-option -t "$SESSION" -g mouse on

exporter_command="source $DATA_COLLECTION_VENV/bin/activate && cd $PROJECT_DIR && python -m gear_sonic.scripts.brainco_data_exporter_any_task --camera-host $CAMERA_HOST --camera-port $CAMERA_PORT --sonic-zmq-host $SONIC_HOST --sonic-zmq-port $SONIC_PORT --state-zmq-host $STATE_HOST --state-zmq-port $STATE_PORT --brainco-network-interface $PICO_INTERFACE --depth-camera-width 1280 --depth-camera-height 720 $EXPORTER_EXTRA_ARGS"
tmux send-keys -t "$SESSION:exporter" "$exporter_command" C-m

if [[ "$ENABLE_CAMERA_VIEWER" == "1" ]]; then
    tmux new-window -d -t "$SESSION" -n viewer
    viewer_command="source $DATA_COLLECTION_VENV/bin/activate && cd $PROJECT_DIR && python -m gear_sonic.scripts.run_camera_viewer --camera-host $CAMERA_HOST --camera-port $CAMERA_PORT --camera-streams ego_view --no-depth --grid-columns 1 --no-motor-states"
    tmux send-keys -t "$SESSION:viewer" "$viewer_command" C-m
fi

tmux select-window -t "$SESSION:exporter"
echo "Started host-side session: $SESSION"
echo "Enter the task name in the exporter window."
echo "Attach: tmux attach -t $SESSION"
