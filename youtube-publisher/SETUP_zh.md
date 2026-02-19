# YouTube 发布工具 - 设置指南

> 仓库地址：[https://github.com/wlzh/skills](https://github.com/wlzh/skills)

## 准备工作

- 已安装 Node.js
- Google 账号
- YouTube 频道

## 1. 创建 Google Cloud 项目

1. 访问 [console.cloud.google.com](https://console.cloud.google.com)
2. 创建新项目或选择已有项目
3. 启用 YouTube Data API v3：
   - 进入 APIs & Services → Library
   - 搜索 "YouTube Data API v3"
   - 点击 Enable

4. （可选）启用字幕上传功能：
   - 进入 APIs & Services → Library
   - 搜索 "YouTube Data API v3"
   - 确保已启用（字幕上传需要完整权限）

## 2. 创建 OAuth 凭据

1. 进入 APIs & Services → Credentials
2. Create Credentials → OAuth client ID
3. **应用类型选择：Desktop app（桌面应用）** ⚠️ 不是 Web application
4. Desktop app 不需要填写 redirect URI
5. 下载 JSON 或复制 Client ID 和 Secret

## 2.1 添加测试用户（新项目必做）

新创建的 Google Cloud 项目需要添加测试用户才能正常使用 API：

1. 在 OAuth 客户端页面，点击左侧菜单 **目标对象 (Audience)**
2. 找到 **测试用户 (Test users)** 区域
3. 点击 **添加用户**
4. 输入你的 Google 邮箱地址（如 xxx@gmail.com）
5. 点击保存

这可以解决新项目的 "403 Access Denied" 错误。

## 2.2 添加 API 权限（字幕上传需要）

要启用字幕上传功能，需要添加对应的权限范围：

1. 在 OAuth 客户端页面，点击左侧菜单 **数据访问 (Data access)**
2. 点击 **添加或移除范围**
3. 搜索并添加：`https://www.googleapis.com/auth/youtube.force-ssl`
4. 点击保存

## 3. 配置环境变量

```bash
cd ~/.claude/skills/youtube-publisher/scripts
cp .env.example .env
```

编辑 `.env` 文件：
```
YOUTUBE_CLIENT_ID=你的_client_id
YOUTUBE_CLIENT_SECRET=你的_client_secret
```

## 4. 安装依赖

```bash
cd ~/.claude/skills/youtube-publisher/scripts
npm install
```

## 5. 首次身份验证

运行上传脚本，会自动：
1. 打开浏览器进行 Google 登录
2. 请求 YouTube 权限
3. 保存刷新令牌供以后使用

```bash
npx ts-node youtube-upload.ts --auth
```

## 6. 标记设置完成

编辑 `SKILL.md` 并修改：
```yaml
setup_complete: true
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 403 Access Denied | 在"目标对象"设置中添加你的邮箱为测试用户 |
| Redirect URI 不匹配 | Desktop app 不需要 redirect URI |
| API 未启用 | 启用 YouTube Data API v3 |
| 字幕上传失败 | 在"数据访问"中添加 `youtube.force-ssl` 权限范围，重新运行 `--auth` |
| 配额超限 | 在 Cloud Console 查看配额 |
| 访问被拒绝 | 重新授权：`npx ts-node youtube-upload.ts --auth` |
