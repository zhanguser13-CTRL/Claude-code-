# PyPI 发布说明

## 问题说明

PyPI 从 2024 年开始不再支持用户名/密码认证，需要使用 **API Token** 或 **Trusted Publishers**。

## 方式 1: 使用 API Token 上传（推荐）

### 步骤 1: 创建 API Token

1. 访问 https://pypi.org/manage/account/token/
2. 点击 "Add API Token"
3. 选择 "Entire account" 或特定项目
4. 复制生成的 Token（格式：`pypi-xxxxxxxxxxxxxxx`）

### 步骤 2: 上传

```bash
cd H:\宠物\claude-pet-companion

# 使用 Token 上传（不要加用户名）
python -m twine upload dist/* --username __token__ --password pypi-你的token
```

或者创建 `.pypirc` 配置文件：

```bash
# 创建 C:\Users\你的用户名\.pypirc
[pypi]
username = __token__
password = pypi-你的token
```

然后直接运行：
```bash
python -m twine upload dist/*
```

---

## 方式 2: 使用 GitHub Trusted Publishers（最安全）

### 步骤 1: 在 PyPI 创建发布者

1. 访问 https://pypi.org/manage/account/publishing/
2. 点击 "Add a new pending publisher"
3. 填写：
   - PyPI Project Name: `claude-pet-companion`
   - Owner: 你的 GitHub 用户名
   - Repository name: `claude-pet-companion`
   - Workflow name: `publish.yml`

### 步骤 2: 推送代码到 GitHub

```bash
git init
git add .
git commit -m "Initial release"
git remote add origin https://github.com/你的用户名/claude-pet-companion.git
git push -u origin main
```

### 步骤 3: 创建发布标签

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions 会自动发布到 PyPI！

---

## 当前状态

你的包已经构建好了，位于：
```
H:\宠物\claude-pet-companion\dist\
├── claude_pet_companion-1.0.0-py3-none-any.whl
└── claude_pet_companion-1.0.0.tar.gz
```

获取 API Token 后即可上传。

---

## 快速上传命令（获取 Token 后）

```bash
cd H:\宠物\claude-pet-companion
python -m twine upload dist/* --username __token__ --password 你的token
```
