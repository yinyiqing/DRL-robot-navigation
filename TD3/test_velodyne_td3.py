import os
import socket
import time
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.tensorboard import SummaryWriter

from velodyne_env import GazeboEnv


class Actor(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(Actor, self).__init__()

        self.layer_1 = nn.Linear(state_dim, 800)
        self.layer_2 = nn.Linear(800, 600)
        self.layer_3 = nn.Linear(600, action_dim)
        self.tanh = nn.Tanh()

    def forward(self, s):
        s = F.relu(self.layer_1(s))
        s = F.relu(self.layer_2(s))
        a = self.tanh(self.layer_3(s))
        return a


class TD3(object):
    def __init__(self, state_dim, action_dim):
        self.actor = Actor(state_dim, action_dim).to(device)

    def get_action(self, state):
        state = torch.Tensor(state.reshape(1, -1)).to(device)
        return self.actor(state).cpu().data.numpy().flatten()

    def load(self, filename, directory):
        self.actor.load_state_dict(
            torch.load("%s/%s_actor.pth" % (directory, filename), map_location=device)
        )


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
seed = 0
max_ep = 500
file_name = "TD3_velodyne"
launchfile = os.environ.get("DRL_TEST_LAUNCHFILE", "multi_robot_scenario_headless.launch")
resume_testing = True
state_path = "./checkpoints/TD3_velodyne_test_state.pt"
test_stats_path = "./results/TD3_velodyne_test.npy"
print_every_episodes = 10


def make_test_run_dir():
    timestamp = datetime.now().strftime("%b%d_%H-%M-%S")
    return os.path.join("runs", f"test_{timestamp}_{socket.gethostname()}")


def load_test_state():
    if not (resume_testing and os.path.exists(state_path)):
        return None
    return torch.load(state_path, map_location="cpu")


def save_test_state(payload):
    os.makedirs("./checkpoints", exist_ok=True)
    torch.save(payload, state_path)


def append_stats(record):
    os.makedirs("./results", exist_ok=True)
    if os.path.exists(test_stats_path):
        history = list(np.load(test_stats_path, allow_pickle=True))
    else:
        history = []
    history.append(record)
    np.save(test_stats_path, np.array(history, dtype=object))


environment_dim = 20
robot_dim = 4
env = GazeboEnv(launchfile, environment_dim)
time.sleep(5)
torch.manual_seed(seed)
np.random.seed(seed)
state_dim = environment_dim + robot_dim
action_dim = 2

network = TD3(state_dim, action_dim)
try:
    network.load(file_name, "./pytorch_models")
except Exception:
    raise ValueError("Could not load the stored model parameters")

test_state = load_test_state() or {}
episode_num = test_state.get("episode_num", 0)
total_steps = test_state.get("total_steps", 0)
success_count = test_state.get("success_count", 0)
collision_count = test_state.get("collision_count", 0)
start_time = time.time()
recent_rewards = []
recent_success = []
recent_collision = []
log_dir = make_test_run_dir()
writer = SummaryWriter(log_dir=log_dir)

print("==============================================")
print("Test version: single-agent-eval-v1-headless")
print("Test process PID:", os.getpid())
print("Launchfile:", launchfile)
print("Device:", device)
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
print("TensorBoard log dir:", log_dir)
print("State path:", state_path)
print("Resume mode:", resume_testing)
print("Starting episode:", episode_num)
print("Starting total steps:", total_steps)
print("==============================================")

done = False
episode_timesteps = 0
state = env.reset()
episode_reward = 0.0
episode_target = False
episode_collision = False
episode_start_time = time.time()

while True:
    action = network.get_action(np.array(state))
    a_in = [(action[0] + 1) / 2, action[1]]
    next_state, reward, done, target = env.step(a_in)
    total_steps += 1
    episode_reward += reward
    episode_timesteps += 1
    episode_target = episode_target or bool(target)
    episode_collision = episode_collision or bool(env.last_step_info["collision"])

    if episode_timesteps >= max_ep:
        done = True

    if done:
        episode_num += 1
        elapsed = time.time() - episode_start_time
        steps_per_sec = episode_timesteps / elapsed if elapsed > 0 else 0.0
        final_distance = env.last_step_info["distance"]

        success_count += int(episode_target)
        collision_count += int(episode_collision)
        recent_rewards.append(episode_reward)
        recent_success.append(int(episode_target))
        recent_collision.append(int(episode_collision))

        avg_reward = float(np.mean(recent_rewards[-print_every_episodes:]))
        avg_success = float(np.mean(recent_success[-print_every_episodes:]))
        avg_collision = float(np.mean(recent_collision[-print_every_episodes:]))

        print(
            "Episode %i complete | total_step=%i | episode_steps=%i | reward=%.3f | "
            "target=%i | collision=%i | final_distance=%.3f | steps/sec=%.3f"
            % (
                episode_num,
                total_steps,
                episode_timesteps,
                episode_reward,
                int(episode_target),
                int(episode_collision),
                final_distance if final_distance is not None else float("nan"),
                steps_per_sec,
            )
        )

        if episode_num % print_every_episodes == 0:
            print(
                "Recent %i episodes | avg_reward=%.3f | success_rate=%.3f | collision_rate=%.3f | "
                "success_count=%i | collision_count=%i"
                % (
                    print_every_episodes,
                    avg_reward,
                    avg_success,
                    avg_collision,
                    success_count,
                    collision_count,
                )
            )

        writer.add_scalar("test/episode_reward", episode_reward, episode_num)
        writer.add_scalar("test/episode_success", int(episode_target), episode_num)
        writer.add_scalar("test/episode_collision", int(episode_collision), episode_num)
        writer.add_scalar("test/final_distance", final_distance, episode_num)
        writer.add_scalar("test/steps_per_sec", steps_per_sec, episode_num)
        writer.add_scalar("test/recent_avg_reward", avg_reward, episode_num)
        writer.add_scalar("test/recent_success_rate", avg_success, episode_num)
        writer.add_scalar("test/recent_collision_rate", avg_collision, episode_num)
        writer.flush()

        save_test_state(
            {
                "episode_num": episode_num,
                "total_steps": total_steps,
                "success_count": success_count,
                "collision_count": collision_count,
                "last_episode_reward": episode_reward,
            }
        )
        append_stats(
            [
                episode_num,
                total_steps,
                episode_timesteps,
                episode_reward,
                int(episode_target),
                int(episode_collision),
                final_distance,
            ]
        )

        state = env.reset()
        done = False
        episode_timesteps = 0
        episode_reward = 0.0
        episode_target = False
        episode_collision = False
        episode_start_time = time.time()
    else:
        state = next_state
