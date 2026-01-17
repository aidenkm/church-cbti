import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import altair as alt
import os

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 모바일 최적화 CSS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="C-BTI: 교회 성향 진단", page_icon="⛪", layout="centered")

st.markdown("""
<style>
    /* 라디오 버튼 카드형 디자인 (모바일 터치 최적화) */
    div.row-widget.stRadio > div {
        flex-direction: column;
        gap: 12px;
    }
    div.row-widget.stRadio > div > label {
        background-color: #262730;
        padding: 15px 20px;
        border-radius: 10px;
        border: 1px solid #4B4B4B;
        width: 100%;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
    }
    div.row-widget.stRadio > div > label:hover {
        background-color: #383942;
        border-color: #FF4B4B;
    }
    /* 폰트 크기 확대 */
    div.row-widget.stRadio > div > label[data-baseweb="radio"] > div {
        font-size: 18px !important;
        font-weight: 500;
    }
    .stMarkdown p {
        font-size: 18px !important;
        line-height: 1.6;
    }
    /* 버튼 크기 확대 */
    button[kind="primary"], button[kind="secondary"] {
        width: 100%;
        padding-top: 15px !important;
        padding-bottom: 15px !important;
        font-size: 18px !important;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 자동 스크롤 함수
def scroll_to_top():
    js = '''
    <script>
        setTimeout(function() {
            var body = window.parent.document.querySelector(".main");
            var html = window.parent.document.documentElement;
            if (body) body.scrollTop = 0;
            if (html) html.scrollTop = 0;
            window.parent.scrollTo(0, 0);
        }, 100);
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
    # 1. 신학 (Theology)
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
    # 2. 동력 (Drive)
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
    # 3. 사회 (Society)
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
    # 4. 문화 (Culture)
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

# -----------------------------------------------------------------------------
# 유형 상세 정보 (이미지 Key 제거 버전)
# -----------------------------------------------------------------------------
TYPE_DETAILS = {
    "TDPL": {"title": "엄격한 신학자형", "person": "장 칼뱅", "quote": "나의 마음을 주님께 드리나이다.", "keywords": ["교리", "경건", "전통", "질서"], "desc": "\"오직 성경, 오직 믿음!\" 흔들리지 않는 신학적 뼈대를 중요하게 생각합니다. 감정적인 예배보다는 깊이 있는 말씀 해석과 거룩한 예전을 선호하는 대쪽 같은 선비형 크리스천입니다."},
    "TDPM": {"title": "지성적 변증가형", "person": "C.S. 루이스", "quote": "나는 태양이 떠오르는 것을 믿듯이 기독교를 믿는다.", "keywords": ["이성", "논리", "현대적", "개인신앙"], "desc": "기독교를 논리적이고 지성적으로 변증하는 것을 즐깁니다. 신학은 보수적이지만, 그것을 현대인들이 이해할 수 있는 세련된 언어와 문화로 풀어내는 뇌가 섹시한 신앙인입니다."},
    "TDSL": {"title": "정의로운 개혁가형", "person": "도산 안창호", "quote": "낙망은 청년의 죽음이요, 청년이 죽으면 민족이 죽는다.", "keywords": ["애국", "실력양성", "사회변혁", "정직"], "desc": "독실한 신앙심을 바탕으로 민족의 실력을 키우고 사회를 변화시키려 노력했던 행동하는 신앙인입니다. 믿음은 곧 정직한 삶과 사회적 책임으로 나타나야 한다고 믿습니다."},
    "TDSM": {"title": "행동하는 순교자형", "person": "디트리히 본회퍼", "quote": "값싼 은혜는 우리 교회의 치명적인 적이다.", "keywords": ["제자도", "저항", "실천", "책임"], "desc": "말뿐인 신앙을 거부하고, 불의한 시대에 맞서 신앙의 대가를 지불합니다. 현대적인 감각을 가지고 있지만, 신앙의 원칙을 지키기 위해 목숨까지 걸 수 있는 강단 있는 유형입니다."},
    "TGPL": {"title": "뜨거운 경건주의자형", "person": "존 웨슬리", "quote": "세계는 나의 교구다.", "keywords": ["성령체험", "개인성화", "규칙", "전통"], "desc": "\"내 마음이 이상하게 뜨거워졌다.\" 교회의 전통과 예전을 존중하면서도, 개인의 뜨거운 회심과 성령 체험을 강조합니다. 기도의 깊이를 아는 영적 모범생입니다."},
    "TGPM": {"title": "열정적 부흥사형", "person": "빌리 그레이엄", "quote": "천국은 예수 그리스도를 통해 가는 곳입니다.", "keywords": ["전도", "축복", "현대적예배", "대중성"], "desc": "복잡한 신학 논쟁보다는 \"예수 믿고 구원받으세요!\"라는 단순하고 강력한 메시지를 좋아합니다. 현대적인 찬양과 뜨거운 통성기도가 있는 부흥회 스타일을 선호합니다."},
    "TGSL": {"title": "빈민가의 성자형", "person": "손양원 목사", "quote": "원수를 사랑하라.", "keywords": ["사랑", "용서", "낮은곳", "헌신"], "desc": "\"사랑의 원자탄.\" 가장 낮은 곳에서 소외된 이들을 섬기며, 인간의 상식을 뛰어넘는 사랑과 용서를 실천합니다. 신학적 보수성을 지키면서도 삶으로 예수의 흔적을 보여주는 행동파입니다."},
    "TGSM": {"title": "사랑의 실천가형", "person": "마더 테레사", "quote": "위대한 사랑으로 작은 일을 할 수 있을 뿐입니다.", "keywords": ["헌신", "봉사", "섬김", "순종"], "desc": "보수적인 신앙관을 가지고 있지만, 말보다는 행동으로 하나님의 사랑을 보여줍니다. 가장 낮은 곳에서 묵묵히 소외된 이들을 섬기는 것이 최고의 예배라고 생각합니다."},
    "CDPL": {"title": "고독한 수도사형", "person": "토마스 머튼", "quote": "침묵은 우리가 하나님께 드릴 수 있는 가장 깊은 기도입니다.", "keywords": ["침묵", "관상", "영성", "열린마음"], "desc": "시끄러운 세상 속에서 고요한 침묵과 묵상을 추구합니다. 전통적인 예전(Liturgy) 속에서 깊은 영성을 찾으며, 타 종교나 사상과도 열린 마음으로 대화합니다."},
    "CDPM": {"title": "문화적 사색가형", "person": "폴 틸리히", "quote": "신앙은 '궁극적인 관심'에 사로잡히는 상태다.", "keywords": ["문화", "철학", "존재", "현대성"], "desc": "성경을 문자적으로 믿기보다 철학적, 인문학적으로 재해석하여 현대인의 삶에 적용합니다. 지적인 호기심이 많고 세련된 신앙을 추구합니다."},
    "CDSL": {"title": "현실적 예언자형", "person": "라인홀드 니버", "quote": "바꿀 수 있는 것을 바꾸는 용기를 주소서.", "keywords": ["현실주의", "정의", "사회윤리", "책임"], "desc": "개인의 도덕성만으로는 사회 문제를 해결할 수 없다고 봅니다. 냉철한 이성으로 사회 구조를 분석하고, 정의를 실현하기 위해 시스템을 바꾸려 노력하는 지성적 참여파입니다."},
    "CDSM": {"title": "사회적 실천가형", "person": "장기려 박사", "quote": "돈이 없어 치료를 못 받는 환자가 있어서는 안 된다.", "keywords": ["인술", "사회복지", "청빈", "지성"], "desc": "\"바보 의사.\" 뛰어난 의술과 지성을 가졌지만, 그것을 자신의 부귀영화가 아닌 가난한 이웃을 위한 사회적 시스템(의료보험)을 만드는 데 사용하는 깨어있는 지식인입니다."},
    "CGPL": {"title": "자연 속의 신비가형", "person": "성 프란치스코", "quote": "주여, 나를 당신의 평화의 도구로 써 주소서.", "keywords": ["평화", "생태", "청빈", "신비"], "desc": "교리는 유연하게, 영성은 깊게. 자연 만물과 교감하며 하나님의 신비를 체험합니다. 딱딱한 설교보다는 시와 노래, 아름다운 예전을 통해 하나님을 만납니다."},
    "CGPM": {"title": "따뜻한 치유자형", "person": "헨리 나우웬", "quote": "우리는 '상처 입은 치유자'입니다.", "keywords": ["치유자", "심리", "내면", "공감"], "desc": "옳고 그름을 따지기보다 서로의 상처를 보듬어주는 공동체를 꿈꿉니다. 성경을 심리학적, 정서적으로 해석하여 현대인의 외로움을 위로하는 따뜻한 멘토형입니다."},
    "CGSL": {"title": "저항하는 평화주의자형", "person": "윤동주 시인", "quote": "별을 노래하는 마음으로 모든 죽어가는 것을 사랑해야지.", "keywords": ["문학", "성찰", "저항", "순수"], "desc": "거친 투쟁보다는 맑은 영혼과 문학적 감수성으로 시대의 아픔에 공감하고 저항합니다. 잎새에 이는 바람에도 괴로워하는 순수한 신앙의 소유자입니다."},
    "CGSM": {"title": "꿈꾸는 혁명가형", "person": "마틴 루터 킹", "quote": "나에게는 꿈이 있습니다.", "keywords": ["자유", "평등", "비폭력", "꿈"], "desc": "낡은 관습과 차별을 철폐하고 모두가 평등한 세상을 만듭니다. 뜨거운 웅변과 감동적인 연설로 사람들의 가슴에 불을 지르는 리더입니다."}
}

AXIS_INFO = {
    "Theology": {"name": "신학 (Theology)", "desc": "성경을 바라보는 관점"},
    "Drive": {"name": "동력 (Drive)", "desc": "신앙생활의 에너지원"},
    "Society": {"name": "사회 (Society)", "desc": "믿음의 방향"},
    "Culture": {"name": "문화 (Culture)", "desc": "예배의 스타일"}
}

AXIS_COMPARISON = {
    "Theology": {
        "title": "신학 (Theology): 성경을 바라보는 눈",
        "left": {"code": "T", "name": "Text (텍스트)", "desc": "성경 문자주의\n보수적 신학\n절대적 권위"},
        "right": {"code": "C", "name": "Context (컨텍스트)", "desc": "시대적 재해석\n유연한 신학\n역사적 맥락"}
    },
    "Drive": {
        "title": "동력 (Drive): 신앙의 에너지원",
        "left": {"code": "D", "name": "Discipline (훈련)", "desc": "제자훈련/공부\n지성적 깨달음\n차분한 성찰"},
        "right": {"code": "G", "name": "Grace (은혜)", "desc": "성령체험/집회\n감성적 뜨거움\n열정적 기도"}
    },
    "Society": {
        "title": "사회 (Society): 믿음의 방향",
        "left": {"code": "P", "name": "Private (개인)", "desc": "개인의 구원\n내면의 평안\n가정/교회 중심"},
        "right": {"code": "S", "name": "Social (사회)", "desc": "사회의 구원\n구조적 정의\n세상/참여 중심"}
    },
    "Culture": {
        "title": "문화 (Culture): 예배의 스타일",
        "left": {"code": "L", "name": "Liturgy (예전)", "desc": "전통적 예배\n엄숙함/경건\n찬송가/오르간"},
        "right": {"code": "M", "name": "Modern (현대)", "desc": "열린 예배\n자유로움/축제\nCCM/밴드"}
    }
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

        st.write(f"**Q{q_num}. {q['text']}**")
        user_choice = st.radio(
            f"Q{q_num} 답변", options=OPTIONS, key=f"radio_{q_key}", 
            horizontal=False, label_visibility="collapsed", index=prev_index
        )
        
        if user_choice:
            st.session_state.answers[q_key] = {
                "score": SCORE_MAP[user_choice], "reverse": q["reverse"], 
                "part": q["part"], "choice_label": user_choice
            }
        st.markdown("")

    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    if st.session_state.step > 1:
        if col1.button("⬅️ 이전 단계"):
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
# 결과 화면 로직 (에러 수정됨)
# -----------------------------------------------------------------------------
else:
    scroll_to_top()
    st.balloons()
    
    # 점수 계산
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
    
    # 안전하게 정보 가져오기
    type_info = TYPE_DETAILS.get(type_code, {"title": "알 수 없음", "person": "-", "quote": "", "keywords": [], "desc": "-"})
    
    st.success("🎉 분석이 완료되었습니다!")
    st.title(f"당신의 유형: [{type_code}]")
    st.header(f"\"{type_info['title']}\"")
    
    col_img, col_desc = st.columns([1, 2])
    
    # [핵심 수정] 이미지 로직: 딕셔너리 키 대신 파일 존재 여부 확인
    with col_img:
        image_found = False
        # 확장자별 체크 (jpg, png)
        for ext in [".jpg", ".png", ".jpeg"]:
            img_path = f"images/{type_code}{ext}"
            if os.path.exists(img_path):
                st.image(img_path, caption=type_info["person"], use_container_width=True)
                image_found = True
                break
        
        # 이미지가 없을 경우 대체 UI 표시
        if not image_found:
            st.warning(f"이미지 없음\n({type_code})")

    with col_desc:
        st.markdown(f"### 👤 **{type_info['person']}**")
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
    
    if st.button("🔄 처음부터 다시 하기", type="secondary"):
        st.session_state.step = 1
        st.session_state.answers = {}
        st.rerun()