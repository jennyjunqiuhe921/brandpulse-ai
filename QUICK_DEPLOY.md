# 🚀 PinSight_AI 一键部署指南

## 部署前准备（已完成 ✓）

- [x] 代码已推送到 GitHub
- [x] 配置文件已更新
- [x] Streamlit Cloud 兼容

---

## 📋 你需要做的事情（5分钟）

### 步骤 1：登录 Streamlit Cloud

👉 打开浏览器访问：**https://streamlit.io/cloud**

点击 **Sign in with GitHub**，使用你的 GitHub 账号登录。

---

### 步骤 2：创建新应用

登录后，点击 **New app** 按钮，填写以下信息：

| 字段 | 值 |
|------|-----|
| **Repository** | `jennyjunqiuhe921/brandpulse-ai` |
| **Branch** | `main` |
| **Main file path** | `main.py` |

---

### 步骤 3：配置 API 密钥（重要！）

在 **Advanced settings** 中，点击 **Secrets** 标签，粘贴以下内容：

```toml
# 方案 A：使用 Freemodel（你当前配置的）
OPENAI_API_KEY = "fe_oa_你的真实密钥"
OPENAI_BASE_URL = "https://api.freemodel.dev/v1"
OPENAI_MODEL = "gpt-4o"

# 方案 B：使用 OpenRouter
# OPENAI_API_KEY = "sk-你的密钥"
# OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
# OPENAI_MODEL = "anthropic/claude-sonnet-4-5"
```

⚠️ **注意**：请替换 `fe_oa_你的真实密钥` 为你实际的 API 密钥！

---

### 步骤 4：点击 Deploy！

点击 **Deploy!** 按钮，等待 2-3 分钟部署完成。

---

## 🎉 部署成功后

你会获得一个类似这样的链接：

```
https://pinsight-ai-xxxxx.streamlit.app
```

把这个链接分享给团队成员即可！

---

## 🔧 如何更新应用

以后代码更新后，只需：

```bash
cd /Users/tuotuo/brandpulse-ai
git add .
git commit -m "你的更新内容"
git push origin main
```

Streamlit Cloud 会**自动重新部署**！

---

## ❓ 常见问题

**Q: API密钥在哪里找？**
A: 查看你本地的 `.env` 文件，或者到 Freemodel/OpenRouter 官网获取。

**Q: 部署失败怎么办？**
A: 查看 Streamlit Cloud 的部署日志，通常是依赖或配置问题。

**Q: 如何删除应用？**
A: 在 Streamlit Cloud 的 app 设置中可以删除。

---

## 📞 需要帮助？

查看 `.streamlit/config.toml` 了解应用配置。
查看 `requirements.txt` 了解依赖版本。
