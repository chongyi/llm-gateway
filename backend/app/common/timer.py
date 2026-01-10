"""
计时器模块

提供请求耗时统计功能，支持首字节延迟和总耗时的精确测量。
"""

import time
from typing import Optional


class Timer:
    """
    高精度计时器
    
    用于测量请求处理过程中的各项耗时指标：
    - 首字节延迟（TTFB）
    - 总耗时
    
    使用 time.perf_counter() 确保高精度计时。
    
    Example:
        timer = Timer()
        timer.start()
        # ... 发送请求 ...
        timer.mark_first_byte()  # 收到第一个字节
        # ... 接收完整响应 ...
        timer.stop()
        print(f"TTFB: {timer.first_byte_delay_ms}ms")
        print(f"Total: {timer.total_time_ms}ms")
    """
    
    def __init__(self):
        """初始化计时器"""
        self._start_time: Optional[float] = None
        self._first_byte_time: Optional[float] = None
        self._end_time: Optional[float] = None
    
    def start(self) -> "Timer":
        """
        开始计时
        
        Returns:
            Timer: 返回自身，支持链式调用
        """
        self._start_time = time.perf_counter()
        self._first_byte_time = None
        self._end_time = None
        return self
    
    def mark_first_byte(self) -> "Timer":
        """
        标记首字节时间
        
        在收到响应的第一个字节时调用，用于计算 TTFB。
        如果已经标记过，则忽略后续调用。
        
        Returns:
            Timer: 返回自身，支持链式调用
        """
        if self._first_byte_time is None:
            self._first_byte_time = time.perf_counter()
        return self
    
    def stop(self) -> "Timer":
        """
        停止计时
        
        Returns:
            Timer: 返回自身，支持链式调用
        """
        self._end_time = time.perf_counter()
        # 如果没有标记首字节时间，使用结束时间
        if self._first_byte_time is None:
            self._first_byte_time = self._end_time
        return self
    
    @property
    def first_byte_delay_ms(self) -> Optional[int]:
        """
        获取首字节延迟（毫秒）
        
        Returns:
            Optional[int]: 首字节延迟，如果计时未完成则返回 None
        """
        if self._start_time is None or self._first_byte_time is None:
            return None
        return int((self._first_byte_time - self._start_time) * 1000)
    
    @property
    def total_time_ms(self) -> Optional[int]:
        """
        获取总耗时（毫秒）
        
        Returns:
            Optional[int]: 总耗时，如果计时未完成则返回 None
        """
        if self._start_time is None or self._end_time is None:
            return None
        return int((self._end_time - self._start_time) * 1000)
    
    def reset(self) -> "Timer":
        """
        重置计时器
        
        Returns:
            Timer: 返回自身，支持链式调用
        """
        self._start_time = None
        self._first_byte_time = None
        self._end_time = None
        return self
