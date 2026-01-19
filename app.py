import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import altair as alt
import os
import datetime
import gspread
from google.oauth2.service_account import Credentials

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 고급 CSS 스타일링
# -----------------------------------------------------------------------------
st.set_page_config(page_title="C-BTI: 영적 성향 진단", page_icon="⛪", layout="centered")

# [디자인] 구글 폰트 + 고급 CSS 적용
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    h1 { color: #FFFFFF; font-weight: 700; letter-spacing: -1px; margin-bottom: 20px; }
    h3 { color: #E0E0E0; font-weight: 600; }
    
    /* 진행바 */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4B89DC, #8E44AD);
        border-radius: 10px;
    }

    /* 질문 카드 */
    .question-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .question-text {
        font-size: 19px;
        font-weight: 500;
        line-height: 1.5;
        color: #FFFFFF;
    }

    /* 라디오 버튼 카드형 디자인 */
    div.row-widget.stRadio > div { flex-direction: column; gap: 10px; }
    div.row-widget.stRadio > div > label {
        background-color: #2D2D2D;
        padding: 16px 20px;
        border-radius: 12px;
        border: 1px solid #3D3D3D;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div.row-widget.stRadio > div > label:hover {
        background-color: #383838;
        border-color: #FF4B4B;
        transform: translateY(-2px);
    }
    div.row-widget.stRadio > div > label[data-baseweb="radio"] > div {
        font-size: 17px !important; font-weight: 500; color: #FAFAFA;
    }
    
    /* 버튼 */
    button[kind="primary"] {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF914D 100%);
        border: none; color: white; padding: 15px 0 !important;
        border-radius: 12px; font-size: 18px !important; font-weight: bold;
        width: 100%; transition: 0.3s;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);
    }
    button[kind="primary"]:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(255, 75, 75, 0.6);
    }
    button[kind="secondary"] {
        width: 100%; padding: 15px 0 !important;
        border-radius: 12px; border: 1px solid #555;
        background-color: transparent; color: #AAA;
    }
    .result-box {
        background-color: #25262B; padding: 25px;
        border-radius: 15px; border: 1px solid #333; margin-bottom: 20px;
    }
    
    /* 공유 섹션 스타일 */
    .share-container {
        background-color: #2D2D2D;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 스크롤 강제 이동 함수
def scroll_to_top():
    js = f'''
    <script>
        // Step: {st.session_state.step}
        var body = window.parent.document.querySelector(".main");
        var html = window.parent.document.documentElement;
        if (body) body.scrollTop = 0;
        if (html) html.scrollTop = 0;
        window.parent.scrollTo(0, 0);
    </script>
    '''
    components.html(js, height=0)

# -----------------------------------------------------------------------------
# 2. 데이터 및 세션 초기화
# -----------------------------------------------------------------------------

if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {}

# 50문항 데이터
questions_data = [
    # 1. 신학
    {"text": "성경에 기록된 기적(홍해 가름 등)은 과학적으로 설명되지 않아도 문자 그대로의 사실이다.", "part": "Theology", "reverse": True},
    {"text": "진화론은 성경의 창조 섭리를 부정하는 것이므로, 타협 없이 배격해야 한다.", "part": "Theology", "reverse": True},
    {"text": "여성이 목사 안수를 받고 설교하는 것은 성경적 질서에 어긋난다고 생각한다.", "part": "Theology", "reverse": True},
    {"text": "타종교에도 구원의 가능성이 있거나 배울 점이 있다고 인정하는 것은 위험하다.", "part": "Theology", "reverse": True},
    {"text": "동성애는 인권 문제가 아니라 성경이 금지하는 '치유받아야 할 죄'의 문제다.", "part": "Theology", "reverse": True},
    {"text": "설교라도 나의 이성과 상식에 비추어 납득이 가지 않으면 비판적으로 수용해야 한다.", "part": "Theology", "reverse": False},
    {"text": "술/담배는 구원과 무관하지만, 직분자라면 엄격히 금해야 한다.", "part": "Theology", "reverse": True},
    {"text": "'예수 천국, 불신 지옥' 구호는 기독교 진리를 너무 단순화시킨 것이라 거부감이 든다.", "part": "Theology", "reverse": False},
    {"text": "설교 시간에 인문학, 철학, 영화 이야기가 자주 인용되는 것이 자연스럽고 유익하다.", "part": "Theology", "reverse": False},
    {"text": "성경의 어떤 명령들은 당시 문화적 배경 때문이므로 현대에 문자 그대로 적용해선 안 된다.", "part": "Theology", "reverse": False},
    {"text": "사랑보다는 죄에 대한 엄격한 지적과 심판을 강조하는 설교가 더 영적이라고 느낀다.", "part": "Theology", "reverse": True},
    {"text": "교회는 세상 문화가 침투하지 못하도록 거룩하게 구별된 방파제 역할을 해야 한다.", "part": "Theology", "reverse": True},
    {"text": "사랑의 하나님이 믿지 않는다는 이유로 사람을 지옥에 던지신다는 교리에 감정적 어려움을 느낀다.", "part": "Theology", "reverse": False},
    {"text": "정신의학보다 기도가 우울증 해결의 근본 열쇠라고 믿는다.", "part": "Theology", "reverse": True},
    {"text": "사도신경이나 주기도문 형식을 생략하는 것은 예배의 거룩함을 해친다.", "part": "Theology", "reverse": True},
    # 2. 동력
    {"text": "다 같이 '주여!'를 크게 외치고 통성 기도할 때 영적인 시원함을 느낀다.", "part": "Drive", "reverse": False},
    {"text": "방언, 신유 같은 성령의 은사는 오늘날 예배 때도 강력하게 나타나야 한다.", "part": "Drive", "reverse": False},
    {"text": "하나님을 잘 믿으면 자녀 성공, 사업 번창 같은 현실적인 복을 주신다고 믿는다.", "part": "Drive", "reverse": False},
    {"text": "눈물이나 가슴 뜨거운 '정서적 체험'이 없는 예배는 건조하다.", "part": "Drive", "reverse": False},
    {"text": "신앙생활의 본질은 복을 누리는 것보다, 자기를 부인하고 고난을 견디는 훈련이다.", "part": "Drive", "reverse": True},
    {"text": "뜨거운 집회보다 성경을 체계적으로 공부하는 제자훈련이 더 유익하다.", "part": "Drive", "reverse": True},
    {"text": "논리적 가르침보다 투박하더라도 강력한 카리스마와 열정으로 선포해주길 원한다.", "part": "Drive", "reverse": False},
    {"text": "단순하고 반복적인 찬양(CCM)을 부르며 감정에 몰입하는 시간이 길었으면 좋겠다.", "part": "Drive", "reverse": False},
    {"text": "예배 순서가 빈틈없이 진행되는 엄숙하고 질서 있는 분위기가 편안하다.", "part": "Drive", "reverse": True},
    {"text": "설교가 나를 꾸짖기보다 지친 마음을 따뜻하게 위로해주길 바란다.", "part": "Drive", "reverse": False},
    {"text": "친근한 리더십보다 범접하기 어려운 영적 권위가 있는 '선지자' 같은 목사님이 좋다.", "part": "Drive", "reverse": False},
    {"text": "신앙 성장은 뜨거운 열심보다 인격이 성숙해지고 삶이 차분해지는 것이다.", "part": "Drive", "reverse": True},
    {"text": "찬양 중 '다 같이 일어납시다' 할 때 기쁘게 동참한다.", "part": "Drive", "reverse": False},
    {"text": "예화 위주 설교보다 원어의 의미를 풀이해주는 강해 설교를 선호한다.", "part": "Drive", "reverse": True},
    {"text": "소리 내어 부르짖는 것보다 침묵하며 관상 기도하는 것이 더 맞는다.", "part": "Drive", "reverse": True},
    # 3. 사회
    {"text": "강단에서 정치나 사회 이슈 발언은 교회의 본질에서 벗어난 것이다.", "part": "Society", "reverse": True},
    {"text": "최우선 사명은 사회 개혁보다 한 영혼 전도하여 구원받게 하는 것이다.", "part": "Society", "reverse": True},
    {"text": "개인의 회개뿐 아니라 사회의 불의한 구조를 바꾸기 위해 교회가 목소리를 내야 한다.", "part": "Society", "reverse": False},
    {"text": "사회적 현장(집회 등)에 기독교인이 깃발을 들고 참여하는 것은 자연스럽다.", "part": "Society", "reverse": False},
    {"text": "교회 예산 상당 부분은 건물 유지보다 외부 구제와 사회적 약자를 위해 쓰여야 한다.", "part": "Society", "reverse": False},
    {"text": "예수님의 사역은 죄 사함만큼이나 가난하고 억눌린 자 해방에 있었다.", "part": "Society", "reverse": False},
    {"text": "세상과 구별됨은 담을 쌓는 게 아니라 세상 속에서 정의를 실천하는 것이다.", "part": "Society", "reverse": False},
    {"text": "차별금지법 등 사회적 법안에 대해 교회가 적극적으로 입장을 표명해야 한다.", "part": "Society", "reverse": False},
    {"text": "직장에서 성공하여 높은 자리에 오르는 것이 곧 하나님께 영광 돌리는 길이다.", "part": "Society", "reverse": True},
    {"text": "'정교분리'는 교회가 사회적 책임을 회피하는 핑계로 쓰일 때가 많다.", "part": "Society", "reverse": False},
    # 4. 문화
    {"text": "예배 시간에 드럼이나 일렉기타 소리가 크면 경건함이 깨진다고 느낀다.", "part": "Culture", "reverse": True},
    {"text": "목사님이 청바지나 티셔츠를 입고 설교하는 것도 괜찮다.", "part": "Culture", "reverse": False},
    {"text": "사도신경/주기도문을 매주 암송하기보다 상황에 맞춰 생략하거나 찬양으로 대체해도 좋다.", "part": "Culture", "reverse": False},
    {"text": "교회 건물은 십자가, 스테인드글라스 등 종교적 상징과 엄숙함이 있어야 한다.", "part": "Culture", "reverse": True},
    {"text": "교회 안에서 '형제/자매님'보다 '장로/권사님' 직분 호칭이 질서 있어 보인다.", "part": "Culture", "reverse": True},
    {"text": "불신자도 오기 쉬운 '카페 같은 분위기'의 열린 예배를 선호한다.", "part": "Culture", "reverse": False},
    {"text": "온라인 예배도 현장 예배만큼이나 영적인 가치가 있다.", "part": "Culture", "reverse": False},
    {"text": "본당은 거룩한 곳이므로 평일에 공연장 등 다른 용도로 쓰는 건 조심스럽다.", "part": "Culture", "reverse": True},
    {"text": "주일 성수도 부득이한 사정이 있으면 융통성 있게(온라인/타교회) 할 수 있다.", "part": "Culture", "reverse": False},
    {"text": "최신 드라마, 영화, 뉴스 등이 설교 예화로 자주 등장하는 것이 좋다.", "part": "Culture", "reverse": False},
]

OPTIONS = ["매우 그렇다", "조금 그렇다", "조금 아니다", "매우 아니다"]
SCORE_MAP = {"매우 그렇다": 10, "조금 그렇다": 6.7, "조금 아니다": 3.3, "매우 아니다": 0}

AXIS_INFO = {
    "Theology": {"name": "신학 (Theology)", "desc": "성경을 바라보는 관점"},
    "Drive": {"name": "동력 (Drive)", "desc": "신앙생활의 에너지원"},
    "Society": {"name": "사회 (Society)", "desc": "믿음의 방향"},
    "Culture": {"name": "문화 (Culture)", "desc": "예배의 스타일"}
}

AXIS_COMPARISON = {
    "Theology": {"title": "신학 (Theology)", "left": {"code": "T", "name": "Text", "desc": "성경 문자주의\n보수적 신학"}, "right": {"code": "C", "name": "Context", "desc": "시대적 재해석\n유연한 신학"}},
    "Drive": {"title": "동력 (Drive)", "left": {"code": "D", "name": "Discipline", "desc": "제자훈련/공부\n지성적 깨달음"}, "right": {"code": "G", "name": "Grace", "desc": "성령체험/집회\n감성적 뜨거움"}},
    "Society": {"title": "사회 (Society)", "left": {"code": "P", "name": "Private", "desc": "개인의 구원\n내면의 평안"}, "right": {"code": "S", "name": "Social", "desc": "사회의 구원\n구조적 정의"}},
    "Culture": {"title": "문화 (Culture)", "left": {"code": "L", "name": "Liturgy", "desc": "전통적 예배\n엄숙함/경건"}, "right": {"code": "M", "name": "Modern", "desc": "열린 예배\n자유로움/축제"}}
}

CODE_DESC = {
    "T": {"title": "Text (텍스트)", "desc": "성경의 절대적 권위와 문자적 해석"},
    "C": {"title": "Context (컨텍스트)", "desc": "성경의 역사적 맥락과 유연한 해석"},
    "D": {"title": "Discipline (훈련)", "desc": "제자훈련과 지성적 깨달음 중시"},
    "G": {"title": "Grace (은혜)", "desc": "성령 체험과 감성적 뜨거움 중시"},
    "P": {"title": "Private (개인)", "desc": "개인의 구원과 내면의 평안 우선"},
    "S": {"title": "Social (사회)", "desc": "사회 정의와 구조적 변혁 우선"},
    "L": {"title": "Liturgy (예전)", "desc": "전통적이고 엄숙한 예배 예전 선호"},
    "M": {"title": "Modern (현대)", "desc": "자유롭고 현대적인 열린 예배 선호"}
}

TYPE_DETAILS = {
    "TDPL": {"title": "엄격한 신학자형", "person": "장 칼뱅", "quote": "나의 마음을 주님께 드리나이다.", "keywords": ["교리", "경건", "전통", "질서"], "desc": "오직 성경, 오직 믿음!"},
    "TDPM": {"title": "지성적 변증가형", "person": "C.S. 루이스", "quote": "기독교를 믿는 것은 태양이 뜬 것을 믿는 것과 같다.", "keywords": ["이성", "논리", "현대적", "개인신앙"], "desc": "기독교를 논리적으로 변증합니다."},
    "TDSL": {"title": "정의로운 개혁가형", "person": "도산 안창호", "quote": "낙망은 청년의 죽음이다.", "keywords": ["애국", "실력양성", "사회변혁", "정직"], "desc": "믿음은 정직한 삶과 사회적 책임입니다."},
    "TDSM": {"title": "행동하는 순교자형", "person": "디트리히 본회퍼", "quote": "값싼 은혜는 교회의 적이다.", "keywords": ["제자도", "저항", "실천", "책임"], "desc": "불의한 시대에 맞서 신앙의 대가를 지불합니다."},
    "TGPL": {"title": "뜨거운 경건주의자형", "person": "존 웨슬리", "quote": "세계는 나의 교구다.", "keywords": ["성령체험", "개인성화", "규칙", "전통"], "desc": "뜨거운 회심과 성령 체험을 강조합니다."},
    "TGPM": {"title": "열정적 부흥사형", "person": "빌리 그레이엄", "quote": "예수 믿고 구원받으세요.", "keywords": ["전도", "축복", "현대적예배", "대중성"], "desc": "단순하고 강력한 메시지를 선호합니다."},
    "TGSL": {"title": "빈민가의 성자형", "person": "손양원 목사", "quote": "원수를 사랑하라.", "keywords": ["사랑", "용서", "낮은곳", "헌신"], "desc": "상식을 뛰어넘는 사랑을 실천합니다."},
    "TGSM": {"title": "사랑의 실천가형", "person": "마더 테레사", "quote": "위대한 사랑으로 작은 일을 하라.", "keywords": ["헌신", "봉사", "섬김", "순종"], "desc": "가장 낮은 곳에서 묵묵히 섬깁니다."},
    "CDPL": {"title": "고독한 수도사형", "person": "토마스 머튼", "quote": "침묵은 가장 깊은 기도다.", "keywords": ["침묵", "관상", "영성", "열린마음"], "desc": "고요한 침묵과 묵상을 추구합니다."},
    "CDPM": {"title": "문화적 사색가형", "person": "폴 틸리히", "quote": "신앙은 궁극적인 관심이다.", "keywords": ["문화", "철학", "존재", "현대성"], "desc": "성경을 인문학적으로 재해석합니다."},
    "CDSL": {"title": "현실적 예언자형", "person": "라인홀드 니버", "quote": "바꿀 수 있는 용기를 주소서.", "keywords": ["현실주의", "정의", "사회윤리", "책임"], "desc": "냉철한 이성으로 사회 구조를 분석합니다."},
    "CDSM": {"title": "사회적 실천가형", "person": "장기려 박사", "quote": "돈 없어서 치료 못 받는 환자는 없어야 한다.", "keywords": ["인술", "사회복지", "청빈", "지성"], "desc": "자신의 재능을 가난한 이웃을 위해 씁니다."},
    "CGPL": {"title": "자연 속의 신비가형", "person": "성 프란치스코", "quote": "나를 평화의 도구로 써 주소서.", "keywords": ["평화", "생태", "청빈", "신비"], "desc": "자연 만물과 교감하며 신비를 체험합니다."},
    "CGPM": {"title": "따뜻한 치유자형", "person": "헨리 나우웬", "quote": "우리는 상처 입은 치유자다.", "keywords": ["치유자", "심리", "내면", "공감"], "desc": "서로의 상처를 보듬어줍니다."},
    "CGSL": {"title": "저항하는 평화주의자형", "person": "윤동주 시인", "quote": "하늘을 우러러 한 점 부끄럼 없기를.", "keywords": ["문학", "성찰", "저항", "순수"], "desc": "맑은 영혼으로 시대의 아픔에 저항합니다."},
    "CGSM": {"title": "꿈꾸는 혁명가형", "person": "마틴 루터 킹", "quote": "나에게는 꿈이 있습니다.", "keywords": ["자유", "평등", "비폭력", "꿈"], "desc": "차별을 철폐하고 평등한 세상을 만듭니다."}
}

# -----------------------------------------------------------------------------
# 3. 메인 UI 로직
# -----------------------------------------------------------------------------
st.title("⛪ C-BTI: 나에게 맞는 영적 집 찾기")
parts_list = ["Theology", "Drive", "Society", "Culture"]

if st.session_state.step <= 4:
    scroll_to_top()
    current_part_name = parts_list[st.session_state.step - 1]
    
    progress_val = (st.session_state.step - 1) / 4
    st.progress(progress_val)
    st.markdown(f"### Part {st.session_state.step}. {AXIS_INFO[current_part_name]['name']}")
    st.caption(f"{AXIS_INFO[current_part_name]['desc']}") 
    st.markdown("---")

    current_questions = [q for q in questions_data if q["part"] == current_part_name]
    start_num = 1
    for i in range(st.session_state.step - 1):
        prev_part = parts_list[i]
        start_num += len([q for q in questions_data if q["part"] == prev_part])

    for idx, q in enumerate(current_questions):
        q_num = start_num + idx
        q_key = f"{current_part_name}_{idx}"
        
        prev_value = st.session_state.answers.get(q_key, {}).get("choice_label", None)
        try: prev_index = OPTIONS.index(prev_value) if prev_value else None
        except ValueError: prev_index = None

        st.markdown(f"""
        <div class="question-card">
            <div class="question-text">Q{q_num}. {q['text']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        user_choice = st.radio(
            f"Q{q_num} 답변", options=OPTIONS, key=f"radio_{q_key}", 
            horizontal=False, label_visibility="collapsed", index=prev_index
        )
        
        if user_choice:
            st.session_state.answers[q_key] = {
                "score": SCORE_MAP[user_choice], "reverse": q["reverse"], 
                "part": q["part"], "choice_label": user_choice
            }
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    if st.session_state.step > 1:
        if col1.button("⬅️ 이전 단계", type="secondary"):
            st.session_state.step -= 1
            st.rerun()
            
    all_answered = True
    for idx, q in enumerate(current_questions):
        q_key = f"{current_part_name}_{idx}"
        if q_key not in st.session_state.answers:
            all_answered = False
            break
    
    btn_text = "다음 단계 ➡️" if st.session_state.step < 4 else "결과 확인하기 🚀"
    
    if col2.button(btn_text, type="primary"):
        if not all_answered:
            st.error("⚠️ 모든 질문에 답변해 주세요!")
        else:
            st.session_state.step += 1
            st.rerun()

# -----------------------------------------------------------------------------
# 결과 화면
# -----------------------------------------------------------------------------
else:
    scroll_to_top()
    st.balloons()
    
    scores = {"Theology": 0, "Drive": 0, "Society": 0, "Culture": 0}
    counts = {"Theology": 0, "Drive": 0, "Society": 0, "Culture": 0}
    
    for key, value in st.session_state.answers.items():
        final_score = value["score"]
        if value["reverse"]: final_score = 10 - final_score
        scores[value["part"]] += final_score
        counts[value["part"]] += 1
        
    avg_scores = {k: round(v / counts[k], 1) for k, v in scores.items()}
    
    type_code = "T" if avg_scores["Theology"] <= 5 else "C"
    type_code += "D" if avg_scores["Drive"] <= 5 else "G"
    type_code += "P" if avg_scores["Society"] <= 5 else "S"
    type_code += "L" if avg_scores["Culture"] <= 5 else "M"
    
    type_info = TYPE_DETAILS.get(type_code, {"title": "알 수 없음", "person": "-", "quote": "", "keywords": [], "desc": "-"})
    
    # [수정 2] Google Sheets 저장 로직 (200 OK 무시하고 저장 처리)
    if "saved" not in st.session_state:
        try:
            if "gcp_service_account" in st.secrets:
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                credentials = Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"],
                    scopes=scopes
                )
                client = gspread.authorize(credentials)
                sheet = client.open("C-BTI_Result").sheet1 
                
                row = [
                    str(datetime.datetime.now()),
                    type_code,
                    avg_scores["Theology"],
                    avg_scores["Drive"],
                    avg_scores["Society"],
                    avg_scores["Culture"]
                ]
                # gspread 6.0.0 이상에서는 append_row가 Response 객체를 반환할 수 있음
                # 하지만 에러가 안 났다면 성공한 것이므로 무조건 성공 처리
                sheet.append_row(row)
                st.session_state.saved = True
                st.toast("✅ 결과 저장 완료!", icon="💾")
        except Exception as e:
            # 200이라는 숫자가 에러 메시지에 포함되어 있다면, 사실은 성공한 것임
            if "200" in str(e):
                st.session_state.saved = True
                st.toast("✅ 결과 저장 완료!", icon="💾")
            else:
                st.error(f"저장 중 문제 발생: {e}")

    # UI 결과 표시
    st.markdown(f"<div class='result-box'>", unsafe_allow_html=True)
    st.success("🎉 분석이 완료되었습니다!")
    st.title(f"당신의 영적 유형: [{type_code}]")
    st.markdown(f"## **\"{type_info['title']}\"**")
    st.markdown("</div>", unsafe_allow_html=True)
    
    col_img, col_desc = st.columns([1, 1.5])
    
    with col_img:
        image_found = False
        for ext in [".jpg", ".png", ".jpeg"]:
            img_path = f"images/{type_code}{ext}"
            if os.path.exists(img_path):
                st.image(img_path, caption=type_info["person"], use_container_width=True)
                image_found = True
                break
        if not image_found:
            st.info(f"🖼️ {type_info['person']}")

    with col_desc:
        st.info(f"❝ {type_info['quote']} ❞")
        st.markdown(f"**📖 유형 설명**")
        st.write(type_info['desc'])
        st.markdown("### 🔑 핵심 키워드")
        k_cols = st.columns(4)
        for i, kw in enumerate(type_info['keywords']):
            if i < 4: k_cols[i].caption(f"#{kw}")

    st.divider()
    st.subheader("🧩 나의 코드 해설")
    code_cols = st.columns(4)
    for idx, char in enumerate(type_code):
        desc_data = CODE_DESC.get(char, {"title": char, "desc": ""})
        with code_cols[idx]:
            st.error(f"{char} : {desc_data['title']}")
            st.caption(desc_data['desc'])

    st.divider()
    
    with st.expander("📚 8가지 성향 기호(Alphabet) 완전 정복"):
        for axis in ["Theology", "Drive", "Society", "Culture"]:
            data = AXIS_COMPARISON[axis]
            st.markdown(f"#### {data['title']}")
            c1, c2, c3 = st.columns([1, 0.2, 1])
            with c1: st.info(f"**{data['left']['code']} ({data['left']['name']})**\n\n{data['left']['desc']}")
            with c2: st.markdown("<h3 style='text-align: center;'>VS</h3>", unsafe_allow_html=True)
            with c3: st.success(f"**{data['right']['code']} ({data['right']['name']})**\n\n{data['right']['desc']}")
            st.markdown("---")

    st.subheader("📊 신앙 좌표 (Radar Check)")
    df_chart = pd.DataFrame({
        "지표": ["신학(진보)", "동력(체험)", "사회(참여)", "문화(현대)"],
        "점수": [avg_scores["Theology"], avg_scores["Drive"], avg_scores["Society"], avg_scores["Culture"]],
        "색상": ["#4B89DC", "#D9534F", "#5CB85C", "#F0AD4E"]
    })
    c = alt.Chart(df_chart).mark_bar().encode(
        x=alt.X('지표', sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('점수', scale=alt.Scale(domain=[0, 10])),
        color=alt.Color('지표', scale=alt.Scale(range=["#4B89DC", "#D9534F", "#5CB85C", "#F0AD4E"]), legend=None),
        tooltip=['지표', '점수']
    ).properties(height=300)
    st.altair_chart(c, use_container_width=True)
    
    # [NEW] 공유하기 섹션 추가
    st.divider()
    st.subheader("📢 친구에게 결과 공유하기")
    
    app_url = "https://faithcheck.streamlit.app/"
    col_share1, col_share2 = st.columns(2)
    
    with col_share1:
        # 트위터/X 공유 버튼
        twitter_url = f"https://twitter.com/intent/tweet?text=나의 영적 성향은 {type_code}입니다! 당신도 확인해보세요.&url={app_url}"
        st.link_button("🐦 트위터로 공유", twitter_url, type="secondary")
        
    with col_share2:
        # 링크 복사 안내 (Streamlit의 st.code는 기본적으로 우측 상단에 복사 버튼이 있음)
        st.caption("👇 아래 링크를 복사해서 카톡으로 보내세요!")
        st.code(app_url, language="None")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔄 처음부터 다시 하기", type="secondary"):
        st.session_state.step = 1
        st.session_state.answers = {}
        st.rerun()