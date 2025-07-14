# Therapy Assistant Mobile App

A React Native mobile application for the Therapy Assistant platform, providing AI-powered diagnostic and treatment planning tools with advanced voice analysis capabilities for licensed mental health professionals.

## Features

- **🤖 AI Diagnostic Assistant**: Symptom analysis and differential diagnosis
- **🎤 Voice Analysis**: Advanced speech pattern, tone, and emotion detection
- **💊 Treatment Planning**: Evidence-based treatment recommendations
- **📋 Clinical Cases**: Synthetic cases for training and education
- **👤 User Profile**: Account management and professional licensing
- **🔐 Secure Authentication**: Token-based authentication with the backend

## Voice Analysis Capabilities

### Audio Processing
- **Real-time Speech Recognition**: Convert patient speech to text
- **Tone Analysis**: Detect calm, anxious, depressed, agitated, or neutral tones
- **Emotion Detection**: Identify emotional states (happy, sad, angry, anxious, etc.)
- **Sentiment Analysis**: Determine positive, negative, or neutral sentiment
- **Speech Metrics**: Calculate speech rate (WPM) and pause frequency
- **Confidence Scoring**: Provide reliability metrics for analysis

### Clinical Applications
- **Enhanced Diagnostics**: Supplement traditional assessment with voice biomarkers
- **Treatment Monitoring**: Track emotional state changes over time
- **Risk Assessment**: Identify potential indicators of mental health crises
- **Objective Measurement**: Quantify subjective clinical observations

## Architecture

- **React Native 0.72.6**: Cross-platform mobile framework
- **TypeScript**: Type-safe development
- **React Navigation**: Navigation and routing
- **React Native Paper**: Material Design components
- **Voice Recognition**: `@react-native-voice/voice` for speech-to-text
- **Audio Recording**: `react-native-audio-recorder-player` for high-quality recording
- **Async Storage**: Local data persistence
- **Axios**: HTTP client for API communication

## Setup

### Prerequisites

- Node.js 16+ and npm
- React Native CLI
- Android Studio (for Android builds)
- Xcode (for iOS builds, macOS only)

### Installation

1. Navigate to the mobile directory:
   ```bash
   cd mobile
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. For iOS (macOS only):
   ```bash
   cd ios && pod install && cd ..
   ```

4. Configure API endpoint in `src/services/api.ts`:
   ```typescript
   const API_BASE_URL = 'http://your-server:8000';
   ```

### Permissions Setup

#### Android
Add to `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
```

#### iOS
Add to `ios/TherapyAssistant/Info.plist`:
```xml
<key>NSMicrophoneUsageDescription</key>
<string>This app needs access to microphone for voice analysis</string>
<key>NSSpeechRecognitionUsageDescription</key>
<string>This app needs access to speech recognition for patient assessment</string>
```

## Development

### Start Metro bundler:
```bash
npm start
```

### Run on Android:
```bash
npm run android
```

### Run on iOS:
```bash
npm run ios
```

### Development tools:
```bash
npm run lint      # ESLint
npm test         # Jest tests
npm run clean    # Clean cache
```

## Voice Analysis Integration

### Mobile App Usage

1. **Start Recording**: Tap the microphone button to begin recording
2. **Stop Recording**: Tap the stop button to end recording
3. **Processing**: Audio is automatically processed for transcription and analysis
4. **Results**: View tone, emotion, sentiment, and speech metrics
5. **Integration**: Transcribed text and analysis are automatically included in diagnostic requests

### API Integration

The mobile app communicates with the backend through these endpoints:

- `POST /voice/transcribe`: Convert audio to text
- `POST /voice/analyze`: Comprehensive voice analysis
- `GET /voice/health`: Service health check

### Voice Analysis Data

```typescript
interface VoiceAnalysis {
  transcription: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  emotion: string;
  tone: 'calm' | 'anxious' | 'depressed' | 'agitated' | 'neutral';
  speechRate: number;      // Words per minute
  pauseFrequency: number;  // Pauses per minute
  confidence: number;      // Analysis confidence (0-1)
}
```

## Building

### Android APK/AAB

Use the provided build script:
```bash
./build-android.sh
```

Or manually:
```bash
# Debug APK
cd android && ./gradlew assembleDebug

# Release APK
cd android && ./gradlew assembleRelease

