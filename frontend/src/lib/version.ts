/**
 * Version management utility for update announcements
 */

export interface UpdateFeature {
  title: string;
  description: string;
  icon?: string;
}

export interface LocalizedUpdateFeature {
  title: Record<string, string>;
  description: Record<string, string>;
  icon?: string;
}

export interface VersionUpdate {
  version: string;
  date: string;
  title: string;
  features: UpdateFeature[];
}

export interface LocalizedVersionUpdate {
  version: string;
  date: string;
  title: Record<string, string>;
  features: LocalizedUpdateFeature[];
}

// Current app version (Semantic Versioning: MAJOR.MINOR.PATCH)
export const CURRENT_VERSION = "1.2.0";

// Localized version history (ko + en)
const VERSION_HISTORY_LOCALIZED: LocalizedVersionUpdate[] = [
  {
    version: "1.2.0",
    date: "2026-01-11",
    title: {
      ko: "성능 최적화 및 사용자 경험 개선",
      en: "Performance optimization and UX improvements",
    },
    features: [
      {
        title: {
          ko: "React Query 통합으로 데이터 로딩 최적화",
          en: "Optimized data loading with React Query",
        },
        description: {
          ko: "더 빠르고 효율적인 데이터 페칭과 캐싱으로 앱 성능이 대폭 향상되었습니다.",
          en: "Faster, more efficient data fetching and caching for significantly improved app performance.",
        },
        icon: "zap",
      },
      {
        title: {
          ko: "스마트 피트니스 데이터 캐싱",
          en: "Smart fitness data caching",
        },
        description: {
          ko: "피트니스 데이터를 지능적으로 캐싱하여 로딩 시간을 단축하고 원활한 사용 경험을 제공합니다.",
          en: "Intelligent fitness data caching for reduced load times and a smoother experience.",
        },
        icon: "hard-drive",
      },
      {
        title: {
          ko: "워크아웃 모듈 자동 정렬 강화",
          en: "Improved workout module auto-ordering",
        },
        description: {
          ko: "Warmup과 Cooldown이 항상 올바른 위치에 배치되어 더욱 안전한 워크아웃을 제공합니다.",
          en: "Warmup and Cooldown always placed correctly for safer workouts.",
        },
        icon: "refresh-cw",
      },
    ],
  },
  {
    version: "1.1.0",
    date: "2026-01-11",
    title: {
      ko: "주간 플랜 및 워크아웃 옵션 업데이트",
      en: "Weekly plan and workout option updates",
    },
    features: [
      {
        title: {
          ko: "주간 워크아웃 플랜 기능 추가",
          en: "Weekly workout plan feature",
        },
        description: {
          ko: "이제 7일 치 워크아웃을 한 번에 생성하고 관리할 수 있습니다. Intervals.icu에 일괄 등록도 가능합니다.",
          en: "Generate and manage 7 days of workouts at once. Bulk register to Intervals.icu.",
        },
        icon: "calendar-days",
      },
      {
        title: {
          ko: "바코드 워크아웃 제외 옵션",
          en: "Exclude barcode-style workouts option",
        },
        description: {
          ko: "워크아웃 생성 시 복잡한 바코드 형식을 제외하고 심플한 워크아웃만 받을 수 있는 옵션이 추가되었습니다.",
          en: "Option to exclude complex barcode-style intervals and receive simpler workouts.",
        },
        icon: "settings",
      },
    ],
  },
];

/**
 * Resolve a localized version history entry to a plain VersionUpdate
 * using the given language code.
 */
function resolveLocale(entry: LocalizedVersionUpdate, lang: string): VersionUpdate {
  return {
    version: entry.version,
    date: entry.date,
    title: entry.title[lang] || entry.title["en"],
    features: entry.features.map((f) => ({
      title: f.title[lang] || f.title["en"],
      description: f.description[lang] || f.description["en"],
      icon: f.icon,
    })),
  };
}

// Version history with update details (resolved at access time)
export function getVersionHistory(lang: string = "en"): VersionUpdate[] {
  return VERSION_HISTORY_LOCALIZED.map((entry) => resolveLocale(entry, lang));
}

// Keep a default export for backward compat (English)
export const VERSION_HISTORY: VersionUpdate[] = getVersionHistory("en");

// LocalStorage key for tracking last seen version
const LAST_SEEN_VERSION_KEY = "lastSeenVersion";

/**
 * Get the last version the user has seen
 */
export function getLastSeenVersion(): string | null {
  try {
    return localStorage.getItem(LAST_SEEN_VERSION_KEY);
  } catch (error) {
    console.error("Failed to read last seen version:", error);
    return null;
  }
}

/**
 * Save the current version as seen by the user
 */
export function markVersionAsSeen(version: string = CURRENT_VERSION): void {
  try {
    localStorage.setItem(LAST_SEEN_VERSION_KEY, version);
  } catch (error) {
    console.error("Failed to save last seen version:", error);
  }
}

/**
 * Compare two semantic versions
 * Returns: 1 if v1 > v2, -1 if v1 < v2, 0 if equal
 */
function compareVersions(v1: string, v2: string): number {
  const parts1 = v1.split(".").map(Number);
  const parts2 = v2.split(".").map(Number);

  for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
    const num1 = parts1[i] || 0;
    const num2 = parts2[i] || 0;

    if (num1 > num2) return 1;
    if (num1 < num2) return -1;
  }

  return 0;
}

/**
 * Check if there's a new version since the last seen version
 */
export function hasNewVersion(): boolean {
  const lastSeen = getLastSeenVersion();

  // First time user - don't show announcement
  if (!lastSeen) {
    markVersionAsSeen();
    return false;
  }

  // Compare versions
  return compareVersions(CURRENT_VERSION, lastSeen) > 0;
}

/**
 * Get the latest update details
 */
export function getLatestUpdate(lang: string = "en"): VersionUpdate | null {
  const history = getVersionHistory(lang);
  return history[0] || null;
}
