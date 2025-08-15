// 全域變數
let currentQuestionnaireIndex = 0;
// 全局變量來跟蹤已提交的帖文
let submittedPosts = new Set();

// 檢查帖文是否可以訪問
function canAccessPost(postIndex) {
    if (postIndex === 0) return true; // 第一個帖文總是可以訪問
    
    // 檢查前一個帖文是否已提交
    for (let i = 0; i < postIndex; i++) {
        if (!submittedPosts.has(i)) {
            return false;
        }
    }
    return true;
}

// 更新navigation dots的狀態
function updateNavigationStatus() {
    const navigationDots = document.querySelectorAll('.nav-dot');
    navigationDots.forEach((dot, index) => {
        if (canAccessPost(index)) {
            dot.classList.remove('locked');
            dot.style.opacity = '1';
            dot.style.cursor = 'pointer';
            dot.title = '';
        } else {
            dot.classList.add('locked');
            dot.style.opacity = '0.3';
            dot.style.cursor = 'not-allowed';
            dot.title = '請先完成前面的帖文';
        }
        
        // 標記已提交的帖文
        if (submittedPosts.has(index)) {
            dot.classList.add('completed');
        }
    });
}

let currentPost = 0;
const totalPosts = 8;
const completedPosts = new Set();
let hasShownCompletionAlert = false; // 記錄是否已經顯示過完成alert

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCMsa0rv-EJnMnFNwQ5X3F7hbjdGvwJ00E",
    authDomain: "socialmedia-7c038.firebaseapp.com",
    databaseURL: "https://socialmedia-7c038-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "socialmedia-7c038",
    storageBucket: "socialmedia-7c038.appspot.com",
    messagingSenderId: "851731795907",
    appId: "1:851731795907:web:c1db66a2f12857b8e2ba64"
};

// Initialize Firebase
if (typeof firebase !== 'undefined') {
    try {
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
            console.log('Firebase initialized in receiver.js');
        }
    } catch (err) {
        console.error('Firebase initialization error:', err);
    }
}

// Function to generate random avatars
function generateRandomAvatars() {
    const avatarElements = document.querySelectorAll('.random-avatar');
    const storedUserId = localStorage.getItem('socialUserId');
    const seed = storedUserId || 'default123';
    
    avatarElements.forEach(avatar => {
        const isCurrentUser = avatar.closest('.nav-icons') !== null || avatar.dataset.currentUser === 'true';
        const isNewsAvatar = avatar.closest('.post-header') !== null || avatar.classList.contains('news-avatar');
        
        const newsSeed = "news123456";
        let imageSeed;
        
        if (isCurrentUser) {
            imageSeed = seed;
        } else if (isNewsAvatar) {
            imageSeed = newsSeed;
        } else {
            imageSeed = avatar.dataset.seed || "other" + Math.random().toString(36).substring(2, 8);
        }
        
        if (isNewsAvatar && !isCurrentUser) {
            avatar.src = `https://api.dicebear.com/7.x/bottts/svg?seed=${imageSeed}&backgroundColor=e53935,c62828&scale=80&radius=50`;
            avatar.alt = "新聞台";
            avatar.classList.add('news-avatar');
        } else if (isCurrentUser) {
            avatar.dataset.currentUser = 'true';
            avatar.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${imageSeed}`;
            avatar.alt = "用戶";
            avatar.classList.remove('news-avatar');
        } else {
            avatar.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${imageSeed}`;
            avatar.alt = "其他用戶";
        }
        
        avatar.onerror = function() {
            this.onerror = null;
            this.src = "https://via.placeholder.com/40x40/e0e0e0/888888?text=用戶";
        };
    });
}

// Function to show notification
function showNotification(message, type = 'info') {
    // Check if notification element already exists
    let notification = document.querySelector('.notification');
    
    // If not, create one
    if (!notification) {
        notification = document.createElement('div');
        notification.className = 'notification';
        document.body.appendChild(notification);
    }
    
    // Set notification type and message
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Show notification
    notification.classList.add('show');
    
    // Set timer to hide notification
    setTimeout(() => {
        notification.classList.remove('show');
        
        // Remove element after animation completes
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Function to detect personal attacks in comments
async function detectPersonalAttack(commentText) {
    try {
        // Get current username
        const username = localStorage.getItem('socialUserId');
        
        const response = await fetch('/api/detect-personal-attack', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                comment: commentText,
                user_id: username || 'anonymous',
                page_type: 'receiver', // Specify this is from the receiver page
                client_timestamp: Date.now()
            })
        });
        
        if (!response.ok) {
            throw new Error('人身攻擊檢測服務回應錯誤');
        }
        
        const result = await response.json();
        console.log('人身攻擊檢測結果:', result);
        return result;
    } catch (error) {
        console.error('檢測人身攻擊時出錯:', error);
        // Return a default result if the API fails
        return {
            is_attack: false,
            attack_thinking: "檢測發生錯誤: " + error.message,
            answer: "無法檢測",
            emotion: "",
            emotion_thinking: "",
            full_response: ""
        };
    }
}

