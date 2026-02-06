/**
 * Link & Learn - Session Page JavaScript
 * WebSocket-driven implementation for Real-time Whiteboard, IDE, Video, and Chat.
 */

document.addEventListener('DOMContentLoaded', function () {
    const sessionPage = document.querySelector('.session-page');
    if (!sessionPage) return;

    const sessionId = sessionPage.dataset.sessionId;
    const userId = sessionPage.dataset.userId;
    const username = sessionPage.dataset.username || 'User';

    // WebSocket Setup
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socketUrl = `${protocol}//${window.location.host}/ws/session/${sessionId}/`;
    const chatSocket = new WebSocket(socketUrl);

    chatSocket.onopen = function (e) { console.log('WebSocket connection established'); };
    chatSocket.onclose = function (e) { console.error('WebSocket connection closed unexpectedly'); };

    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        handleSocketMessage(data);
    };

    function sendSocketMessage(type, payload) {
        if (chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({ type: type, ...payload }));
        }
    }

    function handleSocketMessage(data) {
        switch (data.type) {
            case 'chat_message': appendMessage(data); break;
            case 'whiteboard': handleWhiteboardUpdate(data.data); break;
            case 'code_change': handleCodeUpdate(data); break;
            case 'video_signal_message': case 'video_signal': handleVideoSignal(data.data); break;
            case 'timer': handleTimerUpdate(data); break;
            case 'session_ended':
                alert('Session has ended.');
                window.location.href = data.redirect_url;
                break;
        }
    }

    // ============================================
    // State Persistence
    // ============================================
    let isDirty = false;
    setInterval(() => { if (isDirty) saveState(); }, 10000);

    function saveState() {
        const payload = {
            whiteboard: JSON.stringify(canvas.toJSON()),
            ide_code: editorInstance ? editorInstance.getValue() : '',
            ide_language: languageSelect.value
        };

        fetch(`/session/${sessionId}/save-state/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
            body: JSON.stringify(payload)
        }).then(() => { isDirty = false; });
    }

    function getCsrfToken() {
        return document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    }

    // ============================================
    // Tools / Tabs
    // ============================================
    const tabBtns = document.querySelectorAll('.tab-btn');
    const toolPanels = document.querySelectorAll('.tool-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const tab = this.dataset.tab;
            tabBtns.forEach(b => b.classList.remove('active'));
            toolPanels.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            document.getElementById(`${tab}-panel`).classList.add('active');
            if (tab === 'ide' && editorInstance) editorInstance.layout();
        });
    });

    // ============================================
    // Chat
    // ============================================
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');

    function appendMessage(msg) {
        const div = document.createElement('div');
        div.className = 'message ' + (msg.sender_id == userId ? 'sent' : 'received');
        div.innerHTML = `<div class="message-content">${escapeHtml(msg.content)}</div><div class="message-time">${escapeHtml(msg.sender || 'Unknown')}</div>`;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    sendMessageBtn.addEventListener('click', () => {
        const content = chatInput.value.trim();
        if (content) {
            sendSocketMessage('chat', { content: content });
            chatInput.value = '';
        }
    });

    chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessageBtn.click(); });
    function escapeHtml(text) { const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }

    fetch(`/chat/session/${sessionId}/`).then(res => res.json()).then(data => {
        if (data.messages) { chatMessages.innerHTML = ''; data.messages.forEach(appendMessage); }
    });

    // ============================================
    // IDE (Pyodide & Generic)
    // ============================================
    let editorInstance = null;
    let isRemoteUpdate = false;
    const languageSelect = document.getElementById('languageSelect');
    let pyodide = null;
    const outputConsole = document.getElementById('outputConsole');
    const ideStatus = document.getElementById('ideStatus');

    require(['vs/editor/editor.main'], function () {
        editorInstance = monaco.editor.create(document.getElementById('monaco-editor'), {
            value: typeof initialIdeCode !== 'undefined' ? initialIdeCode : '// Start coding...',
            language: typeof initialIdeLanguage !== 'undefined' ? initialIdeLanguage : 'javascript',
            theme: 'vs-light', automaticLayout: true
        });
        if (typeof initialIdeLanguage !== 'undefined') languageSelect.value = initialIdeLanguage;

        editorInstance.onDidChangeModelContent(() => {
            if (!isRemoteUpdate) {
                isDirty = true;
                sendSocketMessage('code_change', {
                    code: editorInstance.getValue(),
                    language: languageSelect.value
                });
            }
        });
    });

    languageSelect.addEventListener('change', function () {
        const newLang = this.value;
        if (editorInstance) {
            monaco.editor.setModelLanguage(editorInstance.getModel(), newLang);
            sendSocketMessage('code_change', { code: editorInstance.getValue(), language: newLang });
        }
    });

    async function initPyodideLoad() {
        if (typeof loadPyodide === 'undefined') return;
        ideStatus.textContent = 'Loading Python...';
        try {
            pyodide = await loadPyodide();
            ideStatus.textContent = 'Python Ready';
            logToConsole('Python environment loaded.');
        } catch (err) {
            ideStatus.textContent = 'Failed to load';
            console.error(err);
        }
    }
    initPyodideLoad();

    function logToConsole(text, isError = false) {
        const span = document.createElement('div'); // Using div for block display
        span.textContent = text;
        if (isError) span.style.color = '#d32f2f'; // Dark red for errors
        else span.style.color = '#cccccc'; // Light gray for normal output
        outputConsole.appendChild(span);
        outputConsole.scrollTop = outputConsole.scrollHeight;
    }

    const runBtn = document.getElementById('runCodeBtn');
    if (runBtn) {
        runBtn.addEventListener('click', async () => {
            if (!editorInstance) return;
            const code = editorInstance.getValue();
            const lang = languageSelect.value;

            outputConsole.innerHTML = '';
            logToConsole(`> Running ${lang}...`);

            if (lang === 'python') {
                if (!pyodide) {
                    logToConsole('Python is still loading, please wait...', true);
                    return;
                }
                try {
                    pyodide.setStdout({ batched: (msg) => logToConsole(msg) });
                    pyodide.setStderr({ batched: (msg) => logToConsole(msg, true) });
                    await pyodide.runPythonAsync(code);
                } catch (err) {
                    logToConsole(err.toString(), true);
                }
            } else {
                // Javascript or others (treated as JS for now for execution)
                // If users selects other languages, we warn them, but for JS we exec
                if (lang === 'javascript') {
                    const oldLog = console.log;
                    console.log = (...args) => {
                        logToConsole(args.join(' '));
                        oldLog.apply(console, args);
                    };
                    try {
                        const f = new Function(`return (async () => { ${code} })()`);
                        await f();
                    } catch (err) {
                        logToConsole(err.toString(), true);
                    }
                    console.log = oldLog;
                } else {
                    logToConsole(`Execution for ${lang} is simulated. (No backend runner)`, true);
                }
            }
        });
    }

    function handleCodeUpdate(data) {
        if (!editorInstance) return;
        isRemoteUpdate = true;
        const currentPosition = editorInstance.getPosition();
        if (editorInstance.getValue() !== data.code) {
            editorInstance.setValue(data.code);
            editorInstance.setPosition(currentPosition);
        }
        if (data.language && data.language !== languageSelect.value) {
            languageSelect.value = data.language;
            monaco.editor.setModelLanguage(editorInstance.getModel(), data.language);
        }
        isRemoteUpdate = false;
    }

    // ============================================
    // Whiteboard (Fabric.js)
    // ============================================
    const canvas = new fabric.Canvas('whiteboard', {
        isDrawingMode: true,
        backgroundColor: 'rgba(255, 255, 255, 1)',
        width: 3000, height: 2000
    });

    // Initial State Load
    if (typeof initialWhiteboard !== 'undefined' && initialWhiteboard && initialWhiteboard !== "{}") {
        try {
            if (initialWhiteboard.trim().startsWith('{')) {
                canvas.loadFromJSON(initialWhiteboard, canvas.renderAll.bind(canvas));
            } else {
                fabric.Image.fromURL(initialWhiteboard, function (img) { canvas.add(img); });
            }
        } catch (e) { console.error("Error loading whiteboard state", e); }
    }

    canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
    canvas.freeDrawingBrush.width = 3;
    canvas.freeDrawingBrush.color = '#000000';

    let currentTool = 'pen';
    let currentColor = '#000000';
    let brushSize = 3;

    function activateTool(toolName) {
        currentTool = toolName;
        // Update UI
        document.querySelectorAll('[data-tool]').forEach(b => {
            b.classList.toggle('active', b.dataset.tool === toolName);
        });

        // Configure Fabric
        canvas.isDrawingMode = false;
        canvas.selection = false;
        canvas.defaultCursor = 'default';

        if (toolName === 'pen') {
            canvas.isDrawingMode = true;
            canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
            canvas.freeDrawingBrush.width = brushSize;
            canvas.freeDrawingBrush.color = currentColor;
        } else if (toolName === 'eraser') {
            canvas.isDrawingMode = true;
            canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
            canvas.freeDrawingBrush.width = brushSize * 5;
            canvas.freeDrawingBrush.color = '#ffffff';
        } else if (toolName === 'select') {
            canvas.selection = true;
        } else if (toolName === 'text') {
            canvas.selection = false;
            canvas.defaultCursor = 'text';
        }
    }

    document.querySelectorAll('[data-tool]').forEach(btn => {
        btn.addEventListener('click', function () {
            activateTool(this.dataset.tool);
        });
    });

    document.getElementById('colorPicker').addEventListener('change', function () {
        currentColor = this.value;
        if (currentTool === 'pen') {
            canvas.freeDrawingBrush.color = currentColor;
        }
        const activeObj = canvas.getActiveObject();
        if (activeObj) {
            if (activeObj.type === 'i-text') activeObj.set('fill', currentColor);
            else activeObj.set('stroke', currentColor);
            canvas.requestRenderAll();
            canvas.fire('object:modified', { target: activeObj });
        }
    });

    document.getElementById('brushSize').addEventListener('input', function () {
        brushSize = parseInt(this.value);
        if (currentTool === 'pen') canvas.freeDrawingBrush.width = brushSize;
        if (currentTool === 'eraser') canvas.freeDrawingBrush.width = brushSize * 5;
    });

    document.getElementById('deleteSelected').addEventListener('click', function () {
        const activeObjects = canvas.getActiveObjects();
        if (activeObjects.length) {
            canvas.discardActiveObject();
            activeObjects.forEach(obj => { canvas.remove(obj); });
        }
    });

    document.getElementById('clearCanvas').addEventListener('click', function () {
        if (confirm("Clear entire whiteboard?")) {
            canvas.clear();
            canvas.setBackgroundColor('rgba(255, 255, 255, 1)', canvas.renderAll.bind(canvas));
            sendSocketMessage('whiteboard', { data: { type: 'clear' } });
        }
    });

    // Text Creating Logic
    canvas.on('mouse:down', function (opt) {
        // Only run this logic if we are strictly in text tool mode
        if (currentTool === 'text') {
            // Check if we hit an existing object? Fabric handles selection if we let it, 
            // but we disabled selection for text tool. 
            // So any click creates new text.

            const pointer = canvas.getPointer(opt.e);
            const text = new fabric.IText('Type here...', {
                left: pointer.x,
                top: pointer.y,
                fontFamily: 'Arial',
                fill: currentColor,
                fontSize: brushSize * 10
            });
            canvas.add(text);
            canvas.setActiveObject(text);
            text.enterEditing();
            text.selectAll();

            // CRITICAL FIX: Switch to 'select' immediately so next click doesn't create new text
            // or cause weird interactions.
            activateTool('select');
        }
    });

    // Remote Update Log
    let isRemoteWhiteboardUpdate = false;
    canvas.on('object:added', (e) => {
        if (!isRemoteWhiteboardUpdate && e.target) {
            const json = e.target.toJSON();
            if (!e.target.id) e.target.id = Date.now() + '-' + Math.random();
            json.id = e.target.id;
            isDirty = true;
            sendSocketMessage('whiteboard', { data: { type: 'add', object: json } });
        }
    });
    canvas.on('object:modified', (e) => {
        if (!isRemoteWhiteboardUpdate && e.target) {
            const json = e.target.toJSON();
            if (!json.id) json.id = e.target.id;
            isDirty = true;
            sendSocketMessage('whiteboard', { data: { type: 'modify', object: json } });
        }
    });

    function handleWhiteboardUpdate(data) {
        isRemoteWhiteboardUpdate = true;

        if (data.type === 'clear') {
            canvas.clear();
            canvas.setBackgroundColor('rgba(255, 255, 255, 1)', canvas.renderAll.bind(canvas));
        } else if (data.type === 'add') {
            fabric.util.enlivenObjects([data.object], function (objects) {
                objects.forEach(function (o) {
                    const existing = canvas.getObjects().find(obj => obj.id === data.object.id);
                    if (!existing) { o.id = data.object.id; canvas.add(o); }
                });
            });
        } else if (data.type === 'modify') {
            const existing = canvas.getObjects().find(obj => obj.id === data.object.id);
            if (existing) {
                existing.set(data.object);
                existing.setCoords();
                canvas.renderAll();
            }
        }
        isRemoteWhiteboardUpdate = false;
    }


    // ============================================
    // Timer Logic
    // ============================================
    const sessionDurationEl = document.getElementById('sessionDuration');
    const teachingTimerEl = document.getElementById('teachingTimer');
    const startTimerBtn = document.getElementById('startTimerBtn');
    const stopTimerBtn = document.getElementById('stopTimerBtn');
    const endSessionBtn = document.getElementById('endSessionBtn');

    // Global Session Timer
    let startedAtTimestamp = parseFloat(sessionPage.dataset.startedAt || Date.now() / 1000);
    setInterval(() => {
        const now = Date.now() / 1000;
        const diff = now - startedAtTimestamp;
        if (diff > 0) sessionDurationEl.textContent = formatTime(Math.floor(diff));
    }, 1000);

    // Initial Timer Setup from Server
    let teachingSeconds = typeof initialTeachingSeconds !== 'undefined' ? initialTeachingSeconds : 0;
    let timerStartTimestamp = typeof initialTimerStart !== 'undefined' ? initialTimerStart : null;
    let teachingInterval = null;

    // Display initial state
    updateTeachingTimerDisplay();

    // If timer is running, resume counting
    if (timerStartTimestamp) {
        startClientTimer();
        // Update UI buttons
        if (startTimerBtn) {
            startTimerBtn.disabled = true;
            stopTimerBtn.disabled = false;
        }
    }

    function updateTeachingTimerDisplay() {
        // Current total = persisted seconds + (now - start if running)
        let currentTotal = teachingSeconds;
        if (timerStartTimestamp) {
            const now = Math.floor(Date.now() / 1000);
            currentTotal += (now - timerStartTimestamp);
        }
        teachingTimerEl.textContent = formatTime(currentTotal);
    }

    function startClientTimer() {
        if (!teachingInterval) {
            teachingInterval = setInterval(updateTeachingTimerDisplay, 1000);
        }
    }

    function stopClientTimer() {
        if (teachingInterval) {
            clearInterval(teachingInterval);
            teachingInterval = null;
        }
        // When stopping, we should hypothetically update teachingSeconds 
        // using the backend response to be exact, but the socket update handles that.
    }

    if (startTimerBtn) {
        startTimerBtn.addEventListener('click', () => {
            fetch(`/session/${sessionId}/start-timer/`, { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken() } })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        startTimerBtn.disabled = true;
                        stopTimerBtn.disabled = false;
                        // Optimistically set start time to now
                        timerStartTimestamp = Math.floor(Date.now() / 1000);
                        startClientTimer();
                    }
                });
        });
    }

    if (stopTimerBtn) {
        stopTimerBtn.addEventListener('click', () => {
            fetch(`/session/${sessionId}/stop-timer/`, { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken() } })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        startTimerBtn.disabled = false;
                        stopTimerBtn.disabled = true;
                        // Update our baseline teachingSeconds with the finalized duration
                        if (typeof data.duration !== 'undefined') {
                            // This 'duration' is the duration of the *segment* just stopped.
                            // We should add it to our baseline if we tracked it separately,
                            // or simpler: just nullify start time and add elapsed.
                            // Better yet, in handleTimerUpdate or response, we sync.
                            // Let's rely on handleTimerUpdate for sync, but optimistic update here:
                        }
                        // Reset active start
                        const now = Math.floor(Date.now() / 1000);
                        teachingSeconds += (now - timerStartTimestamp);
                        timerStartTimestamp = null;

                        stopClientTimer();
                        updateTeachingTimerDisplay();
                    }
                });
        });
    }

    function handleTimerUpdate(data) {
        const action = data.action;
        if (action === 'start') {
            if (startTimerBtn) {
                startTimerBtn.disabled = true;
                stopTimerBtn.disabled = false;
            }
            if (!timerStartTimestamp) {
                timerStartTimestamp = Math.floor(Date.now() / 1000); // Approximate
                startClientTimer();
            }
        } else if (action === 'stop') {
            if (startTimerBtn) {
                startTimerBtn.disabled = false;
                stopTimerBtn.disabled = true;
            }
            if (timerStartTimestamp) {
                const now = Math.floor(Date.now() / 1000);
                teachingSeconds += (now - timerStartTimestamp);
                timerStartTimestamp = null;
            }
            stopClientTimer();
            updateTeachingTimerDisplay();
        }
    }

    if (endSessionBtn) {
        endSessionBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to end this session?')) {
                fetch(`/session/${sessionId}/end/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCsrfToken() }
                }).then(res => res.json()).then(data => {
                    if (data.success) window.location.href = data.redirect;
                    else alert(data.error || 'Error ending session');
                });
            }
        });
    }

    function formatTime(seconds) {
        if (seconds < 0) seconds = 0;
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        return `${pad(h)}:${pad(m)}:${pad(s)}`;
    }
    function pad(n) { return n.toString().padStart(2, '0'); }

    // Video Call Placeholder (WebRTC logic from previous iterations preserved if needed, or minimal stub)
    let localStream;
    let peerConnection;
    const config = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };
    const localVideo = document.getElementById('localVideo');
    const remoteVideo = document.getElementById('remoteVideo');
    const startVideoBtn = document.getElementById('startVideoBtn');

    if (startVideoBtn) {
        startVideoBtn.addEventListener('click', async () => {
            try {
                localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                localVideo.srcObject = localStream;
                startVideoBtn.disabled = true;

                // Init Call
                peerConnection = new RTCPeerConnection(config);
                peerConnection.onicecandidate = (e) => {
                    if (e.candidate) sendSocketMessage('video_signal', { data: { type: 'candidate', candidate: e.candidate } });
                };
                peerConnection.ontrack = (e) => { remoteVideo.srcObject = e.streams[0]; };
                localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

                const offer = await peerConnection.createOffer();
                await peerConnection.setLocalDescription(offer);
                sendSocketMessage('video_signal', { data: { type: 'offer', offer: offer } });

                document.getElementById('toggleMuteBtn').disabled = false;
                document.getElementById('toggleVideoBtn').disabled = false;
            } catch (e) { console.error(e); alert("Camera access error"); }
        });
    }

    async function handleVideoSignal(data) {
        if (!peerConnection) {
            peerConnection = new RTCPeerConnection(config);
            peerConnection.onicecandidate = (e) => {
                if (e.candidate) sendSocketMessage('video_signal', { data: { type: 'candidate', candidate: e.candidate } });
            };
            peerConnection.ontrack = (e) => { remoteVideo.srcObject = e.streams[0]; };
        }
        try {
            if (data.type === 'offer') {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
                if (!localStream) {
                    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                    localVideo.srcObject = localStream;
                    localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

                    // Enable controls for the receiving user too
                    startVideoBtn.disabled = true;
                    document.getElementById('toggleMuteBtn').disabled = false;
                    document.getElementById('toggleVideoBtn').disabled = false;
                }
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                sendSocketMessage('video_signal', { data: { type: 'answer', answer: answer } });

            } else if (data.type === 'answer') {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
            } else if (data.type === 'candidate') {
                if (data.candidate) await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
            }
        } catch (e) { console.error(e); }
    }

    document.getElementById('toggleMuteBtn').addEventListener('click', function () {
        if (localStream) {
            localStream.getAudioTracks().forEach(t => t.enabled = !t.enabled);
            this.textContent = localStream.getAudioTracks()[0].enabled ? 'Mute' : 'Unmute';
        }
    });

    document.getElementById('toggleVideoBtn').addEventListener('click', function () {
        if (localStream) {
            localStream.getVideoTracks().forEach(t => t.enabled = !t.enabled);
            this.textContent = localStream.getVideoTracks()[0].enabled ? 'Camera Off' : 'Camera On';
        }
    });
});
