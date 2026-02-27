#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory System for Claude Pet Companion

The pet remembers every Claude Code task and can reference them.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
from pathlib import Path
import hashlib
import random


class MemoryType(Enum):
    """记忆类型"""
    # 任务相关
    FILE_WRITE = "file_write"           # 写入文件
    FILE_EDIT = "file_edit"             # 编辑文件
    FILE_READ = "file_read"             # 读取文件
    COMMAND_RUN = "command_run"         # 运行命令
    TOOL_USE = "tool_use"               # 使用工具

    # 交互相关
    USER_QUERY = "user_query"           # 用户查询
    ASSISTANT_RESPONSE = "response"     # 助手响应

    # 状态相关
    ERROR_OCCURRED = "error"             # 发生错误
    SUCCESS = "success"                 # 成功完成
    THINKING = "thinking"               # 思考中

    # 特殊事件
    FIRST_CONTACT = "first_contact"     # 首次接触
    MILESTONE = "milestone"             # 里程碑
    LONG_SESSION = "long_session"       # 长时间会话
    BREAK_TAKEN = "break_taken"         # 休息


class MemoryImportance(Enum):
    """记忆重要性"""
    TRIVIAL = 1      # 琐碎 - 随时间快速遗忘
    LOW = 2          # 低 - 较长时间保留
    NORMAL = 3       # 正常 - 标准保留时间
    HIGH = 4         # 高 - 长期保留
    CRITICAL = 5     # 关键 - 永久保留


