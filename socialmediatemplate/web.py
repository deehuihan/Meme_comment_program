from flask import Flask, render_template, jsonify, request, url_for, send_from_directory, render_template_string
import os
import json
import openai
from config import config
import time
from datetime import datetime
from excel_manager import excel_manager
from comment_manager import CommentManager
import traceback

# 初始化評論管理器
comment_manager = CommentManager()
app = Flask(__name__)

# New API endpoint to expose configuration to frontend
@app.route('/api/config')
def api_config():
    return jsonify({
        "openai_api_key": config.OPENAI_API_KEY,
        "paths": {
            "emotion_folders": config.EMOTION_FOLDERS,
            "news_folder": config.NEWS_FOLDER
        }
    })

# API endpoint to check username availability
@app.route('/api/check-username', methods=['POST'])
def check_username():
    try:
        data = request.json
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'available': False, 'message': 'Username cannot be empty'}), 400
        
        # Simple username validation (you can enhance this)
        if len(username) < 3:
            return jsonify({'available': False, 'message': 'Username must be at least 3 characters long'}), 400
        
        # For simplicity, we'll assume all usernames are available
        # In a real application, you'd check against a database
        return jsonify({'available': True, 'message': 'Username is available'})
    
    except Exception as e:
        print(f"Error checking username: {e}")
        return jsonify({'available': False, 'message': 'Error checking username'}), 500

# API endpoint to register a new user
@app.route('/api/register-user', methods=['POST'])
def register_user():
    try:
        data = request.json
        username = data.get('username', '').strip()
        user_id = data.get('user_id', '').strip()
        
        if not username or not user_id:
            return jsonify({'success': False, 'message': 'Username and User ID are required'}), 400
        
        # Log the registration activity
        success = excel_manager.add_activity(user_id, 'registration', 'input', f'Username: {username}')
        
        if success:
            return jsonify({'success': True, 'message': 'User registered successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to register user'}), 500
    
    except Exception as e:
        print(f"Error registering user: {e}")
        return jsonify({'success': False, 'message': 'Error registering user'}), 500

