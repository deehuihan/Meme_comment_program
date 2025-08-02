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
            console.log('Firebase initialized in sender.js');
        }
    } catch (err) {
        console.error('Firebase initialization error:', err);
    }
}

// Global variables
let currentCommentData = null;
let lastDetectionResult = null;
let stateChangeTimeout = null; // For debouncing state changes
let selectedMeme = null; // Track selected meme

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
        
        // Save toggle states for meme comments
        const toggleStates = {};
        document.querySelectorAll('.comment-toggle-container').forEach((container, index) => {
            const memeView = container.querySelector('.meme-view');
            toggleStates[`meme_${index}`] = memeView.classList.contains('active') ? 'meme' : 'text';
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
        localStorage.setItem(`${username}_senderPageState`, JSON.stringify(userState));
        
    } catch (error) {
        console.error('Error saving sender page state:', error);
    }
}

// New function to restore user state
function restoreUserState() {
    const username = localStorage.getItem('socialUserId');
    if (!username) return;
    
    try {
        const stateJSON = localStorage.getItem(`${username}_senderPageState`);
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
            document.querySelectorAll('.comment-toggle-container').forEach((container, index) => {
                const key = `meme_${index}`;
                if (state.toggleStates[key]) {
                    const memeView = container.querySelector('.meme-view');
                    const textView = container.querySelector('.text-view');
                    const toggleBtn = container.querySelector('.toggle-view-btn');
                    
                    if (state.toggleStates[key] === 'meme') {
                        memeView.classList.add('active');
                        textView.classList.remove('active');
                        if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> 查看原文';
                    } else {
                        memeView.classList.remove('active');
                        textView.classList.add('active');
                        if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> 查看迷因圖';
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
        console.error('Error restoring sender page state:', error);
    }
}

// Debounced version of saveUserState to prevent excessive calls
function debouncedSaveState() {
    clearTimeout(stateChangeTimeout);
    stateChangeTimeout = setTimeout(saveUserState, 300);
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
function showNotification(message, type = 'info', submitButton = null) {
    if (submitButton) {
        // Inline notification under specific comment section
        const commentSection = submitButton.closest('.add-comment');
        const commentsSection = commentSection.closest('.comments-section');
        
        if (commentsSection) {
            const notificationArea = commentsSection.querySelector('.inline-notification-area');
            if (notificationArea) {
                const notification = notificationArea.querySelector('.inline-notification');
                const iconElement = notification.querySelector('.notification-icon');
                const messageElement = notification.querySelector('.notification-message');
                
                // Set proper icon based on notification type
                let iconClass = 'fas fa-info-circle';
                if (type === 'success') {
                    iconClass = 'fas fa-check-circle';
                } else if (type === 'error') {
                    iconClass = 'fas fa-exclamation-circle';
                }
                
                // Set notification type and content
                notification.className = `inline-notification ${type}`;
                iconElement.className = `notification-icon ${iconClass}`;
                messageElement.textContent = message;
                
                // Show notification
                notificationArea.style.display = 'block';
                
                // Hide after timeout
                setTimeout(() => {
                    // Fade out and hide
                    notificationArea.style.opacity = '0';
                    setTimeout(() => {
                        notificationArea.style.display = 'none';
                        notificationArea.style.opacity = '1';
                    }, 300);
                }, 3000);
                
                return; // Exit function since we've shown an inline notification
            }
        }
    }
    
    // Fallback to the original floating notification if inline is not possible
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
                page_type: 'sender', // Specify this is from the sender page
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
        };
    }
}

// Show the attack detection results inline below the comment input
function showAttackDetectionInline(detectionResult, commentText, submitButton) {
    // Store current comment data for later use
    currentCommentData = {
        text: commentText,
        submitButton: submitButton,
        detectionResult: detectionResult
    };
    
    // Find the related detection results area
    const commentSection = submitButton.closest('.add-comment');
    const detectionArea = commentSection.nextElementSibling;
    
    if (!detectionArea || !detectionArea.classList.contains('detection-results-area')) {
        console.error('Could not find detection results area');
        return;
    }
    
    // Hide detection process indicator and show results
    const detectionProcess = detectionArea.querySelector('.detection-process');
    const detectionResults = detectionArea.querySelector('.detection-results');
    
    if (detectionProcess) detectionProcess.style.display = 'none';
    if (detectionResults) detectionResults.style.display = 'block';
    
    // Set suggestion text
    let suggestionText = "建議重新組織你的表達方式，避免直接人身攻擊。";
    if (detectionResult.attack_thinking) {
        suggestionText = detectionResult.attack_thinking;
    }
    
    // Update the content
    const suggestionTextElem = detectionArea.querySelector('.suggestion-text');
    const originalTextElem = detectionArea.querySelector('.original-text');
    
    if (suggestionTextElem) suggestionTextElem.textContent = suggestionText;
    if (originalTextElem) originalTextElem.innerHTML = `<strong>原始留言：</strong> ${commentText}`;
    
    // Show the detection area
    detectionArea.style.display = 'block';
    
    // Set up button events
    const editBtn = detectionArea.querySelector('.edit-comment-btn');
    const continueBtn = detectionArea.querySelector('.continue-comment-btn');
    const memeBtn = detectionArea.querySelector('.meme-comment-btn');
    
    if (editBtn) {
        editBtn.onclick = function() {
            hideDetectionResults(detectionArea);
            // Focus back on input
            commentSection.querySelector('.comment-input').focus();
        };
    }
    
    if (memeBtn) {
        memeBtn.onclick = function() {
            hideDetectionResults(detectionArea);
            
            // Check if this is post_1 for special handling
            const postElement = commentSection.closest('.post');
            const postId = postElement ? postElement.dataset.postId : '';
            
            if (postId === 'post_1') {
                // For post_1, automatically select and use a recommended meme
                useRecommendedMeme(commentText, submitButton, detectionResult);
            } else {
                // For other posts, show meme selection area as usual
                showMemeSelectionArea(commentSection, commentText, submitButton, detectionResult);
            }
        };
    }
    
    if (continueBtn) {
        continueBtn.onclick = function() {
            hideDetectionResults(detectionArea);
            // Continue with comment submission
            submitCommentAfterDetection(currentCommentData);
        };
    }
}

// Hide the detection results
function hideDetectionResults(detectionArea) {
    if (detectionArea) {
        detectionArea.style.display = 'none';
        
        // Reset the detection process for next time
        const detectionProcess = detectionArea.querySelector('.detection-process');
        const detectionResults = detectionArea.querySelector('.detection-results');
        
        if (detectionProcess) detectionProcess.style.display = 'block';
        if (detectionResults) detectionResults.style.display = 'none';
    }
}

// Show meme selection area
function showMemeSelectionArea(commentSection, commentText, submitButton, detectionResult) {
    const commentsSection = commentSection.closest('.comments-section');
    const memeSelectionArea = commentsSection.querySelector('.meme-selection-area');
    
    if (!memeSelectionArea) {
        console.error('Meme selection area not found');
        return;
    }
    
    // Reset selected meme
    selectedMeme = null;
    
    // Unselect all meme items
    const memeItems = memeSelectionArea.querySelectorAll('.meme-item');
    memeItems.forEach(item => {
        item.classList.remove('selected');
        
        // Add click event
        item.onclick = function() {
            // Remove selected class from all items
            memeItems.forEach(i => i.classList.remove('selected'));
            
            // Add selected class to clicked item
            this.classList.add('selected');
            
            // Store selected meme
            selectedMeme = {
                id: this.dataset.memeId,
                src: this.querySelector('img').src,
                alt: this.querySelector('img').alt
            };
            
            // Enable select button
            const selectBtn = memeSelectionArea.querySelector('.select-meme-btn');
            if (selectBtn) {
                selectBtn.disabled = false;
            }
        };
    });
    
    // Setup cancel button
    const cancelBtn = memeSelectionArea.querySelector('.cancel-meme-btn');
    if (cancelBtn) {
        cancelBtn.onclick = function() {
            memeSelectionArea.style.display = 'none';
        };
    }
    
    // Setup select button
    const selectBtn = memeSelectionArea.querySelector('.select-meme-btn');
    if (selectBtn) {
        selectBtn.disabled = true; // Disable until a meme is selected
        
        selectBtn.onclick = function() {
            if (selectedMeme) {
                memeSelectionArea.style.display = 'none';
                
                // Submit as meme comment
                submitMemeComment(commentText, selectedMeme, submitButton, detectionResult);
            }
        };
    }
    
    // Show meme selection area
    memeSelectionArea.style.display = 'block';
}

// Submit comment as meme
function submitMemeComment(commentText, meme, submitButton, detectionResult) {
    const commentSection = submitButton.closest('.add-comment');
    const commentInput = commentSection.querySelector('.comment-input');
    const postElement = commentSection.closest('.post');
    const postId = postElement ? postElement.dataset.postId : 'unknown_post';
    
    // Get current username
    const username = localStorage.getItem('socialUserId');
    if (!username) {
        console.error('用戶未登入，無法儲存評論');
        showNotification('請先登入後再發表評論', 'error', submitButton);
        return;
    }
    
    // Generate unique comment ID
    const commentId = Date.now().toString();
    
    // Add comment to UI with toggle functionality
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
            <div class="comment-toggle-container">
                <div class="meme-view active">
                    <img src="${meme.src}" alt="${meme.alt}" class="meme-image">
                </div>
                <div class="text-view">
                    <p>${commentText}</p>
                </div>
                <button class="toggle-view-btn">
                    <i class="fas fa-exchange-alt"></i> 查看原文
                </button>
            </div>
        </div>
    `;
    
    commentsList.appendChild(newComment);
    commentInput.value = '';
    
    // Add event listener to the toggle button
    const toggleBtn = newComment.querySelector('.toggle-view-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
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
        });
    }
    
    // Add event listener to the meme image itself
    const memeImage = newComment.querySelector('.meme-image');
    if (memeImage) {
        memeImage.addEventListener('click', function() {
            const container = this.closest('.comment-toggle-container');
            const memeView = container.querySelector('.meme-view');
            const textView = container.querySelector('.text-view');
            const toggleBtn = container.querySelector('.toggle-view-btn');
            
            // Switch to text view when clicking on meme
            memeView.classList.remove('active');
            textView.classList.add('active');
            toggleBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> 查看迷因圖';
            
            // Save state
            debouncedSaveState();
        });
    }
    
    // Regenerate avatars
    generateRandomAvatars();
    
    // Save to Firebase
    saveCommentToFirebase({
        text: commentText,
        user_id: username,
        post_id: postId,
        comment_id: commentId,
        is_attack: detectionResult.is_attack,
        attack_thinking: detectionResult.attack_thinking || '',
        answer: detectionResult.answer || '',
        emotion: detectionResult.emotion || '',
        emotion_thinking: detectionResult.emotion_thinking || '',
        timestamp: new Date().toISOString(),
        client_timestamp: Date.now(),
        has_meme: true,
        meme_id: meme.id,
        meme_src: meme.src
    }, submitButton); // Pass submitButton for inline notification
    
    // Scroll to new comment
    setTimeout(() => {
        newComment.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 50);
}

// Submit comment after personal attack detection
function submitCommentAfterDetection(commentData) {
    if (!commentData) return;
    
    const commentSection = commentData.submitButton.closest('.add-comment');
    const commentInput = commentSection.querySelector('.comment-input');
    const postElement = commentSection.closest('.post');
    const postId = postElement ? postElement.dataset.postId : 'unknown_post';
    
    // Get current username
    const username = localStorage.getItem('socialUserId');
    if (!username) {
        console.error('用戶未登入，無法儲存評論');
        showNotification('請先登入後再發表評論', 'error', commentData.submitButton);
        return;
    }
    
    // Generate unique comment ID
    const commentId = Date.now().toString();
    
    // Add comment to UI
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
            <p>${commentData.text}</p>
        </div>
    `;
    
    commentsList.appendChild(newComment);
    commentInput.value = '';
    
    // Regenerate avatars
    generateRandomAvatars();
    
    // Save to Firebase
    saveCommentToFirebase({
        text: commentData.text,
        user_id: username,
        post_id: postId,
        comment_id: commentId,
        is_attack: commentData.detectionResult.is_attack,
        attack_thinking: commentData.detectionResult.attack_thinking || '',
        answer: commentData.detectionResult.answer || '',
        emotion: commentData.detectionResult.emotion || '',
        emotion_thinking: commentData.detectionResult.emotion_thinking || '',
        timestamp: new Date().toISOString(),
        client_timestamp: Date.now()
    }, commentData.submitButton); // Pass the submit button to show inline notification
    
    // Scroll to new comment
    setTimeout(() => {
        newComment.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 50);
}

// Handle comment submission with personal attack detection
async function handleCommentSubmit(event) {
    if (event) {
        event.preventDefault();
    }
    
    const submitButton = this;
    const commentSection = submitButton.closest('.add-comment');
    const commentInput = commentSection.querySelector('.comment-input');
    const commentText = commentInput.value.trim();
    
    if (commentText === '') return;
    
    // Find detection results area and show processing indicator
    const detectionArea = commentSection.nextElementSibling;
    if (detectionArea && detectionArea.classList.contains('detection-results-area')) {
        const detectionProcess = detectionArea.querySelector('.detection-process');
        const detectionResults = detectionArea.querySelector('.detection-results');
        
        if (detectionProcess) detectionProcess.style.display = 'block';
        if (detectionResults) detectionResults.style.display = 'none';
        
        detectionArea.style.display = 'block';
    }
    
    try {
        // Get current username
        const username = localStorage.getItem('socialUserId');
        if (!username) {
            console.error('用戶未登入，無法儲存評論');
            showNotification('請先登入後再發表評論', 'error', submitButton);
            return;
        }
        
        // Check for personal attacks
        const detectionResult = await detectPersonalAttack(commentText);
        lastDetectionResult = detectionResult;
        
        
        if (detectionResult.is_attack) {
            showAttackDetectionInline(detectionResult, commentText, submitButton);
        } else {
            // If detection area is visible, hide it
            if (detectionArea && detectionArea.style.display === 'block') {
                hideDetectionResults(detectionArea);
            }
            
            // If not an attack, proceed with comment submission directly
            currentCommentData = {
                text: commentText,
                submitButton: submitButton,
                detectionResult: detectionResult
            };
            submitCommentAfterDetection(currentCommentData);
        }
    } catch (error) {
        console.error('評論提交過程中發生錯誤:', error);
        showNotification('評論發表時發生錯誤', 'error', submitButton); // Pass submitButton for inline notification
        
        // If detection area is visible, hide it
        if (detectionArea && detectionArea.style.display === 'block') {
            hideDetectionResults(detectionArea);
        }
    }
}

// Function to save comment to Firebase
async function saveCommentToFirebase(commentData, submitButton) {
    try {
        const database = firebase.database();
        
        // Use path structure: users/[username]/sender/comments/[postId]/[commentId]
        const commentRef = database.ref(`users/${commentData.user_id}/sender/comments/${commentData.post_id}/${commentData.comment_id}`);
        
        await commentRef.set(commentData);
        
        console.log('評論成功儲存到 Firebase');
        showNotification('評論已發表', 'success', submitButton); // Pass submitButton for inline notification
        
        // Remove activities logging
    } catch (error) {
        console.error('儲存評論到 Firebase 失敗:', error);
        showNotification('儲存評論時出現錯誤', 'error', submitButton); // Pass submitButton for inline notification
    }
}

// Function to initialize comment display
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
        const commentsRef = database.ref(`users/${username}/sender/comments`);
        
        commentsRef.once('value').then(snapshot => {
            if (!snapshot.exists()) {
                console.log('沒有找到之前的評論');
                return;
            }
            
            console.log('成功載入之前的評論');
            // Here you can choose whether to display previous comments in UI
        }).catch(error => {
            console.error('載入之前的評論時出錯:', error);
        });
    } catch (error) {
        console.error('嘗試載入評論時發生錯誤:', error);
    }
}

// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sender page DOM loaded');
    
    // Get current user
    const username = localStorage.getItem('socialUserId');
    if (!username) {
        console.error('未找到用戶名，重定向到登入頁面');
        window.location.href = '/';
        return;
    }
    
    console.log('當前用戶:', username);
    const pageContentWrapper = document.getElementById('page-content-wrapper');
    
    if (pageContentWrapper) {
        pageContentWrapper.classList.remove('hidden');
        
        // 處理情境說明顯示
        const startPostingBtn = document.getElementById('startPosting');
        const contextIntro = document.getElementById('context-introduction');
        const mainContent = document.getElementById('main-content');
        const postNavigation = document.querySelector('.post-navigation');
        
        // 在情境說明階段隱藏底部導航
        if (postNavigation && contextIntro && contextIntro.style.display !== 'none') {
            postNavigation.style.display = 'none';
        }
        
        if (startPostingBtn) {
            startPostingBtn.addEventListener('click', function() {
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
                
                // 記錄用戶開始發送的時間
                localStorage.setItem('senderPostingStartTime', new Date().toISOString());
                
                // 初始化主要功能
                initializeMainContent();
            });
        }
    }
});

