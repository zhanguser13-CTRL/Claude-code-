#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Activity Tracker - 增强版 Claude Code 活动追踪

实时追踪、分析和优化你的编程工作流程
"""
import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
import time

# 文件路径
DATA_DIR = Path.home() / '.claude-pet-companion'
ACTIVITY_FILE = DATA_DIR / 'activity.json'
STATE_FILE = DATA_DIR / 'pet_state.json'
STATS_FILE = DATA_DIR / 'work_stats.json'
FOCUS_FILE = DATA_DIR / 'focus_session.json'

DATA_DIR.mkdir(parents=True, exist_ok=True)


class WorkSessionTracker:
    """工作会话追踪器"""

    def __init__(self):
        self.session_start = None
        self.focus_periods = []
        self.break_periods = []
        self.total_focus_time = 0
        self.last_activity = None

    def start_session(self):
        """开始会话"""
        self.session_start = datetime.now()
        self.last_activity = datetime.now()

    def record_activity(self, tool_name):
        """记录活动"""
        now = datetime.now()
        if self.last_activity:
            gap = (now - self.last_activity).total_seconds()
            # 超过5分钟算休息
            if gap > 300:
                self.break_periods.append(gap)
            # 连续工作算专注时间
            elif gap < 120:
                self.total_focus_time += gap

        self.last_activity = now

    def get_focus_score(self):
        """计算专注度评分 (0-100)"""
        if not self.session_start:
            return 0

        session_length = (datetime.now() - self.session_start).total_seconds() / 60  # 分钟
        if session_length < 1:
            return 0

        focus_ratio = self.total_focus_time / max(session_length * 60, 1)
        break_penalty = min(len(self.break_periods) * 5, 30)

        return max(0, min(100, int(focus_ratio * 100 - break_penalty)))

    def needs_break(self):
        """判断是否需要休息"""
        if not self.last_activity:
            return False

        # 连续工作超过50分钟建议休息
        continuous_work = (datetime.now() - self.last_activity).total_seconds()
        if continuous_work > 3000:  # 50分钟
            return True

        # 检查最近10分钟的活动密度
        return False


class ProductivityAnalyzer:
    """生产力分析器"""

    def __init__(self):
        self.activity_history = deque(maxlen=100)
        self.tool_counts = {}
        self.peak_hours = {}

    def record_activity(self, tool, status='success'):
        """记录活动"""
        now = datetime.now()
        hour = now.hour

        self.activity_history.append({
            'tool': tool,
            'status': status,
            'time': now.isoformat(),
            'hour': hour
        })

        # 工具统计
        key = f"{tool}:{status}"
        self.tool_counts[key] = self.tool_counts.get(key, 0) + 1

        # 高峰时段
        self.peak_hours[hour] = self.peak_hours.get(hour, 0) + 1

    def get_productivity_score(self):
        """获取生产力评分"""
        if not self.activity_history:
            return 50

        # 最近30分钟的活动
        cutoff = datetime.now() - timedelta(minutes=30)
        recent = [a for a in self.activity_history
                  if datetime.fromisoformat(a['time']) > cutoff]

        if not recent:
            return 30

        # 成功率
        success_rate = sum(1 for a in recent if a['status'] == 'success') / len(recent)

        # 活动频率
        frequency = len(recent) / 30  # 每分钟活动数

        # 综合评分
        score = int(success_rate * 50 + min(frequency * 10, 50))
        return max(0, min(100, score))

    def get_peak_hour(self):
        """获取最高效时段"""
        if not self.peak_hours:
            return None
        return max(self.peak_hours, key=self.peak_hours.get)

    def get_streak_info(self):
        """获取连击信息"""
        if not self.activity_history:
            return {'current': 0, 'best': 0}

        now = datetime.now()
        current_streak = 0
        best_streak = 0

        for activity in reversed(self.activity_history):
            act_time = datetime.fromisoformat(activity['time'])
            if (now - act_time).total_seconds() < 300:  # 5分钟内
                if activity['status'] == 'success':
                    current_streak += 1
            else:
                break

        return {'current': current_streak, 'best': best_streak}


class CodeStatsTracker:
    """代码统计追踪器"""

    def __init__(self):
        self.files_touched = set()
        self.lines_changed_estimate = 0
        self.languages_used = {}
        self.operations = {
            'write': 0,
            'edit': 0,
            'read': 0,
            'bash': 0
        }

    def record_operation(self, tool, file_path=None):
        """记录操作"""
        if tool in self.operations:
            self.operations[tool] += 1

        if file_path:
            self.files_touched.add(file_path)

            # 检测语言
            ext = Path(file_path).suffix.lower()
            lang_map = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.ts': 'TypeScript',
                '.java': 'Java',
                '.cpp': 'C++',
                '.c': 'C',
                '.go': 'Go',
                '.rs': 'Rust',
                '.rb': 'Ruby',
                '.php': 'PHP',
                '.html': 'HTML',
                '.css': 'CSS',
                '.json': 'JSON',
                '.md': 'Markdown',
            }
            if ext in lang_map:
                self.languages_used[lang_map[ext]] = self.languages_used.get(lang_map[ext], 0) + 1

    def get_summary(self):
        """获取统计摘要"""
        return {
            'files_touched': len(self.files_touched),
            'operations': self.operations,
            'top_language': max(self.languages_used, key=self.languages_used.get) if self.languages_used else None,
            'total_ops': sum(self.operations.values())
        }


# 全局实例
session_tracker = WorkSessionTracker()
productivity = ProductivityAnalyzer()
code_stats = CodeStatsTracker()


def load_activity():
    """加载活动状态"""
    if ACTIVITY_FILE.exists():
        try:
            with open(ACTIVITY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'current_tool': None,
        'is_thinking': False,
        'requests_count': 0,
        'last_update': None,
        'activities': [],
        'focus_mode': False,
        'flow_state': False,
    }


def save_activity(activity):
    """保存活动状态"""
    activity['last_update'] = datetime.now().isoformat()
    with open(ACTIVITY_FILE, 'w', encoding='utf-8') as f:
        json.dump(activity, f, indent=2, ensure_ascii=False)


def load_state():
    """加载宠物状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'name': 'Claude',
        'level': 1,
        'xp': 0,
        'xp_to_next': 100,
        'hunger': 100,
        'happiness': 100,
        'energy': 100,
        'files_created': 0,
        'files_modified': 0,
        'commands_run': 0,
        'consecutive_failures': 0,
        'combo': 0,
        'last_combo_time': None,
    }