# API endpoint to log user activity to Excel
@app.route('/api/log-activity', methods=['POST'])
def log_activity():
    try:
        data = request.json
        user_id = data.get('user_id')
        activity_type = data.get('activity_type', 'unknown')
        page = data.get('page', 'unknown')
        details = data.get('details', '')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        success = excel_manager.add_activity(user_id, activity_type, page, details)
        
        if success:
            return jsonify({'success': True, 'message': 'Activity logged successfully'})
        else:
            return jsonify({'error': 'Failed to log activity'}), 500
    except Exception as e:
        print(f"Error logging activity: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoint to get user activities from Excel
@app.route('/api/get-activities/<user_id>', methods=['GET'])
def get_user_activities(user_id):
    try:
        activities = excel_manager.get_user_activities(user_id)
        return jsonify({'activities': activities})
    except Exception as e:
        print(f"Error getting activities: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoint to get all data from Excel (for testing)
@app.route('/api/get-all-data', methods=['GET'])
def get_all_data():
    try:
        data = excel_manager.get_all_data()
        return jsonify({'data': data})
    except Exception as e:
        print(f"Error getting all data: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoint to get comments for a post
@app.route('/api/get-comment/<post_id>', methods=['GET'])
def get_comment(post_id):
    try:
        comment = comment_manager.get_comments_for_post(post_id)
        if comment:
            return jsonify({'comment': comment, 'post_id': post_id})
        else:
            return jsonify({'error': 'Comment not found'}), 404
    except Exception as e:
        print(f"Error getting comment: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoint to analyze comment and get meme recommendations
@app.route('/api/analyze-comment', methods=['POST'])
def analyze_comment():
    try:
        data = request.json
        comment = data.get('comment', '')
        user_id = data.get('user_id', '')
        post_id = data.get('post_id', '')
        
        if not comment:
            return jsonify({'error': 'Comment is required'}), 400
        
        # 分析評論並獲取推薦
        emotion_info, recommended_memes = comment_manager.analyze_comment_and_recommend(comment)
        
        if emotion_info is None:
            return jsonify({
                'is_personal_attack': False,
                'message': 'Comment does not constitute personal attack'
            })
        
        # 記錄到Excel的Sender_Actions表
        emotion_str = f"輕蔑:{emotion_info['contempt']:.3f}, 憤怒:{emotion_info['anger']:.3f}, 厭惡:{emotion_info['disgust']:.3f}"
        analysis_response = emotion_info.get('reasoning', '')
        
        # 轉換meme列表為字符串格式進行記錄
        meme_names_for_excel = [meme['meme_name'] for meme in recommended_memes]
        
        excel_manager.add_sender_action(
            user_id=user_id,
            post_id=post_id,
            original_comment=comment,
            emotion_analysis=emotion_str,
            recommended_memes=meme_names_for_excel,
            claude_response=analysis_response
        )
        
        return jsonify({
            'is_personal_attack': True,
            'emotion_analysis': emotion_info,
            'recommended_memes': recommended_memes,
            'claude_response': analysis_response
        })
        
    except Exception as e:
        print(f"Error analyzing comment: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoint to record meme selection
@app.route('/api/select-meme', methods=['POST'])
def select_meme():
    try:
        data = request.json
        user_id = data.get('user_id', '')
        post_id = data.get('post_id', '')
        chosen_meme = data.get('chosen_meme', '')
        
        # 更新Excel記錄中的chosen_meme字段
        # 這裡我們需要找到最近的記錄並更新
        # 為簡化，我們記錄一個新的活動
        excel_manager.add_user_entry(
            user_id=user_id,
            activity_type='meme_selected',
            page='sender',
            details=f'Selected meme: {chosen_meme} for post: {post_id}'
        )
        
        return jsonify({'success': True, 'message': 'Meme selection recorded'})
        
    except Exception as e:
        print(f"Error recording meme selection: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoint to get top recommended meme for receiver
@app.route('/api/get-top-meme/<post_id>', methods=['GET'])
def get_top_meme(post_id):
    try:
        comment = comment_manager.get_comments_for_post(post_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        top_meme = comment_manager.get_top_recommended_meme(comment)
        
        if top_meme:
            return jsonify({
                'post_id': post_id,
                'recommended_meme': top_meme,
                'original_comment': comment
            })
        else:
            return jsonify({'error': 'No recommendation available'}), 404
            
    except Exception as e:
        print(f"Error getting top meme: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoint to record receiver meme interaction
@app.route('/api/receiver-meme-interaction', methods=['POST'])
def receiver_meme_interaction():
    try:
        data = request.json
        user_id = data.get('user_id', '')
        post_id = data.get('post_id', '')
        recommended_meme = data.get('recommended_meme', '')
        clicked = data.get('clicked', False)
        original_comment_viewed = data.get('original_comment_viewed', '')
        
        # 記錄到Excel的Receiver_Actions表
        excel_manager.add_receiver_action(
            user_id=user_id,
            post_id=post_id,
            recommended_meme=recommended_meme,
            clicked=clicked,
            original_comment_viewed=original_comment_viewed
        )
        
        return jsonify({'success': True, 'message': 'Receiver interaction recorded'})
        
    except Exception as e:
        print(f"Error recording receiver interaction: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoint to get recommended meme for a specific comment
@app.route('/api/get-recommended-meme', methods=['POST'])
def get_recommended_meme():
    try:
        data = request.json
        comment_text = data.get('comment_text', '')
        
        if not comment_text:
            return jsonify({'error': 'Comment text is required'}), 400
        
        # Get the top recommended meme for this comment
        meme_info = comment_manager.get_top_recommended_meme(comment_text)
        
        if meme_info:
            return jsonify({
                "status": "success",
                "meme_filename": meme_info['filename'],
                "similarity_score": meme_info['similarity_score']
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No meme found"
            }), 404
    except Exception as e:
        print(f"Error getting recommended meme: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoint to submit meme survey data
@app.route('/api/submit-meme-survey', methods=['POST'])
def submit_meme_survey():
    try:
        data = request.json
        
        # Extract survey data
        post_id = data.get('postId')
        selected_meme = data.get('selectedMeme')
        responses = data.get('responses', {})
        timestamp = datetime.now().isoformat()
        
        # Validate required fields
        if not post_id or not selected_meme or not responses:
            return jsonify({
                "status": "error", 
                "message": "Missing required fields: postId, selectedMeme, or responses"
            }), 400
        
        # Validate that we have all 5 questions
        required_questions = ['q1_1', 'q1_2', 'q1_3', 'q1_4', 'q2_1']
        for question in required_questions:
            if question not in responses:
                return jsonify({
                    "status": "error", 
                    "message": f"Missing response for question: {question}"
                }), 400
            
            # Validate score range (1-7)
            score = responses[question]
            if not isinstance(score, int) or score < 1 or score > 7:
                return jsonify({
                    "status": "error", 
                    "message": f"Invalid score for {question}: must be integer between 1-7"
                }), 400
        
        # Create survey record
        survey_record = {
            'timestamp': timestamp,
            'post_id': post_id,
            'selected_meme': selected_meme,
            'q1_1_emotion_replacement': responses['q1_1'],
            'q1_2_aggressiveness': responses['q1_2'],
            'q1_3_appropriateness': responses['q1_3'],
            'q1_4_satisfaction': responses['q1_4'],
            'q2_1_emotion_replacement_duplicate': responses['q2_1']
        }
        
        # Log to Excel (you can extend this to use excel_manager if needed)
        print(f"Survey submitted: {survey_record}")
        
        # For now, just log to console. You can enhance this to save to Excel/database
        try:
            # Save to a simple JSON file for now
            survey_file = 'meme_survey_data.json'
            surveys = []
            
            if os.path.exists(survey_file):
                with open(survey_file, 'r', encoding='utf-8') as f:
                    surveys = json.load(f)
            
            surveys.append(survey_record)
            
            with open(survey_file, 'w', encoding='utf-8') as f:
                json.dump(surveys, f, ensure_ascii=False, indent=2)
                
            print(f"Survey data saved to {survey_file}")
            
        except Exception as save_error:
            print(f"Error saving survey data: {save_error}")
            # Continue anyway, don't fail the request
        
        return jsonify({
            "status": "success",
            "message": "Survey submitted successfully",
            "survey_id": len(surveys) if 'surveys' in locals() else None
        })
        
    except Exception as e:
        print(f"Error submitting meme survey: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoint to submit receiver (observer) survey data
@app.route('/api/submit-receiver-survey', methods=['POST'])
def submit_receiver_survey():
    try:
        data = request.json
        
        # Extract survey data
        post_id = data.get('postId')
        user_type = data.get('userType', 'receiver')
        responses = data.get('responses', {})
        timestamp = datetime.now().isoformat()
        
        # Validate required fields
        if not post_id or not responses:
            return jsonify({
                "status": "error", 
                "message": "Missing required fields: postId or responses"
            }), 400
        
        # Validate that we have all 4 questions for receiver
        required_questions = ['q1_1', 'q1_2', 'q1_3', 'q1_4']
        for question in required_questions:
            if question not in responses:
                return jsonify({
                    "status": "error", 
                    "message": f"Missing response for question: {question}"
                }), 400
            
            # Validate score range (1-7)
            score = responses[question]
            if not isinstance(score, int) or score < 1 or score > 7:
                return jsonify({
                    "status": "error", 
                    "message": f"Invalid score for {question}: must be integer between 1-7"
                }), 400
        
        # Create receiver survey record
        receiver_survey_record = {
            'timestamp': timestamp,
            'post_id': post_id,
            'user_type': user_type,
            'q1_1_emotion_replacement': responses['q1_1'],
            'q1_2_aggressiveness': responses['q1_2'],
            'q1_3_appropriateness': responses['q1_3'],
            'q1_4_satisfaction': responses['q1_4']
        }
        
        # Log to console
        print(f"Receiver survey submitted: {receiver_survey_record}")
        
        # Save to JSON file
        try:
            survey_file = 'receiver_survey_data.json'
            surveys = []
            
            if os.path.exists(survey_file):
                with open(survey_file, 'r', encoding='utf-8') as f:
                    surveys = json.load(f)
            
            surveys.append(receiver_survey_record)
            
            with open(survey_file, 'w', encoding='utf-8') as f:
                json.dump(surveys, f, ensure_ascii=False, indent=2)
                
            print(f"Receiver survey data saved to {survey_file}")
            
        except Exception as save_error:
            print(f"Error saving receiver survey data: {save_error}")
            # Continue anyway, don't fail the request
        
        return jsonify({
            "status": "success",
            "message": "Receiver survey submitted successfully",
            "survey_id": len(surveys) if 'surveys' in locals() else None
        })
        
    except Exception as e:
        print(f"Error submitting receiver survey: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoint to get random posts for display
@app.route('/api/get-random-posts/<int:count>', methods=['GET'])
def get_random_posts(count):
    try:
        posts = comment_manager.get_random_posts(count)
        return jsonify({'posts': posts})
    except Exception as e:
        print(f"Error getting random posts: {e}")
        return jsonify({'error': str(e)}), 500

# Update the function to use Config EMOTION_FOLDERS
def ensure_emotion_folders():
    emotion_folders = config.EMOTION_FOLDERS
    for emotion in emotion_folders:
        folder_path = os.path.join(app.static_folder, emotion)
        if not os.path.exists(folder_path):
            print(f"創建情緒資料夾 '{folder_path}'")
            os.makedirs(folder_path, exist_ok=True)

def setup_folders():
    ensure_emotion_folders()
    # Ensure news folder exists
    news_folder = os.path.join(app.static_folder, config.NEWS_FOLDER)
    if not os.path.exists(news_folder):
        print(f"創建新聞資料夾 '{news_folder}'")
        os.makedirs(news_folder, exist_ok=True)

# Run setup at import time
setup_folders()

def get_news_files_for_page(page_type):
    """
    根據頁面類型獲取相應的新聞檔案
    page_type: 'sender' 或 'receiver'
    sender: _1, _2 檔案
    receiver: _3, _4 檔案
    """
    news_folder = os.path.join(app.static_folder, config.NEWS_FOLDER)
    all_news_files = []
    
    if not os.path.exists(news_folder):
        print(f"News folder '{news_folder}' does not exist")
        os.makedirs(news_folder, exist_ok=True)
        return []
    
    # 遍歷所有子資料夾
    for subfolder in ['High_Intentional', 'High_Unintentional', 'Low_Intentional', 'Low_Unintentional']:
        subfolder_path = os.path.join(news_folder, subfolder)
        if os.path.exists(subfolder_path):
            files = [f for f in os.listdir(subfolder_path) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            
            # 根據頁面類型篩選檔案
            if page_type == 'sender':
                # 選擇 _1 和 _2 檔案
                filtered_files = [f for f in files if f.endswith('_1.png') or f.endswith('_2.png')]
            elif page_type == 'receiver':
                # 選擇 _3 和 _4 檔案
                filtered_files = [f for f in files if f.endswith('_3.png') or f.endswith('_4.png')]
            else:
                filtered_files = files
            
            # 添加子資料夾路徑
            for file in filtered_files:
                all_news_files.append(f"{subfolder}/{file}")
    
    # 排序確保一致的顯示順序
    all_news_files.sort()
    return all_news_files

@app.route('/')
def input_page():
    # Serve the input page as the entry point
    return render_template('input.html')

@app.route('/index')
def index():
    # Home page now serves as the selection screen after login
    return render_template('index.html')

# 添加一個測試路由來診斷問題
@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/test-api')
def test_api():
    return render_template('test_api.html')

# Data viewer page
@app.route('/data-viewer')
def data_viewer():
    return render_template('data_viewer.html')

@app.route('/debug_nav')
def debug_nav():
    """調試導航頁面"""
    return render_template('debug_nav.html')

@app.route('/simple_test')
def simple_test():
    """簡化測試頁面"""
    return render_template('simple_test.html')

@app.route('/test_nav')
def test_nav():
    """測試導航頁面"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>測試導航</title>
    <style>
        .test-button {
            padding: 20px;
            margin: 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .test-button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h1>Flask 導航測試頁面</h1>
    
    <button class="test-button" onclick="testSender()">
        測試發送者頁面 (onclick)
    </button>
    
    <button class="test-button" id="testSender2">
        測試發送者頁面 (addEventListener)
    </button>
    
    <button class="test-button" onclick="testReceiver()">
        測試觀察者頁面 (onclick)
    </button>
    
    <button class="test-button" onclick="testIndex()">
        返回主頁
    </button>
    
    <div id="debug"></div>

    <script>
        function testSender() {
            console.log('onclick: 導航到發送者頁面');
            window.location.href = '/sender';
        }
        
        function testReceiver() {
            console.log('onclick: 導航到觀察者頁面');
            window.location.href = '/receiver';
        }
        
        function testIndex() {
            console.log('onclick: 返回主頁');
            window.location.href = '/';
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded');
            
            const testSender2 = document.getElementById('testSender2');
            const debug = document.getElementById('debug');
            
            debug.innerHTML += '<p>找到按鈕: testSender2=' + (testSender2 ? 'Yes' : 'No') + '</p>';
            
            if (testSender2) {
                testSender2.addEventListener('click', function() {
                    console.log('addEventListener: 發送者按鈕被點擊');
                    debug.innerHTML += '<p>發送者按鈕被點擊 (addEventListener) - 正在導航...</p>';
                    window.location.href = '/sender';
                });
            }
        });
    </script>
</body>
</html>
    ''')

@app.route('/receiver')
def receiver():
    # 使用CommentManager獲取觀察者頁面的帖文數據
    from comment_manager import CommentManager
    comment_manager = CommentManager()
    posts_data = comment_manager.get_news_posts_for_page('receiver')
    
    return render_template('receiver.html', posts_data=posts_data)

@app.route('/sender')
def sender():
    # 使用CommentManager獲取傳送者頁面的帖文數據
    from comment_manager import CommentManager
    comment_manager = CommentManager()
    posts_data = comment_manager.get_news_posts_for_page('sender')
    
    return render_template('sender.html', posts_data=posts_data)

@app.route('/api/detect-personal-attack', methods=['POST'])
def detect_personal_attack():
    try:
        openai.api_key = config.OPENAI_API_KEY
        
        comment = request.json.get('comment', '')
        input_style = request.json.get('input_style', 'text')
        
        # Get user ID and page type (sender or receiver)
        user_id = request.json.get('user_id', 'anonymous')
        page_type = request.json.get('page_type', 'unknown')  # 'sender' or 'receiver'
        
        if not comment:
            return jsonify({"error": "留言內容不能為空"}), 400
            
        print(f"正在檢測留言: {comment[:30]}...")
        
        is_attack, attack_thinking, answer, result = detect_attack_content(comment)
        
        if not is_attack:
            response_data = {
                "is_attack": False,
                "attack_thinking": attack_thinking,
                "answer": answer,
                "emotion": "",
                "emotion_thinking": "",
            }
        else:
            emotion, emotion_thinking = classify_emotion(comment)
            
            if emotion_thinking and (
                "思考:" in emotion_thinking or 
                "回答:" in emotion_thinking
            ):
                print("檢測到情緒思考包含攻擊檢測格式標記，將清理掉這些標記")
                emotion_thinking = emotion_thinking.replace("思考:", "").replace("回答:", "").strip()
            
            if not emotion_thinking or emotion_thinking == attack_thinking:
                print("情緒思考為空或與攻擊思考相同，重新進行情緒分析")
                emotion, new_emotion_thinking = classify_emotion(comment)
                if new_emotion_thinking and new_emotion_thinking != attack_thinking:
                    emotion_thinking = new_emotion_thinking
            
            response_data = {
                "is_attack": is_attack,
                "attack_thinking": attack_thinking,
                "answer": answer,
                "emotion": emotion,
                "emotion_thinking": emotion_thinking,
            }
        
        # Add metadata for meme comments if provided
        if input_style == 'meme' and 'meme_src' in request.json:
            response_data['meme_src'] = request.json.get('meme_src')
            response_data['meme_filename'] = request.json.get('meme_filename')
        
        # Note: Firebase recording removed - only using Excel logging now
        print(f"檢測結果: {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"檢測人身攻擊時發生錯誤: {str(e)}")
        return jsonify({
            "error": str(e), 
            "details": error_details,
            "is_attack": False,
            "attack_thinking": "檢測過程中發生錯誤",
            "answer": "非人身攻擊 (檢測失敗)",
            "emotion": "default",
            "emotion_thinking": ""
        }), 500

def detect_attack_content(comment):
    try:           
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": '''
                人身攻擊指對別人的名譽等進行詆毀攻擊。請根據以下留言內容進行一步步思考，並在回答前提供思考過程，最終給出「人身攻擊」或「非人身攻擊」的回答。
                
                留言:
                思考: 
                回答: 
                '''},
                {"role": "user", "content": (f'留言:{comment}')}
            ],
            temperature=0,
            top_p=0.01,
            max_tokens=256
        )
        
        result = response['choices'][0]['message']['content'].strip()
        print(f"人身攻擊檢測結果: {result[:100]}...")
        
        attack_thinking = ""
        answer = ""
        lines = result.split("\n")
        for line in lines:
            if line.startswith("思考:"):
                attack_thinking = line.replace("思考:", "").strip()
            elif line.startswith("回答:"):
                answer = line.replace("回答:", "").strip()
        
        is_attack = "人身攻擊" in answer and "非人身攻擊" not in answer
        
        return is_attack, attack_thinking, answer, result
        
    except Exception as openai_error:
        print(f"OpenAI API 錯誤 (人身攻擊檢測): {str(openai_error)}")
        offensive_words = ["白癡", "笨蛋", "智障", "廢物", "垃圾", "白目", "腦殘"]
        is_attack = any(word in comment for word in offensive_words)
        
        if is_attack:
            result = "思考: 留言中包含侮辱性詞彙。\n回答: 人身攻擊"
            attack_thinking = "留言中包含侮辱性詞彙。"
            answer = "人身攻擊"
        else:
            result = "思考: 無法使用AI檢測，但未發現明顯侮辱性詞彙。\n回答: 非人身攻擊"
            attack_thinking = "無法使用AI檢測，但未發現明顯侮辱性詞彙。"
            answer = "非人身攻擊"
        
        return is_attack, attack_thinking, answer, result

def classify_emotion(comment):
    try:
        # Update the emotion prompt to explicitly request a specific format
        emotion_prompt = f"""
        你是情緒分析專家。請分析留言中表達的主要情緒類型，並選擇以下三種之一：
        - 輕蔑(contempt)：表現為看不起、藐視他人
        - 憤怒(anger)：表現為生氣、發怒、激烈的負面情緒
        - 厭惡(disgust)：表現為極度的反感或不喜歡
        
        請按照以下固定格式提供你的分析：
        
        分析理由：[在此提供詳細分析]
        情緒結論：[在此提供最終情緒分類，只用 contempt、anger 或 disgust 其中一個]
        
        留言: [用戶留言]
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": emotion_prompt},
                {"role": "user", "content": (f'留言：{comment}')}
            ],
            temperature=0,
            top_p=0.01,
            max_tokens=512
        )
        
        emotion_result = response['choices'][0]['message']['content'].strip()
        print(f"情緒分類結果: {emotion_result}")
        
        emotion_thinking = ""
        emotion_type = ""
        
        if "分析理由：" in emotion_result and "情緒結論：" in emotion_result:
            parts = emotion_result.split("情緒結論：")
            if len(parts) >= 2:
                emotion_thinking = parts[0].replace("分析理由：", "").strip()
                emotion_type = parts[1].strip()
                print("成功以新格式解析情緒分析結果")
        else:
            lines = emotion_result.split('\n')
            for i, line in enumerate(lines):
                if "分析理由" in line.lower() or "理由" in line.lower():
                    emotion_thinking = ' '.join(lines[i+1:])
                elif "情緒結論" in line.lower() or "結論" in line.lower() or "情緒類別" in line.lower():
                    emotion_type = line.split("：")[-1].strip() if "：" in line else line.strip()
            
            if not emotion_thinking or not emotion_type:
                print("無法以標準格式解析，使用備用解析方法")
                if "憤怒" in emotion_result or "anger" in emotion_result:
                    emotion_type = "anger"
                    emotion_thinking = emotion_result
                elif "厭惡" in emotion_result or "disgust" in emotion_result:
                    emotion_type = "disgust"
                    emotion_thinking = emotion_result
                else:
                    emotion_type = "contempt"
                    emotion_thinking = emotion_result
        
        if "思考:" in emotion_thinking or "回答:" in emotion_thinking:
            print("發現污染格式，清理中...")
            emotion_thinking = emotion_thinking.replace("思考:", "").replace("回答:", "").strip()
        
        emotion = "contempt"
        if any(term in emotion_type.lower() for term in ["憤怒", "anger"]):
            emotion = "anger"
        elif any(term in emotion_type.lower() for term in ["厭惡", "disgust"]):
            emotion = "disgust"
        
        return emotion, emotion_thinking
        
    except Exception as openai_error:
        print(f"OpenAI API 錯誤 (情緒分類): {str(openai_error)}")
        return "contempt", f"情緒分析過程中出現錯誤: {str(openai_error)}"

def get_emotion_memes(emotion, absolute_paths=True, use_fallback=False):
    memes = []
    
    meme_folder = os.path.join(app.static_folder, emotion)
    
    if not os.path.exists(meme_folder):
        os.makedirs(meme_folder, exist_ok=True)
        print(f"創建了情緒資料夾: {meme_folder}")
    
    if os.path.exists(meme_folder):
        meme_files = [f for f in os.listdir(meme_folder) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        memes = [f"{emotion}/{f}" for f in meme_files]
        print(f"找到 {len(memes)} 張 {emotion} 類型的MEME圖片")
        
        if not memes:
            print(f"'{emotion}' 資料夾中沒有MEME圖片，嘗試查找其他情緒資料夾")
            for backup_emotion in ['contempt', 'anger', 'disgust']:
                if backup_emotion == emotion:
                    continue
                backup_folder = os.path.join(app.static_folder, backup_emotion)
                if os.path.exists(backup_folder):
                    backup_files = [f for f in os.listdir(backup_folder) 
                                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
                    if backup_files:
                        memes = [f"{backup_emotion}/{f}" for f in backup_files]
                        print(f"使用 {backup_emotion} 資料夾中的 {len(memes)} 張圖片作為後備")
                        break
    
    return memes

@app.route('/api/memes/<emotion>')
def get_memes(emotion):
    if emotion not in config.EMOTION_FOLDERS + ['all']:
        return jsonify({"error": "無效的情緒類別"}), 400
        
    if emotion == 'all':
        return get_all_memes()
        
    memes = get_emotion_memes(emotion, absolute_paths=True, use_fallback=False)
    
    return jsonify({
        "memes": memes, 
        "count": len(memes),
        "emotion": emotion
    })

@app.route('/api/memes/all')
def get_all_memes():
    all_memes = []
    
    for emotion in config.EMOTION_FOLDERS:
        memes = get_emotion_memes(emotion, absolute_paths=True, use_fallback=False)
        all_memes.extend(memes)
    
    return jsonify({
        "memes": all_memes, 
        "count": len(all_memes)
    })

# API endpoint to record receiver data
@app.route('/api/record-receiver-data', methods=['POST'])
def record_receiver_data():
    try:
        data = request.json
        user_id = data.get('userId')
        post_id = data.get('postId')
        displayed_meme_name = data.get('displayedMemeName')
        questionnaire_scores = data.get('questionnaireScores')
        
        if not all([user_id, post_id, questionnaire_scores]):
            return jsonify({'success': False, 'message': '缺少必要資料'}), 400
        
        # Use comment_manager to record the data
        comment_manager.record_receiver_data(
            user_id=user_id,
            post_id=post_id,
            displayed_meme_name=displayed_meme_name,
            questionnaire_scores=questionnaire_scores
        )
        
        return jsonify({'success': True, 'message': '資料記錄成功'})
    
    except Exception as e:
        print(f"Error recording receiver data: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'記錄資料時發生錯誤: {str(e)}'}), 500

# API endpoint to record sender data
@app.route('/api/record-sender-data', methods=['POST'])
def record_sender_data():
    try:
        data = request.json
        user_id = data.get('userId')
        post_id = data.get('postId')
        selected_meme_name = data.get('selectedMemeName')
        questionnaire_scores = data.get('questionnaireScores')
        
        if not all([user_id, post_id, questionnaire_scores]):
            return jsonify({'success': False, 'message': '缺少必要資料'}), 400
        
        # Use comment_manager to record the data
        comment_manager.record_sender_data(
            user_id=user_id,
            post_id=post_id,
            selected_meme_name=selected_meme_name,
            questionnaire_scores=questionnaire_scores
        )
        
        return jsonify({'success': True, 'message': '資料記錄成功'})
    
    except Exception as e:
        print(f"Error recording sender data: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'記錄資料時發生錯誤: {str(e)}'}), 500

if __name__ == '__main__':
    # Ensure folders exist before starting the app
    setup_folders()
    # 允許通過網絡IP訪問，host='0.0.0.0' 表示監聽所有網絡接口
    app.run(host='0.0.0.0', port=5000, debug=True)
