import { useEffect } from "react";
import { hasNewVersion } from "@/lib/version";

/**
 * Custom hook for automatic version checking
 *
 * Usage:
 * ```tsx
 * function App() {
 *   useVersionCheck();
 *   // ... rest of component
 * }
 * ```
 *
 * This hook will automatically check for new versions when the component mounts.
 * Pair this with <UpdateAnnouncementModal /> to show update announcements.
 */
export function useVersionCheck() {
  useEffect(() => {
    // Perform version check on mount
    // The actual modal display is handled by UpdateAnnouncementModal component
    hasNewVersion();
  }, []);
}