// Handle comment submission with Firebase storage
async function handleCommentSubmit(event) {
    if (event) {
        event.preventDefault();
    }
    
    const submitButton = this;
    const commentSection = submitButton.closest('.add-comment');
    const commentInput = commentSection.querySelector('.comment-input');
    const commentText = commentInput.value.trim();
    
    if (commentText === '') return;
    
    // Get current username
    const username = localStorage.getItem('socialUserId');
    if (!username) {
        console.error('用戶未登入，無法儲存評論');
        showNotification('請先登入後再發表評論', 'error');
        return;
    }
    
    // Get post ID
    const postElement = commentSection.closest('.post');
    const postId = postElement ? postElement.dataset.postId : 'unknown_post';
    
    // Generate unique comment ID
    const commentId = Date.now().toString();
    
    // Detect if comment is a personal attack
    try {
        const detectionResult = await detectPersonalAttack(commentText);
        
        // Only record to receiver path, not activities
        recordCommentTimestamp(username, postId, commentId);
        
        // Add comment to UI (local only)
        const commentsList = commentSection.closest('.comments-section').querySelector('.comments-list');
        const newComment = document.createElement('div');
        newComment.className = 'comment';
        newComment.dataset.commentId = commentId;
        
        newComment.innerHTML = `
            <div class="user-avatar xsmall">
                <img class="random-avatar" data-current-user="true" src="" alt="用戶">
            </div>
            <div class="comment-content">
                <h4>${username}</h4>
                <p>${commentText}</p>
            </div>
        `;
        
        commentsList.appendChild(newComment);
        commentInput.value = '';
        
        // Regenerate avatars
        generateRandomAvatars();
        
        // Scroll to new comment
        setTimeout(() => {
            newComment.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 50);
        
        if (detectionResult.is_attack) {
            showNotification('警告：你的留言可能包含人身攻擊', 'error');
        } else {
            showNotification('評論已發表', 'success');
        }
    } catch (error) {
        console.error('評論提交過程中發生錯誤:', error);
        showNotification('評論發表時發生錯誤', 'error');
    }
}

// Simplified function to just record a timestamp in receiver path
async function recordCommentTimestamp(userId, postId, commentId) {
    try {
        const database = firebase.database();
        
        // Record in receiver path only
        const receiverRef = database.ref(`users/${userId}/receiver/comments/${postId}/${commentId}`);
        receiverRef.set({
            timestamp: new Date().toISOString(),
            client_timestamp: Date.now()
        });
        
        console.log('評論時間戳記錄成功');
    } catch (error) {
        console.error('記錄評論時間戳失敗:', error);
    }
}

// Handle meme comments (new function)
async function handleMemeComment(memeData, text, postId) {
    const username = localStorage.getItem('socialUserId');
    if (!username) {
        console.error('用戶未登入，無法儲存評論');
        return;
    }
    
    const commentId = Date.now().toString();
    
    try {
        // Detect if comment text has personal attacks
        const detectionResult = await detectPersonalAttack(text);
        
        // Only record to receiver path
        recordCommentTimestamp(username, postId, commentId);
        
        return {
            success: true,
            commentData: {
                user_id: username,
                post_id: postId,
                comment_id: commentId,
                text: text,
                input_style: 'meme',
                meme_src: memeData.src,
                meme_filename: memeData.filename,
                timestamp: new Date().toISOString(),
                client_timestamp: Date.now()
            }
        };
    } catch (error) {
        console.error('處理迷因評論時出錯:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Simplify trackComment to just log action, not sending detailed data
function trackComment(commentData) {
    console.log('Comment action recorded locally:', commentData.timestamp);
    // No API call needed since we're not storing detailed data
}

// Function to initialize comment display (modified to not use scrolling)
function initializeCommentScrolling() {
    const commentsLists = document.querySelectorAll('.comments-list');
    
    commentsLists.forEach(commentList => {
        // No scrolling behavior needed since we want to display all comments
        // Just make sure comments are properly displayed
        commentList.style.height = 'auto';
    });
}

// Function to load user's previous comments
function loadUserComments(username) {
    if (!username) return;
    
    try {
        const database = firebase.database();
        const commentsRef = database.ref(`users/${username}/receiver/comments`);
        
        commentsRef.once('value').then(snapshot => {
            if (!snapshot.exists()) {
                console.log('沒有找到之前的評論');
                return;
            }
            
            console.log('成功載入之前的評論');
            
            // Here you can choose whether to display previous comments in UI
            // For now, we'll just log that they've been loaded
        }).catch(error => {
            console.error('載入之前的評論時出錯:', error);
        });
    } catch (error) {
        console.error('嘗試載入評論時發生錯誤:', error);
    }
}

// Variables for state management
let stateChangeTimeout = null; // For debouncing state changes

// New function to save user state
function saveUserState() {
    const username = localStorage.getItem('socialUserId');
    if (!username) return;
    
    try {
        // Get all comment input values
        const commentInputs = document.querySelectorAll('.comment-input');
        const inputValues = {};
        
        commentInputs.forEach(input => {
            const postElement = input.closest('.post');
            if (postElement && postElement.dataset.postId) {
                inputValues[postElement.dataset.postId] = input.value;
            }
        });
        
        // Save toggle states for User D comments
        const toggleStates = {};
        document.querySelectorAll('.user-d-comment').forEach((comment, index) => {
            const memeView = comment.querySelector('.meme-view');
            toggleStates[`userD_${index}`] = memeView.classList.contains('active') ? 'meme' : 'text';
        });
        
        // Save scroll position
        const scrollPos = window.scrollY;
        
        // Create state object
        const userState = {
            inputValues,
            toggleStates,
            scrollPos,
            lastUpdated: new Date().toISOString()
        };
        
        // Save to localStorage with page-specific key
        localStorage.setItem(`${username}_receiverPageState`, JSON.stringify(userState));
        
    } catch (error) {
        console.error('Error saving receiver page state:', error);
    }
}

// New function to restore user state
function restoreUserState() {
    const username = localStorage.getItem('socialUserId');
    if (!username) return;
    
    try {
        const stateJSON = localStorage.getItem(`${username}_receiverPageState`);
        if (!stateJSON) return;
        
        const state = JSON.parse(stateJSON);
        
        // Restore input values
        if (state.inputValues) {
            Object.keys(state.inputValues).forEach(postId => {
                const post = document.querySelector(`.post[data-post-id="${postId}"]`);
                if (post) {
                    const input = post.querySelector('.comment-input');
                    if (input && state.inputValues[postId]) {
                        input.value = state.inputValues[postId];
                    }
                }
            });
        }
        
        // Restore toggle states
        if (state.toggleStates) {
            document.querySelectorAll('.user-d-comment').forEach((comment, index) => {
                const key = `userD_${index}`;
                if (state.toggleStates[key]) {
                    const memeView = comment.querySelector('.meme-view');
                    const textView = comment.querySelector('.text-view');
                    const toggleBtn = comment.querySelector('.toggle-view-btn');
                    
                    if (state.toggleStates[key] === 'meme') {
                        memeView.classList.add('active');
                        textView.classList.remove('active');
                        toggleBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> 查看原文';
                    } else {
                        memeView.classList.remove('active');
                        textView.classList.add('active');
                        toggleBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> 查看迷因圖';
                    }
                }
            });
        }
        
        // Restore scroll position after a small delay to ensure elements are rendered
        if (state.scrollPos) {
            setTimeout(() => {
                window.scrollTo(0, state.scrollPos);
            }, 100);
        }
        
    } catch (error) {
        console.error('Error restoring receiver page state:', error);
    }
}

// Debounced version of saveUserState to prevent excessive calls
function debouncedSaveState() {
    clearTimeout(stateChangeTimeout);
    stateChangeTimeout = setTimeout(saveUserState, 300);
}

// Function to handle comment view toggling between meme and text
function setupCommentToggles() {
    const toggleButtons = document.querySelectorAll('.toggle-view-btn');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const container = this.closest('.comment-toggle-container');
            const memeView = container.querySelector('.meme-view');
            const textView = container.querySelector('.text-view');
            
            // Toggle active class
            memeView.classList.toggle('active');
            textView.classList.toggle('active');
            
            // Update button text based on current view
            if (memeView.classList.contains('active')) {
                this.innerHTML = '<i class="fas fa-exchange-alt"></i> 查看原文';
            } else {
                this.innerHTML = '<i class="fas fa-exchange-alt"></i> 查看迷因圖';
            }
            
            // Save state when toggle changes
            debouncedSaveState();
            
            // Remove toggle event logging
        });
    });
    
    // Also add click handler to the memes themselves
    const memeImages = document.querySelectorAll('.user-d-comment .meme-image');
    memeImages.forEach(img => {
        img.addEventListener('click', function() {
            const container = this.closest('.comment-toggle-container');
            const memeView = container.querySelector('.meme-view');
            const textView = container.querySelector('.text-view');
            const toggleBtn = container.querySelector('.toggle-view-btn');
            
            // Switch to text view when clicking on meme
            memeView.classList.remove('active');
            textView.classList.add('active');
            toggleBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> 查看迷因圖';
        });
    });
}

// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Receiver page DOM loaded');
    
    // Get current user and phase
    const username = localStorage.getItem('socialUserId');
    const currentPhase = localStorage.getItem('currentPhase');
    
    if (!username) {
        console.error('未找到用戶名，重定向到登入頁面');
        window.location.href = '/';
        return;
    }
    
    console.log('當前用戶:', username, 'phase:', currentPhase);
    const pageContentWrapper = document.getElementById('page-content-wrapper');
    
    if (pageContentWrapper) {
        pageContentWrapper.classList.remove('hidden');
        
        // Check if we should skip introduction and go directly to main content
        if (currentPhase === 'receiver-preview') {
            // Skip introduction, go directly to preview mode
            const contextIntro = document.getElementById('context-introduction');
            const mainContent = document.getElementById('main-content');
            const postNavigation = document.querySelector('.post-navigation');
            
            if (contextIntro) contextIntro.style.display = 'none';
            if (mainContent) mainContent.style.display = 'flex';
            if (postNavigation) postNavigation.style.display = 'flex';
            
            initializeMainContent();
        } else {
            // Normal flow - show introduction first
            const startViewingBtn = document.getElementById('startViewing');
            const contextIntro = document.getElementById('context-introduction');
            const mainContent = document.getElementById('main-content');
            const postNavigation = document.querySelector('.post-navigation');
            
            // 在情境說明階段隱藏底部導航
            if (postNavigation && contextIntro && contextIntro.style.display !== 'none') {
                postNavigation.style.display = 'none';
            }
            
            if (startViewingBtn) {
                startViewingBtn.addEventListener('click', function() {
                    // 隱藏情境說明，顯示主要內容
                    if (contextIntro) {
                        contextIntro.style.display = 'none';
                    }
                    if (mainContent) {
                        mainContent.style.display = 'flex';
                    }
                    
                    // 顯示底部導航
                    if (postNavigation) {
                        postNavigation.style.display = 'flex';
                    }
                    
                    // 記錄用戶開始觀看的時間
                    localStorage.setItem('receiverViewingStartTime', new Date().toISOString());
                    
                    // 初始化主要功能
                    initializeMainContent();
                });
            }
        }
    }
});