# Release AAB (for Play Store)
cd android && ./gradlew bundleRelease
```

### iOS IPA

Use the provided build script:
```bash
./build-ios.sh
```

Or manually:
```bash
# For simulator
npx react-native run-ios

# For device
npx react-native run-ios --device

# Archive for distribution
cd ios && xcodebuild archive -workspace TherapyAssistant.xcworkspace -scheme TherapyAssistant
```

## Project Structure

```
mobile/
├── src/
│   ├── components/         # Reusable UI components
│   │   └── VoiceRecorder.tsx  # Voice recording component
│   ├── screens/           # Screen components
│   │   ├── DiagnosticScreen.tsx  # Enhanced with voice analysis
│   │   └── ...
│   ├── services/          # API services
│   │   ├── api.ts         # API client with voice endpoints
│   │   └── voiceService.ts    # Voice recording and analysis
│   ├── navigation/        # Navigation configuration
│   ├── contexts/          # React contexts
│   ├── types/             # TypeScript types
│   ├── theme/             # Theme configuration
│   └── utils/             # Utility functions
├── android/               # Android platform code
├── ios/                   # iOS platform code
├── build-android.sh       # Android build script
├── build-ios.sh          # iOS build script
└── package.json          # Dependencies and scripts
```

## API Integration

The app connects to the FastAPI backend server for:

- **Authentication**: `/auth/login`, `/auth/me`
- **Diagnostics**: `/diagnostic`
- **Treatment**: `/treatment`
- **Clinical Cases**: `/cases`
- **Voice Analysis**: `/voice/transcribe`, `/voice/analyze`

Authentication is handled via JWT tokens stored in AsyncStorage.

## Voice Analysis Technical Details

### Audio Processing Pipeline

1. **Recording**: High-quality audio capture using device microphone
2. **Encoding**: Audio encoded to base64 for transmission
3. **Transcription**: Speech-to-text using Google Speech Recognition
4. **Feature Extraction**: Librosa-based audio feature analysis
5. **Classification**: Machine learning models for tone/emotion detection
6. **Integration**: Results combined with diagnostic assessment

### Audio Features Analyzed

- **Pitch Analysis**: Fundamental frequency and variance
- **Energy Analysis**: RMS energy and intensity patterns
- **Spectral Features**: Spectral centroid and bandwidth
- **Temporal Features**: Speech rate, pause patterns, rhythm
- **Voice Quality**: Zero-crossing rate and formant analysis

### Clinical Validation

Voice analysis is designed to supplement, not replace, clinical judgment:

- **Evidence-Based**: Features selected based on clinical research
- **Professional Use**: Requires licensed mental health practitioner
- **Confidentiality**: All audio data processed securely
- **Informed Consent**: Patient consent required for recording

## Configuration

### Environment Variables

Update `src/services/api.ts` with your server configuration:

```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### Theme Customization

Modify colors and styling in `src/theme/theme.ts`:

```typescript
export const theme = {
  colors: {
    primary: '#3b82f6',
    accent: '#10b981',
    // ... other colors
  },
};
```

## Security

- JWT tokens are stored securely in AsyncStorage
- API requests include authentication headers
- Audio data is encrypted during transmission
- No sensitive data is logged in production
- Professional licensing verification required
- Patient consent mechanisms built-in

## Distribution

### Android (Google Play Store)

1. Generate signed AAB:
   ```bash
   ./build-android.sh
   ```

2. Upload to Google Play Console
3. Complete store listing and compliance

### iOS (App Store)

1. Build archive:
   ```bash
   ./build-ios.sh
   ```

2. Upload to App Store Connect
3. Submit for review

## Professional Use

This application is designed for licensed mental health professionals only. It provides clinical support tools and should not be used as a substitute for professional clinical judgment.

### Clinical Guidelines

- **Informed Consent**: Always obtain patient consent before recording
- **Data Security**: Ensure secure handling of audio recordings
- **Professional Supervision**: Use under appropriate clinical supervision
- **Evidence-Based Practice**: Combine with traditional assessment methods
- **Ethical Standards**: Follow all applicable professional ethics codes

## Support

For issues and support, please refer to the main project documentation or contact the development team.

## License

This project is licensed under the terms specified in the main project license.

---

**Note**: Voice analysis capabilities are provided as clinical decision support tools and should be used in conjunction with professional clinical judgment and appropriate training.