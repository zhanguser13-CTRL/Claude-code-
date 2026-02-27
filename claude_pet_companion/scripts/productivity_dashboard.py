#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Productivity Dashboard - 生产力仪表板

显示详细的工作统计、效率分析和建议
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# 数据文件路径
DATA_DIR = Path.home() / '.claude-pet-companion'
STATE_FILE = DATA_DIR / 'pet_state.json'
ACTIVITY_FILE = DATA_DIR / 'activity.json'
STATS_FILE = DATA_DIR / 'work_stats.json'


def print_header(title):
    """打印标题"""
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}\n")


def print_section(title):
    """打印小节标题"""
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def load_stats():
    """加载统计数据"""
    files = {
        'state': STATE_FILE,
        'activity': ACTIVITY_FILE,
        'stats': STATS_FILE,
    }
    data = {}
    for key, path in files.items():
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data[key] = json.load(f)
            except:
                data[key] = {}
        else:
            data[key] = {}
    return data


def get_session_duration(activity):
    """获取会话时长"""
    if 'session_start' not in activity:
        return 0
    try:
        start = datetime.fromisoformat(activity['session_start'])
        if 'session_end' in activity:
            end = datetime.fromisoformat(activity['session_end'])
        else:
            end = datetime.now()
        return (end - start).total_seconds() / 60  # 分钟
    except:
        return 0


def get_activity_summary(activity):
    """获取活动摘要"""
    activities = activity.get('activities', [])

    if not activities:
        return {
            'total': 0,
            'by_type': {},
            'hourly': {},
            'last_hour': 0,
        }

    by_type = Counter(a['type'] for a in activities)
    hourly = Counter()

    now = datetime.now()
    last_hour_count = 0

    for a in activities:
        try:
            act_time = datetime.fromisoformat(a['time'])
            hour = act_time.hour
            hourly[hour] += 1

            if (now - act_time).total_seconds() < 3600:
                last_hour_count += 1
        except:
            pass

    return {
        'total': len(activities),
        'by_type': dict(by_type),
        'hourly': dict(hourly),
        'last_hour': last_hour_count,
    }


def calculate_efficiency_score(state, activity, stats):
    """计算综合效率评分"""
    score = 50  # 基础分

    # 等级加成
    level = state.get('level', 1)
    score += min(level * 2, 20)

    # 活动频率
    summary = get_activity_summary(activity)
    if summary['total'] > 0:
        session_min = get_session_duration(activity) or 1
        activity_rate = summary['total'] / max(session_min, 1)
        score += min(activity_rate * 5, 15)

    # 生产力评分
    prod_score = stats.get('productivity_score', 50)
    score = (score + prod_score) // 2

    # 成功率
    failures = state.get('consecutive_failures', 0)
    if failures > 0:
        score -= failures * 5

    return max(0, min(100, score))


def get_recommendations(state, activity, stats):
    """获取改进建议"""
    recommendations = []

    # 专注度建议
    focus_score = stats.get('focus_score', 0)
    if focus_score < 50:
        recommendations.append("🎯 专注度较低，尝试减少中断，专注一项任务")
    elif focus_score >= 80:
        recommendations.append("✨ 专注度很高！继续保持这种心流状态")

    # 连续工作时长
    if stats.get('needs_break'):
        recommendations.append("☕ 你已经连续工作超过50分钟，建议休息5-10分钟")

    # 状态建议
    hunger = state.get('hunger', 100)
    happiness = state.get('happiness', 100)
    energy = state.get('energy', 100)

    if hunger < 40:
        recommendations.append("🍖 宠物饿了，也是时候补充能量了！")
    if happiness < 50:
        recommendations.append("😊 心情不好？双击宠物互动一下吧！")
    if energy < 40:
        recommendations.append("💪 能量不足，考虑休息一下")

    # 连击建议
    combo = state.get('combo', 0)
    if combo >= 5:
        recommendations.append(f"🔥 当前{combo}x连击！趁热打铁继续工作！")

    # 高峰时段
    peak_hour = stats.get('peak_hour')
    if peak_hour is not None:
        recommendations.append(f"⏰ 你的最高效时段是 {peak_hour}:00 - {peak_hour+1}:00")

    return recommendations


