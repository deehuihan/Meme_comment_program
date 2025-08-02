import zipfile
import json
import pandas as pd
import os
from pathlib import Path

def zip_json_to_excel(zip_path, output_excel_path=None):
    """
    從 ZIP 檔案中提取所有 JSON 檔案，並按照範本格式合併為 Excel
    
    Args:
        zip_path (str): ZIP 檔案路徑
        output_excel_path (str, optional): 輸出 Excel 檔案路徑
    
    Returns:
        str: 生成的 Excel 檔案路徑
    """
    
    # 定義欄位順序（與你的範本一致）
    headers = [
        "user_id", "file_name", "unix_start_time", "unix_start_time_ms", "unix_end_time", 
        "unix_end_time_ms", "age", "gender", "user_agent", "user_ip", "status", 
        "email_provided", "attention_passed", "start_time_readable", "end_time_readable", 
        "total_labels", "emotion_summary", "email", "participation", "total_responses", 
        "session_start_unix", "session_status", "last_updated_unix", "image_order", 
        "completion_status", "timestamps_unix", "timestamps_unix_ms", "duration_stats_ms", 
        "filename_updated_unix", "original_filename", "completion_status_in_filename", 
        "resp_image_path", "resp_label", "resp_response_time", "resp_timestamp_unix", 
        "resp_timestamp_unix_ms", "resp_timestamp_readable", "resp_normalized_name", 
        "resp_meme_name", "resp_post_id", "resp_english_label", "resp_response_time_ms", 
        "game_duration"
    ]
    
    # 設定輸出檔案名稱
    if output_excel_path is None:
        zip_name = Path(zip_path).stem
        output_excel_path = f"{zip_name}_combined.xlsx"
    
    all_records = []
    processed_files = 0
    total_responses = 0
    
    print(f"開始處理 ZIP 檔案: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 獲取所有檔案列表
            file_list = zip_ref.namelist()
            
            # 篩選 JSON 檔案
            json_files = [f for f in file_list 
                         if f.lower().endswith('.json') 
                         and not f.startswith('__MACOSX/')
                         and not f.startswith('.')]
            
            if not json_files:
                print("❌ ZIP 檔案中沒有找到 JSON 檔案")
                return None
            
            print(f"找到 {len(json_files)} 個 JSON 檔案")
            
            # 處理每個 JSON 檔案
            for json_file in json_files:
                try:
                    print(f"處理: {json_file}")
                    
                    # 從 ZIP 中讀取 JSON 檔案
                    with zip_ref.open(json_file) as f:
                        json_content = f.read().decode('utf-8')
                        data = json.loads(json_content)
                    
                    # 處理這個 JSON 檔案的數據 - 確保 responses 展開
                    records = process_single_json(data, json_file, headers)
                    all_records.extend(records)
                    
                    processed_files += 1
                    
                    # 詳細統計
                    if records:
                        response_count = len([r for r in records if r.get('resp_image_path')])
                        total_responses += response_count
                        
                        if response_count > 0:
                            print(f"  ✓ 處理完成 - {len(records)} 筆記錄 (展開了 {response_count} 個 responses)")
                        else:
                            print(f"  ✓ 處理完成 - {len(records)} 筆記錄 (無 responses)")
                        
                        # 驗證第一筆記錄是否有 resp_ 資料
                        first_record = records[0]
                        if first_record.get('resp_image_path'):
                            print(f"    第一個 response: {first_record.get('resp_image_path')} -> {first_record.get('resp_label')}")
                    else:
                        print(f"  ✓ 處理完成 - 無有效數據")
                
                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON 解析錯誤: {e}")
                    continue
                except Exception as e:
                    print(f"  ❌ 處理錯誤: {e}")
                    continue
        
        if not all_records:
            print("❌ 沒有找到有效的數據")
            return None
        
        # 創建 DataFrame - 確保欄位順序正確
        print(f"\n建立 Excel 檔案...")
        print(f"總記錄數: {len(all_records)}")
        print(f"欄位數量: {len(headers)}")
        
        # 驗證資料結構
        if all_records:
            sample_record = all_records[0]
            resp_fields = [k for k in sample_record.keys() if k.startswith('resp_')]
            print(f"範例記錄的 resp_ 欄位: {resp_fields}")
            
            if sample_record.get('resp_image_path'):
                print(f"範例記錄的 resp_image_path: {sample_record.get('resp_image_path')}")
        
        df = pd.DataFrame(all_records, columns=headers)
        
        # 輸出到 Excel
        df.to_excel(output_excel_path, sheet_name='Combined_Data', index=False, engine='openpyxl')
        
        # 統計信息 - 詳細驗證
        unique_users = df['user_id'].nunique()
        records_with_responses = len(df[df['resp_image_path'].notna()])
        records_without_responses = len(df[df['resp_image_path'].isna()])
        
        print(f"\n🎉 處理完成！")
        print(f"📁 輸出檔案: {output_excel_path}")
        print(f"📊 統計資訊:")
        print(f"   - 處理的 JSON 檔案: {processed_files}")
        print(f"   - 總記錄數: {len(all_records)}")
        print(f"   - 唯一用戶數: {unique_users}")
        print(f"   - 有 responses 的記錄: {records_with_responses}")
        print(f"   - 無 responses 的記錄: {records_without_responses}")
        print(f"   - 總 responses 數量: {total_responses}")
        print(f"   - Excel 欄位數: {len(df.columns)}")
        
        # 驗證 resp_ 欄位
        resp_columns = [col for col in df.columns if col.startswith('resp_')]
        print(f"   - resp_ 欄位數量: {len(resp_columns)}")
        print(f"   - resp_ 欄位: {resp_columns}")
        
        # 檢查是否正確展開
        if records_with_responses > 0:
            print(f"✅ responses 已正確展開為 {records_with_responses} 筆記錄")
        else:
            print(f"⚠️  警告：沒有找到 responses 資料")
        
        return output_excel_path
        
    except zipfile.BadZipFile:
        print("❌ 無效的 ZIP 檔案")
        return None
    except FileNotFoundError:
        print(f"❌ 找不到檔案: {zip_path}")
        return None
    except Exception as e:
        print(f"❌ 未預期的錯誤: {e}")
        return None

def process_single_json(data, source_file, headers):
    """
    處理單個 JSON 檔案的數據 - 重點：展開所有 responses
    
    Args:
        data: JSON 數據
        source_file: 來源檔案名
        headers: 欄位列表
    
    Returns:
        List[dict]: 處理後的記錄列表（每個 response 一行）
    """
    records = []
    
    try:
        # 關鍵：必須展開 responses 陣列
        responses = data.get('responses', [])
        
        if responses and len(responses) > 0:
            print(f"    展開 {len(responses)} 個 responses")
            # 為每個 response 創建一行記錄
            for i, response in enumerate(responses):
                record = create_record_from_data(data, source_file, response)
                records.append(record)
                if i < 3:  # 只顯示前 3 個的詳細資訊
                    print(f"      Response {i+1}: {response.get('image_path', 'N/A')} -> {response.get('label', 'N/A')}")
        else:
            print(f"    無 responses，創建基本記錄")
            # 如果沒有 responses，創建一行基本記錄
            record = create_record_from_data(data, source_file, None)
            records.append(record)
    
    except Exception as e:
        print(f"    ⚠️  處理 {source_file} 時發生錯誤: {e}")
        # 創建一個最基本的錯誤記錄
        record = {header: None for header in headers}
        record['user_id'] = data.get('user_id', f"error_from_{Path(source_file).stem}")
        record['file_name'] = source_file
        records.append(record)
    
    return records

def create_record_from_data(data, source_file, response=None):
    """
    從 JSON 數據創建一條記錄
    
    Args:
        data: 完整的 JSON 數據
        source_file: 來源檔案名
        response: 單個 response 數據（可選）
    
    Returns:
        dict: 一行記錄
    """
    record = {}
    
    # 基本用戶資料
    record['user_id'] = data.get('user_id')
    record['file_name'] = data.get('file_name')
    record['unix_start_time'] = data.get('unix_start_time')
    record['unix_start_time_ms'] = data.get('unix_start_time_ms')
    record['unix_end_time'] = data.get('unix_end_time')
    record['unix_end_time_ms'] = data.get('unix_end_time_ms')
    record['age'] = data.get('age')
    record['gender'] = data.get('gender')
    record['user_agent'] = data.get('user_agent')
    record['user_ip'] = data.get('user_ip')
    record['status'] = data.get('status')
    record['email_provided'] = data.get('email_provided')
    record['attention_passed'] = data.get('attention_passed')
    record['start_time_readable'] = data.get('start_time_readable')
    record['end_time_readable'] = data.get('end_time_readable')
    record['total_labels'] = data.get('total_labels')
    
    # 複雜物件轉為字串
    record['emotion_summary'] = json.dumps(data.get('emotion_summary')) if data.get('emotion_summary') else None
    
    record['email'] = data.get('email')
    record['participation'] = data.get('participation')
    record['total_responses'] = data.get('total_responses')
    record['session_start_unix'] = data.get('session_start_unix')
    record['session_status'] = data.get('session_status')
    record['last_updated_unix'] = data.get('last_updated_unix')
    
    # 複雜物件轉為字串
    record['image_order'] = json.dumps(data.get('image_order')) if data.get('image_order') else None
    record['completion_status'] = json.dumps(data.get('completion_status')) if data.get('completion_status') else None
    record['timestamps_unix'] = json.dumps(data.get('timestamps_unix')) if data.get('timestamps_unix') else None
    record['timestamps_unix_ms'] = json.dumps(data.get('timestamps_unix_ms')) if data.get('timestamps_unix_ms') else None
    record['duration_stats_ms'] = json.dumps(data.get('duration_stats_ms')) if data.get('duration_stats_ms') else None
    
    record['filename_updated_unix'] = data.get('filename_updated_unix')
    record['original_filename'] = data.get('original_filename')
    record['completion_status_in_filename'] = data.get('completion_status_in_filename')
    
    # Response 相關欄位
    if response:
        record['resp_image_path'] = response.get('image_path')
        record['resp_label'] = response.get('label')
        record['resp_response_time'] = response.get('response_time')
        record['resp_timestamp_unix'] = response.get('timestamp_unix')
        record['resp_timestamp_unix_ms'] = response.get('timestamp_unix_ms')
        record['resp_timestamp_readable'] = response.get('timestamp_readable')
        record['resp_normalized_name'] = response.get('normalized_name')
        record['resp_meme_name'] = response.get('meme_name')
        record['resp_post_id'] = response.get('post_id')
        record['resp_english_label'] = response.get('english_label')
        record['resp_response_time_ms'] = response.get('response_time_ms')
    else:
        # 沒有 response 時設為 None
        record['resp_image_path'] = None
        record['resp_label'] = None
        record['resp_response_time'] = None
        record['resp_timestamp_unix'] = None
        record['resp_timestamp_unix_ms'] = None
        record['resp_timestamp_readable'] = None
        record['resp_normalized_name'] = None
        record['resp_meme_name'] = None
        record['resp_post_id'] = None
        record['resp_english_label'] = None
        record['resp_response_time_ms'] = None
    
    # 計算 game_duration（秒）
    duration_stats = data.get('duration_stats_ms')
    if duration_stats and duration_stats.get('game_duration_ms'):
        record['game_duration'] = duration_stats['game_duration_ms'] / 1000
    else:
        record['game_duration'] = None
    
    return record

def analyze_excel_file(excel_path):
    """
    分析生成的 Excel 檔案
    
    Args:
        excel_path (str): Excel 檔案路徑
    """
    try:
        df = pd.read_excel(excel_path)
        
        print(f"\n📈 Excel 檔案分析: {excel_path}")
        print(f"📊 基本統計:")
        print(f"   - 總行數: {len(df)}")
        print(f"   - 總欄位數: {len(df.columns)}")
        print(f"   - 唯一用戶數: {df['user_id'].nunique()}")
        
        # 情緒標籤統計
        emotion_counts = df['resp_english_label'].value_counts()
        if not emotion_counts.empty:
            print(f"\n😊 情緒標籤統計:")
            for emotion, count in emotion_counts.items():
                print(f"   - {emotion}: {count}")
        
        # 用戶狀態統計
        status_counts = df['status'].value_counts()
        print(f"\n👤 用戶狀態統計:")
        for status, count in status_counts.items():
            print(f"   - {status}: {count}")
        
        print(f"\n✅ 分析完成")
        
    except Exception as e:
        print(f"❌ 分析檔案時發生錯誤: {e}")

def main():
    """
    主程式
    """
    print("=== ZIP JSON 轉 Excel 工具 ===\n")
    
    # 取得 ZIP 檔案路徑
    zip_path = r"C:\Users\deehu\Desktop\Program\data_analysis\user.zip"
    
    if not os.path.exists(zip_path):
        print("❌ 檔案不存在，請檢查路徑")
        return
    
    # 取得輸出路徑（可選）
    output_path = input("請輸入輸出 Excel 檔案路徑（按 Enter 使用預設）: ").strip().strip('"\'')
    if not output_path:
        output_path = None
    
    # 執行轉換
    result = zip_json_to_excel(zip_path, output_path)
    
    if result:
        # 分析結果
        analyze_excel_file(result)
        print(f"\n🎉 轉換成功！檔案已儲存至: {result}")
    else:
        print("\n❌ 轉換失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()