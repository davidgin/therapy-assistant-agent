/**
 * Voice Recording and Analysis for Web Interface
 */

class VoiceRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.isProcessing = false;
        this.recordingStartTime = null;
        this.recordingTimer = null;
        this.stream = null;
        
        // Bind methods
        this.startRecording = this.startRecording.bind(this);
        this.stopRecording = this.stopRecording.bind(this);
        this.onDataAvailable = this.onDataAvailable.bind(this);
        this.onRecordingStop = this.onRecordingStop.bind(this);
    }

    async requestPermissions() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100
                }
            });
            return true;
        } catch (error) {
            console.error('Microphone permission denied:', error);
            return false;
        }
    }

    async startRecording() {
        if (this.isRecording || this.isProcessing) {
            return;
        }

        const hasPermission = await this.requestPermissions();
        if (!hasPermission) {
            this.showError('Microphone permission denied');
            return;
        }

        try {
            this.audioChunks = [];
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            this.mediaRecorder.ondataavailable = this.onDataAvailable;
            this.mediaRecorder.onstop = this.onRecordingStop;

            this.mediaRecorder.start();
            this.isRecording = true;
            this.recordingStartTime = Date.now();
            
            this.updateUI('recording');
            this.startTimer();
            
        } catch (error) {
            console.error('Recording start failed:', error);
            this.showError('Failed to start recording');
        }
    }

    async stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) {
            return;
        }

        this.mediaRecorder.stop();
        this.isRecording = false;
        this.stopTimer();
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        
        this.updateUI('processing');
    }

    onDataAvailable(event) {
        if (event.data.size > 0) {
            this.audioChunks.push(event.data);
        }
    }

    async onRecordingStop() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        await this.processAudio(audioBlob);
    }

    async processAudio(audioBlob) {
        this.isProcessing = true;
        
        try {
            // Convert to base64
            const arrayBuffer = await audioBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            const base64Audio = btoa(String.fromCharCode(...uint8Array));
            
            // Send to backend for analysis
            const response = await fetch('/voice/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getAuthToken()}`
                },
                body: JSON.stringify({
                    audio_data: base64Audio
                })
            });

            if (!response.ok) {
                throw new Error('Voice analysis failed');
            }

            const analysisResult = await response.json();
            this.handleAnalysisResult(analysisResult);
            
        } catch (error) {
            console.error('Audio processing failed:', error);
            this.showError('Failed to process audio: ' + error.message);
        } finally {
            this.isProcessing = false;
            this.updateUI('idle');
        }
    }

    handleAnalysisResult(result) {
        // Update transcription field
        const symptomsField = document.getElementById('symptoms');
        if (symptomsField && result.transcription) {
            if (!symptomsField.value.trim()) {
                symptomsField.value = result.transcription;
            } else {
                symptomsField.value += '\n\nTranscribed speech: ' + result.transcription;
            }
        }

        // Update context field with voice analysis
        const contextField = document.getElementById('patient_context');
        if (contextField && result.tone) {
            const voiceAnalysis = `\n\nVoice Analysis:
- Tone: ${result.tone}
- Emotion: ${result.emotion}
- Sentiment: ${result.sentiment}
- Speech Rate: ${result.speechRate.toFixed(1)} WPM
- Pause Frequency: ${result.pauseFrequency.toFixed(1)}/min
- Confidence: ${(result.confidence * 100).toFixed(1)}%`;
            
            contextField.value += voiceAnalysis;
        }

        // Update analysis display
        this.updateAnalysisDisplay(result);
        this.showSuccess('Voice analysis completed successfully');
    }

    updateAnalysisDisplay(result) {
        const analysisDiv = document.getElementById('voice-analysis-results');
        if (!analysisDiv) return;

        analysisDiv.innerHTML = `
            <h4>🎤 Voice Analysis Results</h4>
            <div class="analysis-chips">
                <span class="chip tone-${result.tone}">Tone: ${result.tone}</span>
                <span class="chip emotion-${result.emotion.toLowerCase()}">Emotion: ${result.emotion}</span>
                <span class="chip sentiment-${result.sentiment}">Sentiment: ${result.sentiment}</span>
            </div>
            <div class="analysis-metrics">
                <div class="metric">
                    <span class="metric-label">Speech Rate</span>
                    <span class="metric-value">${result.speechRate.toFixed(1)} WPM</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Pause Frequency</span>
                    <span class="metric-value">${result.pauseFrequency.toFixed(1)}/min</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Confidence</span>
                    <span class="metric-value">${Math.round(result.confidence * 100)}%</span>
                </div>
            </div>
        `;
        
        analysisDiv.style.display = 'block';
    }

    startTimer() {
        this.recordingTimer = setInterval(() => {
            const elapsed = Date.now() - this.recordingStartTime;
            const seconds = Math.floor(elapsed / 1000);
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            
            const timeDisplay = document.getElementById('recording-time');
            if (timeDisplay) {
                timeDisplay.textContent = `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    stopTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }

    updateUI(state) {
        const recordBtn = document.getElementById('record-btn');
        const stopBtn = document.getElementById('stop-btn');
        const statusDiv = document.getElementById('recording-status');
        const timeDisplay = document.getElementById('recording-time');

        if (!recordBtn || !stopBtn || !statusDiv) return;

        switch (state) {
            case 'recording':
                recordBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
                statusDiv.innerHTML = '<span style="color: #ef4444; font-weight: bold;">🔴 Recording...</span>';
                if (timeDisplay) timeDisplay.style.display = 'inline';
                break;
                
            case 'processing':
                recordBtn.style.display = 'none';
                stopBtn.style.display = 'none';
                statusDiv.innerHTML = '<span style="color: #3b82f6; font-weight: bold;">⏳ Processing audio...</span>';
                if (timeDisplay) timeDisplay.style.display = 'none';
                break;
                
            case 'idle':
            default:
                recordBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
                statusDiv.innerHTML = '';
                if (timeDisplay) {
                    timeDisplay.style.display = 'none';
                    timeDisplay.textContent = '0:00';
                }
                break;
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('voice-error');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
    }

    showSuccess(message) {
        const successDiv = document.getElementById('voice-success');
        if (successDiv) {
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            setTimeout(() => {
                successDiv.style.display = 'none';
            }, 3000);
        }
    }

    getAuthToken() {
        // Get token from cookie or localStorage
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'token') {
                return value;
            }
        }
        return localStorage.getItem('auth_token') || '';
    }
}

// Initialize voice recorder when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.voiceRecorder === 'undefined') {
        window.voiceRecorder = new VoiceRecorder();
    }
});

// Export for use in other scripts
window.VoiceRecorder = VoiceRecorder;