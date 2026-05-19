# 多智能体动态 Reward 实验计划

## 目标

在当前有效 baseline `multi-agent-shared-policy-v4` 的基础上，尝试局部协同 reward：

```text
reward_i = mean(reward_j for j in [i + visible_neighbors_i])
```

其中 `visible_neighbors_i` 表示机器人 `i` 当前感知范围内的其他机器人。如果没有可见邻居，则退化为自己的原始 reward。

这个实验直接对应：每个机器人当前时刻的 reward 在训练阶段改成它雷达感知范围内所有机器人的 reward 平均，看看能不能学到一些多机协同能力。

## 与现有 baseline 的边界

保持现有 baseline 不变：

- 模型名：`TD3_velodyne_multi_v4`
- checkpoint：`TD3/checkpoints/TD3_velodyne_multi_v4_latest.pt`
- 训练结果：`TD3/results/TD3_velodyne_multi_v4.npy`
- 测试结果：`TD3/results/TD3_velodyne_multi_test.npy`

动态 reward 实验使用独立命名：

- 模型名：`TD3_velodyne_multi_v4_coop`
- checkpoint：`TD3/checkpoints/TD3_velodyne_multi_v4_coop_latest.pt`
- 训练结果：`TD3/results/TD3_velodyne_multi_v4_coop.npy`
- 测试结果：`TD3/results/TD3_velodyne_multi_v4_coop_test.npy`

## 实现口径

- policy：继续使用共享 actor/critic。
- observation：暂时不改
- action：暂时不改
- training reward：开启局部动态 reward 平均。
- evaluation/test reward：关闭动态 reward，使用原始 individual reward 统计，保证能和 baseline 横向比较。
- 可见邻居：当前使用几何近邻近似，按距离和前方视野判断。

## 运行命令

启动动态 reward 训练：

```bash
bash scripts/start_training_detached_multi_coop.sh
```

停止动态 reward 训练：

```bash
bash scripts/stop_training_detached_multi_coop.sh
```

训练会以 `setsid` 后台进程运行，断开 SSH 后仍会继续跑。日志写入 `logs/train_multi_coop_detached_*.log`。

重新连接后观察 RViz：

```bash
bash scripts/observe_rviz_multi_coop.sh
```

训练出 coop 模型后，启动测试：

```bash
bash scripts/start_test_detached_multi_coop.sh
```

停止测试：

```bash
bash scripts/stop_test_detached_multi_coop.sh
```

## 对照实验

当前 baseline 仍然用原来的脚本：

```bash
bash scripts/start_training_detached_multi.sh
bash scripts/start_test_detached_multi.sh
```

比较时重点看：

- `success_rate`
- `collision_rate`
- `full_success_rate`
- `avg_final_distance`
- 是否出现更多互相避让、少互撞、少卡死

## 断点续训

coop 训练 checkpoint 独立保存到：

```text
TD3/checkpoints/TD3_velodyne_multi_v4_coop_latest.pt
```

脚本默认 `resume_training = True`。如果训练到第 10 个 epoch 后中断，下次再次执行：

```bash
bash scripts/start_training_detached_multi_coop.sh
```

训练会从 checkpoint 中恢复网络、优化器、replay buffer、评估列表、样本步数、环境步数、探索噪声和 epoch 计数，继续后面的训练。
