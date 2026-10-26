# 🚀 agent-video-to-blog

> **专为 AI Agent（OpenCode / Claude Code / Codex 等）打造的多源视频学习与深度博客合成技能。**  
> 一键将 **B站、YouTube、抖音、小红书** 等视频与多源网页文章转化为**高信息密度、图文并茂（Mermaid 架构图 + 精准视频截帧）、低心智负担**的学习笔记，并在确认后无缝同步至 **Notion 博客库**（原生对接 `next-notion -> Hexo` 静态站点）。

---

## ✨ 核心特性

- 🧠 **复用宿主 AI，零 LLM 配置**：直接利用当前会话正在使用的 Agent 大模型，无需重复填写任何 OpenAI / DeepSeek 的 API Key。
- 📖 **以学习与吸收为主（非盲目搬运）**：
  - 链接发给 AI，**优先在对话框内输出《高密度结构化学习卡片》**，先看懂、学透，拒绝未经过滤的“AI 垃圾文章”直接塞满 Notion。
  - **视角补充与代价提示**：不强行向用户抛出考题，而是主动指出作者方案的边界、隐藏前提与性能副作用。
- 📊 **图文高度契合（拒绝假插图）**：
  - 涉及复杂协议、调用链路与状态机，强制现场手写 **Mermaid 架构与时序图**。
  - 联动 `FFmpeg` 按视频时间戳毫秒级**截取原视频关键帧**（PPT、代码演示、实测数据）。
- 🔌 **按需发布到 Notion & Hexo**：
  - 支持在对话框中随时二次调整润色；
  - 满意后一键写入 Notion Database，自动生成规范属性（Title, Status, Tags, Date, Slug, Summary），触发 Hexo 博客自动化构建。
- 🎙️ **多源与 ASR 支持**：
  - 智能解析 B站、YouTube、抖音、小红书短链。
  - 无字幕视频自动调用云端（Groq Whisper，免费极速）或本地离线 ASR（faster-whisper / SenseVoice）转写。

---

## 🏗️ 架构与工作流

```text
[用户输入视频链接]
       ↓
【阶段 1：对话框内呈现《高密度结构化学习卡片》】
  ├── 1. TL;DR (3 句话直击要害与本质)
  ├── 2. 核心架构时序图 (Mermaid 矢量代码现场手写)
  ├── 3. 脉络化技术要点 (带时间戳秒数锚点)
  ├── 4. 原视频关键截帧 (FFmpeg 精准抓取关键画面)
  └── 5. 视角补充与潜在代价 (直接提示使用边界与妥协，零认知负担)
       ↓
【阶段 2：极简数字延伸支线（可选）】
  提供几个编号支线（如：[1] 展开实操代码 [2] 对比替代方案），回复单个数字即可深挖
       ↓
【阶段 3：二次加工与按需同步 Notion】
  用户确认满意后，输入指令（或选 [3]）一键推送到 Notion 博客草稿箱
```

---

## 🛠️ 快速上手

### 1. 系统依赖安装 (FFmpeg)
本项目依赖 `ffmpeg` 进行音视频抽取与关键帧截图：

- **macOS**：
  ```bash
  brew install ffmpeg
  ```
- **Ubuntu/Debian**：
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```
- **Windows**：
  使用 `winget install Gyan.FFmpeg` 或通过 Scoop/Chocolatey 安装并配置环境变量。

### 2. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

---

## ⚙️ 配置说明

在项目根目录下创建配置文件（可直接复制模板）：
```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`（仅需配置两项外部系统凭证）：

```yaml
# ================= 1. Notion 博客配置 (必填) =================
# 用于承接文章并自动同步到 next-notion -> Hexo
notion:
  token: "secret_xxxxxxxxxxxxxxxxxxxxxxxxxxx"       # 你的 Notion Integration Token
  database_id: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"   # 32 位的 Database ID
  default_status: "Draft"                          # 默认状态: Draft (草稿)
  
  # 字段名称映射 (根据你的 Notion Database 实际列名匹配)
  properties:
    title: "title"                                  # 标题
    status: "status"                                # 状态 (Published / Draft)
    tags: "tags"                                    # 标签
    date: "date"                                    # 日期
    slug: "slug"                                    # 路径标识
    type: "type"                                    # 文章类型 (Post / Page)
    category: "category"                            # 分类
    summary: "summary"                              # 摘要

