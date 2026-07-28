# 实验步骤索引

统一结构：**对应脚本（入口）→ 方式一键 / 方式二手搓 → 验证**。可复制粘贴手操复现。

| 文档                                     | 对应脚本                         | 内容                             |
| -------------------------------------- | ---------------------------- | ------------------------------ |
| [01-场景A-实验准备.md](./01-场景A-实验准备.md)     | `00-reset-workspace.py`      | 清空 workspaces + 裸仓 + Alice/Bob |
| [02-场景A-实验步骤.md](./02-场景A-实验步骤.md)     | `01-scenario-A-...py`        | 公共 rebase → Bob pull 冲突        |
| [03-场景A-错误解冲突.md](./03-场景A-错误解冲突.md)   | `02-wrong-merge-resolve.py`  | 常规解冲突 → 双胞胎提交                  |
| [04-场景A-正确恢复.md](./04-场景A-正确恢复.md)     | `03-proper-recovery-onto.py` | 错误 merge 后：reset + 自己找 oldTip |
| [05-场景B-实验步骤.md](./05-场景B-实验步骤.md)     | `04-scenario-B-...py`        | `--force` 丢他人提交                |
| [common.md](./common.md)               | `common.py`                  | 公共函数说明（非实验）                    |

## 建议顺序

1. **01** → **02** → 在 `workspaces/bob` 看冲突  
2. **03** → 确认双胞胎提交  
3. **04** → reset 撤掉 WRONG merge，自己找 oldTip，`--onto`  
4. **05**（独立目录 `workspaces-lost/`）

```bash
python scripts/00-reset-workspace.py
python scripts/01-scenario-A-duplicate-history.py
```
