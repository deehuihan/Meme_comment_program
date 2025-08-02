(function() {
    const images = JSON.parse(document.getElementById('images-data').textContent);
    const playerName = document.getElementById('player-name').textContent;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    let currentImageIndex = 0;
    let debounceTimeout;
    let selectedIndex = null;
    let keysPressed = {};
    let lastActionTime = 0;
    let modalShown = false; // Flag to check if any modal is shown
    let actionCooldown = false; // Flag to prevent rapid actions

    // 防止瀏覽器回退
    function preventBackNavigation() {
        window.history.pushState(null, null, window.location.href);
        window.addEventListener('popstate', function() {
            window.history.pushState(null, null, window.location.href);
            alert('為了保持遊戲的完整性，請勿使用瀏覽器的返回按鈕。');
        });
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

    function loadImage() {
        if (currentImageIndex < images.length) {
            const imagePath = `/static/socialmedia+meme_practice/${images[currentImageIndex]}`;
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
            resetOptions();
        } else {
            // Show modal instead of direct redirect
            document.getElementById('gameStartModal').style.display = 'flex';
            modalShown = true; // Set the flag when modal is shown
        }
    }

    function startGame() {
        // 使用 CSRF 令牌發送請求
        fetch('/clear_session_and_redirect', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            }
        }).then(() => {
            window.location.href = `/game/${playerName}`;
        }).catch(error => {
            console.error('Error:', error);
            window.location.href = `/game/${playerName}`;
        });
    }

    function highlightOption(index) {
        const options = document.querySelectorAll('.option');
        options.forEach(option => {
            option.classList.remove('selected');
            option.style.backgroundColor = ''; // Reset background color
            option.style.color = ''; // Reset text color
        });
        if (index !== null) {
            options[index].classList.add('selected');
            options[index].style.backgroundColor = '#0056b3';
            options[index].style.color = 'white';
        }
    }

    // 更新進度顯示函數，使用 CSS 變量設置進度條寬度
    function updateProgressDisplay() {
        const progressDisplay = document.getElementById('progress-display');
        if (!progressDisplay) return;
        
        const currentIndex = currentImageIndex;  // 不加1，初始為0
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
        const progressSegments = 5; // 分5段進度條
        const currentSegment = Math.floor((currentIndex / totalImages) * progressSegments);
        const progressPercent = (currentSegment / progressSegments) * 100;
        
        // 設置進度百分比
        progressDisplay.style.setProperty('--progress-percent', `${progressPercent}%`);
    }

    function selectOption(index) {
        highlightOption(index);
        selectedIndex = index;
    }

    function confirmSelection() {
        if (selectedIndex === null) return;

        setTimeout(() => {
            currentImageIndex++;
            loadImage();
            selectedIndex = null; // Reset selected index
        }, 100);
    }

    function handleRapidActions() {
        const currentTime = Date.now();
        if (currentTime - lastActionTime < 100) {
            return true;
        }
        lastActionTime = currentTime;
        return false;
    }

    function resetOptions() {
        const options = document.querySelectorAll('.option');
        options.forEach(option => {
            option.classList.remove('selected');
            option.style.backgroundColor = ''; // Reset background color
            option.style.color = ''; // Reset text color
        });
        selectedIndex = null;
    }

    function setActionCooldown() {
        actionCooldown = true;
        setTimeout(() => {
            actionCooldown = false;
        }, 100); // 100ms cooldown period
    }

    document.addEventListener('keydown', (event) => {
        // 如果模態框已顯示，優先處理 Enter 鍵
        if (modalShown) {
            if (event.key === 'Enter') {
                const startGameButton = document.getElementById('start-game-button');
                if (startGameButton) {
                    startGameButton.click();
                }
                return;
            }
        }

        if (actionCooldown) return;

        keysPressed[event.key] = true;

        // 檢查是否按下多個鍵
        if (Object.keys(keysPressed).length > 1) {
            keysPressed = {};
            return;
        }

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
                confirmSelection();
                setActionCooldown();
                return;
            default:
                return;
        }
        if (handleRapidActions()) return;
        selectOption(index);
        setActionCooldown();
    });

    document.addEventListener('keyup', (event) => {
        if (modalShown) return;

        delete keysPressed[event.key];

        if (debounceTimeout) clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => debounceTimeout = null, 200);
    });

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

    // 禁用滑鼠點擊選項
    document.querySelectorAll('.option').forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        });
    });

    // 禁用滑鼠點擊按鈕
    document.querySelector('.confirm-button').addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        return false;
    });

    // 初始化
    preventBackNavigation();
    
    // 檢查參與情況
    if (!checkPreviousParticipation()) {
        loadImage();
    }

    // 導出 startGame 函數到全局作用域
    window.startGame = startGame;
})();