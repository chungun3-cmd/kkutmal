★ 이 폴더에 words.json 을 반드시 넣어주세요 ★

build_words.py 로 생성한 words.json(약 1~2MB)을 이 위치(리포 루트)에 두고 commit 하세요.
없으면 배포는 되지만 게임이 "사전 파일 없음 — 표본 사전으로 실행 중" 경고와 함께 실행됩니다.

  python build_words.py --xml-dir ./urimalsaem/ --out words.json

words.js 는 로컬 file:// 테스트용이며, 함께 올려두어도 무방합니다.