# ================= 2. ASR 语音识别配置 (可选) =================
# 针对抖音、小红书以及无字幕的视频
asr:
  mode: "cloud"                                    # 可选: "cloud" (推荐) 或 "local"
  cloud:
    provider: "groq"                               # Groq Whisper 极速且免费
    groq_api_key: "gsk_xxxxxxxxxxxxxxxxxxxxxx"     # console.groq.com 免费获取
```

> **快捷环境变量注入**：你也可以直接在系统环境变量中导出（Skill 会优先读取环境变量）：
> ```bash
> export NOTION_TOKEN="secret_xxx"
> export NOTION_DATABASE_ID="xxx"
> export GROQ_API_KEY="gsk_xxx"
> ```

---

## 🩺 运行环境自检 (Doctor)

配置完成后，运行自带的健康检查脚本：
```bash
python scripts/doctor.py
```
当终端提示：
```text
============================================================
🏥 agent-video-to-blog 环境配置自检 (Doctor)
============================================================
[✓] FFmpeg 安装正常
[✓] 基础依赖 yaml OK
[✓] 媒体/知识库依赖 yt-dlp OK
[✓] 配置文件 config.yaml 读取正常
[✓] Notion Token 已配置
[✓] Notion Database ID 已配置
============================================================
🎉 核心环境检查完毕！可以正常加载此 Skill。
============================================================
```
代表所有底层链路已经畅通！

---

## 💬 在 Agent 中的使用示例

将本目录复制或软链接至 Agent 的 skills 路径（如 `~/.agents/skills/agent-video-to-blog/` 或 `.opencode/skills/`）后，直接在对话框中用自然语言使用：

### 场景 1：学习与深度总结（默认不直接推 Notion）
> **你**：“帮我学习并总结这个视频：`https://www.youtube.com/watch?v=xxx`”  
> **AI**：
> 1. 输出包含核心要点与 Mermaid 架构图的**学习卡片**；
> 2. 截取关键帧；
> 3. 列出作者方案的潜在局限性；
> 4. 提供 3 个延伸数字选项（`[1] 展开核心代码 [2] 对比替代方案 [3] 存入 Notion`）。

### 场景 2：二次加工与发布
> **你**：“把第 2 部分关于并发冲突的逻辑结合分布式锁再展开讲讲，然后把整篇文章排版好，存入我的 Notion 博客草稿箱。”  
> **AI**：调整补充内容后，调用脚本一键推送至 Notion，并返回生成的页面链接。

---

## 📂 目录结构说明

```text
agent-video-to-blog/
├── SKILL.md                 # Agent 核心大脑规范 (认知流、质量门禁、写作契约)
├── README.md                # 项目快速入门与介绍
├── SETUP_GUIDE.md           # 详尽配置手册 (含 Notion 集成步骤截图指引)
├── config.example.yaml      # 配置模板文件
├── requirements.txt         # Python 依赖清单
└── scripts/
    ├── config_loader.py     # 统一配置加载器 (支持环境变量插值)
    ├── extract_content.py   # 视频多源内容/字幕抓取入口
    ├── asr_runner.py        # 语音转文字适配器 (Groq/Faster-Whisper)
    ├── capture_frame.py     # 基于时间戳的 FFmpeg 视频精准抽帧工具
    ├── push_to_notion.py    # Notion REST API 页面与原生 Blocks 写入器
    └── doctor.py            # 环境与凭据一键诊断脚本
```

---

## 🤝 贡献与反馈
欢迎提交 Issue 或 Pull Request 来完善更多平台的音视频解析与排版模板！
