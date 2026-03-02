# Reddit Post — r/Zwift 런치 포스트

작성일: 2026-03-02
타겟: 훈련 계획 없이 그날 컨디션에 맞는 워크아웃을 빠르게 하고 싶은 캐주얼 라이더
포스팅 서브레딧: **r/Zwift** (1순위) → r/cycling (2순위)

---

## r/Zwift 버전

### 제목

```
Made a thing: stop overthinking which workout to do — it just picks one based on how you feel today
```

### 본문

```
You know the drill. You open Zwift, browse the workout list for 10 minutes,
pick something random, regret it halfway through because your legs are
already dead from yesterday.

I got tired of that, so I built a small tool that connects to your
Intervals.icu data and just... tells you what to do today.

It looks at your recent fatigue (ATL), fitness (CTL), and form score (TSB),
crosses that with whatever HRV/sleep data your wearable logged, and has an
AI pick a workout module that actually fits where you are right now.

Not "build your season plan" energy. Just "I have 45 minutes, what should
I do today" energy.

The output is a .ZWO file you can drop straight into Zwift. Done.

**What it's good for:**
- You ride 3-4x a week and don't want to think too hard about structure
- Some days you feel great, some days you don't — it adjusts
- You use Intervals.icu already (required)

**What it's NOT:**
- Not a coaching replacement
- Won't build you a 6-month plan
- The AI sometimes picks things that feel easy or hard — feedback welcome

It's free to try. Would love to hear if it actually matches how you feel on
a given day — that's the part I'm still tuning.

[링크 삽입]
```

---

## r/cycling 버전

### 제목

```
I made an AI that picks today's workout based on your actual condition — not your training plan
```

### 본문

```
Quick context: I'm not a coach, just a cyclist who kept skipping workouts
because I couldn't figure out if I should push hard or take it easy.

So I built something that reads from Intervals.icu — your fitness score,
fatigue level, form, sleep, HRV if you have it — and uses an AI to pick
a workout that fits today specifically.

The idea is dead simple: you open it, it shows your current state, and
gives you a workout to do. No planning required.

If your form score is good → it'll push you a bit.
If you're cooked → it gives you something light or suggests rest.

Works with Zwift (outputs .ZWO files). Garmin, Wahoo support would need
the ERG equivalent but that's not there yet.

Built with FastAPI + React. Uses Groq/Gemini for the AI part with
Intervals.icu as the data source.

Happy to answer questions — especially curious if the TSB-based
recommendations actually feel right to people in practice.

[링크 삽입]
```

---

## 포스팅 체크리스트

- [ ] 링크를 실제 URL로 교체
- [ ] 피트니스 차트 스크린샷 1장 첨부 (차트가 시각적으로 가장 강력한 증거)
- [ ] 워크아웃 생성 결과 화면 스크린샷 1장 첨부
- [ ] 첫 번째 댓글 미리 준비 (실제 사용 경험 예시)

### 첫 번째 댓글 예시 (본인이 직접 달기)

```
For context — yesterday my TSB was around -8 (decent fatigue from the
weekend), HRV slightly low. It recommended a 45-min Z2 endurance ride.
Felt exactly right. Curious if others get similar results.
```

---

## 타이밍 & 팁

| 항목 | 내용 |
|------|------|
| 최적 포스팅 시간 | 화~목 오전 (US 동부 기준 저녁 8~10시) |
| 피할 표현 | "혁신적", "게임체인저", "AI-powered" (단독으로) |
| 강조할 표현 | "I built", "I got tired of", "feedback welcome" — 개인 프로젝트 톤 유지 |
| 크로스포스팅 | r/Zwift 반응 본 후 r/cycling에 동일 내용 |
