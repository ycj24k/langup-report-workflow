# -*- coding: utf-8 -*-
"""
数据库管理模块
负责数据库连接、表创建和数据操作
"""
import pymysql
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
from config import DATABASE_CONFIG, BATCH_SIZE


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.connection = None
        self.database_name = DATABASE_CONFIG['database']
        
    def connect(self):
        """
        连接到MySQL数据库
        """
        try:
            # 首先连接到MySQL服务器（不指定数据库）
            connection_string = (
                f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
                f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}"
                f"?charset={DATABASE_CONFIG['charset']}"
            )
            
            temp_engine = create_engine(connection_string)
            
            # 创建数据库（如果不存在）
            with temp_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {self.database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                conn.commit()
            
            # 连接到指定数据库
            connection_string_with_db = (
                f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
                f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}"
                f"/{self.database_name}?charset={DATABASE_CONFIG['charset']}"
            )
            
            self.engine = create_engine(connection_string_with_db)
            self.connection = self.engine.connect()
            
            print(f"成功连接到数据库: {self.database_name}")
            return True
            
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def create_tables(self):
        """
        创建数据库表
        """
        try:
            # 研报文件信息表
            create_files_table = """
            CREATE TABLE IF NOT EXISTS research_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_name VARCHAR(500) NOT NULL COMMENT '文件名',
                file_path TEXT NOT NULL COMMENT '文件完整路径',
                file_size_mb DECIMAL(10,2) COMMENT '文件大小(MB)',
                extension VARCHAR(10) COMMENT '文件扩展名',
                creation_date DATETIME COMMENT '创建日期',
                modification_date DATETIME COMMENT '修改日期',
                access_date DATETIME COMMENT '访问日期',
                category VARCHAR(50) COMMENT '文件分类',
                importance VARCHAR(10) COMMENT '重要性级别',
                tags TEXT COMMENT '标签(JSON格式)',
                notes TEXT COMMENT '备注',
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
                is_processed BOOLEAN DEFAULT FALSE COMMENT '是否已处理',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_file_name (file_name),
                INDEX idx_category (category),
                INDEX idx_importance (importance),
                INDEX idx_modification_date (modification_date),
                INDEX idx_upload_date (upload_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='研报文件信息表'
            """
            
            # 批次上传记录表
            create_batch_table = """
            CREATE TABLE IF NOT EXISTS upload_batches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                batch_name VARCHAR(100) NOT NULL COMMENT '批次名称',
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
                file_count INT DEFAULT 0 COMMENT '文件数量',
                total_size_mb DECIMAL(10,2) COMMENT '总大小(MB)',
                status VARCHAR(20) DEFAULT 'completed' COMMENT '状态',
                notes TEXT COMMENT '备注',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_batch_name (batch_name),
                INDEX idx_upload_date (upload_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='批次上传记录表'
            """
            
            # 文件分类标签表
            create_categories_table = """
            CREATE TABLE IF NOT EXISTS file_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category_name VARCHAR(50) NOT NULL UNIQUE COMMENT '分类名称',
                description TEXT COMMENT '分类描述',
                color VARCHAR(7) COMMENT '分类颜色(十六进制)',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_category_name (category_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件分类表'
            """
            
            with self.connection.begin() as trans:
                self.connection.execute(text(create_files_table))
                self.connection.execute(text(create_batch_table))
                self.connection.execute(text(create_categories_table))
                trans.commit()
            
            print("数据库表创建成功")
            
            # 初始化分类数据
            self._init_categories()
            
            return True
            
        except Exception as e:
            print(f"创建数据库表失败: {e}")
            return False
    
    def _init_categories(self):
        """
        初始化文件分类数据
        """
        categories = [
            ('宏观经济', '宏观经济分析研报', '#FF6B6B'),
            ('行业研究', '行业分析研报', '#4ECDC4'),
            ('公司研究', '公司分析研报', '#45B7D1'),
            ('投资策略', '投资策略研报', '#96CEB4'),
            ('固定收益', '固定收益研报', '#FFEAA7'),
            ('量化研究', '量化分析研报', '#DDA0DD'),
            ('其他', '其他类型研报', '#95A5A6')
        ]
        
        try:
            for category, description, color in categories:
                insert_sql = """
                INSERT IGNORE INTO file_categories (category_name, description, color) 
                VALUES (:category, :description, :color)
                """
                self.connection.execute(text(insert_sql), {
                    'category': category,
                    'description': description,
                    'color': color
                })
            self.connection.commit()
            print("分类数据初始化完成")
        except Exception as e:
            print(f"初始化分类数据失败: {e}")
    
    def upload_files_batch(self, files_data, batch_name=None):
        """
        批量上传文件数据
        """
        if not files_data:
            print("没有文件数据需要上传")
            return False
        
        try:
            if batch_name is None:
                batch_name = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 计算批次统计信息
            file_count = len(files_data)
            total_size = sum(file.get('file_size_mb', 0) for file in files_data)
            
            # 记录批次信息
            batch_sql = """
            INSERT INTO upload_batches (batch_name, file_count, total_size_mb) 
            VALUES (:batch_name, :file_count, :total_size_mb)
            """
            result = self.connection.execute(text(batch_sql), {
                'batch_name': batch_name,
                'file_count': file_count,
                'total_size_mb': total_size
            })
            batch_id = result.lastrowid
            
            # 分批处理文件数据
            success_count = 0
            error_count = 0
            
            for i in range(0, len(files_data), BATCH_SIZE):
                batch_files = files_data[i:i+BATCH_SIZE]
                
                try:
                    # 准备数据
                    insert_data = []
                    for file_data in batch_files:
                        insert_data.append({
                            'file_name': file_data.get('file_name', ''),
                            'file_path': file_data.get('file_path', ''),
                            'file_size_mb': file_data.get('file_size_mb', 0),
                            'extension': file_data.get('extension', ''),
                            'creation_date': file_data.get('creation_date'),
                            'modification_date': file_data.get('modification_date'),
                            'access_date': file_data.get('access_date'),
                            'category': file_data.get('category', ''),
                            'importance': file_data.get('importance', ''),
                            'tags': file_data.get('tags', ''),
                            'notes': file_data.get('notes', '')
                        })
                    
                    # 批量插入
                    insert_sql = """
                    INSERT INTO research_files 
                    (file_name, file_path, file_size_mb, extension, creation_date, 
                     modification_date, access_date, category, importance, tags, notes)
                    VALUES 
                    (:file_name, :file_path, :file_size_mb, :extension, :creation_date,
                     :modification_date, :access_date, :category, :importance, :tags, :notes)
                    """
                    
                    self.connection.execute(text(insert_sql), insert_data)
                    success_count += len(batch_files)
                    
                    print(f"已上传 {success_count}/{file_count} 个文件", end='\r')
                    
                except Exception as e:
                    error_count += len(batch_files)
                    print(f"批次上传出错: {e}")
            
            self.connection.commit()
            print(f"\n批次上传完成: {batch_name}")
            print(f"成功: {success_count} 个文件, 失败: {error_count} 个文件")
            
            return True
            
        except Exception as e:
            print(f"批量上传失败: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_file_statistics(self):
        """
        获取文件统计信息
        """
        try:
            stats = {}
            
            # 总文件数
            result = self.connection.execute(text("SELECT COUNT(*) as total FROM research_files"))
            stats['total_files'] = result.fetchone()[0]
            
            # 按分类统计
            result = self.connection.execute(text("""
                SELECT category, COUNT(*) as count 
                FROM research_files 
                WHERE category != '' 
                GROUP BY category
            """))
            stats['category_stats'] = dict(result.fetchall())
            
            # 按重要性统计
            result = self.connection.execute(text("""
                SELECT importance, COUNT(*) as count 
                FROM research_files 
                WHERE importance != '' 
                GROUP BY importance
            """))
            stats['importance_stats'] = dict(result.fetchall())
            
            # 按月份统计
            result = self.connection.execute(text("""
                SELECT DATE_FORMAT(modification_date, '%Y-%m') as month, COUNT(*) as count
                FROM research_files 
                GROUP BY month 
                ORDER BY month DESC 
                LIMIT 12
            """))
            stats['month_stats'] = dict(result.fetchall())
            
            return stats
            
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}
    
    def search_files(self, keyword=None, category=None, importance=None, date_from=None, date_to=None):
        """
        搜索文件
        """
        try:
            sql = "SELECT * FROM research_files WHERE 1=1"
            params = {}
            
            if keyword:
                sql += " AND (file_name LIKE :keyword OR notes LIKE :keyword)"
                params['keyword'] = f'%{keyword}%'
            
            if category:
                sql += " AND category = :category"
                params['category'] = category
            
            if importance:
                sql += " AND importance = :importance"
                params['importance'] = importance
            
            if date_from:
                sql += " AND modification_date >= :date_from"
                params['date_from'] = date_from
            
            if date_to:
                sql += " AND modification_date <= :date_to"
                params['date_to'] = date_to
            
            sql += " ORDER BY modification_date DESC"
            
            result = self.connection.execute(text(sql), params)
            return result.fetchall()
            
        except Exception as e:
            print(f"搜索文件失败: {e}")
            return []
    
    def close(self):
        """
        关闭数据库连接
        """
        if self.connection:
            self.connection.close()
        if self.engine:
            self.engine.dispose()
        print("数据库连接已关闭")


# 测试函数
def test_database():
    """
    测试数据库功能
    """
    db = DatabaseManager()
    
    if db.connect():
        if db.create_tables():
            print("数据库初始化成功")
            
            # 获取统计信息
            stats = db.get_file_statistics()
            print(f"当前数据库中共有 {stats.get('total_files', 0)} 个文件")
            
        db.close()
    else:
        print("数据库测试失败")


if __name__ == "__main__":
    test_database()