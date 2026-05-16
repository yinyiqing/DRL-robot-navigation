# DRL-robot-navigation 执行文档

本文档整理了本项目在当前机器上的实际可用执行流程，覆盖从开机检查、环境准备、训练启动，到 TensorBoard 监控与效果判断的完整步骤。

适用环境：

- Ubuntu 20.04.6
- Python 3.8.10
- ROS Noetic
- NVIDIA GeForce RTX 4090
- Windows 本地通过 MobaXterm 进行 X11 转发

## 1. 项目路径

项目根目录：

```bash
/home/jiutian/DRL-robot-navigation
```

常用脚本：

- Python 环境激活脚本：
  `/home/jiutian/DRL-robot-navigation/env.python.sh`
- ROS 安装脚本：
  `/home/jiutian/DRL-robot-navigation/scripts/install_ros_noetic_system.sh`
- catkin 编译脚本：
  `/home/jiutian/DRL-robot-navigation/scripts/build_readme_workspace.sh`
- 训练启动脚本：
  `/home/jiutian/DRL-robot-navigation/scripts/run_readme_training.sh`
- 后台训练启动脚本：
  `/home/jiutian/DRL-robot-navigation/scripts/start_training_detached.sh`
- 后台测试启动脚本：
  `/home/jiutian/DRL-robot-navigation/scripts/start_test_detached.sh`
- 重新观察 RViz：
  `/home/jiutian/DRL-robot-navigation/scripts/observe_rviz.sh`
- 停止后台训练：
  `/home/jiutian/DRL-robot-navigation/scripts/stop_training_detached.sh`
- 停止后台测试：
  `/home/jiutian/DRL-robot-navigation/scripts/stop_test_detached.sh`
- 清理旧训练记录：
  `/home/jiutian/DRL-robot-navigation/scripts/clean_training_artifacts.sh`

## 2. 开机后的基础检查

登录服务器后，先确认 Python 和 GPU 正常：

```bash
python3 --version
nvidia-smi
```

预期：

- Python 版本为 `3.8.10`
- `nvidia-smi` 能看到 `NVIDIA GeForce RTX 4090`

## 3. 首次环境安装

本节只需要执行一次。

### 3.1 安装 ROS Noetic

执行：

```bash
sudo bash /home/jiutian/DRL-robot-navigation/scripts/install_ros_noetic_system.sh
```

该脚本会完成：

- 添加 ROS apt 源
- 安装 `ros-noetic-desktop-full`
- 安装 `python3-rosdep`、`python3-rosinstall`、`python3-wstool`
- 初始化 `rosdep`

### 3.2 编译 catkin 工作区

执行：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/build_readme_workspace.sh
```

编译成功后，可用工作区为：

```bash
/home/jiutian/DRL-robot-navigation/catkin_ws
```

### 3.3 Python 隔离环境

本项目当前使用的独立 Python 环境位于：

```bash
/home/jiutian/venvs/drl-robot-nav
```

激活方式：

```bash
source /home/jiutian/DRL-robot-navigation/env.python.sh
```

当前已验证可用的重要依赖包括：

- `torch==2.4.1+cu121`
- `tensorboard==2.14.0`
- `protobuf==4.25.3`
- `numpy==1.24.4`
- `squaternion==2023.9.2`
- `rospkg==1.6.1`
- `catkin_pkg==1.1.0`
- `PyYAML==6.0.3`
- `netifaces==0.11.0`

## 4. Windows 本地图形转发

本项目的训练启动会带起 `rviz`，因此如果你是在 Windows 本地远程运行，必须先打通 X11 转发。

推荐方式：

- 使用 `MobaXterm`

登录后先执行：

```bash
echo $DISPLAY
xclock
```

预期：

- `DISPLAY` 不是空
- `xclock` 能在 Windows 本地弹出小钟表窗口

如果 `xclock` 不能显示，不建议继续启动训练。

## 5. 每次训练前的标准步骤

进入支持 X11 的 MobaXterm 会话后，直接执行：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/run_readme_training.sh
```