// 將原本的初始化邏輯移到這個函數中
function initializeMainContent() {
    const username = localStorage.getItem('socialUserId');
    
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
    loadUserComments(username);
    
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
    
    // Remove page view logging to activities
    try {
        const database = firebase.database();
        const pageViewRef = database.ref(`users/${username}/sender/page_views`);
        pageViewRef.push().set({
            timestamp: new Date().toISOString(),
            action: 'viewed_sender_page',
            client_timestamp: Date.now()
        });
        
        // Remove activities logging
    } catch (error) {
        console.error('記錄頁面訪問時出錯:', error);
    }
    
    // Back button removed - users follow linear experiment flow
    
    // Add logout button functionality
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', showLogoutDialog);
    }
    
    // Listen for scroll events to save position
    window.addEventListener('scroll', debouncedSaveState);
    
    // Restore previous state
    restoreUserState();
    
    // Initialize meme selection UI
    initializeMemeSelection();
    
    // Setup meme toggle features for any existing meme comments
    setupMemeToggleFeatures();
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

// Initialize meme selection UI
function initializeMemeSelection() {
    const memeSelectionAreas = document.querySelectorAll('.meme-selection-area');
    
    memeSelectionAreas.forEach(area => {
        // Hide all meme selection areas on page load
        area.style.display = 'none';
        
        // Set up cancel buttons
        const cancelBtn = area.querySelector('.cancel-meme-btn');
        if (cancelBtn) {
            cancelBtn.onclick = function() {
                area.style.display = 'none';
            };
        }
    });
}