// 將原本的初始化邏輯移到這個函數中
function initializeMainContent() {
    const username = localStorage.getItem('socialUserId');
    const currentPhase = localStorage.getItem('currentPhase');
    
    // 初始化navigation功能
    initializeNavigation();
    
    // Display username
    const usernameDisplays = document.querySelectorAll('.username-display');
    usernameDisplays.forEach(display => {
        display.textContent = username;
    });
    
    // Generate avatars
    generateRandomAvatars();
    
    // Initialize comment scrolling
    initializeCommentScrolling();
    
    // Load user's previous comments
    // loadUserComments(username); // Temporarily disabled due to Firebase issues
    
    // Add comment functionality
    const commentSubmitButtons = document.querySelectorAll('.comment-submit');
    commentSubmitButtons.forEach(button => {
        button.addEventListener('click', handleCommentSubmit);
    });
    
    const commentInputs = document.querySelectorAll('.comment-input');
    commentInputs.forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const submitButton = this.closest('.add-comment').querySelector('.comment-submit');
                handleCommentSubmit.call(submitButton, e);
            }
        });
        
        // Add input event for state tracking
        input.addEventListener('input', debouncedSaveState);
    });
    
    // Log page view to receiver path only - temporarily disabled
    /*
    try {
        const database = firebase.database();
        const pageViewRef = database.ref(`users/${username}/receiver/page_views`);
        pageViewRef.push().set({
            timestamp: new Date().toISOString(),
            action: 'viewed_receiver_page',
            client_timestamp: Date.now()
        });
        
        // Remove activities logging
    } catch (error) {
        console.error('記錄頁面訪問時出錯:', error);
    }
    */
    
    // Back button removed - users follow linear experiment flow
    
    // Add logout button functionality
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', showLogoutDialog);
    }
    
    // Set up comment toggle functionality
    setupToggleCommentHandlers(); // 啟用查看原始留言功能
    
    // Set up questionnaire submission functionality
    setupQuestionnaireSubmission();
    
    // Set up Likert scale value updates
    setupLikertScaleUpdates();
    
    // Set up meme image modal functionality - 移到其他功能設置之後
    setupMemeImageModal();
    
    // Listen for scroll events to save position
    window.addEventListener('scroll', debouncedSaveState);
    
    // Restore previous state
    restoreUserState();
    
    // 設置箭頭鍵導航（總是啟用）
    setupArrowKeyNavigation();
    
    // 檢查是否在預覽模式
    if (currentPhase === 'receiver-preview') {
        // 延遲進入預覽模式，確保DOM已加載
        setTimeout(() => {
            enterPreviewMode();
        }, 100);
    }
}

