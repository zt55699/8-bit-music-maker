class BitMusicMaker {
    constructor() {
        this.audioContext = null;
        this.isPlaying = false;
        this.currentSequence = [];
        this.playbackIndex = 0;
        this.playbackInterval = null;
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
        
        this.playbackInterval = setInterval(() => {
            if (this.playbackIndex < this.currentSequence.length) {
                const note = this.currentSequence[this.playbackIndex];
                this.playNote(note.frequency);
                this.highlightPlayingNote(this.playbackIndex);
                this.playbackIndex++;
            } else {
                this.stopPlayback();
            }
        }, 300);
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
                frequency: note.frequency
            })),
            created: new Date().toISOString()
        };
        
        return JSON.stringify(data, null, 2);
    }
    
    deserializeMusicData(jsonData) {
        try {
            const data = JSON.parse(jsonData);
            if (data.sequence && Array.isArray(data.sequence)) {
                this.currentSequence = data.sequence.map(note => ({
                    key: note.key,
                    frequency: note.frequency,
                    timestamp: Date.now()
                }));
                return true;
            }
        } catch (e) {
            console.error('Failed to parse music data:', e);
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
}

const musicMaker = new BitMusicMaker();

document.addEventListener('DOMContentLoaded', () => {
    musicMaker.updateStatus('8-Bit Music Maker ready! Start typing to create music.');
});