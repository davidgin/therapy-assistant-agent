import React from 'react';
import {View, StyleSheet, ScrollView, Alert} from 'react-native';
import {Text, Card, Title, Paragraph, Button, List, Divider} from 'react-native-paper';
import {useAuth} from '../contexts/AuthContext';
import {theme} from '../theme/theme';

const ProfileScreen: React.FC = () => {
  const {user, logout} = useAuth();

  const handleLogout = () => {
    Alert.alert(
      'Confirm Logout',
      'Are you sure you want to logout?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: logout,
        },
      ],
    );
  };

  if (!user) {
    return null;
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Title style={styles.title}>👤 Profile</Title>
        <Paragraph style={styles.subtitle}>Account information and settings</Paragraph>
      </View>

      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.sectionTitle}>Account Information</Title>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Name:</Text>
            <Text style={styles.infoValue}>{user.name}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Email:</Text>
            <Text style={styles.infoValue}>{user.email}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>User ID:</Text>
            <Text style={styles.infoValue}>{user.id}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Member Since:</Text>
            <Text style={styles.infoValue}>
              {new Date(user.created_at).toLocaleDateString()}
            </Text>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.sectionTitle}>Professional License</Title>
          <View style={styles.licenseContainer}>
            <View style={styles.licenseStatus}>
              <Text style={styles.statusLabel}>Status:</Text>
              <Text
                style={[
                  styles.statusValue,
                  {color: user.is_licensed ? theme.colors.success : theme.colors.warning},
                ]}>
                {user.is_licensed ? '✅ Verified' : '⚠️ Not Verified'}
              </Text>
            </View>
            {user.license_number && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>License Number:</Text>
                <Text style={styles.infoValue}>{user.license_number}</Text>
              </View>
            )}
            {user.license_state && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>License State:</Text>
                <Text style={styles.infoValue}>{user.license_state}</Text>
              </View>
            )}
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.sectionTitle}>App Information</Title>
          <List.Item
            title="Version"
            description="1.0.0"
            left={() => <List.Icon icon="information" />}
          />
          <Divider />
          <List.Item
            title="Privacy Policy"
            description="View our privacy policy"
            left={() => <List.Icon icon="shield-account" />}
            right={() => <List.Icon icon="chevron-right" />}
          />
          <Divider />
          <List.Item
            title="Terms of Service"
            description="View terms and conditions"
            left={() => <List.Icon icon="file-document" />}
            right={() => <List.Icon icon="chevron-right" />}
          />
          <Divider />
          <List.Item
            title="Support"
            description="Get help and support"
            left={() => <List.Icon icon="help-circle" />}
            right={() => <List.Icon icon="chevron-right" />}
          />
        </Card.Content>
      </Card>

      <Card style={styles.disclaimerCard}>
        <Card.Content>
          <Title style={styles.disclaimerTitle}>Important Notice</Title>
          <Paragraph style={styles.disclaimerText}>
            This application is designed for licensed mental health professionals only. 
            It provides clinical support tools and should not be used as a substitute for 
            professional clinical judgment. Always follow your professional training, 
            ethical guidelines, and applicable laws when providing mental health services.
          </Paragraph>
        </Card.Content>
      </Card>

      <View style={styles.buttonContainer}>
        <Button
          mode="contained"
          onPress={handleLogout}
          style={styles.logoutButton}
          buttonColor={theme.colors.notification}>
          Logout
        </Button>
      </View>
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
  card: {
    marginHorizontal: 20,
    marginBottom: 15,
  },
  sectionTitle: {
    fontSize: 18,
    color: theme.colors.primary,
    marginBottom: 15,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoLabel: {
    fontSize: 14,
    color: theme.colors.text,
    fontWeight: '500',
  },
  infoValue: {
    fontSize: 14,
    color: theme.colors.text,
    textAlign: 'right',
    flex: 1,
    marginLeft: 20,
  },
  licenseContainer: {
    marginTop: 10,
  },
  licenseStatus: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
    padding: 12,
    backgroundColor: theme.colors.background,
    borderRadius: 8,
  },
  statusLabel: {
    fontSize: 16,
    color: theme.colors.text,
    fontWeight: '500',
  },
  statusValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  disclaimerCard: {
    marginHorizontal: 20,
    marginBottom: 15,
    backgroundColor: theme.colors.surface,
    borderLeftWidth: 4,
    borderLeftColor: theme.colors.warning,
  },
  disclaimerTitle: {
    fontSize: 18,
    color: theme.colors.primary,
    marginBottom: 10,
  },
  disclaimerText: {
    fontSize: 14,
    color: theme.colors.text,
    lineHeight: 20,
  },
  buttonContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  logoutButton: {
    padding: 8,
  },
});

export default ProfileScreen;