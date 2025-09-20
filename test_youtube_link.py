#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube链接测试和修复工具
用于诊断和修复YouTube下载器无法获取特定链接信息的问题
"""

import yt_dlp
import json
import sys
from urllib.parse import urlparse, parse_qs
import traceback

def test_youtube_link(url):
    """测试YouTube链接并诊断问题"""
    print(f"🔍 测试链接: {url}")
    print("=" * 80)
    
    # 1. URL解析测试
    print("1. URL解析测试:")
    try:
        parsed = urlparse(url)
        print(f"   ✅ Scheme: {parsed.scheme}")
        print(f"   ✅ Netloc: {parsed.netloc}")
        print(f"   ✅ Path: {parsed.path}")
        print(f"   ✅ Query: {parsed.query}")
        
        # 解析查询参数
        query_params = parse_qs(parsed.query)
        print(f"   📋 查询参数:")
        for key, value in query_params.items():
            print(f"      - {key}: {value}")
            
    except Exception as e:
        print(f"   ❌ URL解析失败: {e}")
        return False
    
    print()
    
    # 2. 基础yt-dlp测试
    print("2. 基础yt-dlp测试:")
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,  # 获取完整信息
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("   🔄 正在获取视频信息...")
            info = ydl.extract_info(url, download=False)
            
            print(f"   ✅ 标题: {info.get('title', '未知')}")
            print(f"   ✅ 时长: {info.get('duration', '未知')} 秒")
            print(f"   ✅ 上传者: {info.get('uploader', '未知')}")
            print(f"   ✅ 观看次数: {info.get('view_count', '未知')}")
            print(f"   ✅ 视频ID: {info.get('id', '未知')}")
            
            # 检查是否是播放列表
            if 'entries' in info:
                print(f"   📋 这是一个播放列表，包含 {len(info['entries'])} 个项目")
                for i, entry in enumerate(info['entries'][:3]):  # 只显示前3个
                    print(f"      {i+1}. {entry.get('title', '未知标题')}")
                if len(info['entries']) > 3:
                    print(f"      ... 还有 {len(info['entries']) - 3} 个项目")
            
            return True
            
    except Exception as e:
        print(f"   ❌ yt-dlp基础测试失败: {e}")
        print(f"   📋 错误详情: {traceback.format_exc()}")
    
    print()
    
    # 3. 增强配置测试
    print("3. 增强配置测试:")
    try:
        enhanced_opts = {
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'ignoreerrors': False,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'extractor_retries': 3,
            'playlist_items': '1',  # 只获取播放列表第一项
        }
        
        with yt_dlp.YoutubeDL(enhanced_opts) as ydl:
            print("   🔄 使用增强配置获取信息...")
            info = ydl.extract_info(url, download=False)
            
            print(f"   ✅ 成功获取信息!")
            print(f"   ✅ 标题: {info.get('title', '未知')}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ 增强配置测试失败: {e}")
    
    print()
    
    # 4. 单视频提取测试
    print("4. 单视频提取测试:")
    try:
        # 尝试提取单个视频ID
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        video_id = query_params.get('v', [None])[0]
        
        if video_id:
            single_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"   🔄 测试单视频链接: {single_url}")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(single_url, download=False)
                print(f"   ✅ 单视频测试成功!")
                print(f"   ✅ 标题: {info.get('title', '未知')}")
                return True
        else:
            print("   ⚠️  无法提取视频ID")
            
    except Exception as e:
        print(f"   ❌ 单视频测试失败: {e}")
    
    return False

def get_improved_ydl_opts():
    """获取改进的yt-dlp配置"""
    return {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': False,
        'socket_timeout': 30,
        'retries': 5,
        'fragment_retries': 5,
        'extractor_retries': 5,
        'playlist_items': '1',  # 对于播放列表，只获取第一项
        'writesubtitles': False,
        'writeautomaticsub': False,
        'format': 'best',
        # 添加用户代理
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

def create_fixed_fetch_function():
    """创建修复后的获取函数"""
    code = '''
def fetch_video_info_fixed(self):
    """修复后的获取视频信息函数"""
    url = self.url_entry.get().strip()
    
    # 改进的URL验证
    if not self.validate_url_improved(url):
        messagebox.showerror("错误", "请输入有效的YouTube链接")
        return
    
    def _fetch():
        try:
            # 检查是否是播放列表链接
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # 如果是播放列表链接，提取单个视频
            if 'list' in query_params and 'v' in query_params:
                video_id = query_params['v'][0]
                clean_url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"检测到播放列表链接，使用单视频链接: {clean_url}")
            else:
                clean_url = url
            
            proxy = self.proxy_entry.get().strip() or None
            
            # 改进的yt-dlp配置
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'ignoreerrors': False,
                'socket_timeout': 30,
                'retries': 5,
                'fragment_retries': 5,
                'extractor_retries': 5,
                'proxy': proxy,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                
                title = info.get('title', '未知')
                duration = info.get('duration', 0)
                views = info.get('view_count', 0)
                uploader = info.get('uploader', '未知')
                
                # 格式化时长
                if duration:
                    hours, remainder = divmod(int(duration), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
                else:
                    duration_str = "未知"
                
                # 格式化观看次数
                views_str = f"{views:,}" if views else "未知"
                
                self.root.after(0, lambda: [
                    self.title_var.set(f"标题: {title[:50]}..."),
                    self.duration_var.set(f"时长: {duration_str}"),
                    self.views_var.set(f"观看: {views_str}"),
                    self.uploader_var.set(f"作者: {uploader}")
                ])
                
                self.video_info[clean_url] = info
                self.result_queue.put(('success', f"获取视频信息成功: {title}"))
                
        except Exception as e:
            self.result_queue.put(('error', f"获取视频信息失败: {str(e)}"))
    
    threading.Thread(target=_fetch, daemon=True).start()

def validate_url_improved(self, url):
    """改进的URL验证函数"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # 检查基本URL结构
        if not all([parsed.scheme, parsed.netloc]):
            return False
        
        # 检查是否是YouTube域名
        youtube_domains = [
            'youtube.com', 'www.youtube.com', 
            'youtu.be', 'www.youtu.be',
            'music.youtube.com'
        ]
        
        if parsed.netloc.lower() not in youtube_domains:
            return False
        
        # 对于YouTube链接，检查是否包含视频ID
        if 'youtube.com' in parsed.netloc:
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed.query)
            # 检查watch页面或embed页面
            if '/watch' in parsed.path and 'v' in query_params:
                return True
            elif '/embed/' in parsed.path:
                return True
            elif '/playlist' in parsed.path and 'list' in query_params:
                return True
        elif 'youtu.be' in parsed.netloc:
            # youtu.be短链接格式
            return len(parsed.path) > 1
        
        return True
        
    except Exception:
        return False
'''
    return code

if __name__ == "__main__":
    # 测试提供的链接
    test_url = "https://www.youtube.com/watch?v=lSk-DWAJPbA&list=RDlSk-DWAJPbA&start_radio=1"
    
    print("🚀 YouTube链接诊断工具")
    print("=" * 80)
    
    success = test_youtube_link(test_url)
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 链接测试成功！问题可能在于工具的配置或实现。")
    else:
        print("❌ 链接测试失败！需要进一步调试。")
    
    print("\n📋 修复建议:")
    print("1. 更新URL验证函数以支持复杂的YouTube链接")
    print("2. 改进yt-dlp配置，增加重试和超时设置")
    print("3. 对播放列表链接进行特殊处理")
    print("4. 添加更好的错误处理和日志记录")
    
    print(f"\n🔧 修复后的代码已生成，请查看上面的函数实现。")