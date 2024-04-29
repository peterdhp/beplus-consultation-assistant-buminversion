import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import io
import datetime
from audiorecorder import audiorecorder

from openai import OpenAI

#st.session_state.temp_med_rec="[증상]\n[기타 특이사항]\n[진단]\n[치료, 처방 및 계획]"


openai_api_key = st.secrets["OPENAI_API_KEY"]

if 'transcript_status' not in st.session_state:
    st.session_state.transcript_status=False

if 'transcript' not in st.session_state:
    st.session_state.transcript =''

if "total_cost" not in st.session_state:
    st.session_state.totalcost = 0

def refresh():
    st.session_state.totalcost = 0
    st.session_state.format_type = '기본'
    st.session_state.transcript =''
    st.session_state.temp_medical_record ="[현병력]\n\n[ROS]\n\n[신체검진]"
    st.session_state.recordings = None
    st.session_state.transcript_status = False
    player_field.empty()


def medical_record(transcript):
    """문진 내용을 기반으로 질문을 함"""
    
    prompt_template = """Given the transcript, write a semi-filled medical report of the patient. Only fill in the form based on the transcript. Also after the medical record, write the list of things the doctor explained to the patient in Korean.
                
[transcript]
{transcript}

The output(except the diagnosis) should be in Korean. Here is an example :

[병력] #최대한 구체적으로 빠짐없이, 왜 내원하게 되었는지 설명
상기 환자는 67세 남자로, 3개월 전부터 복부 통증을 호소하였음. 1주일 전부터 증상이 심해지다가 구토와 어지러움을 느껴 내원함
    
[증상] #양성 증상에서 참고하기 좋은 구체적인 내용이 있을 경우 같이 표시해줘
구토(+, 하루 4번)
복통(+, NRS 5)
악화요인(+, 식사하고 나서 심해짐)
토혈(-)
    
[기타 특이사항]
V/S : 130/90, 88, 36.5도
약물력 : 특이사항 없음
가족력 : 모름

주의할 점 : 67세 남성으로 위암을 배제할 수 없으므로 건강검진 시행여부 확인
    
[치료,처방 및 계획]
CBC 시행
위내시경 시행

-----
                
                """

    prompt = PromptTemplate.from_template(prompt_template)
    llm = ChatOpenAI(model_name="gpt-4-turbo", temperature = 0)
    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser    
    
    output = chain.invoke({"transcript" : transcript})
    return output

def medical_record_voicecomplete():
    """문진 내용을 기반으로 질문을 함"""
    
    
    
    prompt_template = """Given a transcript of a patient consultation and a incomplete medical record, complete and edit the medical record. 
Complete or edit the medical record based ONLY on the information given. For the physical examination KEEP THE FORMAT and only change what is necessary.
DON'T give the impression list. After the medical record, write the list of things the doctor explained to the patient in Korean.

[transcript]
{transcript}

[incomplete medical record]
{incomplete_medrec}

-----"""
    
    #user_type_mapping = {'human': '[patient]', 'ai': '[doctor]'}
    #msg_log_text = "\n".join(f"{user_type_mapping[sender]} : {message}" for sender, message in transcript)
    
    prompt = PromptTemplate.from_template(prompt_template)
    
    llm = ChatOpenAI(model_name="gpt-4-turbo", temperature = 0)
    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser    
    
    return chain

def update_text():
    if st.session_state.format_type == '없음' and st.session_state.temp_medical_record == "":
        with st.spinner('음성 녹음을 바탕으로 진료 기록을 완성하고 있습니다...'):
            st.session_state.LLM_medrecord = medical_record(transcript=st.session_state.transcript)
    else :    
        chain = medical_record_voicecomplete()
        with st.spinner('음성 녹음을 바탕으로 진료 기록을 완성하고 있습니다...'):
            st.session_state.LLM_medrecord = chain.invoke({"transcript" : st.session_state.transcript, "incomplete_medrec" : st.session_state.temp_medical_record})
    st.session_state.temp_medical_record = st.session_state.LLM_medrecord 
   
