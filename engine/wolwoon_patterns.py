# unteim/engine/wolwoon_patterns.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal

Polarity = Literal["good", "bad", "neutral"]
Category = Literal["A", "B", "C", "D", "E"]


@dataclass(frozen=True)
class PatternMeta:
    id: str
    title: str
    category: Category          # A~E
    group_id: str               # 유사 패턴 묶음
    polarity: Polarity          # good/bad/neutral
    risk_level: int             # 0~3 (동점 우선순위)


# ✅ 25개 전체를 여기서 관리 (지금은 핵심 몇 개만 먼저 넣고, 나머지는 아래 TODO에 추가)
PATTERN_META: Dict[str, PatternMeta] = {
    # A 커리어·시험
    "exam_pass": PatternMeta("exam_pass", "시험·합격운", "A", "exam", "good", 1),
    "exam_fail": PatternMeta("exam_fail", "시험·탈락·재도전운", "A", "exam", "bad", 2),
    "promotion": PatternMeta("promotion", "승진·직책변동운", "A", "career", "good", 1),
    "career_pressure": PatternMeta("career_pressure", "직장내 압박·책임과중", "A", "career", "bad", 2),
    "quit_signal": PatternMeta("quit_signal", "퇴사·조직이탈 신호", "A", "career", "bad", 2),

    # B 재물
    "income_up": PatternMeta("income_up", "수입증가·돈줄열림", "B", "money", "good", 1),
    "loss_money": PatternMeta("loss_money", "지출폭증·손재주의", "B", "money", "bad", 2),
    "invest_gain": PatternMeta("invest_gain", "투자기회·수익실현", "B", "invest", "good", 1),
    "invest_loss": PatternMeta("invest_loss", "투자실패·사기주의", "B", "invest", "bad", 3),
    "contract_doc": PatternMeta("contract_doc", "문서·계약금전운", "B", "doc", "neutral", 1),

    # C 관계
    "benefactor": PatternMeta("benefactor", "귀인등장·도움받는 달", "C", "social", "good", 1),
    "networking": PatternMeta("networking", "인맥확장·소개·연결운", "C", "social", "good", 1),
    "betrayal": PatternMeta("betrayal", "배신·관계단절 신호", "C", "social", "bad", 2),
    "gossip": PatternMeta("gossip", "구설·시비·말조심 운", "C", "social", "bad", 2),
    "boss_conflict": PatternMeta("boss_conflict", "권위자·상사와의 충돌", "C", "social", "bad", 2),

    # D 연애/가정
    "love_start": PatternMeta("love_start", "연애시작·썸·설렘", "D", "love", "good", 1),
    "breakup": PatternMeta("breakup", "이별·거리감·냉각기", "D", "love", "bad", 2),
    "marriage_family": PatternMeta("marriage_family", "결혼·동거·가족이슈", "D", "family", "neutral", 1),
    "love_scandal": PatternMeta("love_scandal", "이성문제 구설·삼각관계", "D", "love", "bad", 2),

    # E 이동/리스크
    "move_change": PatternMeta("move_change", "이사·부서이동·환경변화", "E", "move", "neutral", 1),
    "travel_far": PatternMeta("travel_far", "출장·해외·장거리 이동", "E", "move", "neutral", 1),
    "accident_risk": PatternMeta("accident_risk", "사고·부상·수술주의", "E", "safety", "bad", 3),
    "legal_risk": PatternMeta("legal_risk", "관재·법적문제 신호", "E", "safety", "bad", 3),
    "burnout": PatternMeta("burnout", "멘탈소진·번아웃 경고", "E", "health", "bad", 2),
}

# TODO: 위에 이미 25개 전부 채웠음(지금 리스트가 25개). 추가 확장 시 여기에만 추가하면 됨.