这个脚本会自动完成：

- 清理本项目残留的旧 `roscore/roslaunch/gzserver`
- 激活 Python 虚拟环境
- `source /opt/ros/noetic/setup.bash`
- `source catkin_ws/devel_isolated/setup.bash`
- 设置 `ROS_MASTER_URI`、`ROS_HOSTNAME`、`GAZEBO_RESOURCE_PATH`
- 启动训练

注意：

- 不要使用 README 里的 `killall -9 ...`，那样可能影响同机其他任务
- 当前脚本只清理本项目自己的 ROS/Gazebo 残留进程

## 6. 训练启动成功的典型日志

如果训练成功拉起，通常会看到类似输出：

```text
Roscore launched!
Gazebo launched!
SpawnModel: Successfully spawned entity
Velodyne laser plugin ready, 16 lasers
DiffDrive(ns = r1/): Advertise odom on odom
```

这说明：

- ROS 正常
- Gazebo 正常
- 机器人模型成功生成
- 激光雷达插件正常
- 里程计 `odom` 正常发布

## 7. 如何确认训练跑在 4090 上

另开一个终端，执行：

```bash
watch -n 1 nvidia-smi
```

当前训练进程名通常表现为：

```text
python3 train_velodyne_td3.py
```

本项目当前环境已验证：

- PyTorch 版本为 `2.4.1+cu121`
- `torch.cuda.is_available() == True`
- GPU 设备名为 `NVIDIA GeForce RTX 4090`

因此只要训练脚本启动，它默认就会选择 GPU：

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

注意：

- `GPU-Util` 瞬时显示为 `0%` 不代表没在用 GPU
- 该项目包含大量 ROS/Gazebo 仿真开销，GPU 负载往往是间歇式的

## 8. TensorBoard 监控

另开一个终端，执行：

```bash
source /home/jiutian/DRL-robot-navigation/env.python.sh
cd /home/jiutian/DRL-robot-navigation/TD3
tensorboard --logdir runs --bind_all
```

然后在本地浏览器访问：

```text
http://192.168.30.4:6006/
```

如果无法直连，可使用 SSH 端口转发。

### 8.1 已修复的 TensorBoard 兼容问题

当前环境已经修复了：

- `tensorboard 2.14.0`
- 与 `protobuf 5.x` 不兼容

现已固定为：

- `protobuf==4.25.3`

因此正常情况下不应再出现 `MessageToJson() got an unexpected keyword argument 'including_default_value_fields'` 这类错误。

## 9. 后台持续训练与断线续跑

如果你晚上要关掉本地 Windows 电脑，但希望 4090 机器继续训练，不要直接在前台跑 `run_readme_training.sh`，而是用后台脚本：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/start_training_detached.sh
```

作用：

- 不依赖当前 SSH/MobaXterm 会话
- 断开 SSH 后训练仍继续
- 使用无 RViz 的 headless launch，减少图形依赖
- 日志写入项目目录，便于后续排查

启动后会输出：

- 后台训练 PID
- 日志文件路径

例如可查看最新日志：

```bash
tail -f /home/jiutian/DRL-robot-navigation/logs/最新日志文件名
```

### 9.1 后台训练后如何重新看 RViz

第二天重新用 MobaXterm 连上，并确认 `xclock` 能弹窗后，执行：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/observe_rviz.sh
```

前提：

- 后台训练还在运行
- 当前会话有 X11 转发

这会连接到正在运行的 ROS master，并在本地重新打开 RViz 观察同一套训练。