// Create and append logout dialog HTML
function createLogoutDialog() {
    const dialogHTML = `
        <div class="logout-dialog-container" id="logoutDialogContainer">
            <div class="logout-dialog">
                <h3>切換使用者</h3>
                <p>你確定要登出嗎？這將會清除目前的使用者資料，並返回選擇頁面。</p>
                <div class="logout-dialog-buttons">
                    <button class="cancel-button" id="cancelLogout">取消</button>
                    <button class="confirm-button" id="confirmLogout">確認</button>
                </div>
            </div>
        </div>
    `;
    
    // Append dialog to body if it doesn't exist
    if (!document.getElementById('logoutDialogContainer')) {
        document.body.insertAdjacentHTML('beforeend', dialogHTML);
        
        // Add event listeners
        document.getElementById('cancelLogout').addEventListener('click', hideLogoutDialog);
        document.getElementById('confirmLogout').addEventListener('click', logout);
        document.getElementById('logoutDialogContainer').addEventListener('click', function(e) {
            if (e.target === this) {
                hideLogoutDialog();
            }
        });
    }
}

// Show the logout confirmation dialog
function showLogoutDialog() {
    createLogoutDialog();
    document.getElementById('logoutDialogContainer').style.display = 'flex';
}

// Hide the logout confirmation dialog
function hideLogoutDialog() {
    const dialog = document.getElementById('logoutDialogContainer');
    if (dialog) {
        dialog.style.display = 'none';
    }
}

// Handle logout functionality
function logout() {
    const username = localStorage.getItem('socialUserId');
    
    // Remove logout action logging to Firebase
    
    // Clear ALL user state data
    localStorage.removeItem(`${username}_senderPageState`);
    localStorage.removeItem(`${username}_receiverPageState`);
    
    // Clear localStorage
    localStorage.removeItem('socialUserId');
    
    // Redirect to login page
    window.location.href = '/';
}

// Set up questionnaire submission functionality
function setupQuestionnaireSubmission() {
    const submitButtons = document.querySelectorAll('.submit-receiver-survey-btn');
    const totalPosts = document.querySelectorAll('.post.news-post').length;
    
    submitButtons.forEach((button, index) => {
        // Find which panel this button belongs to
        const panel = button.closest('.interaction-panel');
        const panelId = panel ? panel.id : '';
        const postIndex = panelId ? parseInt(panelId.split('-')[1]) : index;
        
        button.addEventListener('click', function() {
            handleQuestionnaireSubmit(postIndex, totalPosts);
        });
    });
}

// Handle questionnaire submission
async function handleQuestionnaireSubmit(postIndex, totalPosts) {
    const username = localStorage.getItem('socialUserId');
    if (!username) {
        alert('請先登入後再提交問卷');
        return;
    }
    
    // Get current post data
    const currentPost = document.querySelector(`#post-${postIndex}`);
    if (!currentPost) return;
    
    // Get questionnaire responses from the correct panel
    const panel = document.querySelector(`#panel-${postIndex}`);
    
    if (!panel) {
        console.error(`Panel not found for post ${postIndex}`);
        return;
    }
    
    const questionnaireScores = {};
    
    // Get scores from all available Likert scales dynamically
    const sliders = panel.querySelectorAll('.likert-scale[data-question]');
    sliders.forEach(slider => {
        const questionId = slider.dataset.question; // e.g., "q1", "q2", etc.
        const questionKey = questionId.toUpperCase(); // Convert to "Q1", "Q2", etc.
        questionnaireScores[questionKey] = parseInt(slider.value);
    });
    
    // Get post information
    const originalPostId = currentPost.dataset.originalPostId;
    
    // Get displayed meme information
    const memeImage = currentPost.querySelector('.meme-image');
    const displayedMemeName = memeImage ? memeImage.alt : '';
    
    // Record data using backend API
    await recordReceiverData(username, originalPostId, displayedMemeName, questionnaireScores);
    
    // Mark current post as completed and move to next
    completeCurrentPost();
}

