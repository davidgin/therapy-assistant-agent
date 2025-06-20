import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.therapyassistant.app',
  appName: 'Therapy Assistant',
  webDir: 'build',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: "#3B82F6",
      showSpinner: true,
      spinnerColor: "#ffffff"
    }
  }
};

export default config;