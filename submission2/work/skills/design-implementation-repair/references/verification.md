# 验证策略

验证必须形成证据，而不是走形式。每次补丁后运行范围最小但有效的检查，完成前运行完整验收阶梯。

## 随附验证器

```bash
python3 "$SKILL_ROOT/scripts/verify_project.py" \
  --assets "$ASSET_ROOT" --code "$CODE_ROOT" \
  --output "$OUTPUT_ROOT/verification" --phase compile

python3 "$SKILL_ROOT/scripts/verify_project.py" \
  --assets "$ASSET_ROOT" --code "$CODE_ROOT" \
  --output "$OUTPUT_ROOT/verification" --phase public
```

阶段含义：

- `compile`：编译整个 Maven reactor 的生产源码和测试源码，但不运行测试；
- `unit`：运行模块单元测试；
- `install`：把修复后的模块安装到赛题提供的本地 Maven 仓库；
- `public`：先安装修复模块，再运行赛题提供的公开黑盒测试；
- `acceptance`：依次执行编译、安装和公开黑盒测试；
- `all`：先运行单元测试，再运行公开黑盒测试。

默认使用赛题材料中提供的 Maven settings 和本地仓库，绝不能静默回退到用户级 Maven 配置。如本地验证环境确需覆盖路径，可显式传入 `--settings`、`--repository`、`--maven` 或 `--java-home`，并在验证记录中保留实际参数。

## 必需的最终检查

1. **编译**：全部 reactor 模块编译成功。
2. **定向行为**：用聚焦的单元测试或已有黑盒场景覆盖被修复规则。
3. **公开验收**：全部公开黑盒测试通过。
4. **受保护文件**：README、设计文档、公开测试和配置与初始快照一致。
5. **API 漂移**：比较全部已记录路由、HTTP Method、Header、请求/响应字段名称与类型、成功状态码和错误信封。
6. **结构复审**：重新查询 CodeGraph 中的模块边界、事件消费者、调用者和受影响测试。
7. **负向扫描**：确认不存在禁止路由、伪造数据、遗留占位实现、重复归属模型、错误舍入和绕过路径。
8. **报告校验**：每个已修复 Finding 都包含计划、补丁和成功验证证据。

修复目标中的单元测试可能编码了过期实现行为。不得只为让它们变绿就修改或忽略测试。如果单元测试与权威设计冲突，只能在同一条 Finding 中同步更新并记录理由。公开黑盒测试属于受保护输入，绝不能修改。

不得声称隐藏测试已经通过。记录准确命令、退出码、测试总数、失败数、错误数、跳过数和日志路径。
