// 帖文切換控制邏輯
// 全局變量來跟蹤已提交的帖文
let submittedPosts = new Set();
let totalPosts = 8; // 總帖文數量

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

// 修改提交按鈕邏輯
function setupSubmitButtonLogic() {
    const submitButtons = document.querySelectorAll('.submit-receiver-survey-btn');
    
    submitButtons.forEach((button, index) => {
        button.addEventListener('click', function(event) {
            // 防止默認行為
            event.preventDefault();
            event.stopPropagation();
            
            // 標記當前帖文為已提交
            submittedPosts.add(window.currentPost || 0);
            
            // 更新navigation狀態
            updateNavigationStatus();
            
            // 顯示提交成功訊息
            if (typeof showNotification === 'function') {
                showNotification('帖文已提交成功！', 'success');
            } else {
                alert('帖文已提交成功！');
            }
            
            // 如果還有下一個帖文，自動跳轉
            const nextPost = (window.currentPost || 0) + 1;
            if (nextPost < totalPosts) {
                setTimeout(() => {
                    if (typeof showPost === 'function') {
                        showPost(nextPost);
                    }
                }, 1500); // 1.5秒後自動跳轉
            } else {
                // 所有帖文都完成了
                if (typeof showNotification === 'function') {
                    showNotification('所有帖文都已完成！', 'success');
                } else {
                    alert('所有帖文都已完成！');
                }
            }
        }, true); // 使用捕獲階段
    });
}

// 攔截navigation dots的點擊事件
function setupNavigationControl() {
    const navigationDots = document.querySelectorAll('.nav-dot');
    
    navigationDots.forEach((dot, index) => {
        dot.addEventListener('click', function(event) {
            // 檢查是否可以訪問該帖文
            if (!canAccessPost(index)) {
                event.preventDefault();
                event.stopPropagation();
                
                if (typeof showNotification === 'function') {
                    showNotification('請先完成前面的帖文再繼續', 'warning');
                } else {
                    alert('請先完成前面的帖文再繼續');
                }
                return false;
            }
        }, true); // 使用捕獲階段，優先處理
    });
}

// 監控showPost函數的調用
function interceptShowPost() {
    if (typeof window.showPost === 'function') {
        const originalShowPost = window.showPost;
        
        window.showPost = function(index) {
            // 檢查是否可以訪問該帖文
            if (!canAccessPost(index)) {
                if (typeof showNotification === 'function') {
                    showNotification('請先完成前面的帖文再繼續', 'warning');
                } else {
                    alert('請先完成前面的帖文再繼續');
                }
                return;
            }
            
            // 更新當前帖文索引
            window.currentPost = index;
            
            // 調用原始函數
            originalShowPost.call(this, index);
            
            // 更新navigation狀態
            updateNavigationStatus();
        };
    }
}

// 初始化所有控制邏輯
function initializePostNavigationControl() {
    // 設置初始狀態
    window.currentPost = 0;
    
    // 設置提交按鈕邏輯
    setupSubmitButtonLogic();
    
    // 設置navigation控制
    setupNavigationControl();
    
    // 攔截showPost函數
    interceptShowPost();
    
    // 更新初始狀態
    updateNavigationStatus();
    
    console.log('Post navigation control initialized');
}

// 頁面載入時初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(initializePostNavigationControl, 1000);
    });
} else {
    setTimeout(initializePostNavigationControl, 1000);
}

// 導出函數供全局使用
window.canAccessPost = canAccessPost;
window.updateNavigationStatus = updateNavigationStatus;
window.submittedPosts = submittedPosts;
