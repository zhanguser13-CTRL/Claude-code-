# Claude Pet Companion - 安装指南

## 两种使用方式

### 1. 桌面宠物模式（独立应用）

直接在桌面显示一个可爱的宠物，跟随你的编码活动。

```bash
# 安装
pip install claude-pet-companion

# 启动桌面宠物
claude-pet
# 或
pet-companion
```

### 2. Claude Code 插件模式

将宠物集成到 Claude Code 中，可通过命令互动。

```bash
# 安装
pip install claude-pet-companion

# 安装 Claude Code 插件
claude-pet install
```

然后重启 Claude Code，在对话中使用：

```
/pet:status - 查看宠物状态
/pet:feed   - 喂食
/pet:play   - 玩耍
/pet:sleep  - 睡觉/唤醒
```

## 插件目录

插件会被安装到：

| 平台 | 目录 |
|------|------|
| All | `~/.claude/plugins/claude-pet-companion/` |

## 卸载

```bash
# 卸载 Claude Code 插件
claude-pet uninstall

# 卸载整个包
pip uninstall claude-pet-companion
```

## 功能特性

- **10 个进化阶段** - 从蛋到远古形态
- **5 条进化路线** - 编程者、战士、社交、夜猫子、平衡
- **3D 伪渲染** - 多层深度模拟和动态光照
- **记忆系统** - 宠物会记住你的编码活动
- **主题系统** - 5 种配色方案
- **生产力追踪** - 追踪编码效率和专注时间

## 故障排除

### 插件未显示

1. 确保安装后重启了 Claude Code
2. 检查插件是否在正确目录：
   ```bash
   # Windows
   dir %APPDATA%\Claude\plugins\claude-pet-companion

   # macOS/Linux
   ls ~/.claude/plugins/claude-pet-companion
   ```

### 状态未保存

1. 检查数据目录的写入权限
2. 确保 `data/` 文件夹存在于插件目录中

### 导入错误

1. 验证 Python 3.8+ 已安装：`python --version`
2. 重新安装：`pip install --force-reinstall claude-pet-companion`