def update_text_advise():
    if st.session_state.format_type == '없음' and st.session_state.temp_medical_record == "":
        with st.spinner('음성 녹음을 바탕으로 진료 기록을 완성하고 있습니다...'):
            st.session_state.LLM_medrecord = medical_record(transcript=st.session_state.transcript)
    else :    
        chain = medical_record_voicecomplete()
        with st.spinner('음성 녹음을 바탕으로 진료 기록을 완성하고 있습니다...'):
            st.session_state.LLM_medrecord = chain.invoke({"transcript" : st.session_state.transcript, "incomplete_medrec" : st.session_state.temp_medical_record})
    st.session_state.temp_medical_record = st.session_state.LLM_medrecord 
    st.success("진료 기록을 성공적으로 완성하였습니다.")
    with st.spinner('진료 내용을 검토하고 있습니다...'):
        output = medical_advisor(st.session_state.temp_medical_record,st.session_state.transcript)
    st.session_state.temp_medical_record += '\n\n'+ output
    st.success("진료 내용 검토 성공적으로 완료 되었습니다.")
 
def recorddemo():
    st.session_state.transcript = "아 선생님 제가 최근 며칠부터 너무 죽을 것 같아가지고요 어제는 오늘부터 막 토도 하고 지금 기운도 너무 없고 음식도 못먹겠고 지금 계속 토하고 배아프고 너무 힘들어요 그래요? 토하기 시작한건 언제부터인데요? 토한거는 어제 오후부터 막 속이 안좋더니 오늘부터는 막 계속 토하고 그래요 토를 몇번 하셨어요? 글쎄요 먹은것도 없이 계속 나와서 아 토하면 먹은게 아니라 그냥 음식같은것만 나와요? 네 그냥 먹은것도 없이 계속 마지막으로 식사하신건 언젠가요? 식사는 조금씩 했어요 조금씩 죽같은거 그냥 마지막으로 언제 식사했어요? 아침에도 죽을 먹어야겠다 싶어가지고 너무 지금 기운도 하나도 없고 밥도 힘들어요 설사는 안하셨구요? 설사는 그냥 병이 좀 있다 정도만 했었고 마지막으로 본건 언젠데요? 그건 어제인가 그젠가 배가 아프진 않으세요? 전체적으로 다? 배 아픈것도 그럼 어제부터 그러신거에요? 아 배는 요 근래부터 조금씩 조금씩 아프더니 어제부터 좀 더 아픈데 근래? 근래면 정확히 어느정도 됐을까요? 아 글쎄요 제가 요새 좀 컨디션이 안좋다 싶더니 막 갑자기 이게 심해지네요 요새가 어느정도 되셨어요? 아 글쎄요 한 이번주? 이번주? 그럼 한 일주일정도? 이번주 한 글쎄요 한 3-4일 됐을까? 3-4일? 그냥 제가 좀 몸살기운 나고 좀 기침하고 좀 감기기운이 있더니"
def format_retriever(format_type):
    
    format_lib ={}
    
    format_lib["없음"] = ""
    format_lib["기본"] = "[현병력]\n\n[ROS]\n\n[신체검진]"
    format_lib["어깨통증"] = """[현병력]
    
[ROS]
    
[신체검진]
<shoulder ROM>
Lt. abduction/adduction = 150/30
Rt. abduction/adduction = 150/30
Lt. extension/flexion = 50/150
Rt. extension/flexion = 50/150
"""
    
    output = format_lib.get(format_type)
    
    return output

def call_format():
    st.session_state.temp_medical_record = format_retriever(st.session_state.format_type)

def advise(): 
    output = medical_advisor(st.session_state.temp_medical_record,st.session_state.transcript)
    st.session_state.temp_medical_record += '\n\n'+ output
    st.success("진료 내용 검토 성공적으로 완료 되었습니다.")

