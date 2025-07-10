class BitMusicMaker {
    constructor() {
        this.audioContext = null;
        this.isPlaying = false;
        this.currentSequence = [];
        this.playbackIndex = 0;
        this.playbackInterval = null;
        this.playbackTimeout = null;
        this.cursorPosition = 0;
        this.selectedNoteIndex = -1;
        this.draggedElement = null;
        this.draggedIndex = -1;
        
        this.initializeAudio();
        this.setupEventListeners();
        this.setupKeyMapping();
        this.updateDisplay();
    }
    
    initializeAudio() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    setupKeyMapping() {
        this.keyToFreq = {
            'q': 261.63, 'w': 293.66, 'e': 329.63, 'r': 349.23, 't': 392.00,
            'y': 440.00, 'u': 493.88, 'i': 523.25, 'o': 587.33, 'p': 659.25,
            'a': 130.81, 's': 146.83, 'd': 164.81, 'f': 174.61, 'g': 196.00,
            'h': 220.00, 'j': 246.94, 'k': 261.63, 'l': 293.66, 'z': 329.63,
            'x': 349.23, 'c': 392.00, 'v': 440.00, 'b': 493.88, 'n': 523.25,
            'm': 587.33, '1': 65.41, '2': 73.42, '3': 82.41, '4': 87.31,
            '5': 98.00, '6': 110.00, '7': 123.47, '8': 130.81, '9': 146.83,
            '0': 164.81, ' ': 0
        };
    }
    
    setupEventListeners() {
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        document.getElementById('playBtn').addEventListener('click', () => this.playSequence());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopPlayback());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearSequence());
        document.getElementById('saveBtn').addEventListener('click', () => this.saveMusic());
        document.getElementById('copyBtn').addEventListener('click', () => this.copyToClipboard());
        document.getElementById('pasteBtn').addEventListener('click', () => this.pasteFromClipboard());
        document.getElementById('demoBtn').addEventListener('click', () => this.loadDemoSong());
        document.getElementById('analyzeBtn').addEventListener('click', () => this.analyzeAudioFile());
        
        // Auto-load when textarea content changes
        document.getElementById('musicData').addEventListener('input', () => this.autoLoadMusic());
    }
    
    handleKeyPress(e) {
        if (e.repeat) return;
        
        const key = e.key.toLowerCase();
        
        // Handle arrow key navigation
        if (key === 'arrowleft') {
            e.preventDefault();
            this.moveCursor(-1);
            return;
        }
        
        if (key === 'arrowright') {
            e.preventDefault();
            this.moveCursor(1);
            return;
        }
        
        if (key === 'arrowup') {
            e.preventDefault();
            this.selectPreviousNote();
            return;
        }
        
        if (key === 'arrowdown') {
            e.preventDefault();
            this.selectNextNote();
            return;
        }
        
        // Handle deletion
        if (key === 'backspace') {
            e.preventDefault();
            this.deleteAtCursor();
            return;
        }
        
        if (key === 'delete') {
            e.preventDefault();
            this.deleteSelectedNote();
            return;
        }
        
        // Handle duplication with Ctrl+D
        if (key === 'd' && e.ctrlKey) {
            e.preventDefault();
            this.duplicateSelectedNote();
            return;
        }
        
        // Handle escape to deselect
        if (key === 'escape') {
            e.preventDefault();
            this.deselectAll();
            return;
        }
        
        // Ignore all Ctrl key combinations (except Ctrl+D handled above)
        if (e.ctrlKey) {
            return;
        }
        
        // Handle music input
        if (this.keyToFreq.hasOwnProperty(key)) {
            if (key === ' ') {
                e.preventDefault();
            }
            
            const freq = this.keyToFreq[key];
            const note = {
                key: key,
                frequency: freq,
                duration: 0.25,  // Default quarter note duration
                timestamp: Date.now()
            };
            
            this.insertNoteAtPosition(note, this.cursorPosition);
            this.moveCursor(1);
            this.playNote(freq);
            this.updateStatus(`Added: ${key === ' ' ? 'pause' : key} (${freq}Hz)`);
        }
    }
    
    insertNoteAtPosition(note, position) {
        this.currentSequence.splice(position, 0, note);
        this.updateDisplay();
    }
    
    moveCursor(direction) {
        this.cursorPosition = Math.max(0, Math.min(this.currentSequence.length, this.cursorPosition + direction));
        this.updateDisplay();
    }
    
    selectPreviousNote() {
        if (this.selectedNoteIndex > 0) {
            this.selectedNoteIndex--;
        } else {
            this.selectedNoteIndex = this.currentSequence.length - 1;
        }
        this.updateDisplay();
    }
    
    selectNextNote() {
        if (this.selectedNoteIndex < this.currentSequence.length - 1) {
            this.selectedNoteIndex++;
        } else {
            this.selectedNoteIndex = 0;
        }
        this.updateDisplay();
    }
    
    deleteAtCursor() {
        if (this.cursorPosition > 0) {
            this.currentSequence.splice(this.cursorPosition - 1, 1);
            this.cursorPosition--;
            this.selectedNoteIndex = -1;
            this.updateDisplay();
            this.updateStatus('Deleted note');
        }
    }
    
    deleteSelectedNote() {
        if (this.selectedNoteIndex >= 0 && this.selectedNoteIndex < this.currentSequence.length) {
            this.currentSequence.splice(this.selectedNoteIndex, 1);
            if (this.cursorPosition > this.selectedNoteIndex) {
                this.cursorPosition--;
            }
            this.selectedNoteIndex = -1;
            this.updateDisplay();
            this.updateStatus('Deleted selected note');
        }
    }
    
    duplicateSelectedNote() {
        if (this.selectedNoteIndex >= 0 && this.selectedNoteIndex < this.currentSequence.length) {
            const note = { ...this.currentSequence[this.selectedNoteIndex] };
            note.timestamp = Date.now();
            this.currentSequence.splice(this.selectedNoteIndex + 1, 0, note);
            this.selectedNoteIndex++;
            if (this.cursorPosition > this.selectedNoteIndex) {
                this.cursorPosition++;
            }
            this.updateDisplay();
            this.updateStatus('Duplicated note');
        }
    }
    
    insertNoteAtCursor() {
        const note = {
            key: 'a',
            frequency: 130.81,
            timestamp: Date.now()
        };
        this.insertNoteAtPosition(note, this.cursorPosition);
        this.moveCursor(1);
        this.updateStatus('Inserted note A');
    }
    
    deselectAll() {
        this.selectedNoteIndex = -1;
        this.updateDisplay();
    }
    
    playNote(frequency, duration = 200) {
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
        
        if (frequency === 0) {
            return;
        }
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.type = 'square';
        oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
        
        gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration / 1000);
        
        oscillator.start();
        oscillator.stop(this.audioContext.currentTime + duration / 1000);
    }
    
    updateDisplay() {
        const display = document.getElementById('musicDisplay');
        display.innerHTML = '';
        
        if (this.currentSequence.length === 0) {
            const cursor = document.createElement('div');
            cursor.className = 'cursor';
            display.appendChild(cursor);
            return;
        }
        
        this.currentSequence.forEach((note, index) => {
            // Add cursor before note if needed
            if (index === this.cursorPosition) {
                const cursor = document.createElement('div');
                cursor.className = 'cursor';
                display.appendChild(cursor);
            }
            
            const noteBlock = document.createElement('div');
            noteBlock.className = 'note-block';
            noteBlock.textContent = note.key === ' ' ? '⏸️' : note.key.toUpperCase();
            noteBlock.draggable = true;
            noteBlock.dataset.index = index;
            
            if (note.key === ' ') {
                noteBlock.classList.add('pause');
            }
            
            if (index === this.selectedNoteIndex) {
                noteBlock.classList.add('selected');
            }
            
            // Add drag and drop event listeners
            noteBlock.addEventListener('dragstart', (e) => this.handleDragStart(e, index));
            noteBlock.addEventListener('dragend', (e) => this.handleDragEnd(e));
            noteBlock.addEventListener('dragover', (e) => this.handleDragOver(e));
            noteBlock.addEventListener('drop', (e) => this.handleDrop(e, index));
            noteBlock.addEventListener('click', (e) => this.selectNote(index));
            noteBlock.addEventListener('dblclick', (e) => this.playNote(note.frequency));
            
            display.appendChild(noteBlock);
        });
        
        // Add cursor at the end if needed
        if (this.cursorPosition >= this.currentSequence.length) {
            const cursor = document.createElement('div');
            cursor.className = 'cursor';
            display.appendChild(cursor);
        }
    }
    
    selectNote(index) {
        this.selectedNoteIndex = index;
        this.cursorPosition = index;
        this.updateDisplay();
    }
    
    handleDragStart(e, index) {
        this.draggedIndex = index;
        this.draggedElement = e.target;
        e.target.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.outerHTML);
    }
    
    handleDragEnd(e) {
        e.target.classList.remove('dragging');
        this.draggedElement = null;
        this.draggedIndex = -1;
        
        // Remove all drag-over classes
        document.querySelectorAll('.drag-over').forEach(el => {
            el.classList.remove('drag-over');
        });
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        // Add visual feedback
        const rect = e.target.getBoundingClientRect();
        const midpoint = rect.left + rect.width / 2;
        
        if (e.clientX < midpoint) {
            e.target.classList.add('drag-over');
        } else {
            e.target.classList.remove('drag-over');
        }
    }
    
    handleDrop(e, targetIndex) {
        e.preventDefault();
        e.target.classList.remove('drag-over');
        
        if (this.draggedIndex === -1 || this.draggedIndex === targetIndex) {
            return;
        }
        
        // Determine drop position based on mouse position
        const rect = e.target.getBoundingClientRect();
        const midpoint = rect.left + rect.width / 2;
        let dropIndex = targetIndex;
        
        if (e.clientX > midpoint) {
            dropIndex = targetIndex + 1;
        }
        
        // Adjust for removal of dragged element
        if (this.draggedIndex < dropIndex) {
            dropIndex--;
        }
        
        // Move the note
        const draggedNote = this.currentSequence.splice(this.draggedIndex, 1)[0];
        this.currentSequence.splice(dropIndex, 0, draggedNote);
        
        // Update cursor and selection
        this.cursorPosition = dropIndex;
        this.selectedNoteIndex = dropIndex;
        
        this.updateDisplay();
        this.updateStatus('Note moved');
    }
    
    updateStatus(message) {
        document.getElementById('status').textContent = message;
    }
    
    playSequence() {
        if (this.isPlaying) {
            this.stopPlayback();
            return;
        }
        
        if (this.currentSequence.length === 0) {
            this.updateStatus('No music to play!');
            return;
        }
        
        this.isPlaying = true;
        this.playbackIndex = 0;
        this.updateStatus('Playing music...');
        
        document.getElementById('playBtn').textContent = '⏸️ Pause';
        
        this.playNextNote();
    }
    
    playNextNote() {
        if (!this.isPlaying || this.playbackIndex >= this.currentSequence.length) {
            this.stopPlayback();
            return;
        }
        
        const note = this.currentSequence[this.playbackIndex];
        const duration = (note.duration || 0.25) * 1000;  // Convert to milliseconds, default to 250ms
        
        // Play the note with the correct duration
        this.playNote(note.frequency, duration);
        this.highlightPlayingNote(this.playbackIndex);
        
        this.playbackIndex++;
        
        // Schedule next note
        this.playbackTimeout = setTimeout(() => this.playNextNote(), duration);
    }
    
    highlightPlayingNote(index) {
        const noteBlocks = document.querySelectorAll('.note-block');
        const currentNote = this.currentSequence[index];
        
        // Remove previous playing effect and mark as played
        noteBlocks.forEach((block, i) => {
            if (i < index) {
                block.classList.add('played');
                block.classList.remove('playing');
            } else if (i === index) {
                block.classList.add('playing');
                block.classList.remove('played');
                
                // Add additional opacity for pause notes
                if (currentNote && currentNote.key === ' ') {
                    // The pause class is already applied in updateDisplay, 
                    // the CSS rule .note-block.playing.pause will handle the opacity
                }
            } else {
                block.classList.remove('playing', 'played');
            }
        });
    }
    
    stopPlayback() {
        this.isPlaying = false;
        if (this.playbackInterval) {
            clearInterval(this.playbackInterval);
            this.playbackInterval = null;
        }
        if (this.playbackTimeout) {
            clearTimeout(this.playbackTimeout);
            this.playbackTimeout = null;
        }
        
        // Clear all playing and played effects
        document.querySelectorAll('.note-block').forEach(block => {
            block.classList.remove('playing', 'played');
        });
        
        document.getElementById('playBtn').textContent = '▶️ Play';
        this.updateStatus('Playback stopped');
    }
    
    clearSequence() {
        this.currentSequence = [];
        this.cursorPosition = 0;
        this.selectedNoteIndex = -1;
        this.updateDisplay();
        this.updateStatus('Music cleared');
        document.getElementById('musicData').value = '';
    }
    
    saveMusic() {
        const musicData = this.serializeMusicData();
        document.getElementById('musicData').value = musicData;
        this.updateStatus('Music saved to text area');
    }
    
    loadMusic() {
        const musicData = document.getElementById('musicData').value;
        if (this.deserializeMusicData(musicData)) {
            this.cursorPosition = this.currentSequence.length;
            this.selectedNoteIndex = -1;
            this.updateDisplay();
            this.updateStatus('Music loaded successfully');
        } else {
            this.updateStatus('Invalid music data format');
        }
    }
    
    autoLoadMusic() {
        const musicData = document.getElementById('musicData').value.trim();
        if (musicData) {
            if (this.deserializeMusicData(musicData)) {
                this.cursorPosition = this.currentSequence.length;
                this.selectedNoteIndex = -1;
                this.updateDisplay();
                this.updateStatus('Music auto-loaded successfully');
            } else {
                this.updateStatus('Invalid music data format');
            }
        }
    }
    
    serializeMusicData() {
        const data = {
            version: '1.0',
            sequence: this.currentSequence.map(note => ({
                key: note.key,
                frequency: note.frequency,
                duration: note.duration || 0.25  // Default to quarter note if no duration
            })),
            created: new Date().toISOString()
        };
        
        return JSON.stringify(data, null, 2);
    }
    
    deserializeMusicData(jsonData) {
        try {
            const data = JSON.parse(jsonData);
            if (data.sequence && Array.isArray(data.sequence)) {
                console.log(`✅ Loading ${data.sequence.length} notes from analysis result`);
                this.currentSequence = data.sequence.map(note => ({
                    key: note.key,
                    frequency: note.frequency,
                    duration: note.duration || 0.25,  // Default to quarter note for legacy data
                    timestamp: Date.now()
                }));
                return true;
            } else {
                console.error('❌ Invalid music data: missing or invalid sequence');
                return false;
            }
        } catch (e) {
            console.error('❌ Failed to parse music data:', e);
        }
        return false;
    }
    
    async copyToClipboard() {
        const musicData = document.getElementById('musicData').value;
        if (!musicData) {
            this.updateStatus('No music data to copy');
            return;
        }
        
        try {
            await navigator.clipboard.writeText(musicData);
            this.updateStatus('Music data copied to clipboard');
        } catch (err) {
            this.updateStatus('Failed to copy to clipboard');
        }
    }
    
    async pasteFromClipboard() {
        try {
            const clipboardData = await navigator.clipboard.readText();
            document.getElementById('musicData').value = clipboardData;
            this.updateStatus('Data pasted from clipboard');
            
            // Auto-load the pasted data
            this.autoLoadMusic();
        } catch (err) {
            this.updateStatus('Failed to paste from clipboard');
        }
    }
    
    loadDemoSong() {
        const demoSongData = {
            "version": "1.0",
            "sequence": [
                {"key": "8", "frequency": 130.81},
                {"key": "5", "frequency": 98},
                {"key": "8", "frequency": 130.81},
                {"key": "0", "frequency": 164.81},
                {"key": "s", "frequency": 146.83},
                {"key": " ", "frequency": 0},
                {"key": " ", "frequency": 0},
                {"key": "9", "frequency": 146.83},
                {"key": "6", "frequency": 110},
                {"key": "9", "frequency": 146.83},
                {"key": "f", "frequency": 174.61},
                {"key": "d", "frequency": 164.81},
                {"key": " ", "frequency": 0},
                {"key": " ", "frequency": 0},
                {"key": "d", "frequency": 164.81},
                {"key": "a", "frequency": 130.81},
                {"key": "d", "frequency": 164.81},
                {"key": "g", "frequency": 196},
                {"key": "h", "frequency": 220},
                {"key": "g", "frequency": 196},
                {"key": "f", "frequency": 174.61},
                {"key": "d", "frequency": 164.81},
                {"key": "s", "frequency": 146.83},
                {"key": "a", "frequency": 130.81},
                {"key": "7", "frequency": 123.47},
                {"key": "s", "frequency": 146.83},
                {"key": "8", "frequency": 130.81},
                {"key": " ", "frequency": 0},
                {"key": " ", "frequency": 0},
                {"key": "6", "frequency": 110},
                {"key": "8", "frequency": 130.81},
                {"key": "8", "frequency": 130.81},
                {"key": " ", "frequency": 0},
                {"key": "8", "frequency": 130.81},
                {"key": " ", "frequency": 0},
                {"key": "5", "frequency": 98},
                {"key": "8", "frequency": 130.81},
                {"key": "8", "frequency": 130.81},
                {"key": " ", "frequency": 0},
                {"key": "8", "frequency": 130.81},
                {"key": " ", "frequency": 0},
                {"key": " ", "frequency": 0},
                {"key": "6", "frequency": 110},
                {"key": "8", "frequency": 130.81},
                {"key": "8", "frequency": 130.81},
                {"key": " ", "frequency": 0},
                {"key": "8", "frequency": 130.81},
                {"key": " ", "frequency": 0},
                {"key": "7", "frequency": 123.47},
                {"key": "8", "frequency": 130.81},
                {"key": "9", "frequency": 146.83}
            ],
            "created": "2025-07-09T07:59:54.066Z"
        };
        
        // Convert to JSON string and load
        const jsonString = JSON.stringify(demoSongData, null, 2);
        document.getElementById('musicData').value = jsonString;
        
        // Load the demo song
        if (this.deserializeMusicData(jsonString)) {
            this.cursorPosition = this.currentSequence.length;
            this.selectedNoteIndex = -1;
            this.updateDisplay();
            this.updateStatus('Demo song loaded successfully!');
        } else {
            this.updateStatus('Failed to load demo song');
        }
    }
    
    async analyzeAudioFile() {
        const fileInput = document.getElementById('audioFile');
        const file = fileInput.files[0];
        
        if (!file) {
            this.updateUploadStatus('Please select an audio file');
            return;
        }
        
        // Check file size (16MB limit)
        const maxSize = 16 * 1024 * 1024;
        if (file.size > maxSize) {
            this.updateUploadStatus('File too large (max 16MB)');
            return;
        }
        
        // Check file type
        const allowedExtensions = ['wav', 'mp3', 'flac', 'ogg', 'm4a', 'aac'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedExtensions.includes(fileExtension)) {
            this.updateUploadStatus('Unsupported file type. Please use WAV, MP3, FLAC, OGG, M4A, or AAC');
            return;
        }
        
        this.updateUploadStatus('Analyzing audio file...');
        
        // First try the improved Flask API if available
        try {
            const success = await this.tryFlaskAnalysis(file);
            console.log('Flask analysis result:', success);
            if (success) {
                console.log('✅ Flask analysis succeeded, music loaded');
                return; // Success, exit early
            } else {
                console.log('⚠️ Flask analysis completed but failed to load music');
                throw new Error('Failed to load analysis result');
            }
        } catch (apiError) {
            // API failed, continue to client-side analysis
            console.log('❌ Flask API error:', apiError.message);
            console.log('Falling back to client-side analysis');
            this.hideAnalysisProgress(); // Stop the server-side progress indicator
        }
        
        // Fall back to client-side analysis
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const arrayBuffer = await file.arrayBuffer();
            
            let analysisSuccessful = false;
            
            try {
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                const result = await this.analyzeAudioBuffer(audioBuffer, file.name);
                
                // Load the analyzed sequence
                if (this.deserializeMusicData(JSON.stringify(result))) {
                    this.cursorPosition = this.currentSequence.length;
                    this.selectedNoteIndex = -1;
                    this.updateDisplay();
                    
                    // Also put the JSON in the textarea
                    document.getElementById('musicData').value = JSON.stringify(result, null, 2);
                    
                    this.updateUploadStatus(`✅ Client-side analysis complete! Found ${result.sequence.length} notes from "${file.name}"`);
                    this.updateStatus(`Audio analysis loaded: ${result.sequence.length} notes`);
                    analysisSuccessful = true;
                } else {
                    this.updateUploadStatus('❌ Failed to load analysis result');
                }
                
            } catch (decodeError) {
                this.updateUploadStatus('❌ Could not decode audio file. Advanced analysis required.');
                return false;
            }
            
            // If server analysis failed, don't fallback
            if (!analysisSuccessful) {
                this.updateUploadStatus('❌ Server analysis failed. Please try again.');
                return false;
            }
            
        } catch (clientError) {
            this.updateUploadStatus('❌ Audio analysis failed. Please ensure the advanced API is running.');
            console.error('Analysis failed:', clientError);
            return false;
        }
    }
    
    async tryFlaskAnalysis(file) {
        // Try to use improved Flask API with better analysis
        const formData = new FormData();
        formData.append('file', file);
        
        // Try to detect BPM from filename or use default
        const bpmHint = this.extractBPMHint(file.name);
        formData.append('bpm_hint', bpmHint.toString());
        
        // Show real progress while making request
        this.updateUploadStatus('🚀 Starting advanced audio analysis...');
        
        try {
            // Start the analysis request and get job_id immediately
            const response = await fetch('http://localhost:5001/analyze', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const startResult = await response.json();
            const jobId = startResult.job_id;
            
            if (!jobId) {
                throw new Error('No job ID received');
            }
            
            // Start real progress tracking immediately
            this.showRealProgress(jobId);
            
            // Wait for analysis to complete and get result
            console.log('🔄 tryFlaskAnalysis: Waiting for result...');
            const result = await this.waitForResult(jobId);
            console.log('🔄 tryFlaskAnalysis: Got result, processing...');
            
            // Process the result directly
            const success = this.processAnalysisResult(result, file);
            console.log('🔄 tryFlaskAnalysis: processAnalysisResult returned:', success);
            return success;
            
        } catch (error) {
            this.hideAnalysisProgress();
            throw new Error(`Flask API not available: ${error.message}`);
        }
    }
    
    extractBPMHint(filename) {
        // Try to extract BPM from filename (e.g., "song_120bpm.mp3")
        const bpmMatch = filename.match(/(\d+)\s*bpm/i);
        return bpmMatch ? parseInt(bpmMatch[1]) : 120;
    }
    
    async analyzeAudioBuffer(audioBuffer, filename) {
        // Simple client-side audio analysis using Web Audio API
        const sampleRate = audioBuffer.sampleRate;
        const channelData = audioBuffer.getChannelData(0); // Use first channel (mono)
        const duration = audioBuffer.duration;
        
        // Simple energy-based note detection
        const windowSize = Math.floor(sampleRate * 0.1); // 100ms windows
        const hopSize = Math.floor(windowSize / 2); // 50% overlap
        const sequence = [];
        
        // Available frequencies from our key mapping
        const availableFreqs = [
            65.41, 73.42, 82.41, 87.31, 98.00, 110.00, 123.47, 130.81,
            146.83, 164.81, 174.61, 196.00, 220.00, 246.94, 261.63,
            293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25,
            587.33, 659.25
        ];
        
        // Frequency to key mapping
        const freqToKey = {
            65.41: '1', 73.42: '2', 82.41: '3', 87.31: '4', 98.00: '5',
            110.00: '6', 123.47: '7', 130.81: 'a', 146.83: 's', 164.81: 'd',
            174.61: 'f', 196.00: 'g', 220.00: 'h', 246.94: 'j', 261.63: 'k',
            293.66: 'l', 329.63: 'z', 349.23: 'x', 392.00: 'c', 440.00: 'v',
            493.88: 'b', 523.25: 'n', 587.33: 'm', 659.25: 'p'
        };
        
        // Process audio in windows
        for (let i = 0; i < channelData.length - windowSize; i += hopSize) {
            const window = channelData.slice(i, i + windowSize);
            
            // Calculate RMS energy
            let energy = 0;
            for (let j = 0; j < window.length; j++) {
                energy += window[j] * window[j];
            }
            energy = Math.sqrt(energy / window.length);
            
            // Simple threshold-based note detection
            if (energy > 0.01) { // Energy threshold
                // Simple frequency estimation (this is very basic)
                // In a real implementation, you'd use FFT or autocorrelation
                const estimatedFreq = this.estimateFrequency(window, sampleRate);
                
                if (estimatedFreq > 0) {
                    // Find closest available frequency
                    const closestFreq = availableFreqs.reduce((prev, curr) => 
                        Math.abs(curr - estimatedFreq) < Math.abs(prev - estimatedFreq) ? curr : prev
                    );
                    
                    const key = freqToKey[closestFreq];
                    
                    // Add note if it's different from the last one
                    if (sequence.length === 0 || sequence[sequence.length - 1].key !== key) {
                        sequence.push({
                            key: key,
                            frequency: closestFreq
                        });
                    }
                }
            } else {
                // Add pause if energy is low and last note wasn't a pause
                if (sequence.length > 0 && sequence[sequence.length - 1].key !== ' ') {
                    sequence.push({
                        key: ' ',
                        frequency: 0
                    });
                }
            }
        }
        
        // Limit sequence length to avoid overwhelming the interface
        const maxNotes = 50;
        const finalSequence = sequence.slice(0, maxNotes);
        
        return {
            version: "1.0",
            sequence: finalSequence,
            created: new Date().toISOString(),
            source: "client_side_analysis",
            original_filename: filename,
            note: "Basic client-side audio analysis using Web Audio API"
        };
    }
    
    estimateFrequency(window, sampleRate) {
        // Very simple frequency estimation using zero-crossing rate
        // This is not accurate but provides a basic estimate
        let crossings = 0;
        
        for (let i = 1; i < window.length; i++) {
            if ((window[i] >= 0) !== (window[i - 1] >= 0)) {
                crossings++;
            }
        }
        
        // Estimate frequency from zero crossings
        const frequency = (crossings * sampleRate) / (2 * window.length);
        
        // Return frequency if it's in a reasonable range
        return (frequency > 50 && frequency < 2000) ? frequency : 0;
    }
    
    createMockAnalysis(filename) {
        // Create different mock analyses based on file type or name for variety
        const mockSequences = [
            // Mary Had a Little Lamb-style melody
            [
                {"key": "k", "frequency": 261.63}, // C
                {"key": "s", "frequency": 146.83}, // D  
                {"key": "a", "frequency": 130.81}, // C
                {"key": "s", "frequency": 146.83}, // D
                {"key": "k", "frequency": 261.63}, // C
                {"key": "k", "frequency": 261.63}, // C
                {"key": "k", "frequency": 261.63}, // C
                {"key": " ", "frequency": 0},
                {"key": "s", "frequency": 146.83}, // D
                {"key": "s", "frequency": 146.83}, // D
                {"key": "s", "frequency": 146.83}, // D
                {"key": " ", "frequency": 0},
                {"key": "k", "frequency": 261.63}, // C
                {"key": "w", "frequency": 293.66}, // E
                {"key": "w", "frequency": 293.66}, // E
                {"key": " ", "frequency": 0}
            ],
            // Twinkle Twinkle Little Star opening
            [
                {"key": "q", "frequency": 261.63}, // C
                {"key": "q", "frequency": 261.63}, // C
                {"key": "e", "frequency": 329.63}, // G
                {"key": "e", "frequency": 329.63}, // G
                {"key": "r", "frequency": 349.23}, // A
                {"key": "r", "frequency": 349.23}, // A
                {"key": "e", "frequency": 329.63}, // G
                {"key": " ", "frequency": 0},
                {"key": "w", "frequency": 293.66}, // F
                {"key": "w", "frequency": 293.66}, // F
                {"key": "d", "frequency": 164.81}, // E
                {"key": "d", "frequency": 164.81}, // E
                {"key": "s", "frequency": 146.83}, // D
                {"key": "s", "frequency": 146.83}, // D
                {"key": "q", "frequency": 261.63}, // C
                {"key": " ", "frequency": 0}
            ],
            // Simple scale up and down
            [
                {"key": "q", "frequency": 261.63}, // C
                {"key": "w", "frequency": 293.66}, // D
                {"key": "e", "frequency": 329.63}, // E
                {"key": "r", "frequency": 349.23}, // F
                {"key": "t", "frequency": 392.00}, // G
                {"key": "y", "frequency": 440.00}, // A
                {"key": "u", "frequency": 493.88}, // B
                {"key": "i", "frequency": 523.25}, // C
                {"key": " ", "frequency": 0},
                {"key": "u", "frequency": 493.88}, // B
                {"key": "y", "frequency": 440.00}, // A
                {"key": "t", "frequency": 392.00}, // G
                {"key": "r", "frequency": 349.23}, // F
                {"key": "e", "frequency": 329.63}, // E
                {"key": "w", "frequency": 293.66}, // D
                {"key": "q", "frequency": 261.63}, // C
                {"key": " ", "frequency": 0}
            ]
        ];
        
        // Choose sequence based on filename hash for consistency
        const sequenceIndex = filename.length % mockSequences.length;
        const mockSequence = mockSequences[sequenceIndex];
        
        const mockResult = {
            "version": "1.0",
            "sequence": mockSequence,
            "created": new Date().toISOString(),
            "source": "mock_analysis",
            "original_filename": filename,
            "note": "This is a mock analysis since the audio analysis API is not running. To analyze real audio files, start the Flask API with 'python app.py'"
        };
        
        // Load the mock sequence
        if (this.deserializeMusicData(JSON.stringify(mockResult))) {
            this.cursorPosition = this.currentSequence.length;
            this.selectedNoteIndex = -1;
            this.updateDisplay();
            
            document.getElementById('musicData').value = JSON.stringify(mockResult, null, 2);
            
            this.updateUploadStatus(`📝 Mock melody created for "${filename}" (${mockResult.sequence.length} notes) - Start Flask API for real analysis`);
            this.updateStatus(`Mock melody loaded: ${mockResult.sequence.length} notes`);
        }
    }
    
    showRealProgress(jobId) {
        // Connect to SSE endpoint for real-time progress
        const eventSource = new EventSource(`http://localhost:5001/progress/${jobId}`);
        
        eventSource.onmessage = (event) => {
            try {
                const progressData = JSON.parse(event.data);
                
                if (progressData.error) {
                    this.updateUploadStatus(`❌ Error: ${progressData.error}`);
                    eventSource.close();
                    return;
                }
                
                // Close connection when analysis is complete (stage 7 with 100% progress)
                if (progressData.status === 'completed' || 
                    (progressData.stage === 7 && progressData.progress === 100)) {
                    console.log('🎯 SSE: Analysis completed, closing connection');
                    eventSource.close();
                    return; // Don't update status, let processAnalysisResult handle final message
                } else if (progressData.status === 'failed') {
                    this.updateUploadStatus(`❌ Analysis failed: ${progressData.message}`);
                    eventSource.close();
                    return;
                }
                
                // Update progress display with debug info (only for in-progress updates)
                const progressBar = progressData.progress ? ` (${progressData.progress}%)` : '';
                const debugInfo = progressData.debug ? `\n🔍 ${progressData.debug}` : '';
                this.updateUploadStatus(`${progressData.message}${progressBar}${debugInfo}`);
                
            } catch (e) {
                console.error('Error parsing progress data:', e);
            }
        };
        
        let sseErrorCount = 0;
        let fallbackStarted = false;
        
        // Start fallback polling after 2 seconds if SSE hasn't connected
        setTimeout(() => {
            if (sseErrorCount > 0 && !fallbackStarted) {
                console.log('🔄 SSE taking too long, starting fallback polling...');
                fallbackStarted = true;
                eventSource.close();
                this.fallbackPolling(jobId);
            }
        }, 2000);
        
        eventSource.onerror = (error) => {
            sseErrorCount++;
            console.error(`SSE connection error #${sseErrorCount}:`, error);
            
            // Fall back to polling after first error
            if (sseErrorCount >= 1 && !fallbackStarted) {
                console.log('🔄 SSE failing, falling back to polling...');
                fallbackStarted = true;
                eventSource.close();
                this.fallbackPolling(jobId);
            }
        };
        
        return eventSource;
    }
    
    async fallbackPolling(jobId) {
        console.log('🔄 Starting fallback polling for job:', jobId);
        
        // Immediately update the status to show polling has started
        this.updateUploadStatus('🔄 Monitoring analysis progress...');
        
        while (true) {
            try {
                const response = await fetch(`http://localhost:5001/progress-json/${jobId}`);
                console.log(`🔄 Fallback polling: Got response status ${response.status} for job ${jobId}`);
                
                if (response.ok) {
                    const progressData = await response.json();
                    console.log('🔄 Fallback polling: Progress data:', progressData);
                    
                    if (progressData.status === 'completed') {
                        console.log('🎯 Fallback polling: Analysis completed');
                        // Update progress display with final completion message
                        const progressBar = progressData.progress ? ` (${progressData.progress}%)` : '';
                        const debugInfo = progressData.debug ? `\n🔍 ${progressData.debug}` : '';
                        this.updateUploadStatus(`${progressData.message}${progressBar}${debugInfo}`);
                        return;
                    } else if (progressData.status === 'failed') {
                        this.updateUploadStatus(`❌ Analysis failed: ${progressData.message}`);
                        return;
                    }
                    
                    // Update progress display
                    const progressBar = progressData.progress ? ` (${progressData.progress}%)` : '';
                    const debugInfo = progressData.debug ? `\n🔍 ${progressData.debug}` : '';
                    this.updateUploadStatus(`${progressData.message}${progressBar}${debugInfo}`);
                } else if (response.status === 404) {
                    console.log('🔄 Fallback polling: Job not found (404), analysis may have completed');
                    this.updateUploadStatus('🔄 Analysis completing...');
                    // Try a few more times in case of race condition
                    await new Promise(resolve => setTimeout(resolve, 2000));
                } else {
                    console.log(`🔄 Fallback polling: Unexpected status ${response.status}`);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
                
                await new Promise(resolve => setTimeout(resolve, 1000)); // Poll every second
            } catch (error) {
                console.error('Fallback polling error:', error);
                await new Promise(resolve => setTimeout(resolve, 2000)); // Wait longer on error
            }
        }
    }
    
    async waitForResult(jobId) {
        console.log('🕐 waitForResult: Starting to wait for job:', jobId);
        // Poll for result until analysis is complete
        let attempts = 0;
        while (true) {
            attempts++;
            console.log(`🕐 waitForResult: Attempt ${attempts} for job ${jobId}`);
            try {
                const response = await fetch(`http://localhost:5001/result/${jobId}`);
                console.log(`🕐 waitForResult: Got response status ${response.status}`);
                
                if (response.status === 200) {
                    // Analysis completed successfully - this is the final result
                    const result = await response.json();
                    console.log('✅ waitForResult: Got final result:', result);
                    return result;
                } else if (response.status === 202) {
                    // Analysis still in progress, wait and retry
                    console.log('🕐 waitForResult: Still in progress (202), waiting...');
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    continue;
                } else {
                    // Error occurred
                    const error = await response.json();
                    console.error('❌ waitForResult: API error:', error);
                    throw new Error(error.error || 'Analysis failed');
                }
            } catch (error) {
                console.error('❌ waitForResult: Error in attempt', attempts, ':', error);
                if (error.message.includes('fetch')) {
                    // Network error, wait and retry
                    console.log('🕐 waitForResult: Network error, retrying...');
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    continue;
                } else {
                    console.error('❌ waitForResult: Non-network error, throwing:', error);
                    throw error;
                }
            }
        }
        
        // Store reference for cleanup
        this.currentEventSource = eventSource;
    }
    
    async waitForAnalysisCompletion(jobId) {
        return new Promise((resolve) => {
            const checkStatus = async () => {
                try {
                    const response = await fetch(`http://localhost:5001/progress/${jobId}`);
                    if (response.ok) {
                        // EventSource will handle updates
                        setTimeout(checkStatus, 1000);
                    } else {
                        resolve();
                    }
                } catch (e) {
                    // Connection closed or completed
                    resolve();
                }
            };
            
            // Also resolve when EventSource closes
            if (this.currentEventSource) {
                this.currentEventSource.addEventListener('close', resolve);
                this.currentEventSource.addEventListener('error', resolve);
            }
            
            setTimeout(resolve, 30000); // Timeout after 30 seconds
            checkStatus();
        });
    }
    
    async getAnalysisResult(jobId) {
        // For now, return null since we're using direct response
        // In a full implementation, this would fetch the completed result
        return null;
    }
    
    processAnalysisResult(result, file) {
        try {
            console.log(`🎼 Processing analysis result: ${result.sequence?.length || 0} notes detected`);
            
            // Load the analyzed sequence
            if (this.deserializeMusicData(JSON.stringify(result))) {
                this.cursorPosition = this.currentSequence.length;
                this.selectedNoteIndex = -1;
                this.updateDisplay();
                
                // Also put the JSON in the textarea
                document.getElementById('musicData').value = JSON.stringify(result, null, 2);
                
                // Show improved message based on algorithm used
                const algorithm = result.analysis_params?.algorithm || 'unknown';
                const isAdvanced = algorithm.includes('demucs');
                const algorithmMsg = isAdvanced ? '🎛️ Advanced Demucs analysis' : 'Standard analysis';
                
                this.updateUploadStatus(`✅ ${algorithmMsg} complete! Found ${result.sequence.length} notes. Tempo: ${result.detected_tempo?.toFixed(1) || 'unknown'} BPM`);
                this.updateStatus(`Server audio analysis loaded: ${result.sequence.length} notes`);
                
                console.log(`✅ Music loaded: ${result.sequence.length} notes in sequence`);
                return true;
            } else {
                console.error('❌ Failed to deserialize analysis result');
                this.updateUploadStatus('⚠️ Failed to load analyzed sequence');
                return false;
            }
        } catch (error) {
            console.error('❌ Error processing analysis result:', error);
            this.updateUploadStatus('⚠️ Error processing analysis result');
            return false;
        }
    }
    
    hideAnalysisProgress() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        if (this.currentEventSource) {
            this.currentEventSource.close();
            this.currentEventSource = null;
        }
    }
    
    updateUploadStatus(message) {
        const statusElement = document.getElementById('uploadStatus');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }
}

const musicMaker = new BitMusicMaker();

document.addEventListener('DOMContentLoaded', () => {
    musicMaker.updateStatus('8-Bit Music Maker ready! Start typing to create music.');
});