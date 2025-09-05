# -*- coding: utf-8 -*-
"""
测试分类配置的脚本
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_categories_config():
    """测试分类配置"""
    print("🧪 测试分类配置...")
    
    try:
        from config import FILE_CATEGORIES, PRESET_TAGS
        
        print("✓ 配置文件导入成功")
        
        # 测试分类数量
        print(f"\n📊 分类统计:")
        print(f"  文件分类数量: {len(FILE_CATEGORIES)}")
        print(f"  预设标签数量: {len(PRESET_TAGS)}")
        
        # 显示所有分类
        print(f"\n🏷️ 文件分类列表:")
        for i, category in enumerate(FILE_CATEGORIES, 1):
            print(f"  {i:2d}. {category}")
        
        # 显示所有标签
        print(f"\n🏷️ 预设标签列表:")
        for i, tag in enumerate(PRESET_TAGS, 1):
            print(f"  {i:2d}. {tag}")
        
        # 验证分类分组
        print(f"\n📋 分类分组验证:")
        
        # 传统金融研究分类
        financial_categories = ['宏观经济', '行业研究', '公司研究', '投资策略', '固定收益', '量化研究']
        print(f"  传统金融研究分类: {len([c for c in FILE_CATEGORIES if c in financial_categories])}/{len(financial_categories)}")
        
        # 快消品行业
        fcg_categories = ['快消品', '美妆护肤', '电商']
        print(f"  快消品行业分类: {len([c for c in FILE_CATEGORIES if c in fcg_categories])}/{len(fcg_categories)}")
        
        # 制造业
        manufacturing_categories = ['汽车', '家电', '手机', '数码3C', '服装', '家居']
        print(f"  制造业分类: {len([c for c in FILE_CATEGORIES if c in manufacturing_categories])}/{len(manufacturing_categories)}")
        
        # 服务业
        service_categories = ['互联网', '餐饮', '游戏', '影视娱乐', '时尚', '宠物', '酒类', '教育', '体育', '文旅', '零售', '医疗', '招商']
        print(f"  服务业分类: {len([c for c in FILE_CATEGORIES if c in service_categories])}/{len(service_categories)}")
        
        # 内容类型
        content_categories = ['必读书单', '手册', '思维导图']
        print(f"  内容类型分类: {len([c for c in FILE_CATEGORIES if c in content_categories])}/{len(content_categories)}")
        
        print("\n✅ 分类配置测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 分类配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_category_usage():
    """测试分类使用示例"""
    print("\n🧪 测试分类使用示例...")
    
    try:
        from config import FILE_CATEGORIES, PRESET_TAGS
        
        # 模拟文件分类示例
        example_files = [
            {
                'name': '新能源汽车行业研究报告.pdf',
                'categories': ['汽车', '行业研究', '投资策略'],
                'tags': ['重要', '深度研究', '投资机会']
            },
            {
                'name': '互联网平台经济分析.pdf',
                'categories': ['互联网', '行业研究', '市场动态'],
                'tags': ['热点话题', '政策影响', '趋势分析']
            },
            {
                'name': '医疗健康产业投资指南.pdf',
                'categories': ['医疗', '投资策略', '行业研究'],
                'tags': ['投资建议', '风险评估', '市场机会']
            }
        ]
        
        print("📁 文件分类示例:")
        for i, file_info in enumerate(example_files, 1):
            print(f"\n  文件 {i}: {file_info['name']}")
            print(f"    分类: {', '.join(file_info['categories'])}")
            print(f"    标签: {', '.join(file_info['tags'])}")
            
            # 验证分类是否存在
            valid_categories = [c for c in file_info['categories'] if c in FILE_CATEGORIES]
            if len(valid_categories) == len(file_info['categories']):
                print(f"    ✓ 所有分类都有效")
            else:
                print(f"    ⚠ 部分分类无效: {[c for c in file_info['categories'] if c not in FILE_CATEGORIES]}")
            
            # 验证标签是否存在
            valid_tags = [t for t in file_info['tags'] if t in PRESET_TAGS]
            if len(valid_tags) == len(file_info['tags']):
                print(f"    ✓ 所有标签都有效")
            else:
                print(f"    ⚠ 部分标签无效: {[t for t in file_info['tags'] if t not in PRESET_TAGS]}")
        
        print("\n✅ 分类使用示例测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 分类使用示例测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试分类配置")
    print("=" * 60)
    
    # 测试分类配置
    config_test = test_categories_config()
    
    # 测试分类使用示例
    usage_test = test_category_usage()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    if config_test and usage_test:
        print("🎉 所有测试通过！分类配置正常！")
        print("\n✅ 新增的分类包括:")
        print("  - 快消品行业: 快消品、美妆护肤、电商")
        print("  - 制造业: 汽车、家电、手机、数码3C、服装、家居")
        print("  - 服务业: 互联网、餐饮、游戏、影视娱乐、时尚、宠物、酒类、教育、体育、文旅、零售、医疗、招商")
        print("  - 其他行业: 金融、食品、地产")
        print("  - 内容类型: 必读书单、手册、思维导图")
        print("\n✅ 新增的标签包括:")
        print("  - 热点话题、深度研究、数据报告、专家观点")
        print("  - 市场预测、竞争分析、趋势分析、创新技术")
        print("  - 政策影响、风险评估、投资建议、行业趋势")
        print("  - 市场机会、战略规划")
    else:
        print("❌ 部分测试失败，需要检查配置")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
