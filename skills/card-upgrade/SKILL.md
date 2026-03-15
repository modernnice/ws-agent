---
name: card-upgrade
description: Check for updates in the Weiss Schwarz card database from GitHub. Use when the user asks to check for updates, sync status, or if the database is up to date.
---

# Card Upgrade Skill

## 概述 (Overview)
此技能用于检查本地 Weiss Schwarz 卡牌数据库 (`data/Card_DB/DB`) 与 GitHub 仓库 (`CCondeluci/WeissSchwarz-ENG-DB`) 的同步状态。
你必须运行 `card_upgrade_check.py` 脚本来获取本地最后同步时间和远程仓库最新提交时间，并据此判断是否需要更新。

## 脚本使用 (Script)

**脚本 1: 检查更新 (Check)**
**脚本路径**: `card_upgrade_check.py`
**功能**: 获取本地与远程数据库的更新时间，判断是否需要更新。
**命令**: `export PYTHONPATH=$PYTHONPATH:. && ./venv/bin/python3 skills/card-upgrade/card_upgrade_check.py`

**脚本 2: 执行更新 (Upgrade)**
**脚本路径**: `card_upgrade.py`
**功能**: 执行增量更新，下载新卡牌数据并同步时间戳。仅在确认有更新时使用。
**命令**: `export PYTHONPATH=$PYTHONPATH:. && ./venv/bin/python3 skills/card-upgrade/card_upgrade.py`

**脚本 3: 向量化入库 (Vectorize)**
**脚本路径**: `rag/vector_store.py`
**功能**: 扫描本地数据目录，将新增或变更的文件切分并存入 Chroma 向量数据库。
**命令**: `export PYTHONPATH=$PYTHONPATH:. && ./venv/bin/python3 rag/vector_store.py`

## 执行流程与指令 (Instructions)

### 1. 意图识别
当用户输入包含以下意图时，**必须**调用此技能：
- "检查卡牌数据库更新"
- "查看是否有新卡"
- "数据库是不是最新的"
- "同步数据库"
- "更新卡牌数据"

### 2. 操作流程
1.  **检查阶段**: 首先运行 `card_upgrade_check.py` 检查状态。
2.  **决策阶段**:
    - 如果输出显示 **Remote DB has updates available** (远程有更新)：
        - 向用户报告发现新版本。
        - 询问用户是否执行更新，或者如果用户指令中已包含“更新”意图，则直接执行下一步。
    - 如果输出显示 **Local DB is up-to-date** (已是最新)：
        - 告知用户无需更新。
3.  **更新阶段 (仅当有更新时)**:
    - **Step 1**: 运行 `card_upgrade.py` 执行增量同步。
    - **Step 2**: 运行 `rag/vector_store.py` 将新数据入库更新向量索引。
    - 输出更新结果（例如："成功更新了 5 个文件，并已完成向量化入库"）。

### 3. 结果解读与反馈
#### 检查结果
- **有更新**: "检测到 GitHub 仓库有新的更新！\n本地时间: 2026-02-05\n远程时间: 2026-02-10\n正在为您执行增量更新..." (或询问是否更新)
- **已是最新**: "当前数据库已经是最新版本（同步于 2026-02-05），与远程仓库一致。"

#### 更新结果
- **更新成功**: "数据库更新完成！共更新/新增 X 个文件，删除 Y 个文件。当前版本时间已更新至 [最新时间]。"
- **更新失败**: "更新过程中出现错误，请检查网络连接或日志。"