// Show next post
function showNextPost(currentIndex) {
    // Hide current post
    const currentPost = document.querySelector(`#post-${currentIndex}`);
    if (currentPost) {
        currentPost.style.display = 'none';
        currentPost.classList.remove('active');
    }
    
    // Hide current panel
    const currentPanel = document.querySelector(`#panel-${currentIndex}`);
    if (currentPanel) {
        currentPanel.style.display = 'none';
        currentPanel.classList.remove('active');
    }
    
    // Show next post
    const nextIndex = currentIndex + 1;
    const nextPost = document.querySelector(`#post-${nextIndex}`);
    
    if (nextPost) {
        nextPost.style.display = 'block';
        nextPost.classList.add('active');
    }
    
    // Show next panel
    const nextPanel = document.querySelector(`#panel-${nextIndex}`);
    if (nextPanel) {
        nextPanel.style.display = 'block';
        nextPanel.classList.add('active');
    }
    
    // Scroll to top
    window.scrollTo(0, 0);
}

// Record receiver data (this should be sent to backend)
async function recordReceiverData(userId, postId, displayedMemeName, questionnaireScores) {
    try {
        const response = await fetch('/api/record-receiver-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: userId,
                postId: postId,
                displayedMemeName: displayedMemeName,
                questionnaireScores: questionnaireScores
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Receiver data recorded successfully');
        } else {
            console.error('Failed to record receiver data:', result.message);
        }
    } catch (error) {
        console.error('Error recording receiver data:', error);
    }
}

// Navigation 功能
function initializeNavigation() {
    showPost(0);
    updateNavigationDots();
    setupNavigationEvents();
}

// 顯示指定帖文
function showPost(index) {
    // 隱藏所有帖文
    document.querySelectorAll('.post').forEach(post => {
        post.classList.remove('active');
        post.style.display = 'none';
    });
    
    // 隱藏所有互動面板
    document.querySelectorAll('.interaction-panel').forEach(panel => {
        panel.classList.remove('active');
        panel.style.display = 'none';
    });
    
    // 顯示指定帖文
    const currentPost = document.querySelector(`#post-${index}`);
    const currentPanel = document.querySelector(`#panel-${index}`);
    
    if (currentPost) {
        currentPost.classList.add('active');
        currentPost.style.display = 'block';
        // 確保移除任何可能影響顯示的內聯樣式
        currentPost.style.transform = '';
        currentPost.style.opacity = '';
        currentPostIndex = index;
    }
    
    if (currentPanel) {
        currentPanel.classList.add('active');
        currentPanel.style.display = 'block';
        // 確保移除任何可能影響顯示的內聯樣式
        currentPanel.style.transform = '';
        currentPanel.style.opacity = '';
    }
    
    // 更新切換按鈕的狀態和文字
    // updateToggleButtonStates(index); // 不再需要根據帖文限制功能
    
    updateNavigationDots();
}

// 更新導航點狀態
function updateNavigationDots() {
    const dots = document.querySelectorAll('.nav-dot');
    dots.forEach((dot, index) => {
        dot.classList.remove('active');
        
        if (index === currentPostIndex) {
            dot.classList.add('active');
        }
        
        if (completedPosts.has(index)) {
            dot.classList.add('completed');
        }
    });
    
    // 更新進度顯示
    const progressText = document.querySelector('.nav-progress .current-post');
    if (progressText) {
        progressText.textContent = currentPostIndex + 1;
    }
}

// 設置導航事件
// 設置導航事件
function setupNavigationEvents() {
    // 在正常模式下禁用導航點點擊 - 只作為進度指示器
    const dots = document.querySelectorAll('.nav-dot');
    dots.forEach(dot => {
        dot.style.cursor = 'default';
        dot.title = '完成後可用於預覽';
        
        // 移除任何現有的點擊事件
        dot.removeEventListener('click', handleDotClick);
    });
}

// 標記當前帖文為已完成並移到下一個
function completeCurrentPost() {
    completedPosts.add(currentPostIndex);
    
    // 檢查是否還有未完成的帖文
    const nextPost = findNextIncompletePost();
    if (nextPost !== -1) {
        showPost(nextPost);
    } else {
        // 所有帖文完成 - 只在第一次完成時顯示alert並進入預覽模式
        if (!hasShownCompletionAlert) {
            hasShownCompletionAlert = true;
            
            // 記錄觀察者階段完成時間
            localStorage.setItem('receiverPhaseCompleted', new Date().toISOString());
            localStorage.setItem('currentPhase', 'receiver-preview');
            
            alert('完成！');
            
            // 進入預覽模式，不自動跳轉
            enterPreviewMode();
        }
    }
}

// 找到下一個未完成的帖文
function findNextIncompletePost() {
    for (let i = 0; i < totalPosts; i++) {
        if (!completedPosts.has(i)) {
            return i;
        }
    }
    return -1; // 全部完成
}