def save_state(state):
    """保存宠物状态"""
    state['last_updated'] = datetime.now().isoformat()
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def save_stats():
    """保存统计数据"""
    stats = {
        'productivity_score': productivity.get_productivity_score(),
        'focus_score': session_tracker.get_focus_score(),
        'streak': productivity.get_streak_info(),
        'code_stats': code_stats.get_summary(),
        'peak_hour': productivity.get_peak_hour(),
        'needs_break': session_tracker.needs_break(),
        'last_update': datetime.now().isoformat(),
    }
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    return stats


def handle_pre_tool(tool):
    """工具使用前"""
    activity = load_activity()

    activity['current_tool'] = tool
    activity['is_thinking'] = True
    activity['tool_start_time'] = datetime.now().isoformat()

    # 检测是否进入专注模式
    if activity.get('activities'):
        recent_count = len([a for a in activity['activities'][-10:]
                           if datetime.fromisoformat(a['time']) > datetime.now() - timedelta(minutes=10)])
        if recent_count >= 5:
            activity['focus_mode'] = True

    save_activity(activity)

    # 更新追踪器
    session_tracker.record_activity(tool)
    productivity.record_activity(tool, 'started')

    print(f"🤖 [{tool}] 开始...")


def handle_post_tool(tool, status='success', exit_code=0):
    """工具使用后"""
    activity = load_activity()
    state = load_state()

    activity['current_tool'] = None
    activity['is_thinking'] = False

    # 计算工具使用时长
    if 'tool_start_time' in activity:
        start_time = datetime.fromisoformat(activity['tool_start_time'])
        duration = (datetime.now() - start_time).total_seconds()
        activity['last_tool_duration'] = duration

    # 更新统计和状态
    xp_gain = 0
    mood_change = None

    if tool == 'Write' and status == 'success':
        state['files_created'] = state.get('files_created', 0) + 1
        xp_gain = 20
        state['happiness'] = min(100, state.get('happiness', 100) + 5)
        mood_change = 'excited'
        activity['activities'].append({
            'type': 'write',
            'time': datetime.now().isoformat(),
            'xp': xp_gain
        })
        print(f"✨ 文件创建成功! +{xp_gain} XP")

    elif tool == 'Edit' and status == 'success':
        state['files_modified'] = state.get('files_modified', 0) + 1
        xp_gain = 12
        state['happiness'] = min(100, state.get('happiness', 100) + 3)
        mood_change = 'happy'
        activity['activities'].append({
            'type': 'edit',
            'time': datetime.now().isoformat(),
            'xp': xp_gain
        })
        print(f"✏️ 文件编辑完成! +{xp_gain} XP")

    elif tool == 'Bash':
        state['commands_run'] = state.get('commands_run', 0) + 1
        if exit_code == 0:
            xp_gain = 8
            state['consecutive_failures'] = 0
            activity['activities'].append({
                'type': 'bash',
                'time': datetime.now().isoformat(),
                'xp': xp_gain
            })
            print(f"💻 命令执行成功! +{xp_gain} XP")
        else:
            state['consecutive_failures'] = state.get('consecutive_failures', 0) + 1
            state['happiness'] = max(0, state.get('happiness', 100) - 5)
            mood_change = 'worried'
            print(f"❌ 命令执行失败")

    elif tool == 'Read':
        xp_gain = 3
        activity['activities'].append({
            'type': 'read',
            'time': datetime.now().isoformat(),
            'xp': xp_gain
        })

    # 连击系统
    if xp_gain > 0:
        now = time.time()
        last_combo = state.get('last_combo_time', 0)
        if now - last_combo < 10:  # 10秒内
            state['combo'] = state.get('combo', 0) + 1
            combo_bonus = min(state['combo'] * 2, 10)
            xp_gain += combo_bonus
            if state['combo'] >= 3:
                print(f"🔥 {state['combo']}x 连击! +{combo_bonus} 额外 XP")
        else:
            state['combo'] = 1
        state['last_combo_time'] = now

    # 添加XP
    state['xp'] = state.get('xp', 0) + xp_gain

    # 升级检查
    xp_to_next = state.get('xp_to_next', 100)
    while state['xp'] >= xp_to_next:
        state['xp'] -= xp_to_next
        state['level'] = state.get('level', 1) + 1
        xp_to_next = int(100 * (1.2 ** (state['level'] - 1)))
        state['xp_to_next'] = xp_to_next
        print(f"🎉 升级! 等级 {state['level']}")

    # 更新心情
    if mood_change:
        activity['mood'] = mood_change

    # 请求计数
    activity['requests_count'] = activity.get('requests_count', 0) + 1

    # 保持活动历史
    if len(activity.get('activities', [])) > 100:
        activity['activities'] = activity['activities'][-100:]

    # 更新追踪器
    productivity.record_activity(tool, status)
    code_stats.record_operation(tool)

    # 保存并输出统计
    save_activity(activity)
    save_state(state)
    stats = save_stats()

    # 专注度通知
    if stats['focus_score'] >= 80:
        print(f"🎯 专注度: {stats['focus_score']}% - 进入心流状态!")
        activity['flow_state'] = True

    # 疲劳提醒
    if stats['needs_break']:
        print(f"☕ 你已连续工作50分钟，建议休息一下!")


