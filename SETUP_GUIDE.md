# 🛠️ `agent-video-to-blog` 配置与使用手册

`agent-video-to-blog` 是一个专为 AI Agent（如 OpenCode、Claude Code、Codex）打造的高阶内容合成技能。它能够将 **B站、YouTube、抖音、小红书** 等视频及多源网页文章转化为**高信息密度、图文并茂 (Mermaid + 精准截帧)、严谨溯源**的高质量技术博客，并全自动推送到 Notion，直接无缝衔接你的 `next-notion -> Hexo` 博客发布流水线。

---

## 💡 核心设计理念

1. **直接复用宿主 AI**：无需单独配置任何 OpenAI / DeepSeek 等大模型 API Key，完全由当前会话的 Agent 担任主编和架构师。
2. **图文高度契合**：告别市面上纯文字摘要或假插画，强制输出原生 Mermaid 流程图并联动 FFmpeg 精准截取原视频关键帧。
3. **多源交叉比对**：支持同时喂入多个视频、论文或推文，自动梳理观点共识与技术分歧，合成具备研究深度的综述。

---

## 1. 快速准备

### 1.1 系统工具依赖 (FFmpeg)
本 Skill 依赖 `ffmpeg` 执行音视频分片与毫秒级精准截帧：
- **macOS**：`brew install ffmpeg`
- **Ubuntu/Debian**：`sudo apt update && sudo apt install -y ffmpeg`
- **Windows**：`winget install Gyan.FFmpeg` 或加入系统 PATH。

### 1.2 Python 环境依赖
```bash
pip install -r requirements.txt
```
*(主要包含 `yt-dlp`、`notion-client`、`pyyaml` 等)*

---

## 2. Notion 数据库配置（核心）

用于承接生成的博客文章，并连接你的 `next-notion -> Hexo` 静态博客。

### 步骤 A：获取 Notion Internal Integration Token
1. 访问 [Notion Integrations](https://www.notion.so/my-integrations)。
2. 点击 **"+ New integration"**，命名为 `Blog Synthesizer Agent`，点击 Submit。
3. 复制生成的 **Internal Integration Secret**（以 `secret_` 开头）。

### 步骤 B：确保你的 Hexo 博客 Database 字段匹配
确保你的 Notion 博客数据库中包含以下属性：

| 属性名 (Property) | 类型 (Type) | 说明 |
| :--- | :--- | :--- |
| **Title** | Title | 文章标题 |
| **Status** | Status / Select | 状态值，如 `Draft` (草稿) 或 `Published` (发布) |
| **Tags** | Multi-select | 文章标签 (如 `架构设计`, `分布式`) |
| **Date** | Date | 发布日期 |
| **Slug** | Text / Rich Text | Hexo 文章 URL 路径标识 |

### 步骤 C：为 Database 授权并获取 ID
1. 在 Notion 中打开该博客 Database 页面。
2. 点击右上角 **`...`** $\rightarrow$ **`Connect to`** $\rightarrow$ 勾选刚刚创建的 `Blog Synthesizer Agent`。
3. 从浏览器地址栏复制 32 位的 Database ID：
   `https://www.notion.so/{workspace}/{database_id}?v=...`

---

## 3. 配置文件 `config.yaml` 填写

复制模板并根据你的实际情况填写：
```bash
cp config.example.yaml config.yaml
```

```yaml
# 1. Notion 配置
notion:
  token: "secret_xxxxxxxxxxxxxxxxxxxxxxxxxxx"      # 你的 Notion Token
  database_id: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 你的 32 位 Database ID
  default_status: "Draft"                         # 默认写入草稿状态，供人工复核

# 2. ASR 语音识别 (针对无字幕/抖音/小红书)
asr:
  mode: "cloud"                                   # 推荐: "cloud" 或 "local"
  cloud:
    provider: "groq"                              # Groq Whisper 极速且免费
    groq_api_key: "gsk_xxxxxxxxxxxxxxxxxxxxxx"    # 前往 console.groq.com 免费获取

media:
  enable_screenshot: true                         # 开启原视频关键帧自动精准截帧
```

> **提示**：也可以直接在终端导出环境变量，Skill 会优先读取：
> `export NOTION_TOKEN="secret_xxx"`
> `export NOTION_DATABASE_ID="xxx"`
> `export GROQ_API_KEY="gsk_xxx"`

---

## 4. 环境自检 (Doctor)

配置完成后，运行自检脚本排查问题：
```bash
python scripts/doctor.py
```
当看到 `[✓]` 全绿提示时，代表所有环境与鉴权已完全就绪！

---

## 5. 在 Agent 中的使用示例

在 OpenCode / Codex 中，你可以直接使用自然语言驱动该 Skill：

### 场景 1：单个视频转深度技术博客
> “帮我把这个 B 站视频 `https://www.bilibili.com/video/BVxxx` 转换为一篇深入解析的博客文章，配上 Mermaid 架构图和关键截图，写入 Notion 草稿箱。”

### 场景 2：多源对比合成（视频 + 博客）
> “分析这两个视频关于 Redis 分布式锁与 Redlock 的争议：
> 1. `https://www.bilibili.com/video/BV1...`
> 2. `https://www.youtube.com/watch?v=...`
> 梳理出双方的核心分歧与共识，整理出一篇技术选型对比博客，生成初稿推送到 Notion。”
