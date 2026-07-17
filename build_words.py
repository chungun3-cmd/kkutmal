#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_words.py — 끝말도발용 words.json 빌더
=============================================
우리말샘/표준국어대사전 공개 XML 덤프에서 '일반어 명사'만 추출해
끝말잇기용 사전(words.json)을 생성하고, 한방단어(이을 단어가 0개인
끝글자를 가진 단어)를 두음법칙 적용 상태로 자동 판별합니다.

사용법
------
# 1) 우리말샘 XML 덤프 폴더 (zip 그대로 둬도 됨)
python build_words.py --xml-dir ./urimalsaem/ --out words.json

# 2) 한 줄당 단어 하나인 텍스트 파일
python build_words.py --list mywords.txt --out words.json

옵션: --min-len 2 --max-len 9 (기본값)

데이터 출처(수동 다운로드 필요, 로그인 요구):
- 우리말샘  https://opendict.korean.go.kr  → 사전 내려받기 (CC BY-SA 2.0 KR)
- 표준국어대사전 https://stdict.korean.go.kr → 사전 내려받기
※ 라이선스: 우리말샘 데이터 사용 시 사이트에 출처 표기 필요
"""
import argparse, json, os, sys, zipfile, io, glob
import xml.etree.ElementTree as ET

# ---------- 한글 유틸 ----------
HANGUL_BASE = 0xAC00
CHO_N, JUNG_N, JONG_N = 19, 21, 28

def is_syllable(ch: str) -> bool:
    return 0xAC00 <= ord(ch) <= 0xD7A3

def decompose(ch: str):
    c = ord(ch) - HANGUL_BASE
    return c // (JUNG_N * JONG_N), (c % (JUNG_N * JONG_N)) // JONG_N, c % JONG_N

def compose(cho: int, jung: int, jong: int) -> str:
    return chr(HANGUL_BASE + cho * JUNG_N * JONG_N + jung * JONG_N + jong)

# 초성 인덱스: ㄴ=2, ㄹ=5, ㅇ=11 / ㅣ·y계 중성 인덱스
CHO_N_IDX, CHO_R_IDX, CHO_O_IDX = 2, 5, 11
IY_JUNG = {2, 3, 6, 7, 12, 17, 20}  # ㅑㅒㅕㅖㅛㅠㅣ

def allowed_starts(ch: str) -> set:
    """두음법칙 적용: 이 글자로 '시작 인정'되는 글자 집합 (JS 로직과 동일)"""
    s = {ch}
    if not is_syllable(ch):
        return s
    cho, jung, jong = decompose(ch)
    if cho == CHO_R_IDX:  # ㄹ → ㄴ, (i/y모음이면) ㅇ
        s.add(compose(CHO_N_IDX, jung, jong))
        if jung in IY_JUNG:
            s.add(compose(CHO_O_IDX, jung, jong))
    if cho == CHO_N_IDX and jung in IY_JUNG:  # ㄴ + i/y모음 → ㅇ
        s.add(compose(CHO_O_IDX, jung, jong))
    return s

# ---------- 단어 정제 ----------
def clean_word(raw: str) -> str | None:
    """우리말샘 표기 기호 제거(^ 붙임, - 접사 표시) 후 순수 한글 단어만 통과"""
    w = raw.strip().replace('^', '').replace('-', '').replace(' ', '')
    if not w or not all(is_syllable(ch) for ch in w):
        return None
    return w

# ---------- XML 파싱 (우리말샘/표준국어대사전 공통 관용 구조) ----------
def iter_items_from_xml(fileobj, stats):
    """<item> 단위 스트리밍 파싱. word / pos / type 태그를 관대하게 수집"""
    try:
        for _, elem in ET.iterparse(fileobj, events=('end',)):
            tag = elem.tag.split('}')[-1]  # 네임스페이스 제거
            if tag != 'item':
                continue
            word_el = None
            poses, types = [], []
            for d in elem.iter():
                dt = d.tag.split('}')[-1]
                if dt == 'word' and word_el is None and d.text:
                    word_el = d.text
                elif dt == 'pos' and d.text:
                    poses.append(d.text.strip())
                elif dt == 'type' and d.text:
                    types.append(d.text.strip())
            if word_el:
                yield word_el, poses, types
            elem.clear()
    except ET.ParseError as e:
        stats['parse_errors'] += 1
        print(f'  [경고] XML 파싱 오류(건너뜀): {e}', file=sys.stderr)

def harvest_xml_dir(xml_dir: str, stats) -> set:
    words = set()
    paths = sorted(
        glob.glob(os.path.join(xml_dir, '**', '*.xml'), recursive=True) +
        glob.glob(os.path.join(xml_dir, '**', '*.zip'), recursive=True)
    )
    if not paths:
        sys.exit(f'[오류] {xml_dir} 에서 .xml/.zip 파일을 찾지 못했습니다.')
    for p in paths:
        print(f'  처리 중: {os.path.basename(p)}')
        if p.endswith('.zip'):
            with zipfile.ZipFile(p) as z:
                for name in z.namelist():
                    if not name.endswith('.xml'):
                        continue
                    with z.open(name) as f:
                        collect(iter_items_from_xml(io.TextIOWrapper(f, encoding='utf-8', errors='replace'), stats), words, stats)
        else:
            with open(p, encoding='utf-8', errors='replace') as f:
                collect(iter_items_from_xml(f, stats), words, stats)
    return words

def collect(items, words: set, stats):
    for raw, poses, types in items:
        stats['seen'] += 1
        # 품사: '명사'만 (의존 명사/대명사/고유 명사 제외)
        if '명사' not in poses:
            stats['skip_pos'] += 1
            continue
        # 어휘 유형: 방언/북한어/옛말 제외 (type 정보가 아예 없으면 통과)
        if types and '일반어' not in types:
            stats['skip_type'] += 1
            continue
        w = clean_word(raw)
        if not w:
            stats['skip_clean'] += 1
            continue
        words.add(w)

def harvest_list(path: str, stats) -> set:
    words = set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            stats['seen'] += 1
            w = clean_word(line)
            if w:
                words.add(w)
            else:
                stats['skip_clean'] += 1
    return words

# ---------- 한방단어 판별 ----------
def compute_killers(words: list) -> list:
    """끝글자(두음 변형 포함)로 시작하는 단어가 0개인 단어 = 한방단어"""
    start_count = {}
    for w in words:
        start_count[w[0]] = start_count.get(w[0], 0) + 1
    killers = []
    for w in words:
        if sum(start_count.get(s, 0) for s in allowed_starts(w[-1])) == 0:
            killers.append(w)
    return killers

# ---------- 메인 ----------
def main():
    ap = argparse.ArgumentParser(description='끝말도발 words.json 빌더')
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--xml-dir', help='우리말샘/표준국어대사전 XML(.xml/.zip) 폴더')
    src.add_argument('--list', help='한 줄당 단어 하나인 텍스트 파일')
    ap.add_argument('--out', default='words.json')
    ap.add_argument('--min-len', type=int, default=2)
    ap.add_argument('--max-len', type=int, default=9)
    args = ap.parse_args()

    stats = {'seen': 0, 'skip_pos': 0, 'skip_type': 0, 'skip_clean': 0, 'parse_errors': 0}
    print('[1/4] 원본 데이터 수집…')
    words = harvest_xml_dir(args.xml_dir, stats) if args.xml_dir else harvest_list(args.list, stats)

    print('[2/4] 길이 필터링…')
    words = sorted(w for w in words if args.min_len <= len(w) <= args.max_len)
    if not words:
        sys.exit('[오류] 조건을 만족하는 단어가 없습니다.')

    print('[3/4] 한방단어 판별(두음법칙 적용)…')
    killers = compute_killers(words)

    print('[4/4] words.json 저장…')
    payload = {
        'v': 1,
        'source': '우리말샘/표준국어대사전 공개 데이터 (CC BY-SA 2.0 KR)' if args.xml_dir else f'list:{os.path.basename(args.list)}',
        'count': len(words),
        'killer_count': len(killers),
        'words': words,
        'killers': killers,
    }
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))
    # 로컬(file://) 테스트용 words.js 동시 생성 — script 태그로 로드됨
    js_out = os.path.splitext(args.out)[0] + '.js'
    with open(js_out, 'w', encoding='utf-8') as f:
        f.write('window.WORDS_DATA=')
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';')

    size_mb = os.path.getsize(args.out) / 1024 / 1024
    print('\n===== 완료 =====')
    print(f'  입력 항목      : {stats["seen"]:,}')
    print(f'  품사 제외      : {stats["skip_pos"]:,} / 유형 제외: {stats["skip_type"]:,} / 정제 제외: {stats["skip_clean"]:,}')
    print(f'  최종 단어 수   : {len(words):,}')
    print(f'  한방단어 수    : {len(killers):,}')
    print(f'  파일 크기      : {size_mb:.2f} MB → Cloudflare 자동 압축 시 약 {size_mb*0.3:.2f} MB 전송')
    print(f'  출력           : {args.out} + {os.path.splitext(args.out)[0]}.js (로컬 테스트용)')

if __name__ == '__main__':
    main()
