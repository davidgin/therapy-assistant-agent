import React, {useState, useEffect} from 'react';
import {View, StyleSheet, Alert} from 'react-native';
import {Button, Text, Card, ProgressBar, Chip} from 'react-native-paper';
import {voiceService, RecordingResult, VoiceAnalysis} from '../services/voiceService';
import {theme} from '../theme/theme';
import Toast from 'react-native-toast-message';

interface VoiceRecorderProps {
  onTranscriptionComplete: (transcription: string, analysis?: VoiceAnalysis) => void;
  onError: (error: string) => void;
  disabled?: boolean;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onTranscriptionComplete,
  onError,
  disabled = false,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [analysis, setAnalysis] = useState<VoiceAnalysis | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const startRecording = async () => {
    try {
      await voiceService.startRecording();
      setIsRecording(true);
      setRecordingDuration(0);
      setAnalysis(null);
      
      Toast.show({
        type: 'info',
        text1: 'Recording Started',
        text2: 'Speak clearly into the microphone',
      });
    } catch (error: any) {
      console.error('Recording start failed:', error);
      onError(error.message || 'Failed to start recording');
    }
  };

  const stopRecording = async () => {
    try {
      setIsRecording(false);
      setIsProcessing(true);
      
      const recordingResult = await voiceService.stopRecording();
      
      Toast.show({
        type: 'info',
        text1: 'Processing Audio',
        text2: 'Analyzing speech patterns...',
      });
      
      // Process the recording (transcribe and analyze)
      const processedResult = await voiceService.processRecording(recordingResult);
      
      if (processedResult.transcription) {
        onTranscriptionComplete(processedResult.transcription, processedResult.analysis);
        setAnalysis(processedResult.analysis || null);
        
        Toast.show({
          type: 'success',
          text1: 'Analysis Complete',
          text2: 'Voice analysis has been processed',
        });
      } else {
        throw new Error('No transcription received');
      }
    } catch (error: any) {
      console.error('Recording processing failed:', error);
      onError(error.message || 'Failed to process recording');
    } finally {
      setIsProcessing(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getToneColor = (tone: string) => {
    switch (tone) {
      case 'calm':
        return theme.colors.success;
      case 'anxious':
        return theme.colors.warning;
      case 'depressed':
        return theme.colors.info;
      case 'agitated':
        return theme.colors.notification;
      default:
        return theme.colors.placeholder;
    }
  };

  const getEmotionColor = (emotion: string) => {
    const lowerEmotion = emotion.toLowerCase();
    if (lowerEmotion.includes('happy') || lowerEmotion.includes('joy')) {
      return theme.colors.success;
    }
    if (lowerEmotion.includes('sad') || lowerEmotion.includes('depressed')) {
      return theme.colors.info;
    }
    if (lowerEmotion.includes('angry') || lowerEmotion.includes('frustrated')) {
      return theme.colors.notification;
    }
    if (lowerEmotion.includes('anxious') || lowerEmotion.includes('worried')) {
      return theme.colors.warning;
    }
    return theme.colors.placeholder;
  };

  return (
    <Card style={styles.container}>
      <Card.Content>
        <Text style={styles.title}>🎤 Voice Analysis</Text>
        <Text style={styles.subtitle}>
          Record patient speech to analyze tone, emotion, and speech patterns
        </Text>
        
        {isRecording && (
          <View style={styles.recordingIndicator}>
            <Text style={styles.recordingText}>Recording...</Text>
            <Text style={styles.duration}>{formatDuration(recordingDuration)}</Text>
            <ProgressBar 
              indeterminate 
              color={theme.colors.notification}
              style={styles.progressBar}
            />
          </View>
        )}
        
        {isProcessing && (
          <View style={styles.processingIndicator}>
            <Text style={styles.processingText}>Processing audio...</Text>
            <ProgressBar 
              indeterminate 
              color={theme.colors.primary}
              style={styles.progressBar}
            />
          </View>
        )}
        
        <View style={styles.buttonContainer}>
          {!isRecording ? (
            <Button
              mode="contained"
              onPress={startRecording}
              disabled={disabled || isProcessing}
              style={[styles.button, styles.recordButton]}
              icon="microphone">
              Start Recording
            </Button>
          ) : (
            <Button
              mode="contained"
              onPress={stopRecording}
              disabled={disabled}
              style={[styles.button, styles.stopButton]}
              buttonColor={theme.colors.notification}
              icon="stop">
              Stop Recording
            </Button>
          )}
        </View>
        
        {analysis && (
          <View style={styles.analysisContainer}>
            <Text style={styles.analysisTitle}>Voice Analysis Results</Text>
            
            <View style={styles.chipContainer}>
              <Chip 
                style={[styles.chip, {backgroundColor: getToneColor(analysis.tone)}]}
                textStyle={styles.chipText}>
                Tone: {analysis.tone}
              </Chip>
              
              <Chip 
                style={[styles.chip, {backgroundColor: getEmotionColor(analysis.emotion)}]}
                textStyle={styles.chipText}>
                Emotion: {analysis.emotion}
              </Chip>
              
              <Chip 
                style={[styles.chip, {backgroundColor: 
                  analysis.sentiment === 'positive' ? theme.colors.success :
                  analysis.sentiment === 'negative' ? theme.colors.notification :
                  theme.colors.placeholder
                }]}
                textStyle={styles.chipText}>
                Sentiment: {analysis.sentiment}
              </Chip>
            </View>
            
            <View style={styles.metricsContainer}>
              <View style={styles.metric}>
                <Text style={styles.metricLabel}>Speech Rate</Text>
                <Text style={styles.metricValue}>{analysis.speechRate.toFixed(1)} WPM</Text>
              </View>
              
              <View style={styles.metric}>
                <Text style={styles.metricLabel}>Pause Frequency</Text>
                <Text style={styles.metricValue}>{analysis.pauseFrequency.toFixed(1)}/min</Text>
              </View>
              
              <View style={styles.metric}>
                <Text style={styles.metricLabel}>Confidence</Text>
                <Text style={styles.metricValue}>{Math.round(analysis.confidence * 100)}%</Text>
              </View>
            </View>
          </View>
        )}
        
        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerText}>
            Voice analysis provides additional clinical insights but should not replace 
            professional clinical judgment. Ensure patient consent before recording.
          </Text>
        </View>
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
    backgroundColor: theme.colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.accent,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: theme.colors.text,
    marginBottom: 20,
  },
  recordingIndicator: {
    alignItems: 'center',
    marginBottom: 20,
  },
  recordingText: {
    fontSize: 16,
    color: theme.colors.notification,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  duration: {
    fontSize: 24,
    color: theme.colors.notification,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  processingIndicator: {
    alignItems: 'center',
    marginBottom: 20,
  },
  processingText: {
    fontSize: 16,
    color: theme.colors.primary,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  progressBar: {
    width: '100%',
    height: 4,
  },
  buttonContainer: {
    alignItems: 'center',
    marginBottom: 20,
  },
  button: {
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  recordButton: {
    backgroundColor: theme.colors.success,
  },
  stopButton: {
    backgroundColor: theme.colors.notification,
  },
  analysisContainer: {
    marginTop: 20,
    padding: 16,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
  },
  analysisTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 16,
  },
  chipContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  chip: {
    marginRight: 8,
  },
  chipText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 12,
  },
  metricsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: theme.colors.placeholder,
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.primary,
  },
  disclaimer: {
    marginTop: 20,
    padding: 12,
    backgroundColor: theme.colors.background,
    borderRadius: 4,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.warning,
  },
  disclaimerText: {
    fontSize: 12,
    color: theme.colors.placeholder,
    lineHeight: 16,
  },
});

export default VoiceRecorder;