def medical_advisor(medical_record, transcript):
    prompt_template = """Let's say you are a medical school professor.
Given a transcript of a patient consultation and a complete medical record written, 
Give a list of impression in the format below :
#진단명은 영어로해줘. 예상 되는 진단 5개를 알려주고 왜 그렇게 생각했는지와 해야할 검사들을 알려줘. 진단을 할 때 특별히 유의할 점도 정리해줘
R/O peptic ulcer(복부 통증이 있고, 어지러움을 느낌, 확인을 위해 위내시경을 시행)
DDx1. reflux esophagitis(식사를 하고 나서 악화됨, 위내시경 시행)
DDx2. gastric cancer (3개월전부터 호소, 위내시경 시행)
DDx3. functional dyspepsia (3개월전부터 호소, 경과관찰)
DDx4. trauma (복부 통증, xray로 골절 확인)

Then give medical feedback to the doctor in Korean. ONLY give feedback that could be critical to the patient, you don't have to say anything if nothing is critical.
Be as brief and clear as possible, no longer than 50 Korean characters.

[transcript]
{transcript}

[complete medical record]
{medical_record}
-----"""

    prompt = PromptTemplate.from_template(prompt_template)
    
    llm = ChatOpenAI(model_name="gpt-4-turbo", temperature = 0)
    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser
    output = chain.invoke({"transcript" : transcript, "medical_record" : medical_record})
    
    return output

class NamedBytesIO(io.BytesIO):
    def __init__(self, buffer=None, name=None):
        super().__init__(buffer)
        self.name = name

st.selectbox("진료기록 양식", options=['없음', '기본', '어깨통증'],index=1,on_change=call_format, key='format_type')

st.text_area('진료 기록', value="[현병력]\n\n[ROS]\n\n[신체검진]", height=600, key='temp_medical_record')

st.session_state.audio=audiorecorder(start_prompt="진료 녹음하기 🔴", stop_prompt="진료 녹음 끝내기 🟥", pause_prompt="", key='recordings')
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

#byte_io = io.BytesIO()
#audio.export(byte_io, format='mp3')
#byte_io.seek(0)
st.write(st.session_state)


client = OpenAI()
if st.session_state.recordings and len(st.session_state.audio)>0.1:
    player_field = st.audio(st.session_state.audio.export().read())  
    if not st.session_state.transcript_status :
        with st.spinner('음성 녹음을 받아적고 있습니다...'):
            asr_result = client.audio.transcriptions.create(model="whisper-1", language= "ko",prompt="이것은 의사와 환자의 진료 중 나눈 대화를 녹음한 것입니다.",file= NamedBytesIO(st.session_state.audio.export().read(), name="audio.wav"))
        st.session_state.transcript += '\n'+ asr_result.text 
        st.session_state.transcript_status = True
#st.text_area("진료 음성기록", key='transcript')
st.button('✍🏻 진료기록 자동 완성 ',on_click=update_text)
st.button('✅ impression list 및 진료 내용 검토',on_click=advise)
st.button('🔄 새로운 환자',on_click=refresh,key='refreshbutton')
   
#encoded_image = base64.b64encode(open("logo.png", "rb").read()).decode()


with st.sidebar:
    st.write(st.session_state)
    st.image('logo.png', caption=None, width=None, use_column_width=None, clamp=False, channels="RGB", output_format="auto")
    st.title("진료 도우미 (BETA ver.)")
    st.header("사용설명서")
    st.subheader("1.진료 준비하기")
    st.markdown("`진료기록 양식`에서 원하는 양식을 선택하거나 진료기록 텍스트 상자에 원하는 양식을 붙여넣기한다.")
    st.subheader("2.진료내용 녹음하기")
    st.markdown("`진료 녹음하기 🔴`을 눌러주고 진료를 진행한다. (진료가 시작되기 최소 3초전에는 녹음을 시작하는 것을 추천드립니다.)")
    st.subheader("3.진료 음성기록 변환하기")
    st.markdown("진료가 끝나면 `진료 녹음 끝내기 🟥`을 누르고 `진료 음성기록`이 완성되기를 기다린다.")
    st.subheader("4.진료기록 자동 완성하기")
    st.markdown("`✍🏻 진료기록 자동 완성`을 눌러 진료기록이 완성되기를 기다린다.")
    st.subheader("5.진료기록 검토하기")
    st.markdown("`✅ impression list 및 진료 내용 검토`을 눌러 진료기록이 검토되기를 기다린다.")
    st.subheader("5.새로고침")
    st.markdown("`새로운 환자`을 눌러 이전 진료기록을 지운다.")
    
    st.button("음성녹음 Demo",on_click=recorddemo)
    #st.button("자동작성완료 Demo",on_click=completedemo)
    #st.session_state
