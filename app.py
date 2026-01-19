import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import altair as alt
import os

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 스타일
# -----------------------------------------------------------------------------
st.set_page_config(page_title="C-BTI: 기독교 영성 유형 진단", page_icon="⛪", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    
    /* 헤더 스타일 */
    h1 { color: #333; font-weight: 700; letter-spacing: -1px; margin-bottom: 20px; }
    
    /* 질문 텍스트 */
    .question-text {
        font-size: 18px; font-weight: 600; color: #2c3e50;
        background-color: #f8f9fa; padding: 15px; border-radius: 10px;
        margin-bottom: 15px; border-left: 5px solid #4B89DC;
    }
    
    /* 선택지 라디오 버튼 스타일링 */
    div.row-widget.stRadio > div { flex-direction: column; gap: 10px; }
    div.row-widget.stRadio > div > label {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        padding: 12px; border-radius: 8px; cursor: pointer;
        transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    div.row-widget.stRadio > div > label:hover {
        background-color: #eef2f6; border-color: #4B89DC;
    }

    /* 버튼 스타일 */
    button[kind="primary"] {
        width: 100%; padding: 0.5rem 1rem; font-weight: bold;
        background-color: #4B89DC; border: none;
    }
    button[kind="secondary"] { width: 100%; }

    /* 결과 카드 스타일 */
    .result-card {
        background-color: white; padding: 30px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 30px;
        text-align: center; border-top: 5px solid #8E44AD;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터: 16가지 유형 정의 (최종 합의된 인물 리스트)
# -----------------------------------------------------------------------------
TYPE_DETAILS = {
    "TDPL": {
        "title": "청교도적 수도사형",
        "slogan": "오직 성경, 오직 거룩",
        "desc": "철저한 말씀 연구와 개인의 경건을 최우선으로 여기며, 타협하지 않는 진리를 수호합니다.",
        "people_data": [
            {"name": "에즈라", "type": "Bible", "text": "에스라 7:10 - 여호와의 율법을 연구하여 준행하며 가르치기로 결심하였더라"},
            {"name": "장 칼뱅", "type": "Book", "text": "저서: 《기독교 강요》 (Institutes of the Christian Religion)"},
            {"name": "마틴 로이드 존스", "type": "Book", "text": "저서: 《산상수훈》 (Studies in the Sermon on the Mount)"},
            {"name": "박형룡 박사", "type": "Book", "text": "저서: 《교의신학》"}
        ]
    },
    "TDPM": {
        "title": "지성적 변증가형",
        "slogan": "믿음은 생각하는 것이다",
        "desc": "이성과 논리를 통해 기독교 진리를 변증하며, 세상 문화 속에서 복음의 합리성을 증명합니다.",
        "people_data": [
            {"name": "아볼로", "type": "Bible", "text": "사도행전 18:24 - 성경에 능통한 자라"},
            {"name": "C.S. 루이스", "type": "Book", "text": "저서: 《순전한 기독교》 (Mere Christianity)"},
            {"name": "팀 켈러", "type": "Book", "text": "저서: 《하나님을 말하다》 (The Reason for God)"},
            {"name": "이어령 교수", "type": "Book", "text": "저서: 《지성에서 영성으로》"}
        ]
    },
    "TDSL": {
        "title": "사회 개혁가형",
        "slogan": "하나님의 법대로 세상을 개혁하라",
        "desc": "불의와 타협하지 않는 원칙을 가지고, 사회의 도덕적 타락과 부조리에 맞서 싸웁니다.",
        "people_data": [
            {"name": "느헤미야", "type": "Bible", "text": "느헤미야 2:17 - 예루살렘 성을 건축하여 다시 수치를 당하지 말자"},
            {"name": "마틴 루터", "type": "Book", "text": "저서: 《노예 의지론》 (On the Bondage of the Will)"},
            {"name": "윌리엄 윌버포스", "type": "Quote", "text": "\"노예 무역을 끝내기 전까지 나는 결코 쉬지 않으리라.\""},
            {"name": "안창호 선생", "type": "Quote", "text": "\"낙망은 청년의 죽음이요, 청년이 죽으면 민족이 죽는다.\""}
        ]
    },
    "TDSM": {
        "title": "실용적 전략가형",
        "slogan": "세계는 나의 교구다",
        "desc": "탁월한 리더십과 전략으로 조직을 이끌며, 복음 전파를 위한 실질적인 성과를 만들어냅니다.",
        "people_data": [
            {"name": "다니엘", "type": "Bible", "text": "다니엘 1:8 - 뜻을 정하여 왕의 음식으로 자기를 더럽히지 아니하고"},
            {"name": "얀 후스", "type": "Quote", "text": "\"진리를 사랑하고, 진리를 말하고, 진리를 지켜라.\""},
            {"name": "주기철 목사", "type": "Quote", "text": "\"일사각오(一死覺悟), 한 번 죽음으로 주님을 지킨다.\""},
            {"name": "디트리히 본회퍼", "type": "Book", "text": "저서: 《나를 따르라》 (The Cost of Discipleship)"}
        ]
    },
    "TGPL": {
        "title": "무릎의 성자형",
        "slogan": "기도는 하나님과 대화하는 것이다",
        "desc": "깊은 기도를 통해 하나님과 독대하며, 영적인 순수함과 내면의 거룩함을 추구합니다.",
        "people_data": [
            {"name": "이사야", "type": "Bible", "text": "이사야 6:8 - 내가 여기 있나이다 나를 보내소서"},
            {"name": "성 어거스틴", "type": "Book", "text": "저서: 《고백록》 (Confessions)"},
            {"name": "블레즈 파스칼", "type": "Book", "text": "저서: 《팡세》 (Pensées)"},
            {"name": "한경직 목사", "type": "Quote", "text": "\"템플턴상 상금은 내 것이 아닙니다. 나는 죄인입니다.\""}
        ]
    },
    "TGPM": {
        "title": "불의 전도자형",
        "slogan": "우리가 보고 들은 것을 말하지 않을 수 없다",
        "desc": "복잡한 논리보다는 직관적이고 뜨거운 열정으로 영혼을 구원하는 데 앞장섭니다.",
        "people_data": [
            {"name": "베드로", "type": "Bible", "text": "사도행전 4:12 - 다른 이로써는 구원을 받을 수 없나니"},
            {"name": "D.L. 무디", "type": "Quote", "text": "\"세상은 헌신된 한 사람을 통해 하나님이 하실 일을 보게 될 것이다.\""},
            {"name": "빌리 그래함", "type": "Quote", "text": "\"나의 집은 천국입니다. 나는 단지 여행 중일 뿐입니다.\""},
            {"name": "김익두 목사", "type": "Quote", "text": "\"벙어리가 말하고 앉은뱅이가 일어나는 역사를 보라!\""}
        ]
    },
    "TGSL": {
        "title": "빈민가의 성자형",
        "slogan": "가장 작은 자에게 한 것이 내게 한 것이다",
        "desc": "가장 낮은 곳에서 소외된 이웃을 조건 없이 사랑하며, 청빈과 나눔을 실천합니다.",
        "people_data": [
            {"name": "도르가", "type": "Bible", "text": "사도행전 9:36 - 선행과 구제하는 일이 심히 많더니"},
            {"name": "성 프란치스코", "type": "Quote", "text": "\"주여, 나를 평화의 도구로 써 주소서.\""},
            {"name": "윌리엄 부스", "type": "Quote", "text": "\"한국은 국, 비누, 구원(Soup, Soap, Salvation)이 필요하다.\""},
            {"name": "장기려 박사", "type": "Quote", "text": "\"돈이 없어서 치료받지 못하는 환자는 이 땅에 없어야 한다.\""}
        ]
    },
    "TGSM": {
        "title": "순교자적 선교사형",
        "slogan": "나를 따르려거든 자기를 부인하라",
        "desc": "민족과 공동체를 위해 자신의 모든 기득권을 내려놓고 희생하며 앞장서는 리더입니다.",
        "people_data": [
            {"name": "모세", "type": "Bible", "text": "출애굽기 32:32 - 내 이름을 생명책에서 지워버려 주옵소서"},
            {"name": "에이브러햄 링컨", "type": "Quote", "text": "\"하나님이 우리 편인가보다, 우리가 하나님 편인가를 물으라.\""},
            {"name": "마틴 루터 킹", "type": "Quote", "text": "\"나에게는 꿈이 있습니다 (I have a dream).\""},
            {"name": "조만식 선생", "type": "Quote", "text": "\"나는 3천만 동포와 함께 죽겠노라.\""}
        ]
    },
    "CDPL": {
        "title": "고독한 수도사형",
        "slogan": "침묵은 영혼의 호흡이다",
        "desc": "세상의 소음에서 벗어나 깊은 침묵과 묵상 속에서 하나님의 세미한 음성을 듣습니다.",
        "people_data": [
            {"name": "시므온", "type": "Bible", "text": "누가복음 2:30 - 내 눈이 주의 구원을 보았사오니"},
            {"name": "토마스 아 켐피스", "type": "Book", "text": "저서: 《그리스도를 본받아》 (The Imitation of Christ)"},
            {"name": "토마스 머튼", "type": "Book", "text": "저서: 《칠층산》 (The Seven Storey Mountain)"},
            {"name": "헨리 나우웬", "type": "Book", "text": "저서: 《상처 입은 치유자》 (The Wounded Healer)"}
        ]
    },
    "CDPM": {
        "title": "문화적 사색가형",
        "slogan": "신앙은 궁극적 관심이다",
        "desc": "철학, 예술, 인문학을 통해 성경을 깊이 있게 해석하며 현대인에게 진리를 재해석합니다.",
        "people_data": [
            {"name": "솔로몬", "type": "Bible", "text": "전도서 1:2 - 헛되고 헛되니 모든 것이 헛되도다"},
            {"name": "쇠렌 키르케고르", "type": "Book", "text": "저서: 《공포와 전율》 (Fear and Trembling)"},
            {"name": "폴 틸리히", "type": "Book", "text": "저서: 《존재의 용기》 (The Courage to Be)"},
            {"name": "프란시스 쉐퍼", "type": "Book", "text": "저서: 《그러면 우리는 어떻게 살 것인가》"}
        ]
    },
    "CDSL": {
        "title": "현실적 예언자형",
        "slogan": "정의를 물 같이 흐르게 하라",
        "desc": "성경적 세계관으로 시대를 날카롭게 분석하고, 기술 사회와 권력의 문제를 비판합니다.",
        "people_data": [
            {"name": "아모스", "type": "Bible", "text": "아모스 5:24 - 오직 정의를 물 같이, 공의를 마르지 않는 강 같이"},
            {"name": "라인홀드 니버", "type": "Book", "text": "저서: 《도덕적 인간과 비도덕적 사회》"},
            {"name": "자크 엘륄", "type": "Book", "text": "저서: 《기술 사회》 (The Technological Society)"},
            {"name": "함석헌 선생", "type": "Book", "text": "저서: 《뜻으로 본 한국역사》"}
        ]
    },
    "CDSM": {
        "title": "사회적 실천가형",
        "slogan": "모든 영역에 그리스도의 주권을",
        "desc": "체계적인 훈련과 시스템을 구축하여 정치, 경제, 교육 등 사회 각 영역을 변혁합니다.",
        "people_data": [
            {"name": "사도 바울", "type": "Bible", "text": "사도행전 19:10 - 두란노 서원에서 날마다 강론하니라"},
            {"name": "아브라함 카이퍼", "type": "Book", "text": "저서: 《칼빈주의 강연》 (Lectures on Calvinism)"},
            {"name": "존 스토트", "type": "Book", "text": "저서: 《현대 사회와 기독교적 소명》"},
            {"name": "로렌 커닝햄", "type": "Book", "text": "저서: 《하나님, 정말 당신이십니까?》"}
        ]
    },
    "CGPL": {
        "title": "자연 속 신비가형",
        "slogan": "하늘이 하나님의 영광을 노래하고",
        "desc": "자연 만물과 일상의 아름다움 속에서 하나님의 신비를 발견하며 시적으로 노래합니다.",
        "people_data": [
            {"name": "아삽", "type": "Bible", "text": "시편 73:25 - 하늘에서는 주 외에 누가 내게 있으리요"},
            {"name": "성 패트릭", "type": "Quote", "text": "\"그리스도는 내 앞에도, 뒤에도, 안에도 계십니다.\""},
            {"name": "로제 수사", "type": "Quote", "text": "\"오 주여, 우리의 어둠을 밝히소서.\""},
            {"name": "이현주 목사", "type": "Book", "text": "저서: 《관옥 이현주 산문집》"}
        ]
    },
    "CGPM": {
        "title": "자유 보헤미안형",
        "slogan": "한 알의 모래에서 천국을 본다",
        "desc": "형식에 얽매이지 않는 자유로운 영혼으로, 예술적 상상력을 통해 하나님을 표현합니다.",
        "people_data": [
            {"name": "막달라 마리아", "type": "Bible", "text": "요한복음 20:18 - 내가 주를 보았다 하고"},
            {"name": "단테 알리기에리", "type": "Book", "text": "저서: 《신곡》 (The Divine Comedy)"},
            {"name": "윌리엄 블레이크", "type": "Book", "text": "저서: 《순수의 노래와 경험의 노래》"},
            {"name": "윤동주 시인", "type": "Book", "text": "저서: 《하늘과 바람과 별과 시》"}
        ]
    },
    "CGSL": {
        "title": "평화의 사자형",
        "slogan": "평화가 곧 길이다",
        "desc": "폭력과 혐오가 가득한 세상에서 기도와 비폭력, 화해의 메시지로 평화를 심습니다.",
        "people_data": [
            {"name": "예레미야", "type": "Bible", "text": "예레미야애가 3:49 - 내 눈에 흐르는 눈물이 그치지 아니하고"},
            {"name": "레프 톨스토이", "type": "Book", "text": "저서: 《하나님의 나라는 너희 안에 있다》"},
            {"name": "데스몬드 투투", "type": "Book", "text": "저서: 《용서 없이 미래 없다》"},
            {"name": "스탠리 하우어워스", "type": "Book", "text": "저서: 《나그네 된 백성》 (Resident Aliens)"}
        ]
    },
    "CGSM": {
        "title": "행동하는 개혁가형",
        "slogan": "행함이 없는 믿음은 죽은 것이다",
        "desc": "불의를 참지 못하는 거룩한 분노로, 억압받는 자들의 해방을 위해 온몸을 던집니다.",
        "people_data": [
            {"name": "야고보", "type": "Bible", "text": "야고보서 2:17 - 행함이 없는 믿음은 그 자체가 죽은 것이라"},
            {"name": "오스카 로메로", "type": "Quote", "text": "\"정의는 억압받는 자들의 편이다.\""},
            {"name": "구스타보 구티에레즈", "type": "Book", "text": "저서: 《해방신학》 (A Theology of Liberation)"},
            {"name": "전태일 열사", "type": "Quote", "text": "\"내 죽음을 헛되이 하지 말라. 우리는 기계가 아니다.\""}
        ]
    }
}

# -----------------------------------------------------------------------------
# 3. 데이터: 질문지 (총 45문항 - 님께서 주신 리스트 100% 반영)
# -----------------------------------------------------------------------------
questions_data = [
    # 🏛️ Part 1. 신학 (Theology) - 15문항
    {"text": "성경에 기록된 기적(홍해 가름, 오병이어 등)은 과학적으로 설명되지 않아도 문자 그대로 일어난 역사적 사실이다.", "part": "Theology", "reverse": True},
    {"text": "술, 담배 문제는 구원이나 신앙의 본질과 무관하므로, 무조건 금지하기보다 개인의 양심과 자율에 맡겨야 한다.", "part": "Theology", "reverse": False},
    {"text": "여성이 목사 안수를 받고 강단에서 설교하는 것은 성경적 창조 질서에 어긋난다고 생각한다.", "part": "Theology", "reverse": True},
    {"text": "동성애는 인권 문제가 아니라 성경이 금지하는 치유받아야 할 죄의 문제다.", "part": "Theology", "reverse": True},
    {"text": "예수 천국, 불신 지옥 구호는 기독교 진리를 너무 단순화시킨 것이라 거부감이 든다.", "part": "Theology", "reverse": False},
    {"text": "진화론은 성경의 창조 신앙과 양립하기 어려우므로, 기독교인이라면 이를 무비판적으로 수용해서는 안 된다.", "part": "Theology", "reverse": True},
    {"text": "목사님의 설교라도 나의 이성과 상식에 비추어 납득이 가지 않으면 무조건 믿기보다 비판적으로 수용해야 한다.", "part": "Theology", "reverse": False},
    {"text": "교회는 세상 문화가 침투하지 못하도록 거룩하게 구별된 방파제 역할을 해야 한다.", "part": "Theology", "reverse": True},
    {"text": "지진이나 전염병 같은 대형 재난을 특정 죄에 대한 하나님의 심판으로 해석하는 것은 위험하다고 생각한다.", "part": "Theology", "reverse": False},
    {"text": "타종교에도 구원의 가능성이 있거나 배울 점이 있다고 인정하는 것은 위험하다.", "part": "Theology", "reverse": True},
    {"text": "설교 시간에 인문학, 철학, 영화 이야기 등 세상의 학문이 자주 인용되는 것이 자연스럽고 유익하다.", "part": "Theology", "reverse": False},
    {"text": "정신의학적 상담과 치료보다 기도가 우울증 같은 마음의 병을 해결하는 근본 열쇠라고 믿는다.", "part": "Theology", "reverse": True},
    {"text": "사랑의 하나님이 불신자와 다른 종교를 믿는 사람들을 지옥에 던지신다는 교리에 감정적 어려움을 느낀다.", "part": "Theology", "reverse": False},
    {"text": "사도신경이나 주기도문 형식을 생략하는 것은 예배의 거룩함을 해친다.", "part": "Theology", "reverse": True},
    {"text": "하나님의 공의와 심판을 강조하는 설교보다, 조건 없는 사랑과 용서를 강조하는 설교가 더 복음적이다.", "part": "Theology", "reverse": False},

    # 🔥 Part 2. 동력 (Drive) - 10문항
    {"text": "다 같이 주여!를 크게 외치고 통성 기도할 때 영적인 시원함을 느낀다.", "part": "Drive", "reverse": False},
    {"text": "신앙생활의 본질은 현실의 복을 누리는 것보다, 자기를 부인하고 십자가의 길(고난과 절제)을 걷는 훈련이다.", "part": "Drive", "reverse": True},
    {"text": "목사님이 논리적이고 치밀한 분보다는, 조금 투박하더라도 강력한 영적 카리스마와 열정으로 선포하시는 분이 좋다.", "part": "Drive", "reverse": False},
    {"text": "뜨거운 예배 같은 일시적이고 감정적인 체험보다는, 말씀을 체계적으로 깊이 있게 공부하고 삶에 적용하는 제자 훈련이 신앙의 뼈대라고 생각한다.", "part": "Drive", "reverse": True},
    {"text": "목사님의 설교가 나를 꾸짖는 내용보다는, 지친 마음을 따뜻하게 위로해 주시는 내용이면 좋겠다.", "part": "Drive", "reverse": False},
    {"text": "신앙 성장은 종교적인 체험보다는, 나의 인격이 다듬어지고 일상의 삶이 거룩해지는 것(성화)에서 증명된다.", "part": "Drive", "reverse": True},
    {"text": "복잡한 신학적 지식이나 논리보다는, 단순하더라도 하나님을 향한 순수한 열정과 가슴 뜨거운 은혜가 더 중요하다.", "part": "Drive", "reverse": False},
    {"text": "예배는 감정을 표출하기보다, 빈틈없이 진행되는 엄숙하고 질서 있는 분위기 속에서 경건함을 유지해야 한다.", "part": "Drive", "reverse": True},
    {"text": "방언, 신유(병 고침) 같은 성령의 초자연적인 은사는 오늘날에도 동일하게 나타나며, 이는 성령이 일하시는 강력한 증거다.", "part": "Drive", "reverse": False},
    {"text": "예화가 많은 설교보다는, 성경 본문의 원어적 의미와 배경을 논리적으로 풀어주는 강해 설교를 선호한다.", "part": "Drive", "reverse": True},

    # 🌍 Part 3. 사회 (Society) - 10문항
    {"text": "교회의 최우선 사명은 사회 개혁보다 한 영혼을 전도하여 구원받게 하는 것이다.", "part": "Society", "reverse": True},
    {"text": "성경이 '위에 있는 권세들에게 복종하라'고 했으므로, 정권이 마음에 들지 않더라도 일단 선거로 뽑혔다면 믿고 순응해야 한다.", "part": "Society", "reverse": True},
    {"text": "개인의 죄를 회개하는 것보다, 가난과 차별을 만들어내는 사회의 구조적 악과 모순에 관심을 갖는 것이 더 중요하다.", "part": "Society", "reverse": False},
    {"text": "거리에서 시위나 집회를 하는 것보다는, 열심히 공부하고 자기계발을 통해 사회적 영향력을 갖추는 것이 하나님께 더 영광이 된다.", "part": "Society", "reverse": True},
    {"text": "사회적 현장(집회, 시위 등)에 기독교인이 깃발을 들고 참여하는 것은 자연스러운 일이다.", "part": "Society", "reverse": False},
    {"text": "예수님의 사역은 인류 구원과 죄의 대속만큼이나 가난하고 소외된 사람들을 해방하는 데 있었다.", "part": "Society", "reverse": False},
    {"text": "강단에서 특정 정당을 지지하거나 민감한 정치적 이슈를 언급하는 것은 교회의 본질을 흐리는 일이다.", "part": "Society", "reverse": True},
    {"text": "진정한 이웃 사랑은 단순한 기부나 봉사를 넘어, 억울하고 소외된 자들의 편에 서서 목소리를 내주는 것이다.", "part": "Society", "reverse": False},
    {"text": "포괄적 차별금지법 제정을 반대하는 것은 교회가 거룩함을 지키기 위해 반드시 해야 할 일이다.", "part": "Society", "reverse": True},
    {"text": "세상과 구별됨은 교회 안에 머무는 것이 아니라, 세상 속으로 들어가 정의를 실천하는 것이다.", "part": "Society", "reverse": False},

    # 🎸 Part 4. 문화 (Culture) - 10문항
    {"text": "찬양 시간에 드럼이나 일렉기타 소리가 너무 크면 경건함이 깨진다고 느낀다.", "part": "Culture", "reverse": True},
    {"text": "교독문이나 송영 같은 전통적 형식보다는, 찬양과 기도, 설교에만 집중하는 단순한 예배 순서가 더 편하다.", "part": "Culture", "reverse": False},
    {"text": "교회 건물은 여건상 빌려 쓸 수도 있겠지만, 그래도 언젠가는 하나님께 드려진 구별된 성전이 반드시 있어야 한다.", "part": "Culture", "reverse": True},
    {"text": "주일 성수도 여행이나 출장, 가족행사 등의 부득이한 사유가 있다면 가끔은 건너뛸 수 있다.", "part": "Culture", "reverse": False},
    {"text": "교회 안에서 서로를 부를 때 형제, 자매님보다 장로, 권사, 집사님 같은 직분으로 부르는 것이 질서 있어 보인다.", "part": "Culture", "reverse": True},
    {"text": "목사님이 정장 대신 청바지나 티셔츠 같은 편안한 복장으로 설교하는 것도 괜찮다.", "part": "Culture", "reverse": False},
    {"text": "아무리 시대가 변해도 주일 예배는 온라인보다는 내가 등록한 교회의 현장에 직접 가서 드리는 것이 원칙이다.", "part": "Culture", "reverse": True},
    {"text": "사도신경이나 주기도문을 매주 암송하기보다, 상황에 맞춰 생략하거나 찬양으로 대체해도 좋다.", "part": "Culture", "reverse": False},
    {"text": "본당(예배당)은 거룩한 곳이므로, 평일에 대중 공연장이나 다른 용도로 빌려주는 건 조심스럽다.", "part": "Culture", "reverse": True},
    {"text": "불신자들도 거부감 없이 올 수 있는 카페 같은 분위기의 편안하고 열린 예배를 선호한다.", "part": "Culture", "reverse": False},
]

OPTIONS = ["매우 그렇다", "조금 그렇다", "조금 아니다", "매우 아니다"]
SCORE_MAP = {"매우 그렇다": 10, "조금 그렇다": 6.7, "조금 아니다": 3.3, "매우 아니다": 0}

# -----------------------------------------------------------------------------
# 4. 세션 초기화 및 로직
# -----------------------------------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 1
if "answers" not in st.session_state:
    st.session_state.answers = {}

# 스크롤 초기화 함수
def scroll_to_top():
    js = '''<script>window.scrollTo(0,0);</script>'''
    components.html(js, height=0)

# -----------------------------------------------------------------------------
# 5. UI: 질문 진행
# -----------------------------------------------------------------------------
AXIS_NAMES = ["Theology (신학)", "Drive (동력)", "Society (사회)", "Culture (문화)"]
PARTS_KEY = ["Theology", "Drive", "Society", "Culture"]

if st.session_state.step <= 4:
    scroll_to_top()
    current_part = PARTS_KEY[st.session_state.step - 1]
    
    st.markdown(f"### Step {st.session_state.step}/4 : {AXIS_NAMES[st.session_state.step - 1]}")
    st.progress((st.session_state.step - 1) / 4)
    
    current_q_list = [q for q in questions_data if q["part"] == current_part]
    
    # 문항 번호 계산 (이전 챕터 문항 수 합산)
    start_idx = 0
    for i in range(st.session_state.step - 1):
        prev_part = PARTS_KEY[i]
        start_idx += len([q for q in questions_data if q["part"] == prev_part])
    
    all_answered = True 
    
    for idx, q in enumerate(current_q_list):
        q_real_idx = start_idx + idx + 1
        st.markdown(f"<div class='question-text'>Q{q_real_idx}. {q['text']}</div>", unsafe_allow_html=True)
        
        key_name = f"q_{current_part}_{idx}"
        
        # [중요] 초기화 문제 해결: answers에 저장된 값이 없으면 None (선택 안됨 상태)
        saved_label = st.session_state.answers.get(key_name, {}).get("label")
        saved_index = OPTIONS.index(saved_label) if saved_label in OPTIONS else None
        
        val = st.radio(label=f"Q{q_real_idx}", options=OPTIONS, key=key_name, 
                       index=saved_index, label_visibility="collapsed")
        
        if val:
            st.session_state.answers[key_name] = {
                "score": SCORE_MAP[val],
                "reverse": q["reverse"],
                "part": q["part"],
                "label": val # 라벨 저장 (상태 유지를 위해 필수)
            }
        else:
            all_answered = False 
            
        st.markdown("---")

    col1, col2 = st.columns(2)
    if st.session_state.step > 1:
        if col1.button("⬅️ 이전"):
            st.session_state.step -= 1
            st.rerun()
    
    next_btn_text = "결과 보기 🚀" if st.session_state.step == 4 else "다음 ➡️"
    if col2.button(next_btn_text, type="primary"):
        if not all_answered:
            st.warning("⚠️ 모든 질문에 답변해주세요!")
        else:
            st.session_state.step += 1
            st.rerun()

# -----------------------------------------------------------------------------
# 6. 결과 화면
# -----------------------------------------------------------------------------
else:
    scroll_to_top()
    
    # 1. 점수 계산
    scores = {k: 0 for k in PARTS_KEY}
    counts = {k: 0 for k in PARTS_KEY}
    
    for ans in st.session_state.answers.values():
        s = ans["score"]
        if ans["reverse"]: s = 10 - s
        scores[ans["part"]] += s
        counts[ans["part"]] += 1
        
    avg = {k: (scores[k] / counts[k] if counts[k] > 0 else 0) for k in PARTS_KEY}
    
    # 2. 유형 도출
    res_code = ""
    res_code += "T" if avg["Theology"] <= 5 else "C"
    res_code += "D" if avg["Drive"] <= 5 else "G"
    res_code += "P" if avg["Society"] <= 5 else "S"
    res_code += "L" if avg["Culture"] <= 5 else "M"
    
    info = TYPE_DETAILS.get(res_code, TYPE_DETAILS["TDPL"])
    
    # 3. 결과 표시
    st.markdown(f"""
    <div class="result-card">
        <h2 style='margin-bottom:0px; color:#666; font-size:1.2em;'>당신의 영적 유형은</h2>
        <h1 style="color: #4B89DC; font-size: 3.5em; margin-top:5px; margin-bottom:10px;">{res_code}</h1>
        <h3 style='margin-top:0px; font-weight:700; font-size:1.8em;'>{info['title']}</h3>
        <div style="margin: 20px 0;">
            <span style="font-size: 1.1em; font-weight: bold; color: #555; background-color:#f1f3f5; padding:8px 20px; border-radius:30px;">
                ❝ {info['slogan']} ❞
            </span>
        </div>
        <hr style='border: 0; height: 1px; background: #e0e0e0; margin: 20px 0;'>
        <p style='font-size:1.1em; line-height:1.7; color:#333;'>{info['desc']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 👥 이 유형의 롤모델 (Role Models)")
    st.caption("※ 아이콘 범례: 📖 성경구절 | 📚 대표저서 | 💬 명언")
    
    cols = st.columns(4)
    for i, person in enumerate(info['people_data']):
        img_path = f"images/{res_code}_{i+1}.jpg"
        
        p_type = person.get("type", "Quote")
        if p_type == "Bible":
            icon = "📖"
            bg_color = "#e3f2fd"
        elif p_type == "Book":
            icon = "📚"
            bg_color = "#f3e5f5"
        else:
            icon = "💬"
            bg_color = "#fff3e0"
            
        with cols[i]:
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
            else:
                st.markdown(f"""
                <div style="background-color:#f8f9fa; height:150px; display:flex; align-items:center; justify-content:center; border-radius:8px; border:1px dashed #ced4da; color:#adb5bd; font-size:0.8em; margin-bottom:10px;">
                    {person['name']}<br>(이미지 없음)
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="text-align:center;">
                <div style="font-weight:bold; font-size:1.1em; margin-bottom:8px; color:#2c3e50;">
                    {person['name']}
                </div>
                <div style="font-size:0.85em; color:#495057; background-color:{bg_color}; padding:10px; border-radius:8px; line-height:1.4; min-height:80px; display:flex; align-items:center; justify-content:center;">
                    <span>{icon} {person['text']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    col_chart, col_share = st.columns([1, 1])
    with col_chart:
        st.subheader("📊 나의 성향 분석")
        chart_data = pd.DataFrame({
            "지표": ["신학(T vs C)", "동력(D vs G)", "사회(P vs S)", "문화(L vs M)"],
            "점수": [avg["Theology"], avg["Drive"], avg["Society"], avg["Culture"]]
        })
        c = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X('지표', sort=None),
            y=alt.Y('점수', scale=alt.Scale(domain=[0, 10])),
            color=alt.value("#4B89DC"),
            tooltip=['지표', '점수']
        ).properties(height=250)
        st.altair_chart(c, use_container_width=True)
        
    with col_share:
        st.subheader("📢 공유하기")
        st.info("결과를 캡처해서 친구들과 나눠보세요!")
        st.code(f"https://faithcheck.streamlit.app/", language="none")
        st.caption("👆 위 링크를 복사하세요")

    st.divider()
    
    if st.button("🔄 처음부터 다시 하기", type="secondary"):
        st.session_state.step = 1
        st.session_state.answers = {}
        st.rerun()