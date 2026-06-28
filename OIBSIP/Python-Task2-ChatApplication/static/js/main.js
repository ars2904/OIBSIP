// Main Client Application Logic

document.addEventListener('DOMContentLoaded', () => {
    let socket = null;
    let activeRoom = null;
    let isTyping = false;
    let typingTimeout = null;
    let notificationPermission = 'default';

    // DOM Elements - Auth
    const authContainer = document.getElementById('auth-container');
    const chatContainer = document.getElementById('chat-container');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const goToRegisterBtn = document.getElementById('go-to-register');
    const goToLoginBtn = document.getElementById('go-to-login');
    const loginError = document.getElementById('login-error');
    const registerError = document.getElementById('register-error');

    // DOM Elements - Sidebar
    const userDisplayName = document.getElementById('user-display-name');
    const roomSearchInput = document.getElementById('room-search');
    const roomsListContainer = document.getElementById('rooms-list-container');
    const roomsCounter = document.getElementById('rooms-counter');
    const createRoomForm = document.getElementById('create-room-form');
    const newRoomNameInput = document.getElementById('new-room-name');
    const createRoomError = document.getElementById('create-room-error');

    // DOM Elements - Chat Area
    const activeRoomTitle = document.getElementById('active-room-title');
    const messagesContainer = document.getElementById('messages-container');
    const typingIndicatorText = document.getElementById('typing-indicator-text');
    const chatInputForm = document.getElementById('chat-input-form');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const enableNotificationsBtn = document.getElementById('enable-notifications');
    const notifySound = document.getElementById('notify-sound');

    // DOM Elements - Emojis
    const emojiToggleBtn = document.getElementById('emoji-toggle-btn');
    const emojiPicker = document.getElementById('emoji-picker');
    const closeEmojiPicker = document.getElementById('close-emoji-picker');
    const emojiItems = document.querySelectorAll('.emoji-item');

    // Emoji Mapping
    const EMOJI_MAP = {
        ':smile:': '😊',
        ':laughing:': '😆',
        ':wink:': '😉',
        ':heart_eyes:': '😍',
        ':joy:': '😂',
        ':thinking:': '🤔',
        ':thumbsup:': '👍',
        ':thumbsdown:': '👎',
        ':ok_hand:': '👌',
        ':clap:': '👏',
        ':fire:': '🔥',
        ':heart:': '❤️',
        ':star:': '⭐',
        ':rocket:': '🚀',
        ':eyes:': '👀',
        ':sob:': '😭',
        ':rage:': '😡',
        ':scream:': '😱',
        ':party:': '🥳',
        ':wave:': '👋',
        ':plus1:': '👍',
        ':100:': '💯',
        ':poop:': '💩',
        ':ghost:': '👻'
    };

    // Initialize Notification State
    if ('Notification' in window) {
        notificationPermission = Notification.permission;
        updateNotificationButton();
    } else {
        enableNotificationsBtn.style.display = 'none';
    }

    // Connect socket if user is already logged in (Flask session cookie check)
    if (window.currentUser) {
        initSocket();
        loadRooms();
    }

    // --- Authentication Events ---
    
    // Switch to Register Form
    goToRegisterBtn.addEventListener('click', (e) => {
        e.preventDefault();
        loginForm.classList.add('hidden');
        loginForm.classList.remove('active');
        registerForm.classList.remove('hidden');
        registerForm.classList.add('active');
        loginError.textContent = '';
    });

    // Switch to Login Form
    goToLoginBtn.addEventListener('click', (e) => {
        e.preventDefault();
        registerForm.classList.add('hidden');
        registerForm.classList.remove('active');
        loginForm.classList.remove('hidden');
        loginForm.classList.add('active');
        registerError.textContent = '';
    });

    // Login Form Submit
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const secret = document.getElementById('login-password').value;
        loginError.textContent = '';

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password: secret })
            });
            const data = await response.json();
            if (data.success) {
                window.currentUser = username;
                userDisplayName.textContent = username;
                authContainer.classList.add('hidden');
                chatContainer.classList.remove('hidden');
                
                initSocket();
                loadRooms();
            } else {
                loginError.textContent = data.message;
            }
        } catch (err) {
            loginError.textContent = 'Server connection failed. Try again.';
        }
    });

    // Register Form Submit
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const secret = document.getElementById('register-password').value;
        registerError.textContent = '';

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password: secret })
            });
            const data = await response.json();
            if (data.success) {
                window.currentUser = username;
                userDisplayName.textContent = username;
                authContainer.classList.add('hidden');
                chatContainer.classList.remove('hidden');
                
                initSocket();
                loadRooms();
            } else {
                registerError.textContent = data.message;
            }
        } catch (err) {
            registerError.textContent = 'Registration failed. Try again.';
        }
    });


    // --- Socket.IO & Chat Logic ---

    function initSocket() {
        if (socket) return;
        
        socket = io({
            reconnectionAttempts: 5,
            timeout: 10000
        });

        socket.on('connect', () => {
            console.log('Connected to chat server');
            document.querySelector('.status-dot').className = 'status-dot online';
            document.querySelector('.status-text').textContent = 'Connected';
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from server');
            document.querySelector('.status-dot').className = 'status-dot offline';
            document.querySelector('.status-text').textContent = 'Disconnected';
        });

        // Handle incoming real-time messages
        socket.on('message', (msg) => {
            if (msg.is_system) {
                renderSystemMessage(msg);
            } else {
                renderMessage(msg);
                
                // Audio & Desktop Notification for incoming messages
                if (msg.username !== window.currentUser) {
                    playNotifySound();
                    
                    if (document.visibilityState !== 'visible' && notificationPermission === 'granted') {
                        new Notification(`New message in ${activeRoom}`, {
                            body: `${msg.username}: ${msg.message}`,
                            icon: 'https://cdn-icons-png.flaticon.com/512/1041/1041916.png'
                        });
                    }
                }
            }
        });

        // Handle loading message history
        socket.on('history', (data) => {
            if (data.room === activeRoom) {
                messagesContainer.innerHTML = '';
                if (data.messages.length === 0) {
                    messagesContainer.innerHTML = `
                        <div class="welcome-banner">
                            <i class="fa-solid fa-comments welcome-icon"></i>
                            <h3>Channel #${activeRoom}</h3>
                            <p>This is the start of message history. Send a message to start the conversation!</p>
                        </div>
                    `;
                } else {
                    data.messages.forEach(msg => {
                        renderMessage(msg);
                    });
                }
                scrollToBottom();
            }
        });

        // Handle Typing indicator broadcasts
        socket.on('typing_status', (data) => {
            if (data.is_typing) {
                typingIndicatorText.textContent = `${data.username} is typing...`;
            } else {
                typingIndicatorText.textContent = '';
            }
        });

        // Handle real-time room creation notification
        socket.on('room_created', (room) => {
            appendRoomItem(room);
            const count = parseInt(roomsCounter.textContent, 10);
            roomsCounter.textContent = count + 1;
        });

        socket.on('error_message', (data) => {
            alert(`Error: ${data.message}`);
        });
    }

    // Get list of rooms
    async function loadRooms() {
        try {
            const response = await fetch('/api/rooms');
            const data = await response.json();
            if (data.success) {
                roomsListContainer.innerHTML = '';
                roomsCounter.textContent = data.rooms.length;
                
                data.rooms.forEach(room => {
                    appendRoomItem(room);
                });

                // Auto-join first room "General" if present
                const generalRoom = data.rooms.find(r => r.name.toLowerCase() === 'general');
                if (generalRoom) {
                    joinRoom(generalRoom.name);
                }
            }
        } catch (err) {
            console.error('Failed to load rooms:', err);
        }
    }

    function appendRoomItem(room) {
        const item = document.createElement('div');
        item.className = 'room-item';
        item.dataset.roomName = room.name;
        if (activeRoom === room.name) {
            item.classList.add('active');
        }
        
        item.innerHTML = `
            <div class="room-icon"><i class="fa-solid fa-hashtag"></i></div>
            <span class="room-name">${escapeHTML(room.name)}</span>
        `;
        
        item.addEventListener('click', () => {
            joinRoom(room.name);
        });
        
        roomsListContainer.appendChild(item);
        filterRooms(); // Apply filter if search query exists
    }

    // Join a named room
    function joinRoom(roomName) {
        if (activeRoom === roomName) return;
        
        // Remove typing indicator from previous room
        typingIndicatorText.textContent = '';
        if (isTyping) {
            sendTypingStatus(false);
        }

        activeRoom = roomName;
        activeRoomTitle.textContent = `# ${roomName}`;
        
        // Update sidebar visual selection
        document.querySelectorAll('.room-item').forEach(item => {
            if (item.dataset.roomName === roomName) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Enable input fields
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.placeholder = `Message #${roomName}...`;
        messageInput.focus();

        // Emit Socket.IO join room event
        socket.emit('join', { room: roomName });
    }

    // Create New Room
    createRoomForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const roomName = newRoomNameInput.value.trim();
        createRoomError.textContent = '';

        if (!roomName) return;

        try {
            const response = await fetch('/api/rooms/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ room_name: roomName })
            });
            const data = await response.json();
            if (data.success) {
                newRoomNameInput.value = '';
                joinRoom(data.room.name);
            } else {
                createRoomError.textContent = data.message;
            }
        } catch (err) {
            createRoomError.textContent = 'Room creation failed.';
        }
    });

    // Send Message
    chatInputForm.addEventListener('submit', (e) => {
        e.preventDefault();
        let messageText = messageInput.value.trim();
        if (!messageText || !activeRoom) return;

        // Perform final emoji replacement
        messageText = replaceEmojiTokens(messageText);

        socket.emit('send_message', { message: messageText });
        messageInput.value = '';
        
        // Cancel typing status immediately
        if (isTyping) {
            sendTypingStatus(false);
        }
        messageInput.focus();
    });

    // --- Keyboard/Typing Events ---

    messageInput.addEventListener('input', () => {
        // Render emojis as user types if they match shortcodes
        const cursorPosition = messageInput.selectionStart;
        const originalText = messageInput.value;
        const replacedText = replaceEmojiTokens(originalText);
        
        if (originalText !== replacedText) {
            messageInput.value = replacedText;
            // Restore approximate cursor position
            const diff = replacedText.length - originalText.length;
            messageInput.setSelectionRange(cursorPosition + diff, cursorPosition + diff);
        }

        // Typing indicator trigger
        if (!isTyping) {
            isTyping = true;
            sendTypingStatus(true);
        }
        
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            isTyping = false;
            sendTypingStatus(false);
        }, 1500); // 1.5 seconds typing timeout
    });

    function sendTypingStatus(status) {
        if (socket && activeRoom) {
            socket.emit('typing', { room: activeRoom, is_typing: status });
        }
    }

    // --- Emoji Picker Events ---

    emojiToggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        emojiPicker.classList.toggle('hidden');
    });

    closeEmojiPicker.addEventListener('click', () => {
        emojiPicker.classList.add('hidden');
    });

    // Close emoji picker when clicking outside
    document.addEventListener('click', (e) => {
        if (!emojiPicker.contains(e.target) && e.target !== emojiToggleBtn) {
            emojiPicker.classList.add('hidden');
        }
    });

    // Click emoji item to insert
    emojiItems.forEach(item => {
        item.addEventListener('click', () => {
            const emojiUnicode = item.textContent;
            messageInput.value += emojiUnicode;
            emojiPicker.classList.add('hidden');
            messageInput.focus();
            
            // Fire input event to trigger send status
            const event = new Event('input', { bubbles: true });
            messageInput.dispatchEvent(event);
        });
    });

    // Parse `:emoji_code:` shortcodes in text strings
    function replaceEmojiTokens(text) {
        let result = text;
        for (const [shortcode, unicode] of Object.entries(EMOJI_MAP)) {
            result = result.replaceAll(shortcode, unicode);
        }
        return result;
    }

    // --- Search Rooms Filter ---

    roomSearchInput.addEventListener('input', filterRooms);

    function filterRooms() {
        const query = roomSearchInput.value.toLowerCase().trim();
        const items = document.querySelectorAll('.room-item');
        
        items.forEach(item => {
            const name = item.dataset.roomName.toLowerCase();
            if (name.includes(query)) {
                item.classList.remove('hidden');
            } else {
                item.classList.add('hidden');
            }
        });
    }

    // --- Render Messages helper functions ---

    function renderMessage(msg) {
        const wrapper = document.createElement('div');
        const isOutgoing = msg.username === window.currentUser;
        wrapper.className = `message-wrapper ${isOutgoing ? 'outgoing' : 'incoming'}`;
        
        const timestamp = msg.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        wrapper.innerHTML = `
            <div class="message-meta">
                <span class="message-sender">${escapeHTML(msg.username)}</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-bubble">
                ${escapeHTML(msg.message)}
            </div>
        `;
        
        messagesContainer.appendChild(wrapper);
        scrollToBottom();
    }

    function renderSystemMessage(msg) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message-wrapper system';
        
        wrapper.innerHTML = `
            <div class="message-bubble">
                ${escapeHTML(msg.message)}
            </div>
        `;
        
        messagesContainer.appendChild(wrapper);
        scrollToBottom();
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function escapeHTML(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // --- Notification & Audio Helpers ---

    enableNotificationsBtn.addEventListener('click', async () => {
        if (!('Notification' in window)) return;
        
        if (Notification.permission !== 'granted') {
            const permission = await Notification.requestPermission();
            notificationPermission = permission;
            updateNotificationButton();
        }
    });

    function updateNotificationButton() {
        if (notificationPermission === 'granted') {
            enableNotificationsBtn.classList.add('active');
            enableNotificationsBtn.title = 'Desktop Notifications Enabled';
            enableNotificationsBtn.querySelector('i').className = 'fa-solid fa-bell';
        } else {
            enableNotificationsBtn.classList.remove('active');
            enableNotificationsBtn.title = 'Enable Desktop Notifications';
            enableNotificationsBtn.querySelector('i').className = 'fa-solid fa-bell-slash';
        }
    }

    function playNotifySound() {
        try {
            notifySound.currentTime = 0;
            notifySound.play();
        } catch (e) {
            // Audio policy might block playing until user interacts
            console.log('Audio playback delayed or blocked by browser policy');
        }
    }
});
