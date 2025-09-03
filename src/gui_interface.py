# -*- coding: utf-8 -*-
"""
GUI界面模块
提供文件分类和打标签的用户界面
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.constants import *
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import pandas as pd
from datetime import datetime
import json
import threading
from config import FILE_CATEGORIES, IMPORTANCE_LEVELS, PRESET_TAGS


class ResearchFileGUI:
    def __init__(self):
        self.root = ttk_bs.Window(themename="flatly")
        self.root.title("研报文件分类管理系统")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 600)
        
        # 样式优化：Ant-Design风格（表头、选中、斑马纹、扁平化）
        self.style = ttk.Style()
        try:
            # 行样式（大幅增加行高和边框）
            self.style.configure(
                'Ant.Treeview',
                background='#FFFFFF',
                fieldbackground='#FFFFFF',
                foreground='#1f2329',
                rowheight=50,  # 进一步增加行高
                borderwidth=1,
                relief='solid',  # 显示边框
                font=('微软雅黑', 11)
            )
            self.style.map(
                'Ant.Treeview',
                background=[('selected', '#E6F4FF')],
                foreground=[('selected', '#1D39C4')]
            )
            # 表头样式（增加边框）
            self.style.configure(
                'Ant.Treeview.Heading',
                background='#FAFAFA',
                foreground='#1f2329',
                anchor='center',
                padding=(8, 10),
                borderwidth=1,
                relief='solid',  # 表头也显示边框
                font=('微软雅黑', 11, 'bold')
            )
            self.style.map(
                'Ant.Treeview.Heading',
                background=[('active', '#F0F0F0')]
            )
        except Exception:
            pass
        
        # 数据存储
        self.files_data = []
        self.filtered_data = []
        self.current_file_index = -1
        self.unsaved_changes = False
        # 选择集（按 file_path 记录）
        self.selected_paths = set()
        
        # 分页相关
        self.current_page = 1
        self.page_size = 100  # 每页显示100条数据
        self.total_pages = 1
        
        # 回调函数
        self.on_file_scan = None
        self.on_database_upload = None
        self.on_parse_files = None
        
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
        
        
        
        # 导出按钮
        self.export_btn = ttk_bs.Button(
            self.toolbar_frame,
            text="导出Excel",
            bootstyle="secondary",
            command=self.export_excel
        )
        
        # 上传按钮（上传已选择项）
        self.upload_btn = ttk_bs.Button(
            self.toolbar_frame,
            text="上传到数据库(已选)",
            bootstyle="success",
            command=self.upload_selected_to_database
        )
        
        # 解析按钮（解析已选择项，OCR并自动分类打标签）
        self.parse_btn = ttk_bs.Button(
            self.toolbar_frame,
            text="解析(已选)",
            bootstyle="warning",
            command=self.parse_selected_files
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
        
        # 搜索和筛选框架（使用flex布局）
        self.search_frame = ttk_bs.Frame(self.left_frame)
        
        # 创建flex容器
        flex_container = ttk_bs.Frame(self.search_frame)
        flex_container.pack(fill=X, pady=(0, 5))
        
        # 关键词搜索
        keyword_frame = ttk_bs.Frame(flex_container)
        keyword_frame.pack(side=LEFT, padx=(0, 10), pady=2)
        ttk_bs.Label(keyword_frame, text="关键词:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk_bs.Entry(
            keyword_frame,
            textvariable=self.search_var,
            width=15
        )
        self.search_entry.pack(side=LEFT)
        
        # 状态筛选
        status_frame = ttk_bs.Frame(flex_container)
        status_frame.pack(side=LEFT, padx=(0, 10), pady=2)
        ttk_bs.Label(status_frame, text="状态:").pack(side=LEFT, padx=(0, 5))
        self.status_var = tk.StringVar(value="全部")
        self.status_combo = ttk_bs.Combobox(
            status_frame,
            textvariable=self.status_var,
            values=["全部", "新增", "更新", "未变化"],
            state="readonly",
            width=8
        )
        self.status_combo.pack(side=LEFT)
        self.status_combo.bind('<<ComboboxSelected>>', self.on_status_filter_change)
        
        # 搜索按钮
        self.search_btn = ttk_bs.Button(
            flex_container,
            text="搜索",
            bootstyle="primary",
            command=lambda: self.apply_filters(reset_page=True)
        )
        self.search_btn.pack(side=LEFT, padx=(0, 5), pady=2)
        
        # 重置按钮
        self.clear_btn = ttk_bs.Button(
            flex_container,
            text="重置",
            bootstyle="secondary",
            command=self.clear_filters
        )
        self.clear_btn.pack(side=LEFT, padx=(0, 5), pady=2)
        
        # 清空缓存按钮
        self.clear_cache_btn = ttk_bs.Button(
            flex_container,
            text="清空缓存",
            bootstyle="danger",
            command=self.clear_cache
        )
        self.clear_cache_btn.pack(side=LEFT, padx=(0, 5), pady=2)
        
        # 文件列表
        self.file_list_frame = ttk_bs.Frame(self.left_frame)
        
        # 创建Treeview（选择列在最左边，序号在第二列）
        columns = ("选择", "序号", "文件名", "大小(MB)", "创建时间", "修改时间", "访问时间", "状态", "分类", "重要性")
        self.file_tree = ttk.Treeview(
            self.file_list_frame,
            columns=columns,
            show="headings",  # 不显示树形列，所有列都是数据列
            height=20
        )
        
        # 直接设置样式 - 使用原生tkinter样式
        style = ttk.Style()
        
        # 自定义样式，避免与全局样式冲突并修复表头重复边框
        style.configure("Langup.Treeview",
                       rowheight=60,
                       font=('微软雅黑', 11),
                       borderwidth=1,
                       relief='solid',
                       background='white',
                       foreground='black')
        
        # 表头使用同名前缀样式，去掉重复边框，只保留背景与内边距
        style.configure("Langup.Treeview.Heading",
                       font=('微软雅黑', 11, 'bold'),
                       borderwidth=0,
                       relief='flat',
                       padding=(8, 10),
                       background='#f0f0f0',
                       foreground='black')
        
        # 选中样式
        style.map("Langup.Treeview",
                 background=[('selected', '#1890FF')],
                 foreground=[('selected', 'white')])
        
        # 应用自定义样式到当前Treeview
        self.file_tree.configure(style="Langup.Treeview")
        
        # 斑马纹与悬浮高亮
        self.file_tree.tag_configure('odd', background='#FFFFFF')
        self.file_tree.tag_configure('even', background='#FAFAFA')
        self.file_tree.tag_configure('hover', background='#E6F7FF')
        self.file_tree.tag_configure('selected', background='#1890FF', foreground='white')
        
        # 设置列宽与居中（选择列更宽以显示更大的复选框图标）
        self.file_tree.column("选择", width=60, minwidth=50, anchor=CENTER)
        self.file_tree.column("序号", width=60, minwidth=50, anchor=CENTER)
        self.file_tree.column("文件名", width=200, minwidth=140, anchor=CENTER)
        self.file_tree.column("大小(MB)", width=90, minwidth=70, anchor=CENTER)
        self.file_tree.column("创建时间", width=110, minwidth=90, anchor=CENTER)
        self.file_tree.column("修改时间", width=110, minwidth=90, anchor=CENTER)
        self.file_tree.column("访问时间", width=110, minwidth=90, anchor=CENTER)
        self.file_tree.column("状态", width=80, minwidth=60, anchor=CENTER)
        self.file_tree.column("分类", width=100, minwidth=80, anchor=CENTER)
        self.file_tree.column("重要性", width=80, minwidth=60, anchor=CENTER)
        
        # 设置标题（“全选”显示为复选框样式，根据状态动态更新）
        for col in columns:
            if col == "选择":
                # 初始标题文本，后续在 refresh_file_list 中根据状态更新
                self.file_tree.heading(col, text="☐", anchor=CENTER, command=self.toggle_select_all_current_page)
            else:
                self.file_tree.heading(col, text=col, anchor=CENTER)
        
        # 滚动条
        self.tree_scroll = ttk.Scrollbar(
            self.file_list_frame,
            orient=VERTICAL,
            command=self.file_tree.yview
        )
        self.file_tree.configure(yscrollcommand=self.tree_scroll.set)
        
        # 绑定选择/点击事件
        self.file_tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.file_tree.bind('<Button-1>', self.on_tree_click)
        self.file_tree.bind('<Motion>', self.on_tree_motion)
        self.file_tree.bind('<Leave>', self.on_tree_leave)
        
        # 右侧详情区域
        self.right_frame = ttk_bs.LabelFrame(
            self.content_frame,
            text="文件详情",
            padding=10
        )
        # 设置固定宽度
        self.right_frame.configure(width=500)
        
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
        
        # 分类输入框和按钮
        category_frame = ttk_bs.Frame(self.classify_frame)
        category_frame.grid(row=0, column=1, sticky=W, pady=5)
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk_bs.Combobox(
            category_frame,
            textvariable=self.category_var,
            values=FILE_CATEGORIES,
            state="normal",  # 改为normal以支持手动输入
            width=18
        )
        self.category_combo.pack(side=LEFT)
        self.category_combo.bind('<<ComboboxSelected>>', self.on_category_change)
        self.category_combo.bind('<KeyRelease>', self.on_category_change)
        
        # 添加分类按钮
        self.add_category_btn = ttk_bs.Button(
            category_frame,
            text="+",
            bootstyle="secondary",
            width=3,
            command=self.add_category
        )
        self.add_category_btn.pack(side=LEFT, padx=(5, 0))
        
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
        
        # 标签选择
        ttk_bs.Label(self.classify_frame, text="标签:").grid(
            row=2, column=0, sticky=W+N, padx=(0, 10), pady=5
        )
        
        # 标签选择框架
        tags_frame = ttk_bs.Frame(self.classify_frame)
        tags_frame.grid(row=2, column=1, sticky=W, pady=5)
        
        # 标签输入框
        self.tags_var = tk.StringVar()
        self.tags_entry = ttk_bs.Entry(
            tags_frame,
            textvariable=self.tags_var,
            width=25
        )
        self.tags_entry.pack(side=LEFT)
        self.tags_entry.bind('<KeyRelease>', self.on_tags_change)
        
        # 添加标签按钮
        self.add_tag_btn = ttk_bs.Button(
            tags_frame,
            text="+",
            bootstyle="secondary",
            width=3,
            command=self.add_tag
        )
        self.add_tag_btn.pack(side=LEFT, padx=(5, 0))
        
        # 标签选择按钮
        self.select_tags_btn = ttk_bs.Button(
            tags_frame,
            text="选择",
            bootstyle="info",
            width=6,
            command=self.show_tag_selector
        )
        self.select_tags_btn.pack(side=LEFT, padx=(5, 0))
        
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
        
        # 分页控件
        pagination_frame = ttk_bs.Frame(self.classify_frame)
        pagination_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk_bs.Label(pagination_frame, text="分页:").pack(side=LEFT, padx=(0, 5))
        
        self.page_var = tk.IntVar(value=1)
        self.page_spinbox = ttk_bs.Spinbox(
            pagination_frame,
            from_=1,
            to=1,
            textvariable=self.page_var,
            width=8,
            command=self.on_page_change
        )
        self.page_spinbox.pack(side=LEFT, padx=(0, 5))
        
        ttk_bs.Label(pagination_frame, text="/").pack(side=LEFT, padx=(0, 5))
        
        self.total_pages_var = tk.StringVar(value="1")
        ttk_bs.Label(pagination_frame, textvariable=self.total_pages_var).pack(side=LEFT, padx=(0, 10))
        
        # 每页条数选择
        ttk_bs.Label(pagination_frame, text="每页:").pack(side=LEFT)
        self.page_size_var = tk.StringVar(value=str(self.page_size))
        self.page_size_combo = ttk_bs.Combobox(
            pagination_frame,
            textvariable=self.page_size_var,
            values=["20", "50", "100"],
            state="readonly",
            width=5
        )
        self.page_size_combo.pack(side=LEFT, padx=(5, 10))
        self.page_size_combo.bind('<<ComboboxSelected>>', self.on_page_size_change)
        
        self.prev_page_btn = ttk_bs.Button(
            pagination_frame,
            text="上一页",
            bootstyle="secondary",
            command=self.prev_page
        )
        self.prev_page_btn.pack(side=LEFT, padx=(0, 5))
        
        self.next_page_btn = ttk_bs.Button(
            pagination_frame,
            text="下一页",
            bootstyle="secondary",
            command=self.next_page
        )
        self.next_page_btn.pack(side=LEFT)
        
        # 选择/上传辅助按钮
        self.select_all_btn = ttk_bs.Button(
            pagination_frame,
            text="全选本页",
            bootstyle="info",
            command=self.select_all_current_page
        )
        self.select_all_btn.pack(side=LEFT, padx=(20, 5))
        
        self.clear_select_btn = ttk_bs.Button(
            pagination_frame,
            text="清空选择",
            bootstyle="secondary",
            command=self.clear_selection_current_page
        )
        self.clear_select_btn.pack(side=LEFT)
        
        # 批量上传按钮（当前页已选）
        self.batch_upload_btn = ttk_bs.Button(
            pagination_frame,
            text="批量上传(本页已选)",
            bootstyle="warning",
            command=self.batch_upload_current_page
        )
        self.batch_upload_btn.pack(side=LEFT, padx=(20, 0))
        
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
        
        self.stats_scroll = ttk.Scrollbar(
            self.stats_frame,
            orient=VERTICAL,
            command=self.stats_text.yview
        )
        self.stats_text.configure(yscrollcommand=self.stats_scroll.set)
        
        # 悬浮高亮状态
        self._hover_row_id = None
        
    def setup_layout(self):
        """
        设置界面布局
        """
        # 主框架
        self.main_frame.pack(fill=BOTH, expand=True)
        
        # 工具栏
        self.toolbar_frame.pack(fill=X, pady=(0, 10))
        
        self.scan_btn.pack(side=LEFT, padx=(0, 10))
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
        self.right_frame.pack(side=RIGHT, fill=Y)
        
        self.info_frame.pack(fill=X, pady=(0, 10))
        self.classify_frame.pack(fill=X, pady=(0, 10))
        self.stats_frame.pack(fill=BOTH, expand=True)
        
        self.stats_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.stats_scroll.pack(side=RIGHT, fill=Y)
        
    def set_callbacks(self, scan_callback=None, upload_callback=None, clear_cache_callback=None, parse_callback=None):
        """
        设置回调函数
        """
        self.on_file_scan = scan_callback
        self.on_database_upload = upload_callback
        self.on_clear_cache = clear_cache_callback
        self.on_parse_files = parse_callback
        
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
        # 默认状态：未变化（unchanged）
        for f in self.files_data:
            if not f.get('status'):
                f['status'] = 'unchanged'
        self.selected_paths.clear()
        self.apply_filters(reset_page=True)
        self.update_statistics()
        self.status_label.config(text=f"扫描完成，共找到 {len(files)} 个文件，共 {self.total_pages} 页")
    
    def on_scan_error(self, error_msg):
        """
        扫描错误回调
        """
        self.progress.stop()
        self.status_label.config(text="扫描失败")
        messagebox.showerror("错误", f"扫描文件时出错：{error_msg}")
    
    
    
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
    
    def upload_selected_to_database(self):
        """
        上传已选中的数据（全局，最多100条）
        """
        if not self.files_data:
            messagebox.showwarning("警告", "没有数据可上传")
            return
        
        if not self.selected_paths:
            messagebox.showwarning("警告", "请先在列表中勾选要上传的文件")
            return
        
        # 汇总选择的数据（按 file_path 去重）
        selected_records = [f for f in self.files_data if f.get('file_path') in self.selected_paths]
        if not selected_records:
            messagebox.showwarning("警告", "未找到可上传的数据")
            return
        
        # 限制每次最多100条
        limit = 100
        to_upload = selected_records[:limit]
        remaining = len(selected_records) - len(to_upload)
        
        if self.on_database_upload:
            confirm_msg = f"确定要上传所选的 {len(to_upload)} 个文件到数据库吗？"
            if remaining > 0:
                confirm_msg += f"\n(还有 {remaining} 个已选文件将留待下次上传)"
            
            result = messagebox.askyesno("确认", confirm_msg)
            if not result:
                return
            
            self.progress.start()
            self.status_label.config(text="正在上传所选数据到数据库...")
            
            def upload_thread():
                try:
                    success = self.on_database_upload(to_upload)
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
    
    def parse_selected_files(self):
        """
        解析已选择的文件（PDF OCR处理）
        """
        if not self.files_data:
            messagebox.showwarning("警告", "没有数据可解析")
            return
        
        if not self.selected_paths:
            messagebox.showwarning("警告", "请先在列表中勾选要解析的文件")
            return
        
        # 获取已选择的文件
        selected_records = [f for f in self.files_data if f.get('file_path') in self.selected_paths]
        if not selected_records:
            messagebox.showwarning("警告", "未找到可解析的文件")
            return
        
        # 过滤出PDF文件
        pdf_files = [f for f in selected_records if f.get('extension', '').lower() == '.pdf']
        if not pdf_files:
            messagebox.showwarning("警告", "所选文件中没有PDF文件")
            return
        
        if self.on_parse_files:
            confirm_msg = f"确定要解析所选的 {len(pdf_files)} 个PDF文件吗？\n这将进行OCR识别和向量化处理。"
            
            result = messagebox.askyesno("确认", confirm_msg)
            if not result:
                return
            
            self.progress.start()
            self.status_label.config(text="正在解析PDF文件...")
            
            def parse_thread():
                try:
                    success = self.on_parse_files(pdf_files)
                    self.root.after(0, self.on_parse_complete, success)
                except Exception as e:
                    self.root.after(0, self.on_parse_error, str(e))
            
            threading.Thread(target=parse_thread, daemon=True).start()
        else:
            messagebox.showwarning("警告", "解析功能未启用")
    
    def on_parse_complete(self, success):
        """
        解析完成回调
        """
        self.progress.stop()
        if success:
            self.status_label.config(text="解析成功")
            messagebox.showinfo("成功", "PDF文件解析完成")
            # 刷新文件列表以显示更新后的状态
            self.refresh_file_list()
        else:
            self.status_label.config(text="解析失败")
            messagebox.showerror("错误", "PDF文件解析失败")
    
    def on_parse_error(self, error_msg):
        """
        解析错误回调
        """
        self.progress.stop()
        self.status_label.config(text="解析失败")
        messagebox.showerror("错误", f"解析PDF文件时出错：{error_msg}")
    
    def refresh_file_list(self):
        """
        刷新文件列表
        """
        # 清空现有项目
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # 获取当前页数据
        current_page_data = self.get_current_page_data()
        
        if not current_page_data:
            # 空数据提示
            self.file_tree.insert('', 'end', values=('', '', '（无数据）', '', '', '', '', '', '', ''))
            self.update_pagination()
            return
        
        # 添加新项目
        for i, file_data in enumerate(current_page_data):
            file_name = file_data.get('file_name', '')
            file_size = file_data.get('file_size_mb', 0)
            
            # 处理创建时间
            creation_date = file_data.get('creation_date', '')
            if isinstance(creation_date, datetime):
                creation_date = creation_date.strftime('%Y-%m-%d')
            
            # 处理修改时间
            mod_date = file_data.get('modification_date', '')
            if isinstance(mod_date, datetime):
                mod_date = mod_date.strftime('%Y-%m-%d')
            
            # 处理访问时间
            access_date = file_data.get('access_date', '')
            if isinstance(access_date, datetime):
                access_date = access_date.strftime('%Y-%m-%d')
            
            category = file_data.get('category', '')
            importance = file_data.get('importance', '')
            status_code = file_data.get('status', '') or 'unchanged'
            status = {'new': '新增', 'updated': '更新', 'unchanged': '未变化'}.get(status_code, status_code)
            
            # 计算全局序号
            global_index = (self.current_page - 1) * self.page_size + i + 1
            
            # 更大的Checkbox符号
            sel_mark = '☑' if file_data.get('file_path') in self.selected_paths else '☐'
            
            self.file_tree.insert(
                '',
                'end',
                values=(sel_mark, global_index, file_name, file_size, creation_date, mod_date, access_date, status, category, importance),
                tags=("even" if i % 2 == 0 else "odd",)
            )
        
        # 更新分页信息
        self.update_pagination()
        
        # 刷新表头“全选”复选框文本
        try:
            current = self.get_current_page_data()
            current_paths = {rec.get('file_path') for rec in current if rec.get('file_path')}
            if current and current_paths and current_paths.issubset(self.selected_paths):
                header_text = "☑"
            else:
                header_text = "☐"
            self.file_tree.heading("选择", text=header_text)
        except Exception:
            pass
    
    def clear_filters(self):
        """
        清空筛选条件
        """
        self.search_var.set('')
        self.status_var.set('全部')
        self.apply_filters(reset_page=True)
    
    def apply_filters(self, *args, reset_page=False):
        """
        组合状态和关键词筛选，更新 filtered_data
        """
        keyword = (self.search_var.get() or '').lower().strip()
        status_map = {"全部": "all", "新增": "new", "更新": "updated", "未变化": "unchanged"}
        status_value = status_map.get(self.status_var.get(), "all")
        
        base = self.files_data
        filtered = []
        for f in base:
            # 状态过滤（f['status'] 使用英文代码）
            if status_value != 'all' and (f.get('status') != status_value):
                continue
            # 关键词过滤
            if keyword:
                fn = str(f.get('file_name', '')).lower()
                cat = str(f.get('category', '')).lower()
                tags = str(f.get('tags', '')).lower()
                notes = str(f.get('notes', '')).lower()
                if (keyword not in fn and keyword not in cat and keyword not in tags and keyword not in notes):
                    continue
            filtered.append(f)
        
        self.filtered_data = filtered
        if reset_page:
            self.current_page = 1
        self.refresh_file_list()
    
    def on_status_filter_change(self, event):
        """
        状态筛选改变事件
        """
        self.apply_filters(reset_page=True)
    
    def clear_cache(self):
        """
        清空缓存
        """
        result = messagebox.askyesno(
            "确认清空缓存",
            "确定要清空文件缓存吗？\n这将导致下次扫描时重新扫描所有文件。"
        )
        
        if result:
            try:
                # 通过回调函数清空缓存
                if hasattr(self, 'on_clear_cache') and self.on_clear_cache:
                    self.on_clear_cache()
                    # 清空当前显示的数据
                    self.files_data = []
                    self.filtered_data = []
                    self.selected_paths.clear()
                    self.current_page = 1
                    self.refresh_file_list()
                    self.update_statistics()
                    self.status_label.config(text="缓存已清空")
                    messagebox.showinfo("成功", "缓存已清空，请重新扫描文件")
                else:
                    messagebox.showwarning("警告", "缓存清空功能需要与主程序集成")
            except Exception as e:
                messagebox.showerror("错误", f"清空缓存失败: {e}")
    
    def on_tree_click(self, event):
        """
        点击列表切换选择（仅当点击"选择"列）
        """
        region = self.file_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.file_tree.identify_column(event.x)  # 如 '#1', '#2'
        if col != '#1':  # '#1' 对应第一列"选择"
            return
        row_id = self.file_tree.identify_row(event.y)
        if not row_id:
            return
        
        # 获取行索引（从0开始）
        try:
            row_index = self.file_tree.index(row_id)
        except Exception:
            return
            
        if 0 <= row_index < len(self.get_current_page_data()):
            record = self.get_current_page_data()[row_index]
            path = record.get('file_path')
            if not path:
                return
            if path in self.selected_paths:
                self.selected_paths.remove(path)
            else:
                self.selected_paths.add(path)
            # 刷新该行显示
            self.refresh_file_list()

    def on_tree_motion(self, event):
        """
        鼠标移动到行上时高亮该行（Ant风格悬浮）
        """
        row_id = self.file_tree.identify_row(event.y)
        if row_id == self._hover_row_id:
            return
        # 移除旧hover
        if self._hover_row_id is not None and self.file_tree.exists(self._hover_row_id):
            # 还原为奇偶样式
            idx = self.file_tree.index(self._hover_row_id)
            self.file_tree.item(self._hover_row_id, tags=("even" if idx % 2 == 0 else "odd",))
        self._hover_row_id = row_id if row_id else None
        if self._hover_row_id is not None:
            self.file_tree.item(self._hover_row_id, tags=("hover",))

    def on_tree_leave(self, event):
        """
        鼠标离开控件时移除高亮
        """
        if self._hover_row_id is not None and self.file_tree.exists(self._hover_row_id):
            idx = self.file_tree.index(self._hover_row_id)
            self.file_tree.item(self._hover_row_id, tags=("even" if idx % 2 == 0 else "odd",))
        self._hover_row_id = None
    
    def toggle_select_all_current_page(self):
        """
        表头点击：切换本页全选/全不选
        """
        current = self.get_current_page_data()
        if not current:
            return
        current_paths = {rec.get('file_path') for rec in current if rec.get('file_path')}
        if current_paths.issubset(self.selected_paths):
            # 全不选
            self.selected_paths -= current_paths
        else:
            # 全选
            self.selected_paths |= current_paths
        self.refresh_file_list()
    
    def on_file_select(self, event):
        """
        文件选择事件
        """
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            try:
                # 获取行索引（从0开始）
                row_index = self.file_tree.index(selection[0])
            except Exception:
                return
            
            # 在过滤后的数据中定位
            current_page_data = self.get_current_page_data()
            if 0 <= row_index < len(current_page_data):
                record = current_page_data[row_index]
                try:
                    self.current_file_index = self.files_data.index(record)
                except ValueError:
                    return
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
    
    def add_category(self):
        """
        添加新分类
        """
        new_category = self.category_var.get().strip()
        if new_category and new_category not in FILE_CATEGORIES:
            # 添加到全局分类列表
            FILE_CATEGORIES.append(new_category)
            # 更新下拉框选项
            self.category_combo['values'] = FILE_CATEGORIES
            messagebox.showinfo("成功", f"已添加新分类: {new_category}")
    
    def add_tag(self):
        """
        添加新标签
        """
        new_tag = self.tags_var.get().strip()
        if new_tag:
            current_tags = self.tags_var.get().split(',') if self.tags_var.get() else []
            current_tags = [tag.strip() for tag in current_tags if tag.strip()]
            
            if new_tag not in current_tags:
                current_tags.append(new_tag)
                self.tags_var.set(', '.join(current_tags))
                self.on_tags_change(None)
                messagebox.showinfo("成功", f"已添加新标签: {new_tag}")
            else:
                messagebox.showwarning("警告", f"标签 '{new_tag}' 已存在")
    
    def show_tag_selector(self):
        """
        显示标签选择器
        """
        if not hasattr(self, 'tag_selector_window') or not self.tag_selector_window.winfo_exists():
            self.tag_selector_window = tk.Toplevel(self.root)
            self.tag_selector_window.title("选择标签")
            self.tag_selector_window.geometry("400x300")
            self.tag_selector_window.resizable(False, False)
            
            # 获取当前标签
            current_tags = self.tags_var.get().split(',') if self.tags_var.get() else []
            current_tags = [tag.strip() for tag in current_tags if tag.strip()]
            
            # 创建标签选择框架
            main_frame = ttk_bs.Frame(self.tag_selector_window, padding=10)
            main_frame.pack(fill=BOTH, expand=True)
            
            # 预设标签
            ttk_bs.Label(main_frame, text="预设标签:").pack(anchor=W, pady=(0, 5))
            
            preset_frame = ttk_bs.Frame(main_frame)
            preset_frame.pack(fill=X, pady=(0, 10))
            
            self.preset_tag_vars = {}
            for i, tag in enumerate(PRESET_TAGS):
                var = tk.BooleanVar(value=tag in current_tags)
                self.preset_tag_vars[tag] = var
                
                cb = ttk_bs.Checkbutton(
                    preset_frame,
                    text=tag,
                    variable=var,
                    bootstyle="round-toggle"
                )
                cb.grid(row=i//3, column=i%3, sticky=W, padx=(0, 10), pady=2)
            
            # 自定义标签输入
            ttk_bs.Label(main_frame, text="自定义标签:").pack(anchor=W, pady=(10, 5))
            
            custom_frame = ttk_bs.Frame(main_frame)
            custom_frame.pack(fill=X, pady=(0, 10))
            
            self.custom_tag_var = tk.StringVar()
            custom_entry = ttk_bs.Entry(
                custom_frame,
                textvariable=self.custom_tag_var,
                width=30
            )
            custom_entry.pack(side=LEFT, padx=(0, 5))
            
            add_custom_btn = ttk_bs.Button(
                custom_frame,
                text="添加",
                bootstyle="secondary",
                command=self.add_custom_tag
            )
            add_custom_btn.pack(side=LEFT)
            
            # 按钮
            button_frame = ttk_bs.Frame(main_frame)
            button_frame.pack(fill=X, pady=(20, 0))
            
            ok_btn = ttk_bs.Button(
                button_frame,
                text="确定",
                bootstyle="success",
                command=self.apply_tag_selection
            )
            ok_btn.pack(side=RIGHT, padx=(5, 0))
            
            cancel_btn = ttk_bs.Button(
                button_frame,
                text="取消",
                bootstyle="secondary",
                command=self.tag_selector_window.destroy
            )
            cancel_btn.pack(side=RIGHT)
    
    def add_custom_tag(self):
        """
        添加自定义标签
        """
        custom_tag = self.custom_tag_var.get().strip()
        if custom_tag:
            if custom_tag not in PRESET_TAGS:
                PRESET_TAGS.append(custom_tag)
                # 重新创建标签选择器
                self.tag_selector_window.destroy()
                self.show_tag_selector()
                self.custom_tag_var.set(custom_tag)
            else:
                messagebox.showwarning("警告", f"标签 '{custom_tag}' 已存在")
    
    def apply_tag_selection(self):
        """
        应用标签选择
        """
        selected_tags = []
        
        # 获取选中的预设标签
        for tag, var in self.preset_tag_vars.items():
            if var.get():
                selected_tags.append(tag)
        
        # 获取自定义标签
        custom_tag = self.custom_tag_var.get().strip()
        if custom_tag and custom_tag not in selected_tags:
            selected_tags.append(custom_tag)
        
        # 更新标签输入框
        self.tags_var.set(', '.join(selected_tags))
        self.on_tags_change(None)
        
        # 关闭窗口
        self.tag_selector_window.destroy()
    
    def update_pagination(self):
        """
        更新分页信息
        """
        data_len = len(self.filtered_data) if self.filtered_data is not None else 0
        if data_len <= 0:
            self.total_pages = 1
            self.current_page = 1
        else:
            self.total_pages = max(1, (data_len + self.page_size - 1) // self.page_size)
            self.current_page = min(self.current_page, self.total_pages)
        
        # 更新分页控件
        self.page_var.set(self.current_page)
        self.total_pages_var.set(str(self.total_pages))
        self.page_spinbox.configure(to=self.total_pages)
        
        # 更新按钮状态
        self.prev_page_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_page_btn.configure(state="normal" if self.current_page < self.total_pages else "disabled")
        
        # 更新批量上传按钮状态
        self.batch_upload_btn.configure(state="normal" if self.filtered_data else "disabled")
    
    def get_current_page_data(self):
        """
        获取当前页的数据（基于 filtered_data）
        """
        data = self.filtered_data or []
        if not data:
            return []
        
        start_index = (self.current_page - 1) * self.page_size
        end_index = start_index + self.page_size
        return data[start_index:end_index]
    
    def on_page_change(self):
        """
        页码改变事件
        """
        new_page = self.page_var.get()
        if 1 <= new_page <= self.total_pages and new_page != self.current_page:
            self.current_page = new_page
            self.refresh_file_list()
            self.update_pagination()
    
    def on_page_size_change(self, event):
        """
        每页条数改变
        """
        try:
            new_size = int(self.page_size_var.get())
            if new_size in (20, 50, 100):
                self.page_size = new_size
                self.current_page = 1
                self.refresh_file_list()
        except Exception:
            pass
    
    def prev_page(self):
        """
        上一页
        """
        if self.current_page > 1:
            self.current_page -= 1
            self.page_var.set(self.current_page)
            self.refresh_file_list()
            self.update_pagination()
    
    def next_page(self):
        """
        下一页
        """
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.page_var.set(self.current_page)
            self.refresh_file_list()
            self.update_pagination()
    
    def select_all_current_page(self):
        """
        全选当前页
        """
        for rec in self.get_current_page_data():
            path = rec.get('file_path')
            if path:
                self.selected_paths.add(path)
        self.refresh_file_list()
    
    def clear_selection_current_page(self):
        """
        清空当前页选择
        """
        for rec in self.get_current_page_data():
            path = rec.get('file_path')
            if path and path in self.selected_paths:
                self.selected_paths.remove(path)
        self.refresh_file_list()
    
    def batch_upload_current_page(self):
        """
        批量上传当前页“已选择”的数据（最多100条；如未选择则默认本页全部）
        """
        current_page_data = self.get_current_page_data()
        if not current_page_data:
            messagebox.showwarning("警告", "当前页没有数据可上传")
            return
        
        selected_current = [rec for rec in current_page_data if rec.get('file_path') in self.selected_paths]
        if not selected_current:
            selected_current = current_page_data  # 默认上传本页全部
        
        # 过滤出已分类的数据
        classified_data = [file_data for file_data in selected_current 
                           if file_data.get('category') or file_data.get('importance') or 
                              file_data.get('tags') or file_data.get('notes')]
        
        if not classified_data:
            messagebox.showwarning("警告", "当前页未选择已分类的数据可上传")
            return
        
        limit = 100
        to_upload = classified_data[:limit]
        remaining = len(classified_data) - len(to_upload)
        
        result = messagebox.askyesno(
            "确认上传",
            f"确定要上传 {len(to_upload)} 个文件到数据库吗？" + (f"\n(还有 {remaining} 个将留待下次上传)" if remaining > 0 else "")
        )
        
        if result and self.on_database_upload:
            self.progress.start()
            self.status_label.config(text="正在上传当前页数据到数据库...")
            
            # 在新线程中执行上传
            def upload_thread():
                try:
                    success = self.on_database_upload(to_upload)
                    self.root.after(0, self.on_batch_upload_complete, success, len(to_upload))
                except Exception as e:
                    self.root.after(0, self.on_batch_upload_error, str(e))
            
            threading.Thread(target=upload_thread, daemon=True).start()
    
    def on_batch_upload_complete(self, success, count):
        """
        批量上传完成回调
        """
        self.progress.stop()
        if success:
            self.status_label.config(text=f"批量上传成功，共上传 {count} 个文件")
            messagebox.showinfo("成功", f"当前页数据已成功上传到数据库，共 {count} 个文件")
        else:
            self.status_label.config(text="批量上传失败")
            messagebox.showerror("错误", "批量上传失败")
    
    def on_batch_upload_error(self, error_msg):
        """
        批量上传错误回调
        """
        self.progress.stop()
        self.status_label.config(text="批量上传失败")
        messagebox.showerror("错误", f"批量上传时出错：{error_msg}")
    
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
        stats_text += f"总大小: {total_size:.2f} MB\n"
        stats_text += f"当前页: {self.current_page}/{self.total_pages}\n"
        stats_text += f"每页显示: {self.page_size} 条\n\n"
        
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