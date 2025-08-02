import pandas as pd
import openai

# 設定 OpenAI API 金鑰
openai.api_key = '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'

def filter_with_chatgpt(comment):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": '''
            人身攻擊定義： 指在溝通對話時，攻擊、批評對方個人因素相關之斷言或質疑；如人格、動機、態度、地位、階級、處境或是外貌等。若進一步以此作為論證之基礎，而作出與前提不相關的結論，則是訴諸人身的謬誤。請根據以下留言內容進行一步步思考，並在回答前提供思考過程，並最終給出「人身攻擊」或「非人身攻擊」的回答
            留言: ['東森新聞\n希望大S也不要太過自責先離開...媽媽一定會在天上保護孩子\n完整版看這裡\nhttps://www.youtube.com/watch?v=9JJ8hfUeV_s', 'Wei Ying\n', 'Alex Lee\n都拾多天啦，放過往生者可以嗎？', '許政名\n', 'Ket Ping Yap\n煩人的東西', '王奕鑫\n一路走好']
            思考: 在這些留言中，主要的內容是對於某個事件的反應，並沒有針對個人進行詆毀或攻擊。留言中提到的「放過往生者」和「煩人的東西」雖然表達了某種情緒，但並不針對特定個人進行人身攻擊。整體來看，這些留言更多是對事件的評論或情感表達，而不是對某個人的名譽進行攻擊。
            回答: 非人身攻擊
            
            留言:['東森新聞\n也瘦太快了~', 'Shan Laio\n初階版開始', 'Pao Hsu\n拖鞋哪買', '嚴洪.\n連結在哪裡', '郭喬妮\n黃嬌嬌 團了', 'Lu Lu\nChen Wen Wen', '楊肯肯\n何淑渟要不要', 'Roxanne Carruthers\n我有志龍同款\n一定要跟上節奏', '張維庭\nKaren Chan要跟風嗎？', 'Bao Tao\n男定女、人妖？']
            思考: 在這些留言中，大部分是表達對某個現象或情況的看法，沒有針對某個人進行名譽攻擊。然而，最後一條留言「男定女、人妖？」明顯在提問和質疑某個人的性別或身份，這樣的問題語氣可能會造成對某個個人或群體的冒犯，因此屬於人身攻擊的範疇。
            回答: 人身攻擊
            
            留言:['東森新聞\n大家怎麼看？\nhttps://news.ebc.net.tw/news/sport/470658', '張誌良\n台中人對不起昌哥', 'Yves Cheng\n是政府對你的用心栽培以及民主力量的守護才能有如今的你\n去美國也別忘記飲水思源\n護民主，挺台灣！', '曾宗欽\n成名只是一時.實力才是恆久，若它日不在有本事，回台灣棒球隊.還是會被收留的。', 'Rick Yang\n讓大聯盟看到家正婦的努力！', 'Elsa Ku\n這台狗理事', '林修旭\n提案罷免啦，怎麼可以這麼幫家正。\n蔡其昌', 'Archie Peng\n莫忘中華', '邱錦台\n']	
            思考: 在這些留言中，有些是對某個事件或人物的評論，有些則是表達支持或反對的意見。特別注意到「Elsa Ku」的留言「這台狗理事」，這句話明顯帶有貶義，對某個人進行了侮辱性描述，這屬於人身攻擊的範疇。其他留言則主要是表達觀點或情感，並不涉及對個人名譽的直接攻擊。
            回答: 人身攻擊
            '''},
            {"role": "user", "content": f"留言:{comment}"}
        ],
        response_format={
            "type": "text"
        },
        n=1,
        max_tokens=512,
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
        Categories = df['Category'].tolist()
        Titles = df['Title'].tolist()
        Comments = df['Comments'].tolist()
        print("[INFO] 已提取 Categories, Title 和 Comments")
        if not Comments:
            print("[INFO] 所有資料已處理完畢")
            break
        # 過濾資料並收集結果
        print("執行 Comments 過濾中...")
        for category, title, Comment in zip(Categories, Titles, Comments):            
            try:
                result = filter_with_chatgpt(Comment)
                second_result = filter_with_chatgpt(Comment)
                third_result = filter_with_chatgpt(Comment)
                
                # 解析結果
                result_think, result_answer = parse_response(result)
                second_result_think, second_result_answer = parse_response(second_result)
                third_result_think, third_result_answer = parse_response(third_result)

                
                # 將結果追加到另一個 Excel 檔案中
                filtered_df = pd.DataFrame({
                    '新聞平台': [category],
                    '帖文敘述': [title],
                    '留言思考_1': [result_think],
                    '留言回答_1': [result_answer],
                    '留言思考_2': [second_result_think],
                    '留言回答_2': [second_result_answer],
                    '留言思考_3': [third_result_think],
                    '留言回答_3': [third_result_answer]
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