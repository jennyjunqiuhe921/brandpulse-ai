# 🚀 部署 PinSight_AI 到 Streamlit Cloud 指南

让团队成员可以通过互联网访问 AI 品牌与市场增长工作台。

---

## 方案一：部署到 Streamlit Cloud（推荐，免费）

### 第一步：确保代码已推送到 GitHub

```bash
cd /Users/tuotuo/brandpulse-ai

# 添加并提交所有更改
git add .
git commit -m "Update for Streamlit Cloud deployment"

# 推送到 GitHub
git push origin main
```

### 第二步：连接到 Streamlit Cloud

1. 访问 [https://streamlit.io/cloud](https://streamlit.io/cloud)
2. 使用 GitHub 账号登录
3. 点击 "New app"
4. 选择仓库：`jennyjunqiuhe921/brandpulse-ai`
5. 选择分支：`main`
6. 主文件路径：`main.py`

### 第三步：配置 Secrets（API 密钥）

在 Streamlit Cloud 的设置页面，添加以下 Secrets：

```toml
# Anthropic API (Claude)
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
CLAUDE_MODEL = "claude-sonnet-4-6"

# 或者使用 OpenAI 兼容接口
OPENAI_API_KEY = "fe_oa-your-key-here"
OPENAI_BASE_URL = "https://api.freemodel.dev/v1"
OPENAI_MODEL = "gpt-4o"

# ChromaDB
CHROMA_DB_PATH = "./chroma_db"
```

### 第四步：部署并分享

部署完成后，你会获得一个公开 URL，格式类似：
```
https://brandpulse-ai-yourname.streamlit.app
```

把这个链接分享给团队成员即可！

---

## 方案二：临时方案 - 使用 ngrok（本地测试用）

如果你想在本地测试后快速分享给团队，可以使用 ngrok：

```bash
# 安装 ngrok
brew install ngrok

# 运行 Streamlit
cd /Users/tuotuo/brandpulse-ai
streamlit run main.py

# 在另一个终端运行 ngrok
ngrok http 8501
```

你会得到一个公共 URL，可以临时分享给团队。

⚠️ 注意：这个方案仅适合临时测试，因为 ngrok URL 会过期。

---

## 常见问题

### Q1: Streamlit Cloud 是免费的吗？
是的！Streamlit Cloud 有免费计划：
- 每月 1 个私有应用
- 无限公共应用
- 足够团队使用了

### Q2: 如何更新已部署的应用？
只需将代码推送到 GitHub，Streamlit Cloud 会自动重新部署：
```bash
git add .
git commit -m "Your changes"
git push origin main
```

### Q3: 如何限制访问权限？
在 Streamlit Cloud 设置中：
- 可以设置为"需要登录 GitHub"
- 或者设置为"公开访问"

### Q4: ChromaDB 数据如何处理？
由于 Streamlit Cloud 是无状态的临时环境：
- 建议将重要数据存储到云数据库
- 或者在每次使用时重新上传数据
- 未来可以考虑使用 Streamlit 的持久化存储

### Q5: API 密钥安全吗？
Streamlit Cloud 会将 secrets 加密存储，不会出现在代码或公开日志中。

---

## 下一步

1. ✅ 将代码推送到 GitHub
2. ✅ 访问 [streamlit.io/cloud](https://streamlit.io/cloud)
3. ✅ 连接你的 GitHub 仓库
4. ✅ 配置 API Secrets
5. ✅ 点击 Deploy！
6. ✅ 分享链接给团队成员

---

*有问题？查看 [Streamlit Cloud 文档](https://docs.streamlit.io/streamlit-cloud) 或提交 issue。*