@dataclass
class MemoryItem:
    """单条记忆"""
    id: str
    type: MemoryType
    timestamp: datetime
    importance: MemoryImportance = MemoryImportance.NORMAL

    # 任务内容
    task_id: str = ""                   # 任务ID（关联多次操作）
    tool: str = ""                       # 使用的工具
    input_data: Dict[str, Any] = field(default_factory=dict)  # 输入数据摘要
    output_data: Dict[str, Any] = field(default_factory=dict) # 输出数据摘要

    # 情感上下文
    user_emotion: str = "neutral"        # 用户情绪
    pet_emotion: str = "happy"           # 宠物当时情绪
    pet_reaction: str = ""                # 宠物的反应

    # 关联信息
    related_files: List[str] = field(default_factory=list)      # 相关文件
    related_commands: List[str] = field(default_factory=list) # 相关命令
    tags: List[str] = field(default_factory=list)               # 标签

    # 回忆强度（0-1，随时间衰减）
    strength: float = 1.0
    access_count: int = 0                # 被访问次数

    # 元数据
    session_id: str = ""                 # 会话ID
    duration_ms: int = 0                 # 持续时间（毫秒）
    success: bool = True                  # 是否成功

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type.value,
            'timestamp': self.timestamp.isoformat(),
            'importance': self.importance.value,
            'task_id': self.task_id,
            'tool': self.tool,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'user_emotion': self.user_emotion,
            'pet_emotion': self.pet_emotion,
            'pet_reaction': self.pet_reaction,
            'related_files': self.related_files,
            'related_commands': self.related_commands,
            'tags': self.tags,
            'strength': self.strength,
            'access_count': self.access_count,
            'session_id': self.session_id,
            'duration_ms': self.duration_ms,
            'success': self.success,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """从字典创建"""
        return cls(
            id=data['id'],
            type=MemoryType(data['type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            importance=MemoryImportance(data.get('importance', 3)),
            task_id=data.get('task_id', ''),
            tool=data.get('tool', ''),
            input_data=data.get('input_data', {}),
            output_data=data.get('output_data', {}),
            user_emotion=data.get('user_emotion', 'neutral'),
            pet_emotion=data.get('pet_emotion', 'happy'),
            pet_reaction=data.get('pet_reaction', ''),
            related_files=data.get('related_files', []),
            related_commands=data.get('related_commands', []),
            tags=data.get('tags', []),
            strength=data.get('strength', 1.0),
            access_count=data.get('access_count', 0),
            session_id=data.get('session_id', ''),
            duration_ms=data.get('duration_ms', 0),
            success=data.get('success', True),
        )

    def decay(self, days_passed: float):
        """记忆衰减"""
        # 根据重要性计算衰减率
        decay_rates = {
            MemoryImportance.TRIVIAL: 0.5,   # 2天减半
            MemoryImportance.LOW: 0.2,       # 5天减半
            MemoryImportance.NORMAL: 0.1,    # 10天减半
            MemoryImportance.HIGH: 0.05,      # 20天减半
            MemoryImportance.CRITICAL: 0.01,  # 100天减半
        }
        decay_rate = decay_rates.get(self.importance, 0.1)
        self.strength *= (0.5 ** (days_passed * decay_rate))

    def is_forgotten(self) -> bool:
        """检查记忆是否被遗忘"""
        return self.strength < 0.1


@dataclass
class MemoryPattern:
    """记忆模式 - 从多条记忆中提取的规律"""
    pattern_type: str                   # 模式类型
    description: str                      # 描述
    confidence: float                     # 置信度 0-1
    frequency: int                       # 出现次数
    last_occurrence: datetime             # 最后出现时间

    # 模式数据
    pattern_data: Dict[str, Any] = field(default_factory=dict)

    # 关联的记忆ID
    memory_ids: List[str] = field(default_factory=list)


class MemoryManager:
    """记忆管理器 - 负责存储、检索和管理所有记忆"""

    def __init__(self, max_memories: int = 10000):
        self.max_memories = max_memories
        self.memories: List[MemoryItem] = []
        self.patterns: List[MemoryPattern] = []

        # 记忆文件路径
        self.memory_file = Path.home() / '.claude-pet-companion' / 'memories.json'

        # 统计数据
        self.statistics = {
            'total_memories': 0,
            'by_type': {},
            'by_tool': {},
            'by_file': {},
            'success_rate': 0.0,
            'total_duration_ms': 0,
        }

        # 当前会话
        self.current_session_id: str = ""
        self.session_start: Optional[datetime] = None
        self.session_task_count: int = 0

        # 加载已有记忆
        self.load()

    def _generate_memory_id(self) -> str:
        """生成唯一的记忆ID"""
        return hashlib.md5(
            f"{datetime.now().isoformat()}-{random.randint(0, 1000000)}"
        ).hexdigest()[:12]

    def start_session(self):
        """开始新会话"""
        self.current_session_id = hashlib.md5(
            f"{datetime.now().isoformat()}"
        ).hexdigest()[:8]
        self.session_start = datetime.now()
        self.session_task_count = 0

    def end_session(self):
        """结束会话"""
        if self.session_start:
            duration = (datetime.now() - self.session_start).total_seconds() * 1000
            if duration > 3600000:  # 超过1小时的会话记录
                self.add_memory(MemoryType.LONG_SESSION, {
                    'session_id': self.current_session_id,
                    'duration_ms': duration,
                    'task_count': self.session_task_count
                }, importance=MemoryImportance.HIGH)
        self.current_session_id = ""

    def add_memory(self, memory_type: MemoryType, data: Dict[str, Any],
                    tool: str = "", **kwargs) -> MemoryItem:
        """添加一条记忆"""
        # 生成记忆ID
        memory_id = self._generate_memory_id()

        # 确定重要性
        importance = kwargs.get('importance', MemoryImportance.NORMAL)
        if 'importance' not in kwargs:
            # 自动判断重要性
            if memory_type in [MemoryType.ERROR_OCCURRED, MemoryType.MILESTONE]:
                importance = MemoryImportance.HIGH
            elif memory_type in [MemoryType.SUCCESS, MemoryType.FIRST_CONTACT]:
                importance = MemoryImportance.HIGH
            elif memory_type == MemoryType.FILE_WRITE:
                importance = MemoryImportance.NORMAL
            elif memory_type == MemoryType.COMMAND_RUN:
                importance = MemoryImportance.LOW

        # 创建记忆
        memory = MemoryItem(
            id=memory_id,
            type=memory_type,
            timestamp=datetime.now(),
            importance=importance,
            tool=tool,
            task_id=kwargs.get('task_id', self.current_session_id),
            input_data=data,
            output_data=kwargs.get('output_data', {}),
            user_emotion=kwargs.get('user_emotion', 'neutral'),
            pet_emotion=kwargs.get('pet_emotion', 'happy'),
            pet_reaction=kwargs.get('pet_reaction', ''),
            related_files=kwargs.get('related_files', []),
            related_commands=kwargs.get('related_commands', []),
            tags=kwargs.get('tags', []),
            session_id=self.current_session_id,
            duration_ms=kwargs.get('duration_ms', 0),
            success=kwargs.get('success', True),
        )

        # 添加到列表
        self.memories.append(memory)
        self.session_task_count += 1

        # 更新统计
        self._update_statistics(memory)

        # 检查是否需要清理旧记忆
        if len(self.memories) > self.max_memories:
            self._cleanup_old_memories()

        # 自动保存
        if len(self.memories) % 10 == 0:  # 每10条记忆保存一次
            self.save()

        return memory

    def _update_statistics(self, memory: MemoryItem):
        """更新统计数据"""
        self.statistics['total_memories'] += 1

        # 按类型统计
        mtype = memory.type.value
        self.statistics['by_type'][mtype] = self.statistics['by_type'].get(mtype, 0) + 1

        # 按工具统计
        if memory.tool:
            self.statistics['by_tool'][memory.tool] = self.statistics['by_tool'].get(memory.tool, 0) + 1

        # 按文件统计
        for file in memory.related_files:
            self.statistics['by_file'][file] = self.statistics['by_file'].get(file, 0) + 1

        # 成功率
        if memory.type in [MemoryType.FILE_WRITE, MemoryType.COMMAND_RUN]:
            total = self.statistics['total_memories']
            success_count = sum(1 for m in self.memories if m.success)
            if total > 0:
                self.statistics['success_rate'] = success_count / total

        # 总时长
        self.statistics['total_duration_ms'] += memory.duration_ms

    def _cleanup_old_memories(self):
        """清理旧记忆"""
        # 按时间排序，删除最旧的
        self.memories.sort(key=lambda m: m.timestamp)

        # 计算需要删除多少
        to_remove = len(self.memories) - self.max_memories

        if to_remove > 0:
            # 保留重要记忆
            critical = [m for m in self.memories if m.importance == MemoryImportance.CRITICAL]
            high = [m for m in self.memories if m.importance == MemoryImportance.HIGH]

            # 优先删除不重要的记忆
            self.memories = critical + high + self.memories[
                len(critical + high):len(self.memories) - self.max_memories
            ]

    def search_memories(self, query: str, limit: int = 20) -> List[MemoryItem]:
        """搜索记忆"""
        query = query.lower()
        results = []

        for memory in reversed(self.memories):  # 从最新的开始搜索
            if len(results) >= limit:
                break

            # 搜索工具名称
            if query in memory.tool.lower():
                results.append(memory)
                continue

            # 搜索文件名
            for file in memory.related_files:
                if query in file.lower():
                    results.append(memory)
                    break

            # 搜索标签
            for tag in memory.tags:
                if query in tag.lower():
                    results.append(memory)
                    break

            # 搜索任务描述
            if 'description' in memory.input_data:
                if query in memory.input_data['description'].lower():
                    results.append(memory)
                    continue

        return results

    def get_recent_memories(self, count: int = 10) -> List[MemoryItem]:
        """获取最近的记忆"""
        return list(reversed(self.memories[-count:]))

    def get_memories_by_type(self, memory_type: MemoryType,
                           limit: int = 50) -> List[MemoryItem]:
        """按类型获取记忆"""
        return [m for m in self.memories if m.type == memory_type][-limit:]

    def get_memories_by_file(self, file_path: str,
                           limit: int = 20) -> List[MemoryItem]:
        """获取与特定文件相关的记忆"""
        file_path = file_path.lower()
        return [
            m for m in self.memories
            if any(file_path in f.lower() for f in m.related_files)
        ][-limit:]

    def get_activity_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取活动摘要（过去N小时）"""
        cutoff = datetime.now().timestamp() - (hours * 3600)
        recent_memories = [
            m for m in self.memories
            if m.timestamp.timestamp() > cutoff
        ]

        summary = {
            'total_tasks': len(recent_memories),
            'by_type': {},
            'by_tool': {},
            'files_worked_on': set(),
            'success_rate': 0.0,
            'total_duration_ms': 0,
            'most_active_tool': '',
        }

        for m in recent_memories:
            # 类型统计
            mtype = m.type.value
            summary['by_type'][mtype] = summary['by_type'].get(mtype, 0) + 1

            # 工具统计
            if m.tool:
                summary['by_tool'][m.tool] = summary['by_tool'].get(m.tool, 0) + 1

            # 文件列表
            summary['files_worked_on'].update(m.related_files)

            # 时长和成功率
            summary['total_duration_ms'] += m.duration_ms
            if m.success:
                summary['success_rate'] += 1

        if recent_memories:
            summary['success_rate'] /= len(recent_memories)

        # 找出最常用的工具
        if summary['by_tool']:
            summary['most_active_tool'] = max(
                summary['by_tool'].items(),
                key=lambda x: x[1]
            )[0]

        summary['files_worked_on'] = list(summary['files_worked_on'])

        return summary

    def get_patterns(self) -> List[MemoryPattern]:
        """获取记忆模式"""
        self._detect_patterns()
        return self.patterns

    def _detect_patterns(self):
        """检测记忆中的模式"""
        self.patterns.clear()

        # 检测文件模式
        file_counts = {}
        for memory in self.memories[-500:]:  # 只分析最近500条
            for file in memory.related_files:
                file_counts[file] = file_counts.get(file, 0) + 1

        # 高频文件
        for file, count in file_counts.items():
            if count >= 3:
                self.patterns.append(MemoryPattern(
                    pattern_type="frequent_file",
                    description=f"经常编辑文件: {self._shorten_path(file)}",
                    confidence=min(1.0, count / 10),
                    frequency=count,
                    last_occurrence=max(m.timestamp for m in self.memories if file in m.related_files),
                    pattern_data={'file': file}
                ))

        # 检测工具偏好
        tool_counts = {}
        for memory in self.memories[-500:]:
            if memory.tool:
                tool_counts[memory.tool] = tool_counts.get(memory.tool, 0) + 1

        for tool, count in tool_counts.items():
            if count >= 5:
                self.patterns.append(MemoryPattern(
                    pattern_type="preferred_tool",
                    description=f"偏好工具: {tool}",
                    confidence=min(1.0, count / 20),
                    frequency=count,
                    last_occurrence=max(m.timestamp for m in self.memories if m.tool == tool),
                    pattern_data={'tool': tool}
                ))

        # 检测工作时间模式
        hours = [m.timestamp.hour for m in self.memories if m.type != MemoryType.THINKING]
        if hours:
            from collections import Counter
            hour_counts = Counter(hours)
            peak_hour = hour_counts.most_common(1)[0]

            if hour_counts[peak_hour] >= 5:
                self.patterns.append(MemoryPattern(
                    pattern_type="peak_hour",
                    description=f"高峰时段: {peak_hour}:00",
                    confidence=0.8,
                    frequency=hour_counts[peak_hour],
                    last_occurrence=datetime.now().replace(hour=peak_hour),
                    pattern_data={'hour': peak_hour}
                ))

    def _shorten_path(self, path: str) -> str:
        """缩短文件路径显示"""
        if len(path) > 40:
            parts = path.split('\\') if '\\' in path else path.split('/')
            if len(parts) > 2:
                return f".../{parts[-2]}/{parts[-1]}"
        return path

    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        # 获取最近的对话记忆
        conversations = [
            m for m in self.get_recent_memories(100)
            if m.type in [MemoryType.USER_QUERY, MemoryType.ASSISTANT_RESPONSE]
        ]

        summary = {
            'total_exchanges': len([m for m in conversations if m.type == MemoryType.USER_QUERY]),
            'topics': self._extract_topics(conversations),
            'avg_response_length': 0,
            'last_interaction': None,
        }

        if conversations:
            summary['last_interaction'] = max(m.timestamp for m in conversations)

        return summary

    def _extract_topics(self, conversations: List[MemoryItem]) -> List[str]:
        """提取话题"""
        topics = []

        # 基于文件扩展名提取
        extensions = []
        for m in conversations:
            for file in m.related_files:
                ext = Path(file).suffix.lower()
                if ext:
                    extensions.append(ext)

        # 统计最常见
        from collections import Counter
        ext_counts = Counter(extensions)
        for ext, count in ext_counts.most_common(5):
            if ext:
                topics.append(f"{ext[1:]} 文件")

        return topics

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        # 最近7天的记忆
        week_ago = datetime.now().timestamp() - 7 * 24 * 3600
        recent = [m for m in self.memories if m.timestamp.timestamp() > week_ago]

        return {
            'total_memories': len(self.memories),
            'recent_week': len(recent),
            'by_type': self.statistics['by_type'],
            'by_tool': self.statistics['by_tool'],
            'most_worked_files': sorted(
                self.statistics['by_file'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'success_rate': self.statistics['success_rate'],
            'total_hours': self.statistics['total_duration_ms'] / 3600000,
            'patterns_found': len(self.patterns),
        }

    def remember_task(self, tool: str, input_data: Dict[str, Any],
                      output_data: Dict[str, Any] = None, **kwargs) -> MemoryItem:
        """记录一个任务（主要入口）"""
        # 提取相关信息
        files = kwargs.get('files', [])
        commands = kwargs.get('commands', [])
        duration_ms = kwargs.get('duration_ms', 0)
        success = kwargs.get('success', True)

        # 确定记忆类型
        memory_type = kwargs.get('type', MemoryType.COMMAND_RUN)
        if not kwargs.get('type'):
            if tool in ['Read', 'Write', 'Edit']:
                memory_type = MemoryType.FILE_WRITE if tool == 'Write' else MemoryType.FILE_READ

        # 根据工具调整
        if tool == 'Write' and files:
            memory_type = MemoryType.FILE_WRITE
        elif tool == 'Edit' and files:
            memory_type = MemoryType.FILE_EDIT
        elif tool == 'Bash':
            memory_type = MemoryType.COMMAND_RUN

        # 处理错误
        if not success:
            memory_type = MemoryType.ERROR_OCCURRED

        # 创建记忆
        return self.add_memory(
            memory_type=memory_type,
            data=input_data,
            tool=tool,
            output_data=output_data or {},
            related_files=files,
            related_commands=commands,
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )

    def get_memories_since(self, timestamp: datetime) -> List[MemoryItem]:
        """获取指定时间之后的记忆"""
        return [
            m for m in self.memories
            if m.timestamp > timestamp
        ]

    def decay_all_memories(self, days: float = 1.0):
        """衰减所有记忆"""
        for memory in self.memories:
            memory.decay(days)

        # 移除被遗忘的记忆
        self.memories = [m for m in self.memories if not m.is_forgotten()]

    def save(self):
        """保存记忆到文件"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'memories': [m.to_dict() for m in self.memories],
            'statistics': self.statistics,
            'patterns': [p.__dict__ for p in self.patterns],
            'last_updated': datetime.now().isoformat(),
        }

        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self):
        """从文件加载记忆"""
        if not self.memory_file.exists():
            # 创建初始记忆
            self.add_first_contact_memory()
            return

        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.memories = [
                MemoryItem.from_dict(m) for m in data.get('memories', [])
            ]
            self.statistics = data.get('statistics', self.statistics)
            self.patterns = [
                MemoryPattern(**p) for p in data.get('patterns', [])
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            # 加载失败，创建初始记忆
            self.add_first_contact_memory()

    def add_first_contact_memory(self):
        """添加首次接触记忆"""
        self.add_memory(
            memory_type=MemoryType.FIRST_CONTACT,
            data={'description': 'Claude Pet Companion 首次启动'},
            importance=MemoryImportance.CRITICAL,
            pet_emotion='excited',
            pet_reaction='🎉 Hello! I\'m your coding companion!',
            tags=['milestone', 'first']
        )

    def get_related_memories(self, file_path: str, limit: int = 5) -> List[MemoryItem]:
        """获取与文件相关的记忆"""
        return self.get_memories_by_file(file_path, limit)

    def get_memories_by_time_range(self, start: datetime, end: datetime) -> List[MemoryItem]:
        """获取时间范围内的记忆"""
        return [
            m for m in self.memories
            if start <= m.timestamp <= end
        ]

    def get_memory_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        """根据ID获取记忆"""
        for memory in self.memories:
            if memory.id == memory_id:
                memory.access_count += 1
                return memory
        return None

    def get_random_old_memory(self) -> Optional[MemoryItem]:
        """获取一条随机旧记忆（用于怀旧功能）"""
        old_memories = [m for m in self.memories if m.importance >= MemoryImportance.HIGH]
        if old_memories:
            return random.choice(old_memories)
        return None

    def calculate_affinity(self, tools_used: Dict[str, int]) -> Dict[str, float]:
        """计算亲和度（根据工具使用情况）"""
        # 基础分
        scores = {
            'coder': 0.0,
            'warrior': 0.0,
            'social': 0.0,
            'night_owl': 0.0,
        }

        # 根据记忆计算
        for memory in self.memories[-100:]:  # 只看最近100条
            tool = memory.tool
            if tool == 'Write':
                scores['coder'] += 2
                scores['warrior'] += 1
            elif tool == 'Edit':
                scores['coder'] += 1
                scores['warrior'] += 1
                scores['social'] += 0.5
            elif tool == 'Bash':
                scores['warrior'] += 2
                scores['coder'] += 0.5

        # 夜间编程加成
        for memory in self.memories[-100:]:
            if memory.timestamp.hour >= 22 or memory.timestamp.hour <= 6:
                if memory.tool in ['Write', 'Edit', 'Read']:
                    scores['night_owl'] += 1

        # 归一化
        total = max(1, sum(scores.values()))
        for path in scores:
            scores[path] /= total

        return scores

    # Conversation tracking methods

    def start_conversation(self, title: str, tags: list = None) -> str:
        """Start a new conversation"""
        try:
            from .conversation_store import get_conversation_store
            store = get_conversation_store()
            return store.start_conversation(title, tags, self.current_session_id)
        except ImportError:
            return ""

    def add_conversation_message(self, conversation_id: str, role: str,
                                 content: str, **kwargs) -> bool:
        """Add a message to a conversation"""
        try:
            from .conversation_store import get_conversation_store
            store = get_conversation_store()
            return store.add_message(conversation_id, role, content, **kwargs)
        except ImportError:
            return False

    def end_conversation(self, conversation_id: str, summary: str = "",
                        success: bool = True, rating: int = None):
        """End a conversation"""
        try:
            from .conversation_store import get_conversation_store
            store = get_conversation_store()
            store.end_conversation(conversation_id, summary, success, rating)
        except ImportError:
            pass

    def get_conversation(self, conversation_id: str):
        """Get a conversation by ID"""
        try:
            from .conversation_store import get_conversation_store
            store = get_conversation_store()
            return store.get_conversation(conversation_id)
        except ImportError:
            return None

    def search_conversations(self, query: str, limit: int = 20):
        """Search conversations"""
        try:
            from .conversation_store import get_conversation_store
            store = get_conversation_store()
            return store.search_conversations(query, limit)
        except ImportError:
            return []

    def list_conversations(self, limit: int = 50):
        """List all conversations"""
        try:
            from .conversation_store import get_conversation_store
            store = get_conversation_store()
            return store.list_conversations(limit)
        except ImportError:
            return []


# 全局记忆管理器实例
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """获取全局记忆管理器实例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


if __name__ == "__main__":
    # 测试记忆系统
    manager = MemoryManager()

    print("=== 记忆系统测试 ===")

    # 模拟添加记忆
    manager.start_session()

    manager.add_memory(
        MemoryType.FILE_WRITE,
        {'file': 'main.py', 'description': 'Created new file'},
        tool='Write',
        related_files=['main.py'],
        duration_ms=1500
    )

    manager.add_memory(
        MemoryType.COMMAND_RUN,
        {'command': 'pip install', 'description': 'Installed package'},
        tool='Bash',
        related_commands=['pip install'],
        duration_ms=8000
    )

    print(f"总记忆数: {len(manager.memories)}")
    print(f"统计: {manager.get_memory_stats()}")

    # 搜索测试
    results = manager.search_memories("main")
    print(f"搜索 'main': {len(results)} 条结果")

    manager.end_session()
    manager.save()
