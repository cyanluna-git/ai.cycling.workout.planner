# App Store / Play Store 개발자 계정 등록 가이드

> **Created**: 2026-02-15 (Sat) 17:00 KST

AI Cycling Coach 앱을 App Store / Play Store에 배포하기 위한 개발자 계정 등록 가이드

---

## 1. Apple Developer Program (iOS App Store)

### 기본 정보
- **비용**: $99 USD/년 (약 13만원, 자동갱신)
- **URL**: https://developer.apple.com/programs/enroll/
- **필요**: Apple ID + 2단계 인증 활성화
- **승인 기간**: 최대 48시간

### 등록 절차

1. **Apple ID 준비**
   - 이미 있으면 그대로 사용
   - 없으면 https://appleid.apple.com 에서 생성

2. **2단계 인증 활성화**
   - iPhone: 설정 > Apple ID > 로그인 및 보안 > 2단계 인증
   - 이미 활성화된 경우 스킵

3. **Apple Developer 사이트 접속**
   - https://developer.apple.com/programs/enroll 접속
   - "Start Your Enrollment" 클릭

4. **계정 유형 선택**
   - **Individual (개인)** ← 추천
     - 본인 이름이 앱 개발자명으로 표시됨
     - 등록이 간단하고 빠름
   - **Organization (조직)**
     - 회사명으로 표시 가능
     - D-U-N-S 번호 필요 (발급 2-3주 소요)

5. **개인정보 입력**
   - 이름, 주소, 전화번호 (영문으로)
   - 여권에 있는 영문 이름과 일치해야 함

6. **결제**
   - $99 USD 연간 구독
   - 신용카드 결제

7. **승인 대기**
   - 보통 24-48시간 내 완료
   - 이메일로 승인 알림

### 등록 후 할 일

1. **App Store Connect** 접속: https://appstoreconnect.apple.com
2. "나의 앱" > "새 앱" 등록
   - 앱 이름: `AI Cycling Coach`
   - 번들 ID: `com.aicyclingcoach.app`
   - SKU: `ai-cycling-coach`
3. Xcode에서 Signing & Capabilities 설정
   - Team 선택 (등록한 Apple Developer 계정)
   - Automatic Signing 활성화
4. TestFlight으로 테스트 → 심사 제출

> ⚠️ 참고: 개인 계정으로 등록하면 App Store에 본인 실명이 개발자명으로 표시됩니다.

---

## 2. Google Play Developer (Android Play Store)

### 기본 정보
- **비용**: $25 USD 일회성 (약 3.3만원)
- **URL**: https://play.google.com/console/signup
- **필요**: Google 계정
- **승인 기간**: 계정 승인 최대 2일, 앱 심사 3-7일

### 등록 절차

1. **Google Play Console 접속**
   - https://play.google.com/console/signup
   - Google 계정으로 로그인

2. **계정 유형 선택**
   - **Personal (개인)** ← 추천
   - Organization (조직) - 사업자 등록증 필요

3. **개인정보 입력**
   - 이름, 이메일, 전화번호, 주소
   - 연락처 이메일은 공개됨 (Play Store에 표시)

4. **본인 인증 (필수)**
   - 신분증 사진 업로드 (여권 또는 주민등록증)
   - 2023년부터 모든 신규 개발자에게 요구됨

5. **결제**
   - $25 USD 일회성 등록비
   - 신용카드 결제

6. **계정 승인 대기**
   - 보통 1-2일 소요

### 등록 후 할 일

1. Google Play Console에서 **앱 만들기**
2. 앱 정보 입력
   - 앱 이름: `AI Cycling Coach`
   - 기본 언어: 한국어
   - 설명, 스크린샷, 아이콘 등록
3. **콘텐츠 등급 설문** 완료
4. **타겟 연령 설정** (전체 연령)
5. **개인정보처리방침 URL** 설정 (필수)
6. Android Studio에서 서명된 AAB 빌드 업로드
7. 심사 제출 (첫 심사 3-7일)

> ⚠️ 참고: 2023년부터 신규 개내 계정은 최초 20명의 테스터로 2주간 평가판 테스트 후에만 공개 배포 가능합니다.

---

## 3. 공통 준비물

두 스토어 모두 제출 시 필요한 것들:

| 항목 | iOS | Android |
|------|-----|--------|
| 앱 아이콘 | 1024x1024 PNG | 512x512 PNG |
| 스크린샷 | 6.7" + 5.5" | 폰 + 태블릿 |
| 앱 설명 | 4000자 이내 | 4000자 이내 |
| 짧은 설명 | 170자 이내 | 80자 이내 |
| 개인정보처리방침 | 필수 (URL) | 필수 (URL) |
| 빌드 도구 | Xcode (Mac 전용) | Android Studio |

### MacBook에 설치해야 할 것

```bash
# 1. Xcode (최신 버전)
# App Store에서 설치 (약 12GB)

# 2. Xcode Command Line Tools
xcode-select --install

# 3. CocoaPods (iOS 의존성 관리)
sudo gem install cocoapods

# 4. Android Studio
# https://developer.android.com/studio 에서 다운로드

# 5. Node.js + pnpm (이미 설치되어 있다면 스킵)
```

### 빌드 및 배포 명령어

```bash
# 프로젝트 루트에서
cd frontend

# 1. 웹 빌드
pnpm build

# 2. Capacitor 동기화
npx cap sync

# 3. iOS
npx cap open ios     # Xcode 열기 → 시뮬레이터 테스트 → Archive → App Store 업로드

# 4. Android
npx cap open android  # Android Studio 열기 → 에뮬레이터 테스트 → Signed AAB 빌드
```

---

## 4. 현재 프로젝트 상태

- [x] Capacitor 설정 완료 (`com.aicyclingcoach.app`)
- [x] iOS 프로젝트 생성 (`frontend/ios/`)
- [x] Android 프로젝트 생성 (`frontend/android/`)
- [x] PWA 동시 운영 (Vercel 배포)
- [x] 앱 아이콘 디자인 완료 (`frontend/public/icon.svg`)
- [ ] Apple Developer 계정 등록
- [ ] Google Play Developer 계정 등록
- [ ] 개인정보처리방침 페이지 생성
- [ ] 스크린샷 준비
- [ ] MacBook 개발환경 세팅
- [ ] TestFlight / 내부 테스트 배포
- [ ] 스토어 심사 제출

> 🎯 팀: Apple을 먼저 등록하세요. 심사가 더 엄격하고 시간이 걸리므로 먼저 시작하는 것이 효율적입니다.
