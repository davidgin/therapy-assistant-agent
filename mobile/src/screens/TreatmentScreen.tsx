import React, {useState} from 'react';
import {View, StyleSheet, ScrollView, KeyboardAvoidingView, Platform} from 'react-native';
import {Text, TextInput, Button, Card, Title, Paragraph} from 'react-native-paper';
import {apiService} from '../services/api';
import {TreatmentRequest, TreatmentResponse} from '../types';
import {theme} from '../theme/theme';
import Toast from 'react-native-toast-message';

const TreatmentScreen: React.FC = () => {
  const [diagnosis, setDiagnosis] = useState('');
  const [patientContext, setPatientContext] = useState('');
  const [response, setResponse] = useState<TreatmentResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!diagnosis.trim()) {
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: 'Please enter a diagnosis',
      });
      return;
    }

    setLoading(true);
    try {
      const request: TreatmentRequest = {
        diagnosis: diagnosis.trim(),
        patient_context: patientContext.trim() || undefined,
      };

      const result = await apiService.submitTreatment(request);
      setResponse(result);
      
      Toast.show({
        type: 'success',
        text1: 'Treatment Plan Generated',
        text2: 'Evidence-based recommendations have been created',
      });
    } catch (error: any) {
      console.error('Treatment error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to generate treatment plan';
      Toast.show({
        type: 'error',
        text1: 'Generation Failed',
        text2: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setDiagnosis('');
    setPatientContext('');
    setResponse(null);
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.header}>
          <Title style={styles.title}>💊 Treatment Planning</Title>
          <Paragraph style={styles.subtitle}>
            Evidence-based treatment recommendations and intervention strategies
          </Paragraph>
        </View>

        <Card style={styles.card}>
          <Card.Content>
            <TextInput
              label="Primary Diagnosis *"
              value={diagnosis}
              onChangeText={setDiagnosis}
              mode="outlined"
              placeholder="e.g., Major Depressive Disorder, Generalized Anxiety Disorder"
              style={styles.input}
            />
            
            <TextInput
              label="Patient Context & Considerations"
              value={patientContext}
              onChangeText={setPatientContext}
              mode="outlined"
              multiline
              numberOfLines={4}
              placeholder="Age, severity, comorbidities, previous treatments, cultural factors, preferences, contraindications..."
              style={styles.textArea}
            />
            
            <View style={styles.buttonContainer}>
              <Button
                mode="contained"
                onPress={handleSubmit}
                loading={loading}
                disabled={loading || !diagnosis.trim()}
                style={styles.button}>
                Generate Treatment Plan
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
              <Title style={styles.responseTitle}>🎯 Treatment Recommendations</Title>
              <ScrollView style={styles.responseContent}>
                <Text style={styles.responseText}>{response.treatment_plan}</Text>
              </ScrollView>
              
              {response.interventions && response.interventions.length > 0 && (
                <View style={styles.interventionsContainer}>
                  <Text style={styles.interventionsTitle}>Recommended Interventions:</Text>
                  {response.interventions.map((intervention, index) => (
                    <Text key={index} style={styles.interventionItem}>
                      • {intervention}
                    </Text>
                  ))}
                </View>
              )}
              
              {response.goals && response.goals.length > 0 && (
                <View style={styles.goalsContainer}>
                  <Text style={styles.goalsTitle}>Treatment Goals:</Text>
                  {response.goals.map((goal, index) => (
                    <Text key={index} style={styles.goalItem}>
                      • {goal}
                    </Text>
                  ))}
                </View>
              )}
              
              {response.timeline && (
                <View style={styles.timelineContainer}>
                  <Text style={styles.timelineLabel}>Expected Timeline:</Text>
                  <Text style={styles.timelineValue}>{response.timeline}</Text>
                </View>
              )}
            </Card.Content>
          </Card>
        )}

        <Card style={styles.modalitiesCard}>
          <Card.Content>
            <Title style={styles.modalitiesTitle}>Evidence-Based Treatment Modalities</Title>
            <View style={styles.modalityItem}>
              <Text style={styles.modalityName}>Cognitive Behavioral Therapy (CBT)</Text>
              <Text style={styles.modalityDescription}>
                Effective for anxiety, depression, PTSD. Focuses on identifying and modifying dysfunctional thought patterns.
              </Text>
            </View>
            <View style={styles.modalityItem}>
              <Text style={styles.modalityName}>Dialectical Behavior Therapy (DBT)</Text>
              <Text style={styles.modalityDescription}>
                Particularly effective for borderline personality disorder and emotional dysregulation.
              </Text>
            </View>
            <View style={styles.modalityItem}>
              <Text style={styles.modalityName}>Pharmacotherapy</Text>
              <Text style={styles.modalityDescription}>
                Medication management for depression, anxiety, bipolar disorder, and psychosis.
              </Text>
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
  input: {
    marginBottom: 16,
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
  interventionsContainer: {
    marginTop: 15,
    padding: 15,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
  },
  interventionsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 10,
  },
  interventionItem: {
    fontSize: 14,
    color: theme.colors.text,
    marginBottom: 5,
  },
  goalsContainer: {
    marginTop: 15,
    padding: 15,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
  },
  goalsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 10,
  },
  goalItem: {
    fontSize: 14,
    color: theme.colors.text,
    marginBottom: 5,
  },
  timelineContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 15,
    padding: 10,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
  },
  timelineLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: theme.colors.text,
  },
  timelineValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: theme.colors.primary,
  },
  modalitiesCard: {
    backgroundColor: theme.colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.info,
  },
  modalitiesTitle: {
    fontSize: 18,
    color: theme.colors.primary,
    marginBottom: 15,
  },
  modalityItem: {
    marginBottom: 15,
  },
  modalityName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: 5,
  },
  modalityDescription: {
    fontSize: 14,
    color: theme.colors.placeholder,
    lineHeight: 18,
  },
});

export default TreatmentScreen;