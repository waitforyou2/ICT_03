# CodeGraph 操作手册

使用 `work/setup.sh` 安装的固定版本官方 CodeGraph CLI。使用 setup 脚本设置的环境变量关闭遥测，或手动设置：

```bash
export CODEGRAPH_TELEMETRY=0
export DO_NOT_TRACK=1
export CODEGRAPH_NO_DAEMON=1
```

始终传入准确的代码根目录。在上层工作区初始化会造成根目录混淆和查询不完整。

```bash
codegraph init "$CODE_ROOT"
codegraph status "$CODE_ROOT"
codegraph files --path "$CODE_ROOT" --max-depth 3
```

## 查询顺序

先使用范围窄、结构化的操作，再进行语义探索：

1. `query <term> --path "$CODE_ROOT" --limit 20 --json`
2. `node <symbol> --path "$CODE_ROOT"`
3. `callers <symbol> --path "$CODE_ROOT"`
4. `callees <symbol> --path "$CODE_ROOT"`
5. `impact <symbol> --path "$CODE_ROOT" --depth 2 --json`
6. `affected <changed-files> --path "$CODE_ROOT" --json`
7. `explore "<anchored behavior question>" --path "$CODE_ROOT" --max-files 6`

不要从宽泛的 `explore` 查询开始。它会返回原始源码，可能占用大量上下文。每次探索都必须锚定具体契约、符号、事件、路由或模块，并限制包含的文件数。

## 修复时适合追问的问题

- 哪个 Controller 方法会到达这个 Service，它返回什么状态码？
- 谁调用了这次状态修改，是否存在绕过保护条件的替代路径？
- 哪些监听器消费这个事件，它们的失败是否与发布事务隔离？
- 当前模块是否导入或注入了其他模块的 Repository 或 Entity？
- 修改该符号会影响哪些测试和公开入口？
- 是否存在能够推翻“行为缺失”结论的替代实现？

修改后执行：

```bash
codegraph sync "$CODE_ROOT"
codegraph affected --path "$CODE_ROOT" --stdin --json < changed-files.txt
```

最终交付前，把必要的图证据写入报告，并使用 `codegraph uninit --force "$CODE_ROOT"` 删除索引。
