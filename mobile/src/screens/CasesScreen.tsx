import React, {useState, useEffect} from 'react';
import {View, StyleSheet, ScrollView, RefreshControl} from 'react-native';
import {Text, Card, Title, Paragraph, Chip} from 'react-native-paper';
import {apiService} from '../services/api';
import {ClinicalCase} from '../types';
import {theme} from '../theme/theme';
import Toast from 'react-native-toast-message';

const CasesScreen: React.FC = () => {
  const [cases, setCases] = useState<ClinicalCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadCases = async () => {
    try {
      const result = await apiService.getClinicalCases();
      setCases(result);
    } catch (error: any) {
      console.error('Cases error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to load clinical cases';
      Toast.show({
        type: 'error',
        text1: 'Load Failed',
        text2: errorMessage,
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadCases();
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'mild':
        return '#f59e0b';
      case 'moderate':
        return '#f97316';
      case 'severe':
        return '#ef4444';
      default:
        return theme.colors.placeholder;
    }
  };

  const formatAge = (age: number, gender: string) => {
    return `${age}y ${gender}`;
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
      <View style={styles.header}>
        <Title style={styles.title}>📋 Clinical Cases</Title>
        <Paragraph style={styles.subtitle}>
          Synthetic clinical cases for training and educational purposes
        </Paragraph>
      </View>

      {cases.length === 0 && !loading && (
        <Card style={styles.emptyCard}>
          <Card.Content>
            <Text style={styles.emptyText}>No clinical cases are currently available.</Text>
            <Text style={styles.emptySubtext}>
              Cases may be loaded from the synthetic data files.
            </Text>
          </Card.Content>
        </Card>
      )}

      {cases.map((clinicalCase) => (
        <Card key={clinicalCase.case_id} style={styles.caseCard}>
          <Card.Content>
            <View style={styles.caseHeader}>
              <Text style={styles.caseId}>{clinicalCase.case_id}</Text>
              <Chip
                style={[
                  styles.severityChip,
                  {backgroundColor: getSeverityColor(clinicalCase.severity)},
                ]}>
                {clinicalCase.severity?.toUpperCase()}
              </Chip>
            </View>

            {clinicalCase.patient_demographics && (
              <View style={styles.demographics}>
                <Text style={styles.demographicsText}>
                  {formatAge(
                    clinicalCase.patient_demographics.age,
                    clinicalCase.patient_demographics.gender,
                  )}
                  {clinicalCase.patient_demographics.occupation &&
                    ` | ${clinicalCase.patient_demographics.occupation}`}
                </Text>
              </View>
            )}

            {clinicalCase.presenting_symptoms && (
              <View style={styles.symptomsContainer}>
                <View style={styles.symptomsRow}>
                  {clinicalCase.presenting_symptoms.slice(0, 3).map((symptom, index) => (
                    <Chip key={index} style={styles.symptomChip}>
                      {symptom}
                    </Chip>
                  ))}
                  {clinicalCase.presenting_symptoms.length > 3 && (
                    <Chip style={styles.moreChip}>
                      +{clinicalCase.presenting_symptoms.length - 3} more
                    </Chip>
                  )}
                </View>
              </View>
            )}

            {clinicalCase.clinical_history && (
              <Text style={styles.clinicalHistory}>
                {clinicalCase.clinical_history.length > 150
                  ? `${clinicalCase.clinical_history.substring(0, 150)}...`
                  : clinicalCase.clinical_history}
              </Text>
            )}

            {clinicalCase.suggested_diagnosis && (
              <View style={styles.diagnosisContainer}>
                <Text style={styles.diagnosisText}>
                  {clinicalCase.suggested_diagnosis.primary}
                </Text>
                {clinicalCase.suggested_diagnosis.dsm5_code && (
                  <Text style={styles.dsmCode}>
                    ({clinicalCase.suggested_diagnosis.dsm5_code})
                  </Text>
                )}
                {clinicalCase.suggested_diagnosis.confidence && (
                  <Text style={styles.confidence}>
                    Confidence: {Math.round(clinicalCase.suggested_diagnosis.confidence * 100)}%
                  </Text>
                )}
              </View>
            )}

            {clinicalCase.treatment_recommendations && (
              <View style={styles.treatmentContainer}>
                <Text style={styles.treatmentTitle}>Treatment Recommendations:</Text>
                {clinicalCase.treatment_recommendations.slice(0, 2).map((rec, index) => (
                  <Text key={index} style={styles.treatmentItem}>
                    • {rec}
                  </Text>
                ))}
                {clinicalCase.treatment_recommendations.length > 2 && (
                  <Text style={styles.moreText}>
                    +{clinicalCase.treatment_recommendations.length - 2} more recommendations
                  </Text>
                )}
              </View>
            )}
          </Card.Content>
        </Card>
      ))}

      <Card style={styles.guidelinesCard}>
        <Card.Content>
          <Title style={styles.guidelinesTitle}>Case Study Guidelines</Title>
          <View style={styles.guidelinesList}>
            <Text style={styles.guidelineItem}>
              • These cases are synthetic and created for educational purposes only
            </Text>
            <Text style={styles.guidelineItem}>
              • Use cases to practice diagnostic reasoning and clinical decision-making
            </Text>
            <Text style={styles.guidelineItem}>
              • Consider multiple differential diagnoses for each case
            </Text>
            <Text style={styles.guidelineItem}>
              • Think about cultural, social, and contextual factors
            </Text>
            <Text style={styles.guidelineItem}>
              • Evaluate the appropriateness of suggested treatments
            </Text>
          </View>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    padding: 20,
    alignItems: 'center',
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
  emptyCard: {
    margin: 20,
    backgroundColor: theme.colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.warning,
  },
  emptyText: {
    fontSize: 16,
    color: theme.colors.text,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: theme.colors.placeholder,
  },
  caseCard: {
    marginHorizontal: 20,
    marginBottom: 15,
    elevation: 2,
  },
  caseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  caseId: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.primary,
  },
  severityChip: {
    backgroundColor: theme.colors.warning,
  },
  demographics: {
    marginBottom: 10,
  },
  demographicsText: {
    fontSize: 14,
    color: theme.colors.placeholder,
  },
  symptomsContainer: {
    marginBottom: 15,
  },
  symptomsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  symptomChip: {
    backgroundColor: theme.colors.background,
  },
  moreChip: {
    backgroundColor: theme.colors.background,
  },
  clinicalHistory: {
    fontSize: 14,
    color: theme.colors.placeholder,
    marginBottom: 15,
    lineHeight: 20,
  },
  diagnosisContainer: {
    marginBottom: 15,
    padding: 15,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
  },
  diagnosisText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: 5,
  },
  dsmCode: {
    fontSize: 14,
    color: theme.colors.placeholder,
    marginBottom: 5,
  },
  confidence: {
    fontSize: 12,
    color: theme.colors.placeholder,
  },
  treatmentContainer: {
    padding: 15,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
  },
  treatmentTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: theme.colors.text,
    marginBottom: 8,
  },
  treatmentItem: {
    fontSize: 14,
    color: theme.colors.placeholder,
    marginBottom: 5,
  },
  moreText: {
    fontSize: 12,
    color: theme.colors.placeholder,
    fontStyle: 'italic',
  },
  guidelinesCard: {
    margin: 20,
    backgroundColor: theme.colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.info,
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

export default CasesScreen;