#!/bin/bash

# Build Android APK for Therapy Assistant Mobile App
# This script automates the Android build process

set -e

echo "🤖 Building Android APK for Therapy Assistant..."

# Check if we're in the mobile directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: This script must be run from the mobile directory"
    exit 1
fi

# Check if React Native CLI is installed
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npm/npx not found. Please install Node.js"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
npx react-native clean-project-auto

# Check if Android SDK is configured
if [ -z "$ANDROID_HOME" ]; then
    echo "⚠️  Warning: ANDROID_HOME is not set. Make sure Android SDK is installed and configured."
    echo "   You can install it via Android Studio or command line tools."
fi

# Create Android project if it doesn't exist
if [ ! -d "android" ]; then
    echo "📱 Creating Android project..."
    npx react-native init --template react-native-template-typescript .
fi

# Build debug APK
echo "🔨 Building debug APK..."
cd android
./gradlew assembleDebug

# Build release APK (unsigned)
echo "🔨 Building release APK..."
./gradlew assembleRelease

cd ..

# Show build results
echo "✅ Build completed!"
echo ""
echo "📁 APK files generated:"
echo "   Debug APK: android/app/build/outputs/apk/debug/app-debug.apk"
echo "   Release APK: android/app/build/outputs/apk/release/app-release.apk"
echo ""
echo "📋 Next steps:"
echo "   1. For testing: Install debug APK on your device"
echo "   2. For distribution: Sign the release APK with your keystore"
echo "   3. For Play Store: Generate an AAB (Android App Bundle)"
echo ""
echo "💡 To generate AAB for Play Store:"
echo "   cd android && ./gradlew bundleRelease"
echo ""
echo "🚀 To install on connected device:"
echo "   npx react-native run-android"