// 設置切換留言和迷因圖的功能
function setupToggleCommentHandlers() {
    const toggleButtons = document.querySelectorAll('.toggle-comment-btn');
    
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const commentContent = this.closest('.comment-content');
            const memeView = commentContent.querySelector('.meme-view');
            const textView = commentContent.querySelector('.text-view');
            const currentView = this.dataset.currentView;
            
            if (currentView === 'meme') {
                // 切換到原始留言視圖
                memeView.style.display = 'none';
                textView.style.display = 'block';
                this.textContent = '查看迷因';
                this.dataset.currentView = 'text';
            } else {
                // 切換到迷因圖視圖
                memeView.style.display = 'block';
                textView.style.display = 'none';
                this.textContent = '查看原始留言';
                this.dataset.currentView = 'meme';
            }
        });
    });
}

// 更新切換按鈕的狀態和文字
function updateToggleButtonStates(postIndex) {
    const toggleButtons = document.querySelectorAll('.toggle-comment-btn');
    const canViewOriginalComment = postIndex % 2 === 0;
    
    toggleButtons.forEach(btn => {
        if (canViewOriginalComment) {
            // 偶數索引 (0, 2, 4, 6) - 可以查看原始留言
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
            btn.disabled = false;
            btn.title = '點擊切換查看模式';
        } else {
            // 奇數索引 (1, 3, 5, 7) - 不能查看原始留言
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
            btn.disabled = true;
            btn.title = '此帖文不提供原始留言查看功能';
        }
        
        // 重置到迷因圖視圖
        const commentContent = btn.closest('.comment-content');
        const memeView = commentContent.querySelector('.meme-view');
        const textView = commentContent.querySelector('.text-view');
        
        if (memeView && textView) {
            memeView.style.display = 'block';
            textView.style.display = 'none';
            btn.textContent = '查看原始留言';
            btn.dataset.currentView = 'meme';
        }
    });
}

// 設置Likert量表數值實時更新
function setupLikertScaleUpdates() {
    const likertScales = document.querySelectorAll('.likert-scale');
    
    likertScales.forEach(scale => {
        // 找到對應的數值顯示元素
        const scaleContainer = scale.closest('.scale-container');
        const scaleValueDisplay = scaleContainer ? scaleContainer.querySelector('.scale-value') : null;
        
        if (scaleValueDisplay) {
            // 初始化顯示當前值
            scaleValueDisplay.textContent = scale.value;
            
            // 添加input事件監聽器，實時更新數值
            scale.addEventListener('input', function() {
                scaleValueDisplay.textContent = this.value;
            });
            
            // 添加change事件監聽器，確保最終值正確
            scale.addEventListener('change', function() {
                scaleValueDisplay.textContent = this.value;
            });
        }
    });
}

// 進入預覽模式
function enterPreviewMode() {
    // 禁用所有表單元素
    const forms = document.querySelectorAll('.receiver-survey-section');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, button');
        inputs.forEach(input => {
            if (!input.classList.contains('preview-allowed')) {
                input.disabled = true;
            }
        });
    });
    
    // 啟用導航點擊功能用於預覽
    setupPreviewNavigation();
    
    // 設置數字鍵導航
    setupNumberKeyNavigation();
    
    // 設置右鍵上下文菜單
    setupContextMenu();
    
    // 設置箭頭鍵導航
    setupArrowKeyNavigation();
}

// 設置預覽模式下的導航功能
function setupPreviewNavigation() {
    const dots = document.querySelectorAll('.nav-dot');
    
    dots.forEach((dot, index) => {
        // 移除之前可能存在的點擊事件監聽器
        dot.removeEventListener('click', handleDotClick);
        
        // 添加預覽模式的點擊事件
        dot.addEventListener('click', function(e) {
            e.preventDefault();
            if (localStorage.getItem('currentPhase') === 'receiver-preview') {
                // 只在預覽模式下允許點擊導航
                showPost(index);
            }
        });
        
        // 添加視覺提示表明可以點擊
        dot.style.cursor = 'pointer';
        dot.title = `預覽第 ${index + 1} 個帖文`;
    });
}

// 通用的導航點點擊處理函數
function handleDotClick(e) {
    // 這個函數可以在需要時被其他地方使用
    e.preventDefault();
}

// 設置數字鍵導航（1-8）
function setupNumberKeyNavigation() {
    document.addEventListener('keydown', function(e) {
        // 檢查是否在預覽模式
        if (localStorage.getItem('currentPhase') === 'receiver-preview') {
            const key = parseInt(e.key);
            if (key >= 1 && key <= 8) {
                e.preventDefault();
                showPost(key - 1); // 轉換為0-based索引
            }
        }
    });
}

