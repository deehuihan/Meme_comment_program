import pandas as pd
import openai

# 設定 OpenAI API 金鑰
openai.api_key = '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'

def filter_with_chatgpt(title, content):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": '''
            政治是政府、政黨、集團或個人在國家事務方面的活動。治理國家施行的措施。請根據以下帖文敘述和新聞內容進行一步步思考，並在回答前提供思考過程，最終給出「政治」或「非政治」的回答。            
            帖文敘述:
            新聞內容:
            思考: 
            回答: 
            '''},
            {"role": "user", "content": f"帖文敘述:{title}" + "\n\n" + f"新聞內容:{content}"}
        ],
        response_format={
            "type": "text"
        },
        n=1,
        max_tokens=2048,
        temperature=0,
        top_p=0.01
    )
    return response['choices'][0]['message']['content'].strip()

def parse_response(response):
    think = ""
    answer = ""
    lines = response.split("\n")
    for line in lines:
        if line.startswith("思考:"):
            think = line.replace("思考:", "").strip()
        elif line.startswith("回答:"):
            answer = line.replace("回答:", "").strip()
    return think, answer

def main():
    while True:
        print("執行中...")
        # 讀取 Excel 檔案
        df = pd.read_excel('data_1.xlsx')
        print("[INFO] 已讀取 data_1.xlsx")
        # 提取 title 底下的 column 資料
        Titles = df['Title'].tolist()
        Contents = df['Contents'].tolist()
        print("[INFO] 已提取 Title 和 Contents")
        if not Titles or not Contents:
            print("[INFO] 所有資料已處理完畢")
            break
        # 過濾資料並收集結果
        print("執行 title 和 contents 過濾中...")
        for title, content in zip(Titles, Contents):
            try:
                result = filter_with_chatgpt(title, content)
                second_result = filter_with_chatgpt(title, content)
                third_result = filter_with_chatgpt(title, content)
                
                # 解析結果
                result_think, result_answer = parse_response(result)
                second_result_think, second_result_answer = parse_response(second_result)
                third_result_think, third_result_answer = parse_response(third_result)

                
                # 將結果追加到另一個 Excel 檔案中
                filtered_df = pd.DataFrame({
                    '帖文敘述': [title],
                    '新聞內容': [content],
                    '思考_1': [result_think],
                    '回答_1': [result_answer],
                    '思考_2': [second_result_think],
                    '回答_2': [second_result_answer],
                    '思考_3': [third_result_think],
                    '回答_3': [third_result_answer]
                })                 
                with pd.ExcelWriter('chatgpt_filter_1.xlsx', mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    if 'Sheet1' in writer.sheets:
                        startrow = writer.sheets['Sheet1'].max_row
                        header = startrow == 1
                    else:
                        startrow = 0
                        header = True
                    filtered_df.to_excel(writer, index=False, header=header, startrow=startrow)
                print(f"[INFO] 已處理並儲存:{title}")# 移除已處理的資料
                df = df.iloc[1:]
                df.to_excel('data_1.xlsx', index=False)
            except Exception as e:
                print(f"[ERROR] 處理 {title} 時發生錯誤: {e}")


if __name__ == "__main__":
    main()