import os
import sys
import tempfile
import subprocess

# Import config to get the OpenAI API key
sys.path.append("C:/Users/deehu/Desktop/Program/socialmediatemplate")
from config import config

# Function to compress audio file
def compress_audio_file(input_path, max_size_mb=25):
    """壓縮音訊檔案至 API 限制大小以下"""
    max_size_bytes = max_size_mb * 1024 * 1024
    print(f"原始檔案大小: {os.path.getsize(input_path) / (1024*1024):.2f} MB")
    
    # 使用臨時檔案
    output_path = tempfile.mktemp(suffix='.mp3')
    
    # 開始使用較高的比特率，如果檔案仍然太大則逐步降低
    bitrates = ["64k", "48k", "32k", "24k", "16k", "8k"]
    
    for bitrate in bitrates:
        try:
            # 使用 ffmpeg 壓縮檔案
            print(f"嘗試以 {bitrate} 比特率壓縮音訊檔案...")
            cmd = [
                "ffmpeg", "-y", "-i", input_path, 
                "-c:a", "libmp3lame", "-b:a", bitrate, 
                output_path
            ]
            
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_path):
                compressed_size = os.path.getsize(output_path)
                print(f"壓縮後檔案大小: {compressed_size / (1024*1024):.2f} MB")
                
                # 檢查是否達到目標大小
                if compressed_size < max_size_bytes:
                    print(f"成功壓縮檔案至 {max_size_mb}MB 以下")
                    return output_path
                else:
                    print(f"檔案仍然太大，嘗試更低的比特率...")
            else:
                print("壓縮失敗，無法創建輸出檔案")
                break
                
        except Exception as e:
            print(f"壓縮過程中出錯: {e}")
            break
    
    print("無法將檔案壓縮至所需大小，繼續使用原始檔案...")
    return input_path

# Method 1: Using OpenAI API
def transcribe_with_openai_api(audio_file_path):
    import openai
    
    # Use the API key from config
    openai.api_key = config.OPENAI_API_KEY
    
    # 檢查檔案大小 (OpenAI API 限制為 25MB)
    file_size = os.path.getsize(audio_file_path)
    if file_size > 25 * 1024 * 1024:  # 25MB 轉換為位元組
        print(f"檔案大小 ({file_size / (1024*1024):.2f} MB) 超過 API 限制 (25MB)")
        print("正在壓縮檔案...")
        compressed_file_path = compress_audio_file(audio_file_path)
        
        if compressed_file_path != audio_file_path:
            # 再次檢查大小確保符合要求
            comp_size = os.path.getsize(compressed_file_path)
            if comp_size > 25 * 1024 * 1024:
                print(f"壓縮後檔案仍然過大 ({comp_size / (1024*1024):.2f} MB)，改用本地 Whisper 模型...")
                if os.path.exists(compressed_file_path) and compressed_file_path != audio_file_path:
                    os.remove(compressed_file_path)
                return transcribe_with_whisper_local(audio_file_path)
                
            try:
                print(f"使用壓縮檔案進行轉錄: {compressed_file_path}")
                
                with open(compressed_file_path, "rb") as audio_file:
                    transcript = openai.Audio.transcribe(
                        model="whisper-1",
                        file=audio_file
                    )
                
                # 清理臨時檔案
                if os.path.exists(compressed_file_path) and compressed_file_path != audio_file_path:
                    os.remove(compressed_file_path)
                return transcript["text"]
            except Exception as e:
                print(f"使用壓縮檔案時出錯: {e}")
                print("改用本地 Whisper 模型...")
                # 清理臨時檔案
                if os.path.exists(compressed_file_path) and compressed_file_path != audio_file_path:
                    os.remove(compressed_file_path)
                return transcribe_with_whisper_local(audio_file_path)
    
    print(f"轉錄檔案: {audio_file_path}")
    with open(audio_file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file
        )
    
    return transcript["text"]

# Method 2: Using local whisper package
def transcribe_with_whisper_local(audio_file_path):
    try:
        # 確保使用正確的 Whisper 套件
        try:
            # 先嘗試使用 OpenAI 官方的 whisper 套件
            import whisper as openai_whisper
            print(f"載入 OpenAI Whisper 模型...")
            model = openai_whisper.load_model("large")  # Options: tiny, base, small, medium, large
        except (ImportError, AttributeError):
            # 如果出錯，可能是未安裝或安裝了錯誤的 whisper 套件
            print("未找到正確的 OpenAI Whisper 套件，請確保已安裝 'openai-whisper'")
            print("嘗試安裝: pip install openai-whisper")
            raise ImportError("請安裝正確的 Whisper 套件: pip install openai-whisper")
        
        print(f"轉錄檔案: {audio_file_path}")
        result = model.transcribe(audio_file_path)
        
        return result["text"]
    except Exception as e:
        print(f"本地 Whisper 轉錄失敗: {e}")
        return f"轉錄失敗: {str(e)}"

if __name__ == "__main__":
    # 定義要處理的音頻文件列表
    audio_files = [
        r"C:\Users\deehu\Downloads\20250730_audio.m4a",
    ]
    
    successful_transcriptions = 0
    failed_transcriptions = 0
    
    for i, audio_file_path in enumerate(audio_files, 1):
        print(f"\n{'='*50}")
        print(f"處理第 {i}/{len(audio_files)} 個文件: {os.path.basename(audio_file_path)}")
        print(f"{'='*50}")
        
        # Check if file exists
        if not os.path.exists(audio_file_path):
            print(f"錯誤: 找不到檔案 {audio_file_path}")
            failed_transcriptions += 1
            continue
        
        try:
            # Option 1: Using OpenAI API (with API key from config)
            text = transcribe_with_openai_api(audio_file_path)
            
            # Option 2: Using local whisper package (runs offline)
            # text = transcribe_with_whisper_local(audio_file_path)
            
            print(f"\n轉錄結果 ({os.path.basename(audio_file_path)}):")
            print(text)
            
            # Save the result to a text file
            output_file = os.path.splitext(audio_file_path)[0] + "_transcript.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"轉錄文本已儲存到: {output_file}")
            
            successful_transcriptions += 1
            
        except Exception as e:
            print(f"轉錄過程中出錯: {e}")
            failed_transcriptions += 1
            
    # 顯示處理結果摘要
    print(f"\n{'='*50}")
    print("批量處理完成摘要:")
    print(f"成功轉錄: {successful_transcriptions} 個文件")
    print(f"失敗: {failed_transcriptions} 個文件")
    print(f"{'='*50}")
    
    if failed_transcriptions > 0:
        print("\n如果您需要安裝相關套件:")
        print("OpenAI API 方法: pip install openai")
        print("本地 Whisper 方法: pip install openai-whisper")
        print("音訊壓縮需要: ffmpeg (https://ffmpeg.org/download.html)")