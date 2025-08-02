import os
from dotenv import load_dotenv

load_dotenv()  # 載入 .env 檔案內容到環境變數

# 配置類別
class Config:
    SECRET_KEY = 'your_secret_key'
    FIREBASE_DATABASE_URL = 'https://socialmedia-7c038-default-rtdb.asia-southeast1.firebasedatabase.app/'
    FIREBASE_CREDENTIALS_PATH = "C:/Users/deehu/Desktop/Program/socialmediatemplate/socialmedia-7c038-firebase-adminsdk-fbsvc-a3b30f46e1.json"
    OPENAI_API_KEY = "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"
    CLAUDE_API_KEY = "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"  # 請替換為您的Claude API Key
    
    # Firebase Web Configuration
    FIREBASE_CONFIG = {
        "apiKey": "AIzaSyCMsa0rv-EJnMnFNwQ5X3F7hbjdGvwJ00E",
        "authDomain": "socialmedia-7c038.firebaseapp.com",
        "databaseURL": "https://socialmedia-7c038-default-rtdb.asia-southeast1.firebasedatabase.app",
        "projectId": "socialmedia-7c038",
        "storageBucket": "socialmedia-7c038.appspot.com",
        "messagingSenderId": "851731795907",
        "appId": "1:851731795907:web:c1db66a2f12857b8e2ba64"
    }
    
    # Path configuration
    EMOTION_FOLDERS = ['contempt', 'anger', 'disgust']
    NEWS_FOLDER = 'news'

config = Config()

