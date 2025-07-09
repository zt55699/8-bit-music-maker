class BitMusicMaker {
    constructor() {
        this.audioContext = null;
        this.isPlaying = false;
        this.currentSequence = [];
        this.playbackIndex = 0;
        this.playbackInterval = null;
        
        this.initializeAudio();
        this.setupEventListeners();
        this.setupKeyMapping();
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
        document.getElementById('loadBtn').addEventListener('click', () => this.loadMusic());
        document.getElementById('copyBtn').addEventListener('click', () => this.copyToClipboard());
        document.getElementById('pasteBtn').addEventListener('click', () => this.pasteFromClipboard());
    }
    
    handleKeyPress(e) {
        if (e.repeat) return;
        
        const key = e.key.toLowerCase();
        
        if (key === 'backspace') {
            e.preventDefault();
            if (this.currentSequence.length > 0) {
                this.currentSequence.pop();
                this.updateDisplay();
                this.updateStatus('Deleted last note');
            }
            return;
        }
        
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
            
            this.currentSequence.push(note);
            this.updateDisplay();
            this.playNote(freq);
            this.updateStatus(`Played: ${key === ' ' ? 'pause' : key} (${freq}Hz)`);
        }
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
        const sequence = this.currentSequence.map(note => {
            return note.key === ' ' ? '⏸️' : `${note.key.toUpperCase()}`;
        }).join(' ');
        
        display.textContent = sequence || 'Your music will appear here...';
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
                this.playbackIndex++;
            } else {
                this.stopPlayback();
            }
        }, 300);
    }
    
    stopPlayback() {
        this.isPlaying = false;
        if (this.playbackInterval) {
            clearInterval(this.playbackInterval);
            this.playbackInterval = null;
        }
        document.getElementById('playBtn').textContent = '▶️ Play';
        this.updateStatus('Playback stopped');
    }
    
    clearSequence() {
        this.currentSequence = [];
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
            this.updateDisplay();
            this.updateStatus('Music loaded successfully');
        } else {
            this.updateStatus('Invalid music data format');
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
        } catch (err) {
            this.updateStatus('Failed to paste from clipboard');
        }
    }
}

const musicMaker = new BitMusicMaker();

document.addEventListener('DOMContentLoaded', () => {
    musicMaker.updateStatus('8-Bit Music Maker ready! Start typing to create music.');
});