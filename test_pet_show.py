# -*- coding: utf-8 -*-
import time

# ANSI 控制码
print("\033[2J")  # 清屏
print("\033[H")   # 光标归位

# 移动到中心位置
print("\033[10;40H")

# 绘制宠物
pet = [
    "     ,-----.",
    "    / .   . \\",
    "   |   ^   |",
    "  ,--.---.--.",
    " /   |   |   \\",
    "     \\---/",
    "     '---'",
]

for line in pet:
    print(line)

# 显示状态
print("\033[18;40HLevel 1 | <3 100 | )( 100 | XP: 0")
print("\033[20;40HPress SPACE to pet, F to feed, Q to quit")

# 等待输入
import sys
if sys.platform == "win32":
    import msvcrt
    print("\033[22;40HWaiting...")

    for _ in range(100):
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'q':
                break
            elif key == b' ':
                print("\033[9;45H<3 <3")
            elif key == b'f':
                print("\033[9;45HYummy!")
        time.sleep(0.1)

print("\033[2J")  # 清屏退出