### 9.2 如何停止后台训练

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/stop_training_detached.sh
```

这个脚本会停止这套后台训练对应的进程组。

## 10. 训练过程中的文件输出

训练过程中会逐步产生以下内容：

### 10.1 TensorBoard 日志

目录：

```bash
/home/jiutian/DRL-robot-navigation/TD3/runs
```

如果不断出现新的时间戳目录，说明训练正在持续写日志。

### 10.2 评估结果

目录：

```bash
/home/jiutian/DRL-robot-navigation/TD3/results
```

通常会出现：

```bash
TD3_velodyne.npy
```

### 10.3 模型参数

目录：

```bash
/home/jiutian/DRL-robot-navigation/TD3/pytorch_models
```

通常会出现：

```bash
TD3_velodyne_actor.pth
TD3_velodyne_critic.pth
```

### 10.4 训练断点恢复文件

目录：

```bash
/home/jiutian/DRL-robot-navigation/TD3/checkpoints
```

通常会出现：

```bash
TD3_velodyne_latest.pt
```

这个文件包含：

- actor / critic 参数
- target network 参数
- optimizer 状态
- replay buffer
- 当前 step / epoch / exploration noise
- 当前 TensorBoard 日志目录

因此如果训练中断，再次启动训练时可以接着跑，而不是从 0 开始。

## 11. 如何判断训练是否有效

本项目目标是让小车到达目标点并尽量避免碰撞。

### 11.1 环境中的关键判定阈值

在环境定义里：

- 到达目标阈值：`0.3m`
- 碰撞阈值：`0.35m`

### 11.2 看行为

最直观的判断方式是观察 `rviz`：

- 小车是否开始朝目标点移动
- 是否减少原地转圈
- 是否减少撞墙
- 是否能在一个 episode 内多次成功接近目标

### 11.3 看评估输出

训练脚本会每 `5000` step 做一次评估，并打印类似：

```text
Validating at global_step=5000
Average Reward over 10 Evaluation Episodes, Epoch X: ...
```

可重点关注：

- `Average Reward` 是否逐步上升
- 碰撞行为是否减少
- 是否开始产生稳定的朝目标移动行为

### 11.4 训练早期的正常现象

在训练早期，以下现象通常是正常的：

- 小车原地转圈
- 偶尔后退
- 奖励值很负
- TensorBoard 曲线增长很慢

原因是：

- 初始探索噪声较大
- 有随机探索逻辑
- ROS/Gazebo 步进本身较慢

### 11.5 推荐观察节点

建议按以下节点判断：

- `5k step`：确认训练正常、有第一次验证
- `50k step`：作为第一阶段效果判断点
- `200k step` 以后：再判断是否逐渐学会到达目标

对本项目来说，`50k step` 前仍然学得很差是正常的。

## 12. 训练时你会看到哪些更有用的控制台信息

当前训练脚本已增加以下输出：

- 当前训练进程 PID
- 当前使用的 launchfile
- 当前设备是 `cuda` 还是 `cpu`
- 当前 GPU 名称
- TensorBoard 日志目录
- checkpoint 路径
- 是否为 resume 模式
- 起始 step 和 epoch
- 每个 episode 结束后的：
  - `global_step`
  - `episode_steps`
  - `reward`
  - `expl_noise`
  - `replay` 大小
  - `steps/sec`
- 每次验证时的 `global_step`
- 每次 checkpoint 保存提示

## 13. 如何停止训练

如果要结束当前训练，在训练终端直接按：

```bash
Ctrl+C
```

不要使用全局 `killall -9 ...`。

如果训练中断后需要重新开始，直接重新运行：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/run_readme_training.sh
```

脚本会自动清理本项目残留进程。

## 14. 如何恢复训练

如果训练因为网络断开、手动停止、窗口关闭或其他原因中断，只要 checkpoint 文件还在，就可以继续：

前台恢复：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/run_readme_training.sh
```

后台恢复：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/start_training_detached.sh
```

恢复时控制台会打印类似：

```text
Resumed training from checkpoint: ./checkpoints/TD3_velodyne_latest.pt
```

如果你已经跑到第 10 次评估附近，再恢复后会继续往后跑，不必重新从头训练。

## 15. 如何测试已训练模型

当 `pytorch_models` 中已有模型文件后，可以执行测试：