def show_dashboard():
    """显示生产力仪表板"""
    data = load_stats()
    state = data['state']
    activity = data['activity']
    stats = data['stats']

    # 标题
    print_header("📊 Claude Pet 生产力仪表板")

    # 宠物状态
    print(f"🤖 {state.get('name', 'Claude')} 状态")
    print(f"   等级: {state.get('level', 1)}")
    print(f"   经验: {state.get('xp', 0)}/{state.get('xp_to_next', 100)}")
    print(f"   状态: {activity.get('mood', 'happy').title()}")
    print(f"   连击: {state.get('combo', 0)}x")

    # 会话统计
    print_section("⏱️  会话统计")
    duration = get_session_duration(activity)
    hours = int(duration // 60)
    mins = int(duration % 60)
    print(f"   本次会话: {hours}小时 {mins}分钟")

    summary = get_activity_summary(activity)
    print(f"   总操作数: {summary['total']}")
    print(f"   最近1小时: {summary['last_hour']} 次操作")

    if summary['by_type']:
        print(f"\n   操作分布:")
        for op, count in sorted(summary['by_type'].items(), key=lambda x: -x[1]):
            emoji = {'write': '📝', 'edit': '✏️', 'read': '📖', 'bash': '💻'}.get(op, '•')
            print(f"      {emoji} {op.capitalize()}: {count}")

    # 效率分析
    print_section("📈 效率分析")
    prod_score = stats.get('productivity_score', 50)
    focus_score = stats.get('focus_score', 0)
    efficiency = calculate_efficiency_score(state, activity, stats)

    print(f"   生产力评分: {prod_score}/100")
    print(f"   专注度: {focus_score}/100")
    print(f"   综合效率: {efficiency}/100")

    # 评分条
    def score_bar(score, width=30):
        filled = int(width * score / 100)
        bar = '█' * filled + '░' * (width - filled)
        colors = {0: '\033[91m', 1: '\033[93m', 2: '\033[92m'}  # 红, 黄, 绿
        color_idx = 0 if score < 50 else (1 if score < 80 else 2)
        return f"{colors[color_idx]}{bar}\033[0m"

    print(f"\n   生产力: {score_bar(prod_score)}")
    print(f"   专注度: {score_bar(focus_score)}")
    print(f"   综合:   {score_bar(efficiency)}")

    # 建议和提醒
    print_section("💡 建议与提醒")
    recommendations = get_recommendations(state, activity, stats)
    if recommendations:
        for rec in recommendations:
            print(f"   {rec}")
    else:
        print(f"   继续保持当前的工作节奏！")

    # 统计数据
    if stats.get('code_stats'):
        print_section("📁 代码统计")
        code = stats['code_stats']
        print(f"   接触文件: {code.get('files_touched', 0)}")
        print(f"   总操作: {code.get('total_ops', 0)}")
        if code.get('top_language'):
            print(f"   主要语言: {code['top_language']}")

    print(f"\n{'=' * 50}")
    print(f"  更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 50}\n")


def show_simple():
    """简化版输出"""
    data = load_stats()
    state = data['state']
    stats = data['stats']

    print(f"\n🤖 {state.get('name', 'Claude')} | Lv.{state.get('level', 1)} | "
          f"生产力: {stats.get('productivity_score', 50)}/100 | "
          f"连击: {state.get('combo', 0)}x\n")


def main():
    """主入口"""
    if len(sys.argv) > 1 and sys.argv[1] == '--simple':
        show_simple()
    else:
        show_dashboard()


if __name__ == '__main__':
    main()
