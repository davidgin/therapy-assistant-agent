import Voice from '@react-native-voice/voice';
import {PermissionsAndroid, Platform} from 'react-native';
import AudioRecorderPlayer from 'react-native-audio-recorder-player';
import RNFS from 'react-native-fs';
import {apiService} from './api';

export interface VoiceAnalysis {
  transcription: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  emotion: string;
  tone: 'calm' | 'anxious' | 'depressed' | 'agitated' | 'neutral';
  speechRate: number;
  pauseFrequency: number;
  confidence: number;
}

export interface RecordingResult {
  uri: string;
  duration: number;
  transcription?: string;
  analysis?: VoiceAnalysis;
}

class VoiceService {
  private audioRecorderPlayer: AudioRecorderPlayer;
  private isRecording: boolean = false;
  private isListening: boolean = false;
  private currentRecordingUri: string | null = null;

  constructor() {
    this.audioRecorderPlayer = new AudioRecorderPlayer();
    this.setupVoiceRecognition();
  }

  private setupVoiceRecognition() {
    Voice.onSpeechStart = this.onSpeechStart;
    Voice.onSpeechRecognized = this.onSpeechRecognized;
    Voice.onSpeechEnd = this.onSpeechEnd;
    Voice.onSpeechError = this.onSpeechError;
    Voice.onSpeechResults = this.onSpeechResults;
    Voice.onSpeechPartialResults = this.onSpeechPartialResults;
  }

  private onSpeechStart = (e: any) => {
    console.log('Speech recognition started', e);
  };

  private onSpeechRecognized = (e: any) => {
    console.log('Speech recognized', e);
  };

  private onSpeechEnd = (e: any) => {
    console.log('Speech recognition ended', e);
    this.isListening = false;
  };

  private onSpeechError = (e: any) => {
    console.error('Speech recognition error', e);
    this.isListening = false;
  };

  private onSpeechResults = (e: any) => {
    console.log('Speech results', e);
  };

  private onSpeechPartialResults = (e: any) => {
    console.log('Speech partial results', e);
  };

  async requestPermissions(): Promise<boolean> {
    if (Platform.OS === 'android') {
      try {
        const granted = await PermissionsAndroid.requestMultiple([
          PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
          PermissionsAndroid.PERMISSIONS.READ_EXTERNAL_STORAGE,
        ]);

        return (
          granted['android.permission.RECORD_AUDIO'] === PermissionsAndroid.RESULTS.GRANTED &&
          granted['android.permission.WRITE_EXTERNAL_STORAGE'] === PermissionsAndroid.RESULTS.GRANTED &&
          granted['android.permission.READ_EXTERNAL_STORAGE'] === PermissionsAndroid.RESULTS.GRANTED
        );
      } catch (err) {
        console.error('Permission request failed', err);
        return false;
      }
    }
    return true; // iOS permissions are handled in Info.plist
  }

  async startRecording(): Promise<void> {
    const hasPermission = await this.requestPermissions();
    if (!hasPermission) {
      throw new Error('Microphone permission denied');
    }

    const path = `${RNFS.DocumentDirectoryPath}/voice_recording_${Date.now()}.m4a`;
    
    try {
      await this.audioRecorderPlayer.startRecorder(path);
      this.isRecording = true;
      this.currentRecordingUri = path;
      console.log('Recording started at:', path);
    } catch (error) {
      console.error('Failed to start recording', error);
      throw error;
    }
  }

  async stopRecording(): Promise<RecordingResult> {
    if (!this.isRecording || !this.currentRecordingUri) {
      throw new Error('No active recording');
    }

    try {
      const result = await this.audioRecorderPlayer.stopRecorder();
      this.isRecording = false;
      
      const stats = await RNFS.stat(this.currentRecordingUri);
      
      return {
        uri: this.currentRecordingUri,
        duration: parseInt(result) / 1000, // Convert to seconds
      };
    } catch (error) {
      console.error('Failed to stop recording', error);
      throw error;
    }
  }

  async startListening(): Promise<void> {
    const hasPermission = await this.requestPermissions();
    if (!hasPermission) {
      throw new Error('Microphone permission denied');
    }

    try {
      await Voice.start('en-US');
      this.isListening = true;
    } catch (error) {
      console.error('Failed to start voice recognition', error);
      throw error;
    }
  }

  async stopListening(): Promise<string[]> {
    if (!this.isListening) {
      return [];
    }

    try {
      await Voice.stop();
      this.isListening = false;
      // Return the latest recognition results
      return await Voice.getSpeechRecognitionServices();
    } catch (error) {
      console.error('Failed to stop voice recognition', error);
      throw error;
    }
  }

  async transcribeAudio(audioUri: string): Promise<string> {
    try {
      // Convert audio file to base64
      const audioData = await RNFS.readFile(audioUri, 'base64');
      
      // Send to backend for transcription
      const response = await apiService.transcribeAudio(audioData);
      return response.transcription;
    } catch (error) {
      console.error('Transcription failed', error);
      throw error;
    }
  }

  async analyzeVoice(audioUri: string): Promise<VoiceAnalysis> {
    try {
      // Convert audio file to base64
      const audioData = await RNFS.readFile(audioUri, 'base64');
      
      // Send to backend for analysis
      const response = await apiService.analyzeVoice(audioData);
      return response;
    } catch (error) {
      console.error('Voice analysis failed', error);
      throw error;
    }
  }

  async processRecording(recordingResult: RecordingResult): Promise<RecordingResult> {
    try {
      // Get transcription
      const transcription = await this.transcribeAudio(recordingResult.uri);
      
      // Get voice analysis
      const analysis = await this.analyzeVoice(recordingResult.uri);
      
      return {
        ...recordingResult,
        transcription,
        analysis,
      };
    } catch (error) {
      console.error('Failed to process recording', error);
      throw error;
    }
  }

  isCurrentlyRecording(): boolean {
    return this.isRecording;
  }

  isCurrentlyListening(): boolean {
    return this.isListening;
  }

  async cleanup(): Promise<void> {
    try {
      if (this.isRecording) {
        await this.stopRecording();
      }
      if (this.isListening) {
        await this.stopListening();
      }
      Voice.destroy();
    } catch (error) {
      console.error('Cleanup failed', error);
    }
  }
}

export const voiceService = new VoiceService();
export default voiceService;