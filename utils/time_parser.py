import re
from datetime import timedelta

def parse_duration(duration_str: str) -> timedelta | None:
    """
    解析时间字符串，如 "30s", "5m", "1h", "1d"。
    返回一个timedelta对象，解析失败则返回None。
    
    Args:
        duration_str: 时间字符串，如 "30s", "5m", "1h", "1d"
        
    Returns:
        timedelta: 转换后的时间间隔对象，失败则返回None
    """
    match = re.fullmatch(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None
    
    value, unit = int(match.group(1)), match.group(2)
    
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    return None  # 按照正则表达式不应该进入这里，但作为良好实践保留