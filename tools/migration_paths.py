"""SRC-04: extracted digest/path collision helpers; no archive writer."""
from __future__ import annotations
import hashlib
import unicodedata

class TransferError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise TransferError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    require(isinstance(name, str) and name and '\\' not in name, '文件路径不合法')
    require(len(name.encode('utf-8')) <= 1024, '文件路径过长')
    parts = name.split('/')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
                *(f'LPT{i}' for i in range(1, 10))}
    for part in parts:
        require(len(part.encode('utf-8')) <= 255, '文件路径段过长')
        require(part not in ('', '.', '..') and not part.endswith((' ', '.')),
                '路径包含空段、父目录或Windows歧义名称')
        require(not any(ord(c) < 32 or c in '<>:"|?*' for c in part), '路径包含不安全字符')
        require(part.split('.')[0].upper() not in reserved, '路径包含设备名称')
    return '/'.join(parts)


def path_key(name):
    return unicodedata.normalize('NFKC', safe_name(name)).casefold()


def check_tree(names):
    keys = [path_key(n) for n in names]
    require(len(set(keys)) == len(keys), '路径重复或大小写/Unicode碰撞')
    all_keys = set(keys)
    for key in keys:
        parts = key.split('/')
        require(not any('/'.join(parts[:i]) in all_keys for i in range(1, len(parts))),
                '文件与目录路径冲突')
