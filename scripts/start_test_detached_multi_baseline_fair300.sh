#!/usr/bin/env bash
set -eo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TD3_DIR="$PROJECT_ROOT/TD3"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/.test_multi_baseline_fair300_detached.pid"
LAUNCHFILE="multi_robot_scenario_multi_2.launch"
ROS_PORT="11351"
GAZEBO_PORT="11391"

mkdir -p "$LOG_DIR"

timestamp="$(date +%Y%m%d_%H%M%S)"
log_file="$LOG_DIR/test_multi_baseline_fair300_detached_${timestamp}.log"

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "A detached baseline fair300 test process is already running with PID $old_pid"
    exit 1
  fi
fi

setsid bash -lc "
  source /opt/ros/noetic/setup.bash
  source '$PROJECT_ROOT/env.python.sh'
  export ROS_HOSTNAME=localhost
  export ROS_MASTER_URI=http://localhost:${ROS_PORT}
  export ROS_PORT_SIM=${ROS_PORT}
  export GAZEBO_MASTER_URI=http://localhost:${GAZEBO_PORT}
  export GAZEBO_RESOURCE_PATH='$PROJECT_ROOT/catkin_ws/src/multi_robot_scenario/launch'
  export DRL_MULTI_TEST_LAUNCHFILE='$LAUNCHFILE'
  export DRL_MULTI_TEST_FILE_NAME='TD3_velodyne_multi_v4'
  export DRL_MULTI_TEST_STATE_PATH='./checkpoints/TD3_velodyne_multi_v4_baseline_fair300_test_state.pt'
  export DRL_MULTI_TEST_STATS_PATH='./results/TD3_velodyne_multi_v4_baseline_fair300_test.npy'
  export DRL_MULTI_TEST_TARGET_EPISODES='300'
  cd '$PROJECT_ROOT/catkin_ws'
  source devel_isolated/setup.bash
  cd '$TD3_DIR'
  exec python3 -u test_velodyne_td3_multi.py
" >"$log_file" 2>&1 < /dev/null &

echo $! > "$PID_FILE"

echo "Detached baseline fair300 test started."
echo "PID: $(cat "$PID_FILE")"
echo "Log: $log_file"
