import os
from dotenv import load_dotenv

# 載入 .env 檔案內容到環境變數 (指定完整路徑)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

# 配置類別
class Config:
    SECRET_KEY = 'your_secret_key'
    
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    
    # Path configuration
    EMOTION_FOLDERS = ['contempt', 'anger', 'disgust']
    NEWS_FOLDER = 'news'

config = Config()

