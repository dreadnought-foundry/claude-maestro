# App Store Setup Guide

Complete guide for setting up Apple Developer, Google Play Console, EAS Build, and Sentry for CorrData Field mobile app deployment.

## Overview

| Account | Purpose | Cost | Time |
|---------|---------|------|------|
| Apple Developer Program | iOS TestFlight + App Store | $99/year | 24-48h enrollment |
| Google Play Console | Android Internal Testing + Play Store | $25 one-time | Same day |
| Expo Account | EAS Build & Submit | Free | Immediate |
| Sentry | Crash reporting | Free tier | Immediate |

---

## Step 1: Apple Developer Program

### 1.1 Enroll in Apple Developer Program

1. Go to [developer.apple.com/programs/enroll](https://developer.apple.com/programs/enroll/)
2. Sign in with your Apple ID (or create one)
3. Choose **Individual** or **Organization**:
   - **Individual**: Personal use, your name on the store
   - **Organization**: Company name on store, requires D-U-N-S number
4. Pay $99/year
5. Wait for approval (24-48 hours for individuals, longer for organizations)

### 1.2 Create App ID (after enrollment approved)

1. Go to [Certificates, Identifiers & Profiles](https://developer.apple.com/account/resources/identifiers/list)
2. Click **+** to add new identifier
3. Select **App IDs** → **App**
4. Fill in:
   - **Description**: CorrData Field
   - **Bundle ID**: Explicit → `com.corrdata.field`
5. Enable capabilities:
   - [x] Push Notifications (if using)
   - [x] Access WiFi Information (for network detection)
6. Click **Continue** → **Register**

### 1.3 Create App in App Store Connect

1. Go to [appstoreconnect.apple.com](https://appstoreconnect.apple.com/)
2. Click **My Apps** → **+** → **New App**
3. Fill in:
   - **Platforms**: iOS
   - **Name**: CorrData Field
   - **Primary Language**: English (U.S.)
   - **Bundle ID**: Select `com.corrdata.field`
   - **SKU**: `corrdata-field-ios`
   - **User Access**: Full Access (or Limited)
4. Click **Create**

**Note**: You don't need to fill out the full store listing yet. This just creates the app entry for TestFlight.

### 1.4 Add Internal Testers (TestFlight)

1. In App Store Connect, go to your app
2. Click **TestFlight** tab
3. Click **Internal Testing** → **+**
4. Create a group (e.g., "CorrData Team")
5. Add testers by email (they must have Apple IDs)

---

## Step 2: Google Play Console

### 2.1 Create Google Play Console Account

1. Go to [play.google.com/console](https://play.google.com/console/)
2. Sign in with your Google account
3. Accept the Developer Agreement
4. Pay $25 one-time registration fee
5. Complete account details

### 2.2 Create App in Play Console

1. Click **Create app**
2. Fill in:
   - **App name**: CorrData Field
   - **Default language**: English (United States)
   - **App or game**: App
   - **Free or paid**: Free
3. Accept declarations
4. Click **Create app**

### 2.3 Set Up Internal Testing Track

1. Go to **Testing** → **Internal testing**
2. Click **Create new release**
3. Click **Testers** tab → **Create email list**
4. Name it "CorrData Team"
5. Add tester email addresses

### 2.4 Generate Upload Key (for EAS)

Option A: Let EAS manage keys (recommended for starting):
- EAS will generate and manage signing keys automatically
- Keys stored securely in Expo's infrastructure

Option B: Use your own keystore:
```bash
# Generate a new keystore
keytool -genkeypair -v -storetype PKCS12 -keystore corrdata-upload.keystore -alias corrdata-field -keyalg RSA -keysize 2048 -validity 10000

# Store securely - you'll need this for eas.json
```

---

## Step 3: Expo / EAS Setup

### 3.1 Create Expo Account

1. Go to [expo.dev/signup](https://expo.dev/signup)
2. Create account with email or GitHub
3. Verify email

### 3.2 Install EAS CLI

```bash
npm install -g eas-cli
```

### 3.3 Login to EAS

```bash
cd packages/mobile-app
npm run eas:login
# Or: eas login
```

Enter your Expo credentials.

### 3.4 Initialize EAS Project

```bash
npm run eas:init
# Or: eas init
```

This will:
- Create/link an Expo project
- Generate a project ID
- Output the ID to add to `app.json`

**Update `app.json`** with the project ID:
```json
{
  "expo": {
    "extra": {
      "eas": {
        "projectId": "YOUR_PROJECT_ID_HERE"
      }
    }
  }
}
```

### 3.5 Configure Credentials

```bash
npm run eas:credentials
# Or: eas credentials
```

This interactive wizard will:
- Ask for Apple Developer credentials
- Create/download iOS provisioning profiles
- Create/manage Android keystores

**For iOS**, you'll need:
- Apple ID (email)
- Apple ID password or app-specific password
- Team ID (found in Apple Developer portal)

**For Android**, choose:
- "Let EAS manage" for new projects
- "Use existing keystore" if you have one

---

## Step 4: Sentry Setup

### 4.1 Create Sentry Account

1. Go to [sentry.io/signup](https://sentry.io/signup/)
2. Sign up with email or GitHub
3. Choose **Developer** plan (free, 5k errors/month)

### 4.2 Create Sentry Project

1. Click **Create Project**
2. Choose platform: **React Native**
3. Name it: `corrdata-field`
4. Click **Create Project**

### 4.3 Get Your DSN

1. Go to **Settings** → **Projects** → **corrdata-field**
2. Click **Client Keys (DSN)**
3. Copy the DSN (looks like `https://abc123@sentry.io/12345`)

### 4.4 Configure in Mobile App

Create a `.env` file in `packages/mobile-app/`:
```bash
EXPO_PUBLIC_SENTRY_DSN=https://your-dsn-here@sentry.io/12345
EXPO_PUBLIC_SENTRY_ENVIRONMENT=production
```

Or set in EAS environment variables:
```bash
eas secret:create --name EXPO_PUBLIC_SENTRY_DSN --value "https://your-dsn@sentry.io/12345" --scope project
```

---

## Step 5: Update Configuration Files

### 5.1 Update `app.json`

Replace placeholders:
```json
{
  "expo": {
    "extra": {
      "eas": {
        "projectId": "YOUR_EAS_PROJECT_ID"  // From eas init
      }
    }
  }
}
```

### 5.2 Update `eas.json`

Replace Apple/Google placeholders (if using manual submission):
```json
{
  "submit": {
    "production": {
      "ios": {
        "appleId": "your-apple-id@email.com",
        "ascAppId": "1234567890"  // From App Store Connect
      },
      "android": {
        "serviceAccountKeyPath": "./google-service-account.json"
      }
    }
  }
}
```

**Note**: The `ascAppId` is the App Store Connect App ID (numeric), found in App Store Connect → App Information → Apple ID.

### 5.3 Set Production API URL

The `eas.json` already has the production URLs configured:
```json
{
  "build": {
    "preview": {
      "env": {
        "EXPO_PUBLIC_API_URL": "https://api.corrdata.com/api/v1/mobile",
        "EXPO_PUBLIC_GRAPHQL_URL": "https://api.corrdata.com/graphql"
      }
    }
  }
}
```

---

## Step 6: Build and Submit

### 6.1 Build iOS for TestFlight

```bash
cd packages/mobile-app
npm run build:preview:ios
# Or: eas build --platform ios --profile preview
```

This will:
- Build the iOS app in the cloud
- Sign it with your Apple credentials
- Return a link to download the .ipa

**First build takes ~15-20 minutes.**

### 6.2 Submit to TestFlight

```bash
npm run submit:ios
# Or: eas submit --platform ios
```

Select the build to submit. It will:
- Upload to App Store Connect
- Process (5-10 minutes)
- Appear in TestFlight → Internal Testing

### 6.3 Build Android for Internal Testing

```bash
npm run build:preview:android
# Or: eas build --platform android --profile preview
```

This creates an APK for direct install or AAB for Play Store.

### 6.4 Submit to Internal Testing

```bash
npm run submit:android
# Or: eas submit --platform android
```

First time may require Google Play Console setup for automated submissions.

---

## Step 7: Test Installation

### iOS (TestFlight)

1. Testers receive email invitation
2. Install TestFlight app from App Store
3. Accept invitation in TestFlight
4. Install CorrData Field
5. Open and verify login works

### Android (Internal Testing)

1. Testers receive email with opt-in link
2. Click link to join testing program
3. Install from Play Store (Internal Testing)
4. Open and verify login works

---

## Troubleshooting

### Apple Issues

| Issue | Solution |
|-------|----------|
| "No suitable application records found" | Create app in App Store Connect first |
| "Invalid provisioning profile" | Run `eas credentials` to regenerate |
| Build stuck in processing | Wait 24h, then contact Apple support |
| Testers not receiving invite | They must have Apple ID, check spam |

### Google Issues

| Issue | Solution |
|-------|----------|
| "App not found" | Ensure app created in Play Console |
| "You need to add a tester" | Add email to Internal Testing track |
| Upload failed | Check keystore configuration |

### EAS Issues

| Issue | Solution |
|-------|----------|
| "Not logged in" | Run `eas login` |
| "Project not found" | Run `eas init` |
| Build failed | Check build logs in Expo dashboard |

---

## Quick Reference Commands

```bash
# Navigate to mobile app
cd packages/mobile-app

# Login to EAS
npm run eas:login

# Initialize project
npm run eas:init

# Configure credentials (interactive)
npm run eas:credentials

# Build iOS preview
npm run build:preview:ios

# Build Android preview
npm run build:preview:android

# Submit to TestFlight
npm run submit:ios

# Submit to Play Internal Testing
npm run submit:android

# Build both platforms
npm run build:preview:all
```

---

## Cost Summary

| Item | Cost | Frequency |
|------|------|-----------|
| Apple Developer Program | $99 | Annual |
| Google Play Console | $25 | One-time |
| Expo / EAS | $0 | Free tier (30 builds/month) |
| Sentry | $0 | Free tier (5k errors/month) |
| **Total First Year** | **$124** | |
| **Annual Renewal** | **$99** | Apple only |

---

## Checklist

Use this checklist to track your progress:

- [ ] Apple Developer Program enrolled ($99)
- [ ] Apple App ID created (com.corrdata.field)
- [ ] App Store Connect app created
- [ ] TestFlight internal testers added
- [ ] Google Play Console account created ($25)
- [ ] Play Console app created
- [ ] Internal Testing track configured
- [ ] Expo account created
- [ ] EAS CLI installed
- [ ] EAS login completed
- [ ] EAS project initialized
- [ ] EAS credentials configured
- [ ] Sentry account created
- [ ] Sentry project created
- [ ] Sentry DSN added to env
- [ ] app.json projectId updated
- [ ] First iOS build completed
- [ ] First iOS submit to TestFlight
- [ ] First Android build completed
- [ ] First Android submit to Internal Testing
- [ ] Test installation verified on iOS
- [ ] Test installation verified on Android
