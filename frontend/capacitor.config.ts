import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.aicyclingcoach.app',
  appName: 'AI Cycling Coach',
  webDir: 'dist',
  server: {
    // In production, the app loads from bundled files
    // For development, uncomment below to use live reload:
    // url: 'http://YOUR_DEV_IP:5173',
    // cleartext: true,
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
      backgroundColor: '#2563eb',
    },
  },
  ios: {
    contentInset: 'automatic',
    preferredContentMode: 'mobile',
  },
  android: {
    backgroundColor: '#2563eb',
  },
};

export default config;
