/**
 * Version management utility for update announcements
 */

export interface UpdateFeature {
  title: string;
  description: string;
  icon?: string;
}

export interface VersionUpdate {
  version: string;
  date: string;
  title: string;
  features: UpdateFeature[];
}

// Current app version (Semantic Versioning: MAJOR.MINOR.PATCH)
export const CURRENT_VERSION = "1.2.0";

// Version history with update details
export const VERSION_HISTORY: VersionUpdate[] = [
  {
    version: "1.2.0",
    date: "2026-01-11",
    title: "성능 최적화 및 사용자 경험 개선",
    features: [
      {
        title: "React Query 통합으로 데이터 로딩 최적화",
        description: "더 빠르고 효율적인 데이터 페칭과 캐싱으로 앱 성능이 대폭 향상되었습니다.",
        icon: "⚡",
      },
      {
        title: "스마트 피트니스 데이터 캐싱",
        description: "피트니스 데이터를 지능적으로 캐싱하여 로딩 시간을 단축하고 원활한 사용 경험을 제공합니다.",
        icon: "💾",
      },
      {
        title: "워크아웃 모듈 자동 정렬 강화",
        description: "Warmup과 Cooldown이 항상 올바른 위치에 배치되어 더욱 안전한 워크아웃을 제공합니다.",
        icon: "🔄",
      },
    ],
  },
  {
    version: "1.1.0",
    date: "2026-01-11",
    title: "주간 플랜 및 워크아웃 옵션 업데이트",
    features: [
      {
        title: "주간 워크아웃 플랜 기능 추가",
        description: "이제 7일 치 워크아웃을 한 번에 생성하고 관리할 수 있습니다. Intervals.icu에 일괄 등록도 가능합니다.",
        icon: "📅",
      },
      {
        title: "바코드 워크아웃 제외 옵션",
        description: "워크아웃 생성 시 복잡한 바코드 형식을 제외하고 심플한 워크아웃만 받을 수 있는 옵션이 추가되었습니다.",
        icon: "⚙️",
      },
    ],
  },
];

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
export function getLatestUpdate(): VersionUpdate | null {
  return VERSION_HISTORY[0] || null;
}
