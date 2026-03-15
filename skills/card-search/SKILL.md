---
name: card-search
description: 用于查询 Weiss Schwarz (WS) 卡牌的详细信息、效果文本、俗语、专有名词、特定概念及相关规则。当用户询问卡牌效果、属性、ID、俗语、专有名词、特定概念或相关规则时调用此技能。
---

# Card Search Skill

## 概述 (Overview)
本技能提供对 Weiss Schwarz 卡牌数据库和规则书的检索能力。
核心功能是通过 RAG (检索增强生成) 技术，从本地向量数据库中查找卡牌的英文原始数据，并将其**翻译为中文**反馈给用户。
同时支持对游戏规则的查询辅助。

## 约束与规则 (Constraints)
- **必须优先使用工具**：执行查询时，**必须且只能首先**调用 `skills/card-search/card_search.py` 脚本。
- **必须使用 Python 解释器调用脚本**：调用 `card_search.py` 时，必须使用 `./venv/bin/python3`（或等价的 `python3`）作为前缀。禁止直接执行 `.py` 文件路径，否则会被 shell 误当作脚本解析并报错（如 `from: command not found`）。
- **禁止直接遍历数据库**：在未获得用户明确许可前，**严禁**直接读取 `data/Card_DB` 目录下的所有文件或使用 `grep` 等命令进行全量搜索。这会消耗大量资源并导致性能问题。
- **低置信度处理**：如果 `card_search.py` 返回的结果完全不正确、相关性低或未找到预期结果，**必须**先向用户报告情况，并询问：“搜索工具未找到准确结果，是否允许我直接对数据库进行全量检索？（这可能需要较长时间）”。只有在用户回复“是”或“确认”后，才允许使用其他手段（如 `grep` 或遍历文件）进行搜索。
- **禁止自行生成代码**：严禁编写新的 Python 脚本来尝试连接数据库或读取文件，必须使用现有的 RAG 工具。
- **强制中文翻译**：数据库返回的内容通常是英文的，你**必须**将所有卡牌效果、特征、名称等信息翻译成流畅的中文游戏术语。

## 工具定义 (Tools)

# card_search.py
用于查询知识库的核心工具。

- **输入参数**:
  - `query` (string): 用户的自然语言查询或关键词。应主要包含卡牌名称、特征、编号或规则关键词，并且在查询中包含"检索"前缀。
  - `category` (string, optional): 查询类别。可选值为 `"card"` (仅查卡牌), `"rule"` (仅查规则), `"all"` (默认，查所有)。

- **输入示例**:
  - `export PYTHONPATH=$PYTHONPATH:. && ./venv/bin/python3 skills/card-search/card_search.py "检索Armin Level 0" --category card`
  - `export PYTHONPATH=$PYTHONPATH:. && ./venv/bin/python3 skills/card-search/card_search.py "检索Encore step" --category rule`
  - 错误示例（禁止）：`export PYTHONPATH=$PYTHONPATH:. && /Volumes/T7/WS_Agent/skills/card-search/card_search.py "检索Takamatsu Tomori" --category card`
  
- **预期输出**:
  - 返回一个字符串，包含从英文数据库中检索到的卡牌原始文本信息或规则片段。

## 执行流程与指令 (Instructions)

### 1. 意图识别与类别选择 (Intent Recognition & Category Selection)
当用户输入包含以下意图时，**必须**调用此技能，并根据意图选择正确的 `category` 参数：

- **查卡牌 (category="card")**:
  - 用户询问具体卡牌的效果、数值、属性。
  - **重要**: 如果用户输入的查卡角色是中文名，**务必先调用 `search_web` 工具获取该角色的英文名和所属作品**，再执行 `card_search.py` 脚本。
  - 示例: "查一下这张卡的效果", "这张卡是几级的", "搜索名为 [Name] 的卡"
  
- **查规则 (category="rule")**:
  - 用户询问游戏流程、特定关键词，俗语等名称定义、裁定。
  - 示例: "什么是 [Keyword] 效果", "安可步骤怎么处理", "联动是什么意思"

- **混合查询 (category="all")**:
  - 用户问题既涉及卡牌又涉及规则，或意图不明确。
  - 示例: "帮我找几张强力的三级联动卡，并解释一下什么是联动"

### 2. 构建查询 (Query Construction)
- **目标识别**: 提取用户提到的卡牌名称、系列或特征。
- **中英文转换**:
  - **规则**: 数据库仅包含英文数据。
  - **强制执行**: 遇到中文角色名或系列名，**必须先使用 `search_web`** 搜索该角色的官方英文名及所属系列英文名。
  - **示例**: 用户输入 "千早爱音"，你应先搜索 "千早爱音 英文名 Weiss Schwarz"，得知是 "Anon Chihaya" (BanG Dream! It's MyGO!!!!!)。
  - **构建 Query**: 使用搜索到的英文名调用 `card_search.py` 
  (例如: `export PYTHONPATH=$PYTHONPATH:. && ./venv/bin/python3 skills/card-search/card_search.py "检索Anon Chihaya" --category card`)，在查询中包含"检索"前缀。
- **调用工具**: `export PYTHONPATH=$PYTHONPATH:. && ./venv/bin/python3 skills/card-search/card_search.py "检索[English Name]" --category card`

### 3. 结果处理与反馈 (Response Generation)
工具返回英文结果后，按以下格式处理：

#### A. 卡牌信息 (Card Info)
将检索到的英文卡牌信息**完整翻译成中文**，并按结构化格式输出：
- **卡牌名称**: [中文译名] (原文名称)
- **编号**: [卡牌编号]
- **基本属性**: 颜色、等级、费用、魂、触发、特征（全部中文化）
- **效果文本**: **(重点)** 将卡牌的英文效果文本翻译为准确、流畅的中文游戏术语。
  - *术语对照*:
    - Waiting Room -> 休息室/墓地
    - Climax -> 高潮卡
    - Stock -> 库存/费
    - Encore -> 再演
    - Brainstorm -> 集中
- **Flavor Text**: (可选) 卡面引言的翻译。

#### B. 规则说明 (Rules)
仅在用户询问规则或卡牌效果涉及复杂机制时补充规则说明。

#### C. 异常处理
- **未找到**: "很抱歉，在数据库中未找到相关卡牌。请确认卡名或提供更多关键词。"
- **多结果**: "找到多张相关卡牌，请明确您想查询的是哪一张："（列出选项）
