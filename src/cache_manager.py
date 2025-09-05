# -*- coding: utf-8 -*-
"""
缓存管理模块
负责文件缓存、版本控制和增量更新
"""
import os
import json
import hashlib
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional
from config import NETWORK_PATH


class FileCache:
    def __init__(self, cache_file="file_cache.pkl"):
        # 确保缓存文件保存在data目录中
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        self.cache_file = data_dir / cache_file
        self.cache_data = {
            'files': {},  # 文件路径 -> 文件信息
            'last_scan': None,  # 最后扫描时间
            'version': '1.0'  # 缓存版本
        }
        self.load_cache()
    
    def load_cache(self):
        """加载缓存数据"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    self.cache_data = pickle.load(f)
                print(f"缓存加载成功，共 {len(self.cache_data['files'])} 个文件记录")
            else:
                print("缓存文件不存在，将创建新缓存")
        except Exception as e:
            print(f"加载缓存失败: {e}，将创建新缓存")
            self.cache_data = {
                'files': {},
                'last_scan': None,
                'version': '1.0'
            }
    
    def save_cache(self):
        """保存缓存数据"""
        try:
            self.cache_data['last_scan'] = datetime.now()
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache_data, f)
            print(f"缓存保存成功，共 {len(self.cache_data['files'])} 个文件记录")
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def get_file_hash(self, file_path: str) -> str:
        """获取文件的哈希值（基于修改时间和大小）"""
        try:
            stat = os.stat(file_path)
            # 使用修改时间、大小和路径生成哈希
            hash_data = f"{stat.st_mtime}_{stat.st_size}_{file_path}"
            return hashlib.md5(hash_data.encode()).hexdigest()
        except Exception:
            return ""
    
    def is_file_changed(self, file_path: str) -> bool:
        """检查文件是否发生变化"""
        current_hash = self.get_file_hash(file_path)
        cached_hash = self.cache_data['files'].get(file_path, {}).get('hash', '')
        return current_hash != cached_hash
    
    def update_file_cache(self, file_path: str, file_info: dict):
        """更新文件缓存"""
        file_info['hash'] = self.get_file_hash(file_path)
        file_info['cached_at'] = datetime.now()
        # 持久化必要字段，避免不可序列化对象
        safe_info = dict(file_info)
        # 确保日期为 datetime，可被pickle序列化
        for key in ('creation_date', 'modification_date', 'access_date'):
            v = safe_info.get(key)
            safe_info[key] = v
        self.cache_data['files'][file_path] = safe_info
    
    def remove_file_cache(self, file_path: str):
        """移除文件缓存"""
        if file_path in self.cache_data['files']:
            del self.cache_data['files'][file_path]
    
    def get_cached_files(self) -> Dict[str, dict]:
        """获取所有缓存的文件"""
        return self.cache_data['files']
    
    def clear_cache(self):
        """清空缓存"""
        self.cache_data['files'] = {}
        self.cache_data['last_scan'] = None
        self.save_cache()
        print("缓存已清空")


class DatabaseVersionManager:
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.version_table_name = "file_versions"
        self.create_version_table()
    
    def create_version_table(self):
        """创建版本控制表"""
        try:
            from sqlalchemy import text
            create_version_table = f"""
            CREATE TABLE IF NOT EXISTS {self.version_table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_path VARCHAR(500) NOT NULL UNIQUE,
                file_hash VARCHAR(32) NOT NULL,
                file_size_mb DECIMAL(10,2),
                modification_date DATETIME,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status ENUM('new', 'updated', 'unchanged') DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_file_path (file_path(191)),
                INDEX idx_file_hash (file_hash),
                INDEX idx_status (status),
                INDEX idx_modification_date (modification_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件版本控制表'
            """
            
            if self.db_manager.connection:
                self.db_manager.connection.execute(text(create_version_table))
                self.db_manager.connection.commit()
                print("版本控制表创建成功")
        except Exception as e:
            print(f"创建版本控制表失败: {e}")
    
    def get_file_version(self, file_path: str) -> Optional[dict]:
        """获取文件在数据库中的版本信息"""
        try:
            from sqlalchemy import text
            if not self.db_manager.connection:
                return None
            
            sql = f"SELECT * FROM {self.version_table_name} WHERE file_path = :file_path"
            result = self.db_manager.connection.execute(text(sql), {'file_path': file_path})
            row = result.fetchone()
            
            if row:
                return dict(row._mapping)
            return None
        except Exception as e:
            print(f"获取文件版本失败: {e}")
            return None
    
    def update_file_version(self, file_path: str, file_hash: str, file_size: float, mod_date: datetime, status: str = 'updated'):
        """更新文件版本信息"""
        try:
            from sqlalchemy import text
            if not self.db_manager.connection:
                return False
            
            sql = f"""
            INSERT INTO {self.version_table_name} 
            (file_path, file_hash, file_size_mb, modification_date, status) 
            VALUES (:file_path, :file_hash, :file_size_mb, :modification_date, :status)
            ON DUPLICATE KEY UPDATE 
            file_hash = VALUES(file_hash),
            file_size_mb = VALUES(file_size_mb),
            modification_date = VALUES(modification_date),
            status = VALUES(status),
            updated_at = CURRENT_TIMESTAMP
            """
            
            self.db_manager.connection.execute(text(sql), {
                'file_path': file_path,
                'file_hash': file_hash,
                'file_size_mb': file_size,
                'modification_date': mod_date,
                'status': status
            })
            self.db_manager.connection.commit()
            return True
        except Exception as e:
            print(f"更新文件版本失败: {e}")
            return False
    
    def get_files_by_status(self, status: str) -> List[dict]:
        """根据状态获取文件列表"""
        try:
            from sqlalchemy import text
            if not self.db_manager.connection:
                return []
            
            sql = f"SELECT * FROM {self.version_table_name} WHERE status = :status"
            result = self.db_manager.connection.execute(text(sql), {'status': status})
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            print(f"获取文件状态列表失败: {e}")
            return []
    
    def mark_files_processed(self, file_paths: List[str]):
        """标记文件为已处理"""
        try:
            from sqlalchemy import text
            if not self.db_manager.connection or not file_paths:
                return
            
            placeholders = ','.join([':path' + str(i) for i in range(len(file_paths))])
            sql = f"UPDATE {self.version_table_name} SET status = 'unchanged' WHERE file_path IN ({placeholders})"
            
            params = {f'path{i}': path for i, path in enumerate(file_paths)}
            self.db_manager.connection.execute(text(sql), params)
            self.db_manager.connection.commit()
        except Exception as e:
            print(f"标记文件已处理失败: {e}")


class IncrementalScanner:
    def __init__(self, cache_manager: FileCache, version_manager: DatabaseVersionManager):
        self.cache_manager = cache_manager
        self.version_manager = version_manager
        self.current_year = datetime.now().year
    
    def scan_incremental(self, path: str = None) -> dict:
        """增量扫描文件"""
        if path is None:
            path = NETWORK_PATH
        
        print(f"开始增量扫描路径: {path}")
        
        # 获取当前文件列表
        current_files = self._get_current_files(path)
        cached_files = self.cache_manager.get_cached_files()
        
        # 分析文件变化
        new_files = []
        updated_files = []
        unchanged_files = []
        deleted_files = []
        
        # 检查新增和更新的文件
        for file_path in current_files:
            if file_path not in cached_files:
                # 新文件
                file_info = self._get_file_info(file_path)
                if self._is_current_year_file(file_info):
                    new_files.append(file_info)
                    self.cache_manager.update_file_cache(file_path, file_info)
            elif self.cache_manager.is_file_changed(file_path):
                # 文件已更新
                file_info = self._get_file_info(file_path)
                if self._is_current_year_file(file_info):
                    updated_files.append(file_info)
                    self.cache_manager.update_file_cache(file_path, file_info)
            else:
                # 文件未变化
                file_info = cached_files[file_path]
                if self._is_current_year_file(file_info):
                    unchanged_files.append(file_info)
        
        # 检查删除的文件
        for file_path in cached_files:
            if file_path not in current_files:
                deleted_files.append(file_path)
                self.cache_manager.remove_file_cache(file_path)
        
        # 更新数据库版本信息
        self._update_database_versions(new_files, updated_files)
        
        # 保存缓存
        self.cache_manager.save_cache()
        
        # 返回扫描结果
        result = {
            'new_files': new_files,
            'updated_files': updated_files,
            'unchanged_files': unchanged_files,
            'deleted_files': deleted_files,
            'total_files': len(new_files) + len(updated_files) + len(unchanged_files),
            'scan_time': datetime.now()
        }
        
        print(f"增量扫描完成:")
        print(f"  新增文件: {len(new_files)}")
        print(f"  更新文件: {len(updated_files)}")
        print(f"  未变化文件: {len(unchanged_files)}")
        print(f"  删除文件: {len(deleted_files)}")
        print(f"  总计: {result['total_files']} 个文件")
        
        return result
    
    def _get_current_files(self, path: str) -> Set[str]:
        """获取当前文件列表"""
        current_files = set()
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    current_files.add(file_path)
        except Exception as e:
            print(f"获取文件列表失败: {e}")
        return current_files
    
    def _get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        try:
            stat = os.stat(file_path)
            creation_time = datetime.fromtimestamp(stat.st_ctime)
            modification_time = datetime.fromtimestamp(stat.st_mtime)
            access_time = datetime.fromtimestamp(stat.st_atime)
            file_size = round(stat.st_size / (1024 * 1024), 2)
            
            return {
                'file_name': os.path.basename(file_path),
                'file_path': file_path,
                'file_size_mb': file_size,
                'creation_date': creation_time,
                'modification_date': modification_time,
                'access_date': access_time,
                'extension': os.path.splitext(file_path)[1].lower(),
                'category': '',
                'importance': '',
                'tags': '',
                'notes': '',
                'status': 'new'  # 新增状态字段
            }
        except Exception as e:
            print(f"获取文件信息失败 {file_path}: {e}")
            return {}
    
    def _is_current_year_file(self, file_info: dict) -> bool:
        """检查文件是否在今年内"""
        dates_to_check = [
            file_info.get('creation_date'),
            file_info.get('modification_date'),
            file_info.get('access_date')
        ]
        
        for date_obj in dates_to_check:
            if date_obj and date_obj.year == self.current_year:
                return True
        return False
    
    def _update_database_versions(self, new_files: List[dict], updated_files: List[dict]):
        """更新数据库版本信息"""
        for file_info in new_files:
            self.version_manager.update_file_version(
                file_info['file_path'],
                self.cache_manager.get_file_hash(file_info['file_path']),
                file_info['file_size_mb'],
                file_info['modification_date'],
                'new'
            )
        
        for file_info in updated_files:
            self.version_manager.update_file_version(
                file_info['file_path'],
                self.cache_manager.get_file_hash(file_info['file_path']),
                file_info['file_size_mb'],
                file_info['modification_date'],
                'updated'
            )
    
    def get_files_by_status(self, status: str) -> List[dict]:
        """根据状态获取文件"""
        if status == 'all':
            # 返回所有文件
            all_files = []
            cached_files = self.cache_manager.get_cached_files()
            for file_info in cached_files.values():
                if self._is_current_year_file(file_info):
                    all_files.append(file_info)
            return all_files
        elif status in ['new', 'updated', 'unchanged']:
            # 从数据库获取指定状态的文件
            db_files = self.version_manager.get_files_by_status(status)
            result = []
            for db_file in db_files:
                cached_file = self.cache_manager.get_cached_files().get(db_file['file_path'])
                if cached_file and self._is_current_year_file(cached_file):
                    cached_file['status'] = db_file['status']
                    result.append(cached_file)
            return result
        else:
            return []