def handle_tool_error(tool, error):
    """工具错误处理"""
    activity = load_activity()
    state = load_state()

    activity['current_tool'] = None
    activity['is_thinking'] = False
    activity['last_error'] = {
        'tool': tool,
        'error': str(error)[:200],
        'time': datetime.now().isoformat()
    }

    state['consecutive_failures'] = state.get('consecutive_failures', 0) + 1
    state['happiness'] = max(0, state.get('happiness', 100) - 8)
    activity['mood'] = 'worried'

    # 记录错误
    productivity.record_activity(tool, 'error')

    save_activity(activity)
    save_state(state)

    print(f"😟 检测到错误: {str(error)[:100]}")


def handle_session_start():
    """会话开始"""
    activity = load_activity()
    state = load_state()

    activity['session_start'] = datetime.now().isoformat()
    activity['is_thinking'] = False

    # 时间衰减计算
    last_update = state.get('last_updated')
    if last_update:
        try:
            last_time = datetime.fromisoformat(last_update)
            hours_passed = (datetime.now() - last_time).total_seconds() / 3600
            if hours_passed > 0:
                decay = int(hours_passed * 3)
                state['hunger'] = max(0, state.get('hunger', 100) - decay)
                state['happiness'] = max(0, state.get('happiness', 100) - decay // 2)
                print(f"⏰ 离开 {hours_passed:.1f} 小时，状态衰减: -{decay}")
        except:
            pass

    # 启动会话追踪
    session_tracker.start_session()

    save_activity(activity)
    save_state(state)

    # 显示欢迎信息
    level = state.get('level', 1)
    xp = state.get('xp', 0)
    xp_to_next = state.get('xp_to_next', 100)
    print(f"🐾 欢迎回来! {state.get('name', 'Claude')} (Lv.{level} {xp}/{xp_to_next} XP)")
    print(f"💡 输入 /pet-status 查看详细状态")


def handle_session_end():
    """会话结束"""
    activity = load_activity()
    state = load_state()

    activity['session_end'] = datetime.now().isoformat()

    # 会话统计
    if 'session_start' in activity:
        start = datetime.fromisoformat(activity['session_start'])
        duration = (datetime.now() - start).total_seconds() / 60  # 分钟

        # 计算会话奖励
        activity_count = len(activity.get('activities', []))
        bonus_xp = min(50, 10 + activity_count * 2)

        state['xp'] = state.get('xp', 0) + bonus_xp
        state['happiness'] = min(100, state.get('happiness', 100) + 10)
        state['total_sessions'] = state.get('total_sessions', 0) + 1

        print(f"📊 会话统计:")
        print(f"   ⏱️  时长: {int(duration)} 分钟")
        print(f"   📝 操作: {activity_count} 次")
        print(f"   🎯 专注度: {session_tracker.get_focus_score()}%")
        print(f"   🎁 会话奖励: +{bonus_xp} XP")

    save_activity(activity)
    save_state(state)


def handle_skill_command(command):
    """处理技能命令"""
    if command == 'status':
        show_status()
    elif command == 'stats':
        show_stats()
    elif command == 'focus':
        toggle_focus_mode()
    elif command == 'break':
        take_break()


def show_status():
    """显示详细状态"""
    activity = load_activity()
    state = load_state()

    print(f"\n{'='*40}")
    print(f"🤖 {state.get('name', 'Claude')} 状态面板")
    print(f"{'='*40}")
    print(f"📊 等级: {state.get('level', 1)}")
    print(f"⭐ 经验: {state.get('xp', 0)}/{state.get('xp_to_next', 100)}")
    print(f"")
    print(f"🍖 饱食度: {state.get('hunger', 100)}/100")
    print(f"😊 快乐值: {state.get('happiness', 100)}/100")
    print(f"⚡ 能量: {state.get('energy', 100)}/100")
    print(f"")
    print(f"📁 文件创建: {state.get('files_created', 0)}")
    print(f"✏️  文件编辑: {state.get('files_modified', 0)}")
    print(f"💻 命令执行: {state.get('commands_run', 0)}")
    print(f"🔥 当前连击: {state.get('combo', 0)}x")
    print(f"{'='*40}\n")


def show_stats():
    """显示生产力统计"""
    stats = save_stats()

    print(f"\n{'='*40}")
    print(f"📈 生产力统计")
    print(f"{'='*40}")
    print(f"🎯 生产力评分: {stats['productivity_score']}/100")
    print(f"🧠 专注度: {stats['focus_score']}/100")
    print(f"🔥 连击: {stats['streak']['current']} (最佳: {stats['streak']['best']})")
    print(f"")
    code = stats['code_stats']
    print(f"📁 接触文件: {code['files_touched']}")
    print(f"🔧 总操作: {code['total_ops']}")
    if code['top_language']:
        print(f"💻 主要语言: {code['top_language']}")
    print(f"")
    print(f"⏰ 高效时段: {stats['peak_hour']}:00" if stats['peak_hour'] else "")
    print(f"{'='*40}\n")


def toggle_focus_mode():
    """切换专注模式"""
    activity = load_activity()
    current = activity.get('focus_mode', False)
    activity['focus_mode'] = not current
    save_activity(activity)

    status = "开启" if activity['focus_mode'] else "关闭"
    print(f"🎯 专注模式已{status}")


def take_break():
    """主动休息"""
    activity = load_activity()
    state = load_state()

    activity['break_start'] = datetime.now().isoformat()
    state['energy'] = min(100, state.get('energy', 100) + 20)
    state['happiness'] = min(100, state.get('happiness', 100) + 10)

    save_activity(activity)
    save_state(state)

    print(f"☕ 休息模式已开启 - 喝杯水，放松一下!")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="Enhanced Claude Pet Activity Tracker")
    parser.add_argument('--event', required=True, help='Event type')
    parser.add_argument('--tool', help='Tool name')
    parser.add_argument('--status', default='success', help='Status')
    parser.add_argument('--exit_code', type=int, default=0, help='Exit code')
    parser.add_argument('--error', help='Error message')
    parser.add_argument('--command', help='Skill command')
    parser.add_argument('--file', help='File path')

    args = parser.parse_args()

    try:
        if args.event == 'PreToolUse':
            handle_pre_tool(args.tool)

        elif args.event == 'PostToolUse':
            handle_post_tool(args.tool, args.status, args.exit_code)

        elif args.event == 'PostToolUseFailure':
            handle_tool_error(args.tool, args.error)

        elif args.event == 'SessionStart':
            handle_session_start()

        elif args.event == 'SessionEnd':
            handle_session_end()

        elif args.event == 'SkillCommand':
            handle_skill_command(args.command)

    except Exception as e:
        print(f"Tracker error: {e}")
        sys.exit(0)


if __name__ == '__main__':
    main()
