# 项目规则：验证策略

## 不要自动触发全量回归

每轮改动完成后，**只验证与本轮改动直接相关的部分**。全量回归（全量单测、in-Anki 全量自测）
属于「需批准」操作：如果认为本轮必须跑全量（例如改动触及共享内核、多模块交叉、或相关
验证覆盖不到风险点），**先说明理由、征得用户同意后才执行**，不得自行启动。

### 可以自动运行（相关验证，无需询问）

- Python 语法检查：`python -m py_compile <改过的文件>.py`
- web 模板内嵌 JS 语法检查：提取 `<script>` 内容后 `node --check`
  （`language_study_anki/web/*.html`）
- 改动涉及 openspec 规格时：`openspec validate --all`（秒级，只校验规格格式）
- 与改动直接对应的**单个**单元测试文件，例如：
  `python -m unittest tests.test_hub`（按需挑选，不跑 discover）
- 代码走查：读改动及其调用方，确认行为符合预期

### 必须先询问、获得批准后才能运行（全量回归）

- 全量单元测试：`python -m unittest discover -s tests`（约 150 项）
- in-Anki 全量自测：`LSA_SELFTEST=1 tools/scratch-anki.sh [--fresh]`
  （启动一个 scratch Anki 实例，运行全部 17 项检查，耗时数分钟，会弹出窗口）
- 其他任何明显属于「全量回归」的命令或组合

### 每轮收尾要求

在总结中明确说明：**验证了什么、没有验证什么**。如果因为本规则没有跑全量回归，
要指出剩余风险点（例如「in-Anki 自测未运行，键盘行为仅经 `node --check` 与走查」），
让用户自行决定是否批准补跑。
