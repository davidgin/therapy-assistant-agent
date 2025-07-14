#!/bin/bash

# Build iOS IPA for Therapy Assistant Mobile App
# This script automates the iOS build process

set -e

echo "🍎 Building iOS app for Therapy Assistant..."

# Check if we're in the mobile directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: This script must be run from the mobile directory"
    exit 1
fi

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: iOS builds require macOS with Xcode"
    exit 1
fi

# Check if Xcode is installed
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Error: Xcode not found. Please install Xcode from the App Store"
    exit 1
fi

# Check if CocoaPods is installed
if ! command -v pod &> /dev/null; then
    echo "❌ Error: CocoaPods not found. Installing..."
    sudo gem install cocoapods
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Install iOS dependencies
if [ -d "ios" ]; then
    echo "📱 Installing iOS pods..."
    cd ios
    pod install
    cd ..
else
    echo "📱 Creating iOS project..."
    npx react-native init --template react-native-template-typescript .
    cd ios
    pod install
    cd ..
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
npx react-native clean-project-auto

# Build for simulator (debug)
echo "🔨 Building for iOS Simulator (Debug)..."
npx react-native run-ios --simulator="iPhone 15"

# Build archive for distribution
echo "🔨 Building iOS Archive..."
cd ios

# Build workspace
xcodebuild clean archive \
    -workspace TherapyAssistant.xcworkspace \
    -scheme TherapyAssistant \
    -archivePath ./build/TherapyAssistant.xcarchive \
    -configuration Release \
    -destination "generic/platform=iOS" \
    CODE_SIGN_IDENTITY="" \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGNING_ALLOWED=NO

# Export IPA (for development/ad-hoc distribution)
echo "📦 Exporting IPA..."
xcodebuild -exportArchive \
    -archivePath ./build/TherapyAssistant.xcarchive \
    -exportPath ./build \
    -exportOptionsPlist ./ExportOptions.plist || true

cd ..

# Show build results
echo "✅ Build completed!"
echo ""
echo "📁 Build artifacts:"
echo "   Archive: ios/build/TherapyAssistant.xcarchive"
echo "   IPA: ios/build/TherapyAssistant.ipa (if export succeeded)"
echo ""
echo "📋 Next steps:"
echo "   1. For testing: Use Xcode to install on device or simulator"
echo "   2. For TestFlight: Upload IPA to App Store Connect"
echo "   3. For App Store: Submit through App Store Connect"
echo ""
echo "💡 To run on simulator:"
echo "   npx react-native run-ios"
echo ""
echo "💡 To run on device:"
echo "   npx react-native run-ios --device"
echo ""
echo "⚠️  Note: For distribution, you'll need:"
echo "   - Apple Developer Account"
echo "   - Valid code signing certificates"
echo "   - Provisioning profiles"