// New function to automatically use a recommended meme for post_1
function useRecommendedMeme(commentText, submitButton, detectionResult) {
    // Get the appropriate emotion-based meme
    const emotion = detectionResult.emotion || 'anger';
    
    // Get available meme files for this emotion
    let memeFiles = [];
    
    // Use the global memeImagesData if available
    if (typeof memeImagesData !== 'undefined' && memeImagesData[emotion] && memeImagesData[emotion].length > 0) {
        memeFiles = memeImagesData[emotion];
    }
    
    // Select a random meme from the available files
    let memeFilename;
    if (memeFiles.length > 0) {
        const randomIndex = Math.floor(Math.random() * memeFiles.length);
        memeFilename = memeFiles[randomIndex];
    } else {
        // Fallback if no meme files are found
        console.warn(`No meme files found for emotion: ${emotion}`);
        memeFilename = 'meme1.jpg'; // Fallback to a default name
    }
    
    // Create a simulated selected meme
    const recommendedMeme = {
        id: `${emotion}/${memeFilename}`,
        src: `/static/${emotion}/${memeFilename}`,
        alt: `${emotion} 迷因圖片`
    };
    
    // Show a notification that a meme was automatically selected
    showNotification('已自動選擇適合的迷因圖片', 'info', submitButton);
    
    // Submit using the recommended meme
    submitMemeComment(commentText, recommendedMeme, submitButton, detectionResult);
}

// Add new function to set up toggle behavior for all existing meme comments
function setupMemeToggleFeatures() {
    // Setup toggle buttons
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
        });
    });
    
    // Setup click event on meme images
    const memeImages = document.querySelectorAll('.meme-image');
    memeImages.forEach(img => {
        img.addEventListener('click', function() {
            const container = this.closest('.comment-toggle-container');
            const memeView = container.querySelector('.meme-view');
            const textView = container.querySelector('.text-view');
            const toggleBtn = container.querySelector('.toggle-view-btn');
            
            // Switch to text view when clicking on meme
            memeView.classList.remove('active');
            textView.classList.add('active');
            if (toggleBtn) toggleBtn.innerHTML = '<i class="fas fa-exchange-alt"></i> 查看迷因圖';
            
            // Save state
            debouncedSaveState();
        });
    });
}
