# 股票交易记录系统 - 部署指南

## 🚀 部署到 Render（推荐）

### 第一步：准备代码

1. 将 `stock-tracker` 文件夹中的代码上传到 GitHub 仓库

### 第二步：创建 Render 账号

1. 访问 [https://render.com](https://render.com)
2. 使用 GitHub 账号登录

### 第三步：创建 Web 服务

1. 点击 "New +" → "Web Service"
2. 连接你的 GitHub 仓库
3. 配置服务：
   - **Name**: stock-tracker（或你喜欢的名字）
   - **Region**: Singapore（新加坡，离中国最近）
   - **Branch**: main
   - **Root Directory**: 留空（如果代码在根目录）
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

### 第四步：配置环境变量

Render 会自动创建 PostgreSQL 数据库，需要修改 `app.py` 支持 PostgreSQL：

在 Render 控制台中添加以下环境变量：
- `SECRET_KEY`: 点击 "Generate" 自动生成随机密钥

### 第五步：部署

1. 点击 "Create Web Service"
2. 等待部署完成（约 2-5 分钟）
3. 部署成功后，你会获得一个 `https://xxx.onrender.com` 的网址

### 第六步：访问使用

1. 打开浏览器访问你的网站地址
2. 点击 "免费注册" 创建账号
3. 使用账号密码登录
4. 在家里任何设备上用同一账号登录即可同步数据

---

## 🚀 部署到 Railway

### 第一步：准备代码

1. 将 `stock-tracker` 文件夹中的代码上传到 GitHub 仓库

### 第二步：创建 Railway 账号

1. 访问 [https://railway.app](https://railway.app)
2. 使用 GitHub 账号登录

### 第三步：创建新项目

1. 点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 选择你的仓库

### 第四步：配置服务

Railway 会自动识别 Python 项目并安装依赖

### 第五步：添加数据库

1. 点击 "New" → "Database" → "PostgreSQL"
2. Railway 会自动配置 `DATABASE_URL` 环境变量

### 第六步：部署

1. 点击 "Deploy"
2. 等待部署完成
3. 获得你的网站地址

---

## 💻 本地运行测试

### 安装依赖

```bash
cd stock-tracker
pip install -r requirements.txt
```

### 运行应用

```bash
python app.py
```

### 访问

打开浏览器访问：http://localhost:5000

---

## 📱 多设备访问

部署成功后：

1. **电脑访问**：直接在浏览器输入网站地址
2. **手机/平板访问**：
   - 在浏览器中输入网站地址
   - 建议添加到主屏幕，像 App 一样使用

### 安全提示

- 使用强密码（字母 + 数字 + 符号，至少 8 位）
- 不要在公共电脑上勾选"记住我"
- 定期备份重要数据

---

## 📊 功能说明

### 交易记录
- 记录股票代码、名称、买卖类型
- 记录交易数量、价格、日期
- 记录交易想法和思路

### 每日复盘
- 记录每日投资心得
- 记录当日盈亏情况
- 支持文字格式化

### 报表统计
- **日报表**：查看某一天的交易详情
- **月报表**：查看整月的交易统计
- **年报表**：查看全年的交易汇总

---

## 🔧 技术支持

如遇到问题，请检查：
1. Render/Railway 服务是否正常运行
2. 数据库连接是否正常
3. 浏览器控制台是否有错误信息
