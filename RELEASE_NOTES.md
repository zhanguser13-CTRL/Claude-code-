# Claude Code Pet Companion v2.0 发布说明

## 版本信息
- **版本号**: 2.0.0
- **发布日期**: 2025-02-25
- **类型**: 重大更新 (Breaking Change)

## 主要更新

### 🎨 全新高分辨率界面
- **紧凑尺寸**: 240x280 像素，比之前版本减少 30% 屏幕占用
- **高 DPI 渲染**: 清晰的文字和图形
- **40 FPS 动画**: 流畅的视觉体验
- **精美排版**: Segoe UI / Consolas 字体

### 🔗 深度 Claude Code 集成
- **实时监控**: 每 0.2 秒检测一次 Claude Code 状态
- **工具检测**: 自动识别 Write、Edit、Read、Bash 操作
- **状态响应**: 根据活动自动切换表情
- **活动记录**: 完整的编码活动历史

### 😊 5种动态表情
| 状态 | 触发条件 | 视觉效果 |
|------|---------|---------|
| 闲置 💤 | 无活动 | 开笑眼 + 蓝色光 |
| 思考 🤔 | AI 思考中 | 眼睛转动 + 问号 |
| 工作 ⚡ | 执行命令 | 专注大眼 + 汗滴 |
| 错误 ❌ | 检测到错误 | X 眼 + 担心 |
| 成功 ✨ | 操作完成 | 闪闪眼 + 星星 |

### 📊 实时信息显示
- 等级和 XP 进度条
- 当前状态指示灯
- 文件统计 (创建+修改)
- 命令执行计数
- 当前使用的工具
- 实时时间显示

## 清理内容

### 已删除的旧版本文件
- `animated_pet.py` - 旧版动画宠物
- `cute_pet.py` - 旧版可爱宠物
- `simple_window_pet.py` - 简化版宠物
- `desktop_pet.py` - 桌面宠物
- `improved_pet.py` - 改进版宠物
- `pet.py` / `terminal_pet.py` - 终端宠物
- `simple_pet.py` - 简单宠物
- `claude_pet.py` - 旧版 Claude 宠物

### 已删除的启动脚本
- `启动宠物.vbs`
- `启动宠物.bat`
- `启动可爱宠物.vbs`
- `启动可爱宠物.bat`
- `启动Claude宠物.vbs`
- `启动Claude宠物.bat`

## 新的启动方式

### Windows 用户
```batch
# 双击静默启动（推荐）
启动Claude宠物HD.vbs

# 或使用批处理（查看输出）
启动Claude宠物HD.bat
```

### 命令行
```bash
# 直接运行
python claude_pet_companion/claude_pet_hd.py

# 或安装后运行
pip install -e .
claude-pet
```

## 系统要求
- Python 3.8+
- Windows 10/11 (推荐)
- tkinter (通常随 Python 安装)

## 数据文件位置
```
%USERPROFILE%\.claude-pet-companion\
├── pet_state.json       # 宠物状态
├── activity.json        # 活动记录
└── pet_window_state.json # 窗口位置
```

## 升级指南

### 从 v1.x 升级
1. 备份旧版本数据（可选）
2. 下载 v2.0
3. 直接运行 - 会自动读取现有状态
4. 旧文件已自动清理

### 注意事项
- v2.0 完全重写了 UI，旧版本文件已删除
- 状态文件格式兼容，会自动迁移
- 窗口位置会自动重置到默认位置

## 已知问题
- PyPI Token 需要更新才能在线发布
- 本地安装不受影响

## 下一步计划
- [ ] 更多表情动画
- [ ] 语音反馈
- [ ] 多宠物支持
- [ ] 宠物配件系统

---

**感谢使用 Claude Code Pet Companion!**
