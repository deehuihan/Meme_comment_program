// static/js/game_utils.js

// 創建一個命名空間來存放共用函數
const GameUtils = {
    // 獲取 cookie 函數
    getCookie: function(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    },

    // 檢查之前是否已參與過遊戲（透過 cookie）
    checkPreviousParticipation: function() {
        const participated = this.getCookie('participated');
        if (participated === 'true') {
            alert('您似乎已經參與過此遊戲。每人僅限參與一次。');
            window.location.href = '/'; // 重定向到首頁
            return true;
        }
        return false;
    },

    // 防止返回上一頁
    preventBackNavigation: function() {
        window.history.pushState(null, null, window.location.href);
        window.addEventListener('popstate', function() {
            window.history.pushState(null, null, window.location.href);
            alert('為了保持遊戲的完整性，請勿使用瀏覽器的返回按鈕。');
        });
    },

    // 高亮選項
    highlightOption: function(index) {
        const options = document.querySelectorAll('.option');
        options.forEach(option => {
            option.classList.remove('selected');
            option.style.backgroundColor = ''; // Reset background color
            option.style.color = ''; // Reset text color
        });
        if (index !== null && index >= 0 && index < options.length) {
            options[index].classList.add('selected');
            options[index].style.backgroundColor = '#0056b3'; // Example highlight color
            options[index].style.color = 'white'; // Example highlight text color
        }
    },

    // 重置選項樣式
    resetOptions: function() {
        const options = document.querySelectorAll('.option');
        options.forEach(option => {
            option.classList.remove('selected');
            option.style.backgroundColor = ''; // Reset background color
            option.style.color = ''; // Reset text color
        });
        // 注意：這裡不重置 selectedIndex，由呼叫它的地方處理
    },

    // 處理快速操作（防止連按）- 簡易版本
    // 返回 true 表示操作過快，應忽略；返回 false 表示可以執行
    // 需要一個外部變數來追蹤上次操作時間，這裡假設傳入和傳出
    handleRapidActions: function(lastActionTime, threshold = 100) {
        const currentTime = Date.now();
        if (currentTime - lastActionTime < threshold) {
            return { tooRapid: true, newTime: lastActionTime };
        }
        return { tooRapid: false, newTime: currentTime };
    },

    // 設置冷卻時間 - 簡易版本
    // 需要一個外部變數來追蹤是否在冷卻中
    // 返回 true 表示設置了冷卻，外部應更新冷卻狀態；返回 false (理論上不會)
    setActionCooldown: function(cooldownSetter, duration = 100) {
       cooldownSetter(true); // 設置外部的冷卻狀態為 true
        setTimeout(() => {
            cooldownSetter(false); // 指定時間後設置外部的冷卻狀態為 false
        }, duration);
        return true; // 表示已啟動冷卻
    },

    // 模擬按下空白鍵時按鈕的視覺效果
    animateSpacebarPress: function(buttonSelector) {
        const confirmButton = document.querySelector(buttonSelector);
        if (confirmButton) {
            confirmButton.classList.add('space-active'); // 假設有 .space-active 的 CSS 樣式
            // 按下時添加樣式
            document.addEventListener('keyup', function spacebarUp(event) {
                if (event.code === 'Space') {
                    if (confirmButton) {
                        confirmButton.classList.remove('space-active');
                    }
                    // 移除監聽器，避免重複
                    document.removeEventListener('keyup', spacebarUp);
                }
            }, { once: true }); // 使用 once 選項確保監聽器只觸發一次後自動移除
        }
    },

    // 禁用指定選擇器的元素的點擊事件
    disableMouseClick: function(selector) {
         document.querySelectorAll(selector).forEach(element => {
            element.addEventListener('click', function(e) {
                // 允許程式觸發的點擊（例如 .click()）
                if (!e.isTrusted) {
                    return true;
                }
                e.preventDefault();
                e.stopPropagation();
                console.warn(`Mouse click disabled for: ${selector}`); // 可選的警告
                return false;
            });
        });
    }
};