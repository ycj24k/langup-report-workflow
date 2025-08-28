# -*- coding: utf-8 -*-
"""
GUI界面模块
提供文件分类和打标签的用户界面
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import pandas as pd
from datetime import datetime
import json
import threading
from config import FILE_CATEGORIES, IMPORTANCE_LEVELS


class ResearchFileGUI:
    def __init__(self):
        self.root = ttk_bs.Window(themename="flatly")
        self.root.title("研报文件分类管理系统")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 600)
        
        # 数据存储
        self.files_data = []
        self.filtered_data = []
        self.current_file_index = -1
        self.unsaved_changes = False
        
        # 回调函数
        self.on_file_scan = None
        self.on_database_upload = None
        
        self.create_widgets()
        self.setup_layout()
        
    def create_widgets(self):
        """
        创建界面组件
        """
        # 主容器
        self.main_frame = ttk_bs.Frame(self.root, padding=10)
        
        # 顶部工具栏
        self.toolbar_frame = ttk_bs.Frame(self.main_frame)
        
        # 扫描按钮
        self.scan_btn = ttk_bs.Button(
            self.toolbar_frame,
            text="扫描文件",
            bootstyle="primary",
            command=self.scan_files
        )
        
        # 导入按钮
        self.import_btn = ttk_bs.Button(
            self.toolbar_frame,
            text="导入Excel",
            bootstyle="secondary",
            command=self.import_excel
        )
        
        # 导出按钮
        self.export_btn = ttk_bs.Button(
            self.toolbar_frame,
            text="导出Excel",
            bootstyle="secondary",
            command=self.export_excel
        )
        
        # 上传按钮
        self.upload_btn = ttk_bs.Button(
            self.toolbar_frame,
            text="上传到数据库",
            bootstyle="success",
            command=self.upload_to_database
        )
        
        # 进度条
        self.progress = ttk_bs.Progressbar(
            self.toolbar_frame,
            mode='indeterminate',
            bootstyle="primary"
        )
        
        # 状态标签
        self.status_label = ttk_bs.Label(
            self.toolbar_frame,
            text="就绪",
            bootstyle="info"
        )
        
        # 主内容区域
        self.content_frame = ttk_bs.Frame(self.main_frame)
        
        # 左侧文件列表
        self.left_frame = ttk_bs.LabelFrame(
            self.content_frame,
            text="文件列表",
            padding=10
        )
        
        # 搜索框
        self.search_frame = ttk_bs.Frame(self.left_frame)
        ttk_bs.Label(self.search_frame, text="搜索:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_files)
        self.search_entry = ttk_bs.Entry(
            self.search_frame,
            textvariable=self.search_var,
            width=30
        )
        self.search_entry.pack(side=LEFT, fill=X, expand=True)
        
        # 文件列表
        self.file_list_frame = ttk_bs.Frame(self.left_frame)
        
        # 创建Treeview
        columns = ("文件名", "大小(MB)", "修改时间", "分类", "重要性")
        self.file_tree = ttk.Treeview(
            self.file_list_frame,
            columns=columns,
            show="tree headings",
            height=20
        )
        
        # 设置列宽
        self.file_tree.column("#0", width=50, minwidth=50)
        self.file_tree.column("文件名", width=250, minwidth=200)
        self.file_tree.column("大小(MB)", width=80, minwidth=60)
        self.file_tree.column("修改时间", width=120, minwidth=100)
        self.file_tree.column("分类", width=100, minwidth=80)
        self.file_tree.column("重要性", width=60, minwidth=50)
        
        # 设置标题
        self.file_tree.heading("#0", text="序号")
        for col in columns:
            self.file_tree.heading(col, text=col)
        
        # 滚动条
        self.tree_scroll = ttk.Scrollbar(
            self.file_list_frame,
            orient=VERTICAL,
            command=self.file_tree.yview
        )
        self.file_tree.configure(yscrollcommand=self.tree_scroll.set)
        
        # 绑定选择事件
        self.file_tree.bind('<<TreeviewSelect>>', self.on_file_select)
        
        # 右侧详情区域
        self.right_frame = ttk_bs.LabelFrame(
            self.content_frame,
            text="文件详情",
            padding=10
        )
        
        # 文件信息区域
        self.info_frame = ttk_bs.LabelFrame(
            self.right_frame,
            text="基本信息",
            padding=10
        )
        
        # 文件信息标签
        self.info_labels = {}
        info_fields = [
            ("文件名", "file_name"),
            ("文件路径", "file_path"),
            ("文件大小", "file_size_mb"),
            ("扩展名", "extension"),
            ("创建时间", "creation_date"),
            ("修改时间", "modification_date"),
            ("访问时间", "access_date")
        ]
        
        for i, (label_text, field_name) in enumerate(info_fields):
            ttk_bs.Label(self.info_frame, text=f"{label_text}:").grid(
                row=i, column=0, sticky=W, padx=(0, 10), pady=2
            )
            self.info_labels[field_name] = ttk_bs.Label(
                self.info_frame,
                text="",
                wraplength=400
            )
            self.info_labels[field_name].grid(
                row=i, column=1, sticky=W, pady=2
            )
        
        # 分类和标签区域
        self.classify_frame = ttk_bs.LabelFrame(
            self.right_frame,
            text="分类和标签",
            padding=10
        )
        
        # 分类选择
        ttk_bs.Label(self.classify_frame, text="分类:").grid(
            row=0, column=0, sticky=W, padx=(0, 10), pady=5
        )
        self.category_var = tk.StringVar()
        self.category_combo = ttk_bs.Combobox(
            self.classify_frame,
            textvariable=self.category_var,
            values=FILE_CATEGORIES,
            state="readonly",
            width=20
        )
        self.category_combo.grid(row=0, column=1, sticky=W, pady=5)
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        
        # 重要性选择
        ttk_bs.Label(self.classify_frame, text="重要性:").grid(
            row=1, column=0, sticky=W, padx=(0, 10), pady=5
        )
        self.importance_var = tk.StringVar()
        self.importance_combo = ttk_bs.Combobox(
            self.classify_frame,
            textvariable=self.importance_var,
            values=IMPORTANCE_LEVELS,
            state="readonly",
            width=20
        )
        self.importance_combo.grid(row=1, column=1, sticky=W, pady=5)
        self.importance_combo.bind('<<ComboboxSelected>>', self.on_importance_change)
        
        # 标签输入
        ttk_bs.Label(self.classify_frame, text="标签:").grid(
            row=2, column=0, sticky=W+N, padx=(0, 10), pady=5
        )
        self.tags_var = tk.StringVar()
        self.tags_entry = ttk_bs.Entry(
            self.classify_frame,
            textvariable=self.tags_var,
            width=30
        )
        self.tags_entry.grid(row=2, column=1, sticky=W, pady=5)
        self.tags_entry.bind('<KeyRelease>', self.on_tags_change)
        
        # 备注输入
        ttk_bs.Label(self.classify_frame, text="备注:").grid(
            row=3, column=0, sticky=W+N, padx=(0, 10), pady=5
        )
        self.notes_text = tk.Text(
            self.classify_frame,
            width=40,
            height=4,
            wrap=tk.WORD
        )
        self.notes_text.grid(row=3, column=1, sticky=W, pady=5)
        self.notes_text.bind('<KeyRelease>', self.on_notes_change)
        
        # 操作按钮
        self.action_frame = ttk_bs.Frame(self.classify_frame)
        self.action_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.save_btn = ttk_bs.Button(
            self.action_frame,
            text="保存修改",
            bootstyle="success",
            command=self.save_current_file
        )
        self.save_btn.pack(side=LEFT, padx=(0, 10))
        
        self.next_btn = ttk_bs.Button(
            self.action_frame,
            text="下一个",
            bootstyle="primary",
            command=self.next_file
        )
        self.next_btn.pack(side=LEFT, padx=(0, 10))
        
        self.prev_btn = ttk_bs.Button(
            self.action_frame,
            text="上一个",
            bootstyle="secondary",
            command=self.prev_file
        )
        self.prev_btn.pack(side=LEFT)
        
        # 统计信息区域
        self.stats_frame = ttk_bs.LabelFrame(
            self.right_frame,
            text="统计信息",
            padding=10
        )
        
        self.stats_text = tk.Text(
            self.stats_frame,
            width=50,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        
        stats_scroll = ttk.Scrollbar(
            self.stats_frame,
            orient=VERTICAL,
            command=self.stats_text.yview
        )
        self.stats_text.configure(yscrollcommand=stats_scroll.set)
        
    def setup_layout(self):
        """
        设置界面布局
        """
        # 主框架
        self.main_frame.pack(fill=BOTH, expand=True)
        
        # 工具栏
        self.toolbar_frame.pack(fill=X, pady=(0, 10))
        
        self.scan_btn.pack(side=LEFT, padx=(0, 10))
        self.import_btn.pack(side=LEFT, padx=(0, 10))
        self.export_btn.pack(side=LEFT, padx=(0, 10))
        self.upload_btn.pack(side=LEFT, padx=(0, 10))
        
        self.progress.pack(side=RIGHT, padx=(10, 0))
        self.status_label.pack(side=RIGHT, padx=(10, 0))
        
        # 主内容区域
        self.content_frame.pack(fill=BOTH, expand=True)
        
        # 左侧文件列表
        self.left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        
        self.search_frame.pack(fill=X, pady=(0, 10))
        self.file_list_frame.pack(fill=BOTH, expand=True)
        
        self.file_tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.tree_scroll.pack(side=RIGHT, fill=Y)
        
        # 右侧详情区域
        self.right_frame.pack(side=RIGHT, fill=Y, width=500)
        
        self.info_frame.pack(fill=X, pady=(0, 10))
        self.classify_frame.pack(fill=X, pady=(0, 10))
        self.stats_frame.pack(fill=BOTH, expand=True)
        
        self.stats_text.pack(side=LEFT, fill=BOTH, expand=True)
        stats_scroll.pack(side=RIGHT, fill=Y)
        
    def set_callbacks(self, scan_callback=None, upload_callback=None):
        """
        设置回调函数
        """
        self.on_file_scan = scan_callback
        self.on_database_upload = upload_callback
        
    def scan_files(self):
        """
        扫描文件
        """
        if self.on_file_scan:
            self.progress.start()
            self.status_label.config(text="正在扫描文件...")
            
            # 在新线程中执行扫描
            def scan_thread():
                try:
                    files = self.on_file_scan()
                    self.root.after(0, self.on_scan_complete, files)
                except Exception as e:
                    self.root.after(0, self.on_scan_error, str(e))
            
            threading.Thread(target=scan_thread, daemon=True).start()
    
    def on_scan_complete(self, files):
        """
        扫描完成回调
        """
        self.progress.stop()
        self.files_data = files
        self.filtered_data = files.copy()
        self.refresh_file_list()
        self.update_statistics()
        self.status_label.config(text=f"扫描完成，共找到 {len(files)} 个文件")
    
    def on_scan_error(self, error_msg):
        """
        扫描错误回调
        """
        self.progress.stop()
        self.status_label.config(text="扫描失败")
        messagebox.showerror("错误", f"扫描文件时出错：{error_msg}")
    
    def import_excel(self):
        """
        从Excel导入文件数据
        """
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if file_path:
            try:
                df = pd.read_excel(file_path)
                self.files_data = df.to_dict('records')
                self.filtered_data = self.files_data.copy()
                self.refresh_file_list()
                self.update_statistics()
                self.status_label.config(text=f"导入成功，共 {len(self.files_data)} 个文件")
                messagebox.showinfo("成功", "Excel文件导入成功")
            except Exception as e:
                messagebox.showerror("错误", f"导入Excel文件失败：{e}")
    
    def export_excel(self):
        """
        导出到Excel
        """
        if not self.files_data:
            messagebox.showwarning("警告", "没有数据可导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存Excel文件",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if file_path:
            try:
                df = pd.DataFrame(self.files_data)
                df.to_excel(file_path, index=False)
                self.status_label.config(text="导出成功")
                messagebox.showinfo("成功", f"数据已导出到：{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出Excel文件失败：{e}")
    
    def upload_to_database(self):
        """
        上传到数据库
        """
        if not self.files_data:
            messagebox.showwarning("警告", "没有数据可上传")
            return
        
        if self.on_database_upload:
            result = messagebox.askyesno(
                "确认",
                f"确定要将 {len(self.files_data)} 个文件上传到数据库吗？"
            )
            
            if result:
                self.progress.start()
                self.status_label.config(text="正在上传到数据库...")
                
                # 在新线程中执行上传
                def upload_thread():
                    try:
                        success = self.on_database_upload(self.files_data)
                        self.root.after(0, self.on_upload_complete, success)
                    except Exception as e:
                        self.root.after(0, self.on_upload_error, str(e))
                
                threading.Thread(target=upload_thread, daemon=True).start()
    
    def on_upload_complete(self, success):
        """
        上传完成回调
        """
        self.progress.stop()
        if success:
            self.status_label.config(text="上传成功")
            messagebox.showinfo("成功", "数据已成功上传到数据库")
        else:
            self.status_label.config(text="上传失败")
            messagebox.showerror("错误", "数据上传失败")
    
    def on_upload_error(self, error_msg):
        """
        上传错误回调
        """
        self.progress.stop()
        self.status_label.config(text="上传失败")
        messagebox.showerror("错误", f"上传数据时出错：{error_msg}")
    
    def refresh_file_list(self):
        """
        刷新文件列表
        """
        # 清空现有项目
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # 添加新项目
        for i, file_data in enumerate(self.filtered_data):
            file_name = file_data.get('file_name', '')
            file_size = file_data.get('file_size_mb', 0)
            mod_date = file_data.get('modification_date', '')
            if isinstance(mod_date, datetime):
                mod_date = mod_date.strftime('%Y-%m-%d')
            category = file_data.get('category', '')
            importance = file_data.get('importance', '')
            
            self.file_tree.insert(
                '',
                'end',
                text=str(i + 1),
                values=(file_name, file_size, mod_date, category, importance)
            )
    
    def filter_files(self, *args):
        """
        根据搜索条件过滤文件
        """
        keyword = self.search_var.get().lower()
        
        if not keyword:
            self.filtered_data = self.files_data.copy()
        else:
            self.filtered_data = []
            for file_data in self.files_data:
                file_name = file_data.get('file_name', '').lower()
                category = file_data.get('category', '').lower()
                tags = file_data.get('tags', '').lower()
                notes = file_data.get('notes', '').lower()
                
                if (keyword in file_name or keyword in category or 
                    keyword in tags or keyword in notes):
                    self.filtered_data.append(file_data)
        
        self.refresh_file_list()
    
    def on_file_select(self, event):
        """
        文件选择事件
        """
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            index = int(item['text']) - 1
            
            # 在原始数据中找到对应文件
            if 0 <= index < len(self.filtered_data):
                self.current_file_index = self.files_data.index(self.filtered_data[index])
                self.load_file_details()
    
    def load_file_details(self):
        """
        加载文件详情
        """
        if 0 <= self.current_file_index < len(self.files_data):
            file_data = self.files_data[self.current_file_index]
            
            # 更新基本信息
            for field_name, label in self.info_labels.items():
                value = file_data.get(field_name, '')
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif field_name == 'file_size_mb':
                    value = f"{value} MB"
                label.config(text=str(value))
            
            # 更新分类信息
            self.category_var.set(file_data.get('category', ''))
            self.importance_var.set(file_data.get('importance', ''))
            self.tags_var.set(file_data.get('tags', ''))
            
            # 更新备注
            self.notes_text.delete(1.0, tk.END)
            self.notes_text.insert(1.0, file_data.get('notes', ''))
    
    def on_category_change(self, event):
        """
        分类改变事件
        """
        if 0 <= self.current_file_index < len(self.files_data):
            self.files_data[self.current_file_index]['category'] = self.category_var.get()
            self.unsaved_changes = True
            self.refresh_file_list()
    
    def on_importance_change(self, event):
        """
        重要性改变事件
        """
        if 0 <= self.current_file_index < len(self.files_data):
            self.files_data[self.current_file_index]['importance'] = self.importance_var.get()
            self.unsaved_changes = True
            self.refresh_file_list()
    
    def on_tags_change(self, event):
        """
        标签改变事件
        """
        if 0 <= self.current_file_index < len(self.files_data):
            self.files_data[self.current_file_index]['tags'] = self.tags_var.get()
            self.unsaved_changes = True
    
    def on_notes_change(self, event):
        """
        备注改变事件
        """
        if 0 <= self.current_file_index < len(self.files_data):
            notes = self.notes_text.get(1.0, tk.END).strip()
            self.files_data[self.current_file_index]['notes'] = notes
            self.unsaved_changes = True
    
    def save_current_file(self):
        """
        保存当前文件的修改
        """
        if self.unsaved_changes:
            self.unsaved_changes = False
            self.status_label.config(text="修改已保存")
            messagebox.showinfo("成功", "文件信息已保存")
    
    def next_file(self):
        """
        下一个文件
        """
        if self.current_file_index < len(self.files_data) - 1:
            self.current_file_index += 1
            self.load_file_details()
            self.select_current_file_in_tree()
    
    def prev_file(self):
        """
        上一个文件
        """
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self.load_file_details()
            self.select_current_file_in_tree()
    
    def select_current_file_in_tree(self):
        """
        在树形控件中选择当前文件
        """
        if 0 <= self.current_file_index < len(self.files_data):
            current_file = self.files_data[self.current_file_index]
            
            # 在过滤后的数据中找到对应项
            for i, filtered_file in enumerate(self.filtered_data):
                if filtered_file == current_file:
                    items = self.file_tree.get_children()
                    if i < len(items):
                        self.file_tree.selection_set(items[i])
                        self.file_tree.see(items[i])
                    break
    
    def update_statistics(self):
        """
        更新统计信息
        """
        if not self.files_data:
            return
        
        # 计算统计信息
        total_files = len(self.files_data)
        total_size = sum(file.get('file_size_mb', 0) for file in self.files_data)
        
        # 分类统计
        category_stats = {}
        importance_stats = {}
        extension_stats = {}
        
        for file_data in self.files_data:
            category = file_data.get('category', '未分类')
            importance = file_data.get('importance', '未标记')
            extension = file_data.get('extension', '未知')
            
            category_stats[category] = category_stats.get(category, 0) + 1
            importance_stats[importance] = importance_stats.get(importance, 0) + 1
            extension_stats[extension] = extension_stats.get(extension, 0) + 1
        
        # 显示统计信息
        stats_text = f"总文件数: {total_files}\n"
        stats_text += f"总大小: {total_size:.2f} MB\n\n"
        
        stats_text += "按分类统计:\n"
        for category, count in sorted(category_stats.items()):
            stats_text += f"  {category}: {count}\n"
        
        stats_text += "\n按重要性统计:\n"
        for importance, count in sorted(importance_stats.items()):
            stats_text += f"  {importance}: {count}\n"
        
        stats_text += "\n按文件类型统计:\n"
        for ext, count in sorted(extension_stats.items()):
            stats_text += f"  {ext}: {count}\n"
        
        # 更新统计信息显示
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
        self.stats_text.config(state=tk.DISABLED)
    
    def run(self):
        """
        运行GUI
        """
        self.root.mainloop()


if __name__ == "__main__":
    # 测试GUI
    app = ResearchFileGUI()
    app.run()