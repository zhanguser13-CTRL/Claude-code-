# PyPI 可信发布配置指南

## GitHub 仓库信息
- **Owner**: zhanguser13-CTRL
- **Repository**: Claude-code-
- **Workflow**: .github/workflows/release.yml
- **Environment**: pypi

## PyPI 配置步骤

### 1. 登录 PyPI
访问: https://pypi.org/manage/account/

### 2. 进入发布设置
访问: https://pypi.org/manage/account/publishing/

### 3. 添加新的发布者

点击 "Add a new pending publisher" 并填写以下信息：

| 字段 | 值 |
|------|-----|
| **PyPI Project Name** | `claude-pet-companion` |
| **Owner** | `zhanguser13-CTRL` |
| **Repository name** | `Claude-code-` |
| **Workflow name** | `release.yml` |
| **Environment name** | `pypi` |

### 4. 确认配置

配置完成后应该显示：
```
Publisher: zhanguser-CTRL/Claude-code-
Workflow: release.yml
Environment: pypi
```

## GitHub 环境配置

### 在 GitHub 上创建 pypi 环境

1. 访问: https://github.com/zhanguser13-CTRL/Claude-code-/settings/environments

2. 点击 "New environment"

3. 创建名为 `pypi` 的环境

4. 配置环境（可选但推荐）：
   - **Deployment branches**: 选择 main 分支
   - **Wait timer**: 0 分钟
   - **Required reviewers**: 可选添加审查者

## 验证配置

### 测试发布

```bash
# 创建测试标签
git tag v2.3.2-test -m "Test release"
git push origin v2.3.2-test
```

然后在 GitHub Actions 中查看工作流是否成功执行。

### 检查日志

成功后应该看到：
```
✓ Check package
✓ Create GitHub Release
✓ Publish to PyPI
```

## 常见问题

### Q: 发布失败提示 "Forbidden"
A: 检查 PyPI 上的环境名称是否与 GitHub 上的环境名称完全一致。

### Q: OIDC token not found
A: 确保 workflow 中有 `id-token: write` 权限。

### Q: Skip-existing: false 导致失败
A: 如果版本已存在，使用 `skip-existing: true` 或升级版本号。

## 删除测试标签

```bash
git tag -d v2.3.2-test
git push origin :refs/tags/v2.3.2-test
```

## 有用的链接

- PyPI Trusted Publishers: https://docs.pypi.org/trusted-publishers/
- GitHub OIDC: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-pypi
- PyPI Publishing: https://pypi.org/manage/account/publishing/
