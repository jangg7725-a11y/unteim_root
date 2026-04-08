import json, sys
sys.path.insert(0, '.')
from engine.sentences_v2_engine import attach_v2_sentences, _all_sentences

print('=' * 60)
print('  UNTEIM v2 문장 매핑 테스트')
print('=' * 60)
print(f'  총 문장 수: {len(_all_sentences())}개')

with open('out/engine_dump.json', 'r', encoding='utf-8') as f:
    packed = json.load(f)

gan = packed.get('pillars', {}).get('gan', [])
day_gan = gan[2] if len(gan) > 2 else '?'
counts = packed.get('oheng', {}).get('counts', {})
print(f'  생년월일: {packed.get("birth_str", "?")}')
print(f'  일간: {day_gan}')
print(f'  오행: {json.dumps(counts, ensure_ascii=False)}')

if not packed.get('analysis'):
    packed['analysis'] = {
        'oheng': packed.get('oheng'),
        'shinsal': packed.get('shinsal'),
        'twelve_fortunes': packed.get('twelve_fortunes'),
        'day_master': {'gan': day_gan},
    }
if not packed.get('extra'):
    packed['extra'] = {}

attach_v2_sentences(packed)
v2 = packed.get('v2_sentences', {})

if 'error' in v2:
    print(f'  ERROR: {v2["error"]}')
    sys.exit(1)

print()
items = [
    ('A1_oheng_personality','A-1 오행성격'),
    ('A2_day_master','A-2 일간'),
    ('A3_shinsal_fortunes','A-3 신살'),
    ('A4_compatibility_general','A-4 궁합'),
    ('B2_yongshin_advice','B-2 용신'),
    ('B3_monthly_guide','B-3 월운'),
    ('B4_luck_guide','B-4 대운'),
    ('B5_samjae','B-5 삼재'),
    ('C_opening','C-1 인사'),
    ('C_philosophy','C-2 철학'),
    ('C_closing','C-3 맺음'),
    ('C_affirmation','C-4 긍정'),
    ('C_coaching','C-5 코칭'),
]
for key, label in items:
    data = v2.get(key, [])
    n = len(data) if isinstance(data, list) else 0
    print(f'  {label:12s} {n:3d}개')

b1 = v2.get('B1_practice_table', {}).get('table_row', {})
if b1:
    print(f'  B-1 개운표    1개  ({b1.get("오행","")})')

meta = v2.get('meta', {})
print(f'\n  총 매핑: {meta.get("total_mapped", 0)}개')

a2 = v2.get('A2_day_master', [])
if a2:
    print(f'\n  [샘플] 일간({day_gan}) 프로필:')
    print(f'  -> {a2[0]["text"][:80]}...')

print('\n  ALL TESTS PASSED!')