// 設置右鍵上下文菜單
function setupContextMenu() {
    document.addEventListener('contextmenu', function(e) {
        if (localStorage.getItem('currentPhase') === 'receiver-preview') {
            e.preventDefault();
            
            // 創建自定義右鍵菜單
            let contextMenu = document.querySelector('.custom-context-menu');
            if (!contextMenu) {
                contextMenu = document.createElement('div');
                contextMenu.className = 'custom-context-menu';
                contextMenu.innerHTML = `
                    <div class="context-menu-item" data-action="next-phase">
                        <i class="fas fa-arrow-right"></i>
                        進入發送者階段
                    </div>
                `;
                document.body.appendChild(contextMenu);
                
                // 添加點擊事件
                contextMenu.addEventListener('click', function(e) {
                    const action = e.target.closest('.context-menu-item')?.dataset.action;
                    if (action === 'next-phase') {
                        localStorage.setItem('currentPhase', 'sender');
                        window.location.href = '/sender';
                    }
                    hideContextMenu();
                });
            }
            
            // 顯示菜單
            contextMenu.style.display = 'block';
            contextMenu.style.left = e.pageX + 'px';
            contextMenu.style.top = e.pageY + 'px';
            
            // 點擊其他地方隱藏菜單
            setTimeout(() => {
                document.addEventListener('click', hideContextMenu, { once: true });
            }, 0);
        }
    });
}

// 隱藏右鍵菜單
function hideContextMenu() {
    const contextMenu = document.querySelector('.custom-context-menu');
    if (contextMenu) {
        contextMenu.style.display = 'none';
    }
}

// 設置箭頭鍵導航
function setupArrowKeyNavigation() {
    document.addEventListener('keydown', function(e) {
        // 檢查是否按下左右箭頭鍵
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            e.preventDefault();
            
            const currentPhase = localStorage.getItem('currentPhase');
            
            if (e.key === 'ArrowLeft') {
                // 左箭頭：回到上一個階段
                if (currentPhase === 'sender' || currentPhase === 'sender-preview') {
                    localStorage.setItem('currentPhase', 'receiver-preview');
                    window.location.href = '/receiver';
                } else if (currentPhase === 'receiver-preview' || currentPhase === 'receiver') {
                    // 回到輸入頁面
                    window.location.href = '/';
                }
            } else if (e.key === 'ArrowRight') {
                // 右箭頭：前往下一個階段
                if (currentPhase === 'receiver-preview' || currentPhase === 'receiver') {
                    localStorage.setItem('currentPhase', 'sender');
                    window.location.href = '/sender';
                } else if (currentPhase === 'sender') {
                    localStorage.setItem('currentPhase', 'sender-preview');
                    // 如果有更多階段，在這裡添加
                }
            }
        }
    });
}

// 設置迷因圖模態框功能
function setupMemeImageModal() {
    // 創建模態框HTML（如果不存在）
    if (!document.getElementById('memeModal')) {
        const modalHTML = `
            <div id="memeModal" class="meme-modal" style="display: none;">
                <span class="meme-modal-close">&times;</span>
                <img class="meme-modal-image" id="memeModalImage" src="" alt="">
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    const modal = document.getElementById('memeModal');
    const modalImg = document.getElementById('memeModalImage');
    const closeBtn = document.querySelector('.meme-modal-close');
    
    // 確保模態框初始狀態是隱藏的
    modal.style.display = 'none';
    
    // 為所有迷因圖片添加點擊事件
    function addMemeClickHandlers() {
        const memeImages = document.querySelectorAll('.meme-image');
        memeImages.forEach(img => {
            img.addEventListener('click', function(e) {
                e.stopPropagation(); // 防止事件冒泡
                modal.style.display = 'flex'; // 使用 flex 佈局來居中
                modalImg.src = this.src;
                modalImg.alt = this.alt;
                document.body.style.overflow = 'hidden'; // 防止背景滾動
            });
        });
    }
    
    // 關閉模態框
    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // 恢復滾動
    }
    
    // 點擊關閉按鈕
    closeBtn.addEventListener('click', closeModal);
    
    // 點擊背景或圖片旁邊區域關閉
    modal.addEventListener('click', function(e) {
        // 只要點擊的不是圖片本身，就關閉模態框
        if (e.target !== modalImg) {
            closeModal();
        }
    });
    
    // ESC鍵關閉
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            closeModal();
        }
    });
    
    // 初始化點擊處理器
    addMemeClickHandlers();
    
    // 監聽DOM變化，為新添加的迷因圖片添加點擊事件
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                addMemeClickHandlers();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}