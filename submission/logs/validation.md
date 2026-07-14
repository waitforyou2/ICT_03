# 验证记录

日期：2026-07-14（Asia/Shanghai）

- 官方 npm 包确认：`@colbymchenry/codegraph@1.4.1`，CLI 输出版本 `1.4.1`。
- npm 私有目录安装：通过；没有使用全局权限。
- CodeGraph 首次 `init`：通过。
- CodeGraph 图反证：6/6 `explore` 成功。
- 公开基准：6/6 已知主题全部命中；正式问题数为 6。
- 自建题：命名常量、硬上限、TODO、分支抢占、MUST NOT 开关、MAY 负向、合规负向、替代实现反证、证据复核均通过。
- Python 测试：7 个测试方法通过。
- Skill：`quick_validate.py` 通过（`Skill is valid!`）。

分析输入只有源码、benchmark 和 RFC 缓存；`Difference/issues` 只用于测试结束后的人工对照，不进入工具运行路径。
