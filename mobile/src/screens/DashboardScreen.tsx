import React from 'react';
import {View, StyleSheet, ScrollView} from 'react-native';
import {Text, Card, Title, Paragraph, Button} from 'react-native-paper';
import {useAuth} from '../contexts/AuthContext';
import {theme} from '../theme/theme';
import {useNavigation} from '@react-navigation/native';
import {BottomTabNavigationProp} from '@react-navigation/bottom-tabs';
import {BottomTabParamList} from '../types';

type DashboardNavigationProp = BottomTabNavigationProp<BottomTabParamList, 'Dashboard'>;

const DashboardScreen: React.FC = () => {
  const {user} = useAuth();
  const navigation = useNavigation<DashboardNavigationProp>();

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Title style={styles.title}>🧠 Therapy Assistant</Title>
        <Paragraph style={styles.welcome}>Welcome back, {user?.name}!</Paragraph>
      </View>

      <View style={styles.grid}>
        <Card style={styles.card} onPress={() => navigation.navigate('Diagnostic')}>
          <Card.Content style={styles.cardContent}>
            <Text style={styles.cardIcon}>🤖</Text>
            <Title style={styles.cardTitle}>Diagnostic Assistant</Title>
            <Paragraph style={styles.cardDescription}>
              AI-powered symptom analysis and differential diagnosis
            </Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.card} onPress={() => navigation.navigate('Treatment')}>
          <Card.Content style={styles.cardContent}>
            <Text style={styles.cardIcon}>💊</Text>
            <Title style={styles.cardTitle}>Treatment Planning</Title>
            <Paragraph style={styles.cardDescription}>
              Evidence-based treatment recommendations
            </Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.card} onPress={() => navigation.navigate('Cases')}>
          <Card.Content style={styles.cardContent}>
            <Text style={styles.cardIcon}>📋</Text>
            <Title style={styles.cardTitle}>Clinical Cases</Title>
            <Paragraph style={styles.cardDescription}>
              Review synthetic cases for training
            </Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.card} onPress={() => navigation.navigate('Profile')}>
          <Card.Content style={styles.cardContent}>
            <Text style={styles.cardIcon}>👤</Text>
            <Title style={styles.cardTitle}>Profile</Title>
            <Paragraph style={styles.cardDescription}>
              Manage your account and preferences
            </Paragraph>
          </Card.Content>
        </Card>
      </View>

      <Card style={styles.statusCard}>
        <Card.Content>
          <Title style={styles.statusTitle}>System Status</Title>
          <View style={styles.statusRow}>
            <Text style={styles.statusLabel}>License Status:</Text>
            <Text style={[styles.statusValue, {color: user?.is_licensed ? theme.colors.success : theme.colors.warning}]}>
              {user?.is_licensed ? 'Verified' : 'Not Verified'}
            </Text>
          </View>
          {user?.license_number && (
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>License Number:</Text>
              <Text style={styles.statusValue}>{user.license_number}</Text>
            </View>
          )}
          {user?.license_state && (
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>License State:</Text>
              <Text style={styles.statusValue}>{user.license_state}</Text>
            </View>
          )}
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
    fontSize: 28,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 10,
  },
  welcome: {
    fontSize: 16,
    color: theme.colors.text,
  },
  grid: {
    padding: 20,
    gap: 15,
  },
  card: {
    marginBottom: 15,
    elevation: 3,
  },
  cardContent: {
    alignItems: 'center',
    padding: 20,
  },
  cardIcon: {
    fontSize: 48,
    marginBottom: 10,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.primary,
    marginBottom: 8,
    textAlign: 'center',
  },
  cardDescription: {
    fontSize: 14,
    color: theme.colors.text,
    textAlign: 'center',
    lineHeight: 20,
  },
  statusCard: {
    margin: 20,
    marginTop: 0,
    backgroundColor: theme.colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.info,
  },
  statusTitle: {
    fontSize: 18,
    color: theme.colors.primary,
    marginBottom: 15,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusLabel: {
    fontSize: 14,
    color: theme.colors.text,
    fontWeight: '500',
  },
  statusValue: {
    fontSize: 14,
    color: theme.colors.text,
  },
});

export default DashboardScreen;