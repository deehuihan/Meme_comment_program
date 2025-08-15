#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memetemplate 配置檔案
"""

import os
from dotenv import load_dotenv

# 載入環境變數
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

class Config:
    # Flask 應用程式設定
    SECRET_KEY = 'meme_template_secret_key_2025'
    
    # 如果需要 API keys，可以從環境變數讀取
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

# 創建配置實例
config = Config()

# Facebook 設定 (從 config.py.bak 中讀取)
FB_EMAIL = "huihandeee@gmail.com"
FB_PASSWORD = "dee123456"
