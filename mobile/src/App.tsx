import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {Provider as PaperProvider} from 'react-native-paper';
import Toast from 'react-native-toast-message';
import {AuthProvider} from './contexts/AuthContext';
import {AppNavigator} from './navigation/AppNavigator';
import {theme} from './theme/theme';

const App: React.FC = () => {
  return (
    <PaperProvider theme={theme}>
      <AuthProvider>
        <NavigationContainer>
          <AppNavigator />
        </NavigationContainer>
        <Toast />
      </AuthProvider>
    </PaperProvider>
  );
};

export default App;