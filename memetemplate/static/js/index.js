(function() {
    const imagesDataElement = document.getElementById('images-data');
    const playerNameElement = document.getElementById('player-name');
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    if (!imagesDataElement || !playerNameElement) {
        console.error('Required data elements are missing.');
        return;
    }

    // 檢查之前是否已參與過遊戲（透過 cookie）
    function checkPreviousParticipation() {
        const participated = getCookie('participated');
        if (participated === 'true') {
            alert('您似乎已經參與過此遊戲。每人僅限參與一次。');
            window.location.href = '/';
            return true;
        }
        return false;
    }

    // 獲取 cookie 函數
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // 防止返回上一頁
    function preventBackNavigation() {
        window.history.pushState(null, null, window.location.href);
        window.addEventListener('popstate', function() {
            window.history.pushState(null, null, window.location.href);
            alert('為了保持遊戲的完整性，請勿使用瀏覽器的返回按鈕。');
        });
    }

    const images = JSON.parse(imagesDataElement.textContent);
    const playerName = playerNameElement.textContent;
    let currentImageIndex = 0;
    let debounce = false;
    let selectedIndex = null;
    let timerInterval;
    let keysPressed = {};
    let lastActionTime = 0;
    let debounceTimeout;
    let modalShown = false;
    let actionCooldown = false;
    let taskCompleted = false; // 追蹤任務是否完成

    // 加載圖片並更新進度
    function loadImage() {
        if (currentImageIndex < images.length) {
            const imagePath = `/selected_images/${images[currentImageIndex]}`;
            const imageElement = document.getElementById('image');
            
            // 添加載入圖片的錯誤處理
            imageElement.onerror = function() {
                console.error(`無法載入圖片: ${imagePath}`);
                const fallbackPath = '/static/fallback-image.png'; // 確保有一個預設圖片
                if (imagePath !== fallbackPath) {
                    this.src = fallbackPath;
                }
            };
            
            imageElement.src = imagePath;
            updateProgressDisplay();
            resetTimer();
            resetOptions();
        } else {
            clearInterval(timerInterval);
            document.getElementById('gameEndModal').style.display = 'flex';
            taskCompleted = true; // 完成任務後設置 taskCompleted 為 true
            modalShown = true; // 標記 modal 已顯示
            
            // 使用 CSRF 令牌發送請求
            fetch('/clear_session_and_redirect', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                }
            });
        }
    }

    // 提交標註
    async function submitLabel(imageName, label) {
        if (debounce) return;
        debounce = true;

        const timerDisplay = document.getElementById('timer-display');
        const currentTime = timerDisplay ? timerDisplay.textContent.replace('Time: ', '') : '';

        try {
            const response = await fetch(`/label/${playerName}`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken // Include CSRF token here
                },
                body: JSON.stringify({ 
                    image_name: imageName, 
                    label: label,
                    response_time: currentTime
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.message) {
                currentImageIndex++;
                resetTimer();
                loadImage();
            } else {
                console.error('Error:', data.error);
                alert('提交失敗');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('發生錯誤');
        } finally {
            debounce = false;
        }
    }

    // 高亮選項
    function highlightOption(index) {
        const options = document.querySelectorAll('.option');
        options.forEach(option => {
            option.classList.remove('selected');
            option.style.backgroundColor = '';
            option.style.color = '';
        });
        if (index !== null) {
            options[index].classList.add('selected');
            options[index].style.backgroundColor = '#0056b3';
            options[index].style.color = 'white';
        }
    }

    // 處理快速操作（防止連按）
    function handleRapidActions() {
        const currentTime = Date.now();
        if (currentTime - lastActionTime < 100) { // 降低閾值避免錯誤觸發
            return true;
        }
        lastActionTime = currentTime;
        return false;
    }

    // 重置選項
    function resetOptions() {
        const options = document.querySelectorAll('.option');
        options.forEach(option => {
            option.classList.remove('selected');
            option.style.backgroundColor = '';
            option.style.color = '';
        });
        selectedIndex = null;
    }

    // 設置冷卻時間，避免頻繁操作
    function setActionCooldown() {
        actionCooldown = true;
        setTimeout(() => {
            actionCooldown = false;
        }, 100); // 縮短冷卻時間
    }

    // 確認選擇
    function confirmSelection() {
        if (selectedIndex === null) return;
        setTimeout(() => {
            submitLabel(
                images[currentImageIndex],
                document.querySelectorAll('.option')[selectedIndex].textContent.trim()
            );
            selectedIndex = null;
        }, 0);
    }

    // 監聽鍵盤事件
    document.addEventListener('keydown', (event) => {
        // 如果遊戲結束對話框顯示，只處理 Enter 鍵
        const gameEndModalVisible = document.getElementById('gameEndModal')?.style.display === 'flex';
        if (gameEndModalVisible || actionCooldown) {
            if (event.key === 'Enter') {
                const viewResultsButton = document.querySelector('.modal-button');
                if (viewResultsButton) {
                    viewResultsButton.click();
                }
            }
            return;
        }
        
        keysPressed[event.key] = true;

        let index;
        switch (event.key) {
            case 'ArrowUp':
                index = 0;
                break;
            case 'ArrowLeft':
                index = 1;
                break;
            case 'ArrowRight':
                index = 2;
                break;
            case 'ArrowDown':
                index = 3;
                break;
            case ' ':
                if (selectedIndex !== null && !modalShown) { // 按空白鍵時不會顯示 modal
                    confirmSelection(); // 確認選擇
                    setActionCooldown();
                }
                return;
            default:
                return;
        }

        if (handleRapidActions()) return;

        highlightOption(index);
        selectedIndex = index;
        setActionCooldown();
    });

    // 防止在任務完成前離開頁面
    window.addEventListener('beforeunload', function (e) {
        if (!taskCompleted) {
            e.preventDefault();
            e.returnValue = '您確定要離開嗎？您的進度將不會被保存。'; // 這會顯示瀏覽器的原生警告
            return e.returnValue;
        }
    });

    // 更新進度顯示 - 只在開始為0，結束為100%
    function updateProgressDisplay() {
        const progressDisplay = document.getElementById('progress-display');
        const currentIndex = currentImageIndex;  // 注意這裡改為不加1，因為我們希望初始顯示為0
        const totalImages = images.length;
        
        // 如果是第一張圖片，顯示為0%
        if (currentIndex === 0) {
            progressDisplay.style.setProperty('--progress-percent', '0%');
            return;
        }
        
        // 如果是最後一張圖片(或已完成)，顯示為100%
        if (currentIndex >= totalImages) {
            progressDisplay.style.setProperty('--progress-percent', '100%');
            return;
        }
        
        // 中間階段，使用分段進度
        // 將進度條分為幾個段，從1到n-1
        const progressSegments = 18; // 分5段進度條
        
        // 計算當前應處於哪個段
        const currentSegment = Math.floor((currentIndex / totalImages) * progressSegments);
        
        // 計算對應的百分比
        const progressPercent = (currentSegment / progressSegments) * 100;
        
        // 設置進度百分比
        progressDisplay.style.setProperty('--progress-percent', `${progressPercent}%`);
    }

    // 重置計時器
    function resetTimer() {
        clearInterval(timerInterval);
        const timerDisplay = document.getElementById('timer-display');
        if (timerDisplay) {
            timerDisplay.textContent = 'Time: 00:00:00.000';
        }
        
        let startTime = Date.now();
        timerInterval = setInterval(() => {
            const elapsedTime = Date.now() - startTime;
            const milliseconds = elapsedTime % 1000;
            const seconds = Math.floor(elapsedTime / 1000) % 60;
            const minutes = Math.floor(elapsedTime / (1000 * 60)) % 60;
            const hours = Math.floor(elapsedTime / (1000 * 60 * 60));

            if (timerDisplay) {
                timerDisplay.textContent = `Time: ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`;
            }
        }, 100);
    }

    document.addEventListener('keydown', function(event) {
        if (event.code === 'Space') {
            const confirmButton = document.querySelector('.confirm-button');
            if (confirmButton) {
                confirmButton.classList.add('space-active');
            }
        }
    });
    
    document.addEventListener('keyup', function(event) {
        if (event.code === 'Space') {
            const confirmButton = document.querySelector('.confirm-button');
            if (confirmButton) {
                confirmButton.classList.remove('space-active');
                confirmButton.click(); // Trigger the button click event
            }
        }
    });
    
    // 禁用鼠標事件
    document.querySelectorAll('.option, .confirm-button').forEach(element => {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        });
    });

    // 處理模態框按鈕 - 只允許鍵盤操作
    document.querySelectorAll('.modal-button').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!e.isTrusted) {
                // 允許通過代碼觸發的點擊事件
                return true;
            }
            e.preventDefault();
            e.stopPropagation();
            return false;
        });
    });

    document.getElementById('viewResultsButton').addEventListener('click', function () {
        const button = this;
    
        // 禁用按鈕以防止多次點擊
        button.disabled = true;
        button.textContent = '正在跳轉...';
    
        // 跳轉到 summary 頁面
        const playerName = document.getElementById('player-name').textContent.trim();
        window.location.href = `/summary/${playerName}`;
    });
    
    // 禁用所有tabindex，防止鼠標點擊選擇
    document.querySelectorAll('[tabindex]').forEach(element => {
        element.setAttribute('tabindex', '-1');
    });

    // 初始化
    preventBackNavigation();
    
    // 只在開始時檢查一次是否已參與
    if (!checkPreviousParticipation()) {
        loadImage(); // 初始化加載第一張圖片
    }
})();