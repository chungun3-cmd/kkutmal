# 끝말잇기 마스터 (kkutmal)

도발이와 대결하며 **한방단어**를 배우는 학습형 끝말잇기 게임.
🔗 https://kkutmal.dobal-e.com

## 스택
- 정적 HTML/CSS/JS (프레임워크·빌드 없음, 서버 없음)
- 사전: 국립국어원 우리말샘 공개 데이터 (CC BY-SA 2.0 KR) → `words.json`
- 배포: Cloudflare Pages (main 브랜치 push 시 자동 배포)

## 구조
```
index.html          게임 본체 (단일 파일: UI·게임로직·사전로더)
words.json          사전 데이터 ★필수 — 없으면 표본 사전으로 폴백
words.js            로컬(file://) 테스트용 사전 (window.WORDS_DATA)
about/privacy/terms/contact.html   애드센스 승인용 필수 페이지
articles/           SEO 콘텐츠 4편
_headers            words.json 7일 캐시
```

## 게임 규칙 (설계 의도)
- 도발이는 32만 단어를 알지만 **한방단어는 절대 사용하지 않음**
- 플레이어가 한방단어를 내면 **즉시 승리** → 도감에 수집
- 패배 시 **놓친 승리 찬스** 분석으로 학습 유도
- 하트 3 / 힌트 2 / 한방찬스 1, 턴당 15초

## 로컬 테스트
```bash
python -m http.server 8000   # → http://localhost:8000
```
※ file:// 로 직접 열면 fetch가 막혀 `words.js`(있을 경우)로 폴백됩니다.

## 사전 재생성
```bash
python build_words.py --xml-dir ./urimalsaem/ --out words.json
# words.json + words.js 동시 생성
```

## 배포 전 교체 필요 (`[출시설정]` 주석 검색)
| 항목 | 자리표시자 | 위치 |
|---|---|---|
| 카카오 JS 키 | `YOUR_KAKAO_JS_KEY` | index.html |
| 애드센스 게시자 ID | `ca-pub-XXXXXXXXXXXXXXXX` | 전체 HTML |
| 애드센스 슬롯 ID | `data-ad-slot="0000000000"` | 전체 HTML |
| GA4 측정 ID | `G-XXXXXXXXXX` | index.html (2곳) |
| 운영 이메일 | `contact@dobal-e.com` | privacy/terms/contact |

자세한 절차는 `docs/출시가이드.md` 참고.