```bash
source /home/jiutian/DRL-robot-navigation/env.python.sh
source /opt/ros/noetic/setup.bash
cd /home/jiutian/DRL-robot-navigation/catkin_ws
source devel_isolated/setup.bash
cd /home/jiutian/DRL-robot-navigation/TD3
python3 test_velodyne_td3.py
```

如果你想像训练一样让测试在后台继续跑，直接执行：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/start_test_detached.sh
```

后台测试默认使用 headless launch，不会主动打开 RViz。  
你之后可以再单独执行：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/observe_rviz.sh
```

来重新观察同一套 ROS/Gazebo 运行状态。

测试日志会写到：

```bash
/home/jiutian/DRL-robot-navigation/logs/test_detached_*.log
```

测试状态会写到：

```bash
/home/jiutian/DRL-robot-navigation/TD3/checkpoints/TD3_velodyne_test_state.pt
```

注意：

- 测试不像训练那样需要保存 optimizer 或 replay buffer
- 这里保存的是测试进度和统计信息，方便断线后继续看结果

测试脚本会加载：

```bash
./pytorch_models/TD3_velodyne_actor.pth
```

并持续运行策略。

## 16. 如何删除旧 TensorBoard 曲线和旧训练结果

如果你想把以前的训练曲线、结果和模型都清掉，执行：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/clean_training_artifacts.sh
```

会清理：

- `TD3/runs` 下旧 TensorBoard 日志
- `TD3/results` 下旧评估结果
- `TD3/pytorch_models` 下旧模型
- `TD3/checkpoints` 下断点恢复文件
- `logs/` 下后台训练日志

注意：

- 这会删除本项目现有训练成果
- 不会影响别的项目
- 建议先确认没有正在运行的训练

## 17. 常见问题

### 17.1 `DISPLAY` 为空

现象：

- `echo $DISPLAY` 无输出
- `xclock` 报错
- `rviz` 无法启动

处理：

- 用 `MobaXterm`
- 确保 X11 forwarding 正常

### 17.2 `gzserver` 反复退出

常见原因：

- 之前的 `roscore/gzserver` 残留占住端口

处理：

- 直接重新运行 `run_readme_training.sh`
- 脚本会自动清理本项目旧进程

### 17.3 TensorBoard 页面报 `protobuf` 相关错误

处理：

- 确认当前环境中 `protobuf==4.25.3`
- 停掉 TensorBoard 后重新启动

### 17.4 小车只会原地转圈

训练早期这通常正常。

建议：

- 至少跑到 `50k step` 再做第一轮判断
- 不要在几十到几百 step 就判断失败

### 17.5 断开 SSH 后训练会不会停

如果你是用前台方式启动：

- 会停

如果你是用：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/start_training_detached.sh
```

启动：

- 正常情况下不会停
- 本地 Windows 关机后，4090 主机仍会继续训练

## 18. 建议执行顺序总结

首次部署：

```bash
sudo bash /home/jiutian/DRL-robot-navigation/scripts/install_ros_noetic_system.sh
bash /home/jiutian/DRL-robot-navigation/scripts/build_readme_workspace.sh
```

每次训练：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/start_training_detached.sh
```

监控训练：

```bash
watch -n 1 nvidia-smi
```

```bash
source /home/jiutian/DRL-robot-navigation/env.python.sh
cd /home/jiutian/DRL-robot-navigation/TD3
tensorboard --logdir runs --bind_all
```

重新连接后观察 RViz：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/observe_rviz.sh
```

停止后台训练：

```bash
bash /home/jiutian/DRL-robot-navigation/scripts/stop_training_detached.sh
```

测试模型：

```bash
source /home/jiutian/DRL-robot-navigation/env.python.sh
source /opt/ros/noetic/setup.bash
cd /home/jiutian/DRL-robot-navigation/catkin_ws
source devel_isolated/setup.bash
cd /home/jiutian/DRL-robot-navigation/TD3
python3 test_velodyne_td3.py
```
