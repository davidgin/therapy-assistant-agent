import React, {useState} from 'react';
import {View, StyleSheet, ScrollView, KeyboardAvoidingView, Platform} from 'react-native';
import {Text, TextInput, Button, Card, Title, Paragraph} from 'react-native-paper';
import {apiService} from '../services/api';
import {DiagnosticRequest, DiagnosticResponse} from '../types';
import {theme} from '../theme/theme';
import Toast from 'react-native-toast-message';
import VoiceRecorder from '../components/VoiceRecorder';
import {VoiceAnalysis} from '../services/voiceService';

const DiagnosticScreen: React.FC = () => {
  const [symptoms, setSymptoms] = useState('');
  const [patientContext, setPatientContext] = useState('');
  const [response, setResponse] = useState<DiagnosticResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [voiceAnalysis, setVoiceAnalysis] = useState<VoiceAnalysis | null>(null);
  const [transcribedText, setTranscribedText] = useState('');

  const handleSubmit = async () => {
    if (!symptoms.trim()) {
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: 'Please enter patient symptoms',
      });
      return;
    }

    setLoading(true);
    try {
      // Combine manual symptoms with voice analysis
      let enhancedSymptoms = symptoms.trim();
      if (transcribedText) {
        enhancedSymptoms += `\n\nTranscribed speech: ${transcribedText}`;
      }

      let enhancedContext = patientContext.trim();
      if (voiceAnalysis) {
        enhancedContext += `\n\nVoice Analysis:
- Tone: ${voiceAnalysis.tone}
- Emotion: ${voiceAnalysis.emotion}
- Sentiment: ${voiceAnalysis.sentiment}
- Speech Rate: ${voiceAnalysis.speechRate.toFixed(1)} WPM
- Pause Frequency: ${voiceAnalysis.pauseFrequency.toFixed(1)}/min
- Confidence: ${(voiceAnalysis.confidence * 100).toFixed(1)}%`;
      }

      const request: DiagnosticRequest = {
        symptoms: enhancedSymptoms,
        patient_context: enhancedContext || undefined,
      };

      const result = await apiService.submitDiagnostic(request);
      setResponse(result);
      
      Toast.show({
        type: 'success',
        text1: 'Analysis Complete',
        text2: 'Diagnostic analysis has been generated',
      });
    } catch (error: any) {
      console.error('Diagnostic error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to analyze symptoms';
      Toast.show({
        type: 'error',
        text1: 'Analysis Failed',
        text2: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSymptoms('');
    setPatientContext('');
    setResponse(null);
    setVoiceAnalysis(null);
    setTranscribedText('');
  };

  const handleVoiceTranscription = (transcription: string, analysis?: VoiceAnalysis) => {
    setTranscribedText(transcription);
    setVoiceAnalysis(analysis || null);
    
    // Auto-populate symptoms field with transcribed text
    if (transcription && !symptoms.trim()) {
      setSymptoms(transcription);
    }
  };

  const handleVoiceError = (error: string) => {
    Toast.show({
      type: 'error',
      text1: 'Voice Recording Error',
      text2: error,
    });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.header}>
          <Title style={styles.title}>🤖 AI Diagnostic Assistant</Title>
          <Paragraph style={styles.subtitle}>
            Evidence-based differential diagnosis using DSM-5-TR criteria
          </Paragraph>
        </View>

        <VoiceRecorder
          onTranscriptionComplete={handleVoiceTranscription}
          onError={handleVoiceError}
          disabled={loading}
        />

        <Card style={styles.card}>
          <Card.Content>
            <TextInput
              label="Patient Symptoms *"
              value={symptoms}
              onChangeText={setSymptoms}
              mode="outlined"
              multiline
              numberOfLines={6}
              placeholder="Describe the patient's presenting symptoms, including duration, severity, and impact on functioning..."
              style={styles.textArea}
            />
            
            <TextInput
              label="Patient Context"
              value={patientContext}
              onChangeText={setPatientContext}
              mode="outlined"
              multiline
              numberOfLines={4}
              placeholder="Additional context such as medical history, psychosocial factors, current medications..."
              style={styles.textArea}
            />
            
            <View style={styles.buttonContainer}>
              <Button
                mode="contained"
                onPress={handleSubmit}
                loading={loading}
                disabled={loading || !symptoms.trim()}
                style={styles.button}>
                Analyze Symptoms
              </Button>
              
              <Button
                mode="outlined"
                onPress={handleClear}
                disabled={loading}
                style={styles.clearButton}>
                Clear
              </Button>
            </View>
          </Card.Content>
        </Card>

        {response && (
          <Card style={styles.responseCard}>
            <Card.Content>
              <Title style={styles.responseTitle}>🎯 Diagnostic Analysis</Title>
              <ScrollView style={styles.responseContent}>
                <Text style={styles.responseText}>{response.analysis}</Text>
              </ScrollView>
              
              {response.suggested_diagnoses && response.suggested_diagnoses.length > 0 && (
                <View style={styles.diagnosesContainer}>
                  <Text style={styles.diagnosesTitle}>Suggested Diagnoses:</Text>
                  {response.suggested_diagnoses.map((diagnosis, index) => (
                    <Text key={index} style={styles.diagnosisItem}>
                      • {diagnosis}
                    </Text>
                  ))}
                </View>
              )}
              
              {response.confidence && (
                <View style={styles.confidenceContainer}>
                  <Text style={styles.confidenceLabel}>Confidence Level:</Text>
                  <Text style={styles.confidenceValue}>
                    {Math.round(response.confidence * 100)}%
                  </Text>
                </View>
              )}
            </Card.Content>
          </Card>
        )}

        <Card style={styles.guidelinesCard}>
          <Card.Content>
            <Title style={styles.guidelinesTitle}>Clinical Guidelines</Title>
            <View style={styles.guidelinesList}>
              <Text style={styles.guidelineItem}>• Always conduct comprehensive clinical interviews</Text>
              <Text style={styles.guidelineItem}>• Consider medical causes for psychiatric symptoms</Text>
              <Text style={styles.guidelineItem}>• Use standardized assessment tools when appropriate</Text>
              <Text style={styles.guidelineItem}>• Obtain collateral information when clinically indicated</Text>
              <Text style={styles.guidelineItem}>• Document all clinical reasoning and decision-making</Text>
              <Text style={styles.guidelineItem}>• Consult with colleagues or supervisors for complex cases</Text>
            </View>
          </Card.Content>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollContainer: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 14,
    color: theme.colors.text,
    textAlign: 'center',
  },
  card: {
    marginBottom: 20,
  },
  textArea: {
    marginBottom: 16,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    flex: 1,
    padding: 6,
  },
  clearButton: {
    flex: 1,
    padding: 6,
  },
  responseCard: {
    marginBottom: 20,
    backgroundColor: theme.colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.success,
  },
  responseTitle: {
    fontSize: 20,
    color: theme.colors.primary,
    marginBottom: 15,
  },
  responseContent: {
    maxHeight: 200,
    marginBottom: 15,
  },
  responseText: {
    fontSize: 14,
    color: theme.colors.text,
    lineHeight: 20,
  },
  diagnosesContainer: {
    marginTop: 15,
    padding: 15,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
  },
  diagnosesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 10,
  },
  diagnosisItem: {
    fontSize: 14,
    color: theme.colors.text,
    marginBottom: 5,
  },
  confidenceContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 15,
    padding: 10,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
  },
  confidenceLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.text,
  },
  confidenceValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.primary,
  },
  guidelinesCard: {
    backgroundColor: theme.colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.warning,
  },
  guidelinesTitle: {
    fontSize: 18,
    color: theme.colors.primary,
    marginBottom: 15,
  },
  guidelinesList: {
    gap: 8,
  },
  guidelineItem: {
    fontSize: 14,
    color: theme.colors.text,
    lineHeight: 18,
  },
});

export default DiagnosticScreen;