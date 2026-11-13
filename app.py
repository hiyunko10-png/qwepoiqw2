import hashlib
import hmac
import secrets
from datetime import date, timedelta
import requests
import streamlit as st

st.set_page_config(page_title="한상가족", page_icon="🍚", layout="centered")
st.markdown("""<style>.stApp{background:#faf9f5} .block-container{max-width:850px;padding-top:2rem} h1,h2,h3{color:#285b48} div.stButton>button{border-radius:12px} </style>""", unsafe_allow_html=True)
st.title("🍚 한상가족")
st.caption("함께 고르고, 나눠 준비하는 우리 집 저녁")

RECIPES = [
 {"name":"두부 달걀 덮밥","ingredients":{"두부":1,"달걀":3,"쌀":2},"allergens":["대두","달걀"],"minutes":20},
 {"name":"닭고기 채소볶음","ingredients":{"닭고기":1,"양배추":1,"당근":1},"allergens":[],"minutes":25},
 {"name":"돼지고기 감자조림","ingredients":{"돼지고기":1,"감자":3,"양파":1},"allergens":["돼지고기"],"minutes":30},
 {"name":"소고기 버섯 덮밥","ingredients":{"소고기":1,"버섯":1,"쌀":2},"allergens":["쇠고기"],"minutes":25},
 {"name":"참치 달걀 볶음밥","ingredients":{"참치":1,"달걀":3,"쌀":2},"allergens":["생선","달걀"],"minutes":15},
 {"name":"토마토 채소 파스타","ingredients":{"파스타":1,"토마토":3,"양파":1},"allergens":["밀","토마토"],"minutes":25},
 {"name":"감자 채소 카레","ingredients":{"감자":3,"당근":1,"양파":1,"카레가루":1,"쌀":2},"allergens":["밀"],"minutes":30},
 {"name":"연어 구이와 밥","ingredients":{"연어":2,"쌀":2,"브로콜리":1},"allergens":["생선"],"minutes":25},
 {"name":"두부 버섯 전골","ingredients":{"두부":1,"버섯":1,"배추":1},"allergens":["대두"],"minutes":25},
 {"name":"닭고기 감자 수프","ingredients":{"닭고기":1,"감자":3,"당근":1},"allergens":[],"minutes":30},
 {"name":"달걀 채소전","ingredients":{"달걀":4,"애호박":1,"당근":1},"allergens":["달걀"],"minutes":20},
 {"name":"소고기 무국과 밥","ingredients":{"소고기":1,"무":1,"쌀":2},"allergens":["쇠고기"],"minutes":30},
]
ALLERGENS=["대두","달걀","돼지고기","쇠고기","생선","밀","토마토","우유","땅콩","견과류","갑각류","조개류"]

def pw_hash(password, salt):
 return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),200000).hex()

def api(method, suffix='', **kwargs):
 url=st.secrets['SUPABASE_URL'].rstrip('/')+'/rest/v1/families'+suffix
 key=st.secrets['SUPABASE_SERVICE_ROLE_KEY']
 r=requests.request(method,url,headers={'apikey':key,'Authorization':'Bearer '+key,'Prefer':'return=representation'},timeout=20,**kwargs)
 r.raise_for_status()
 return r.json() if r.content else []

def load():
 rows=api('GET','?id=eq.'+st.session_state.room)
 if not rows: raise RuntimeError('가족 공간을 찾을 수 없습니다.')
 return rows[0]

def save(row, data):
 updated=api('PATCH',f"?id=eq.{row['id']}&revision=eq.{row['revision']}",json={'data':data,'revision':row['revision']+1})
 if not updated:
  st.error('다른 가족이 먼저 수정했습니다. 새로고침 후 다시 시도하세요.')
  st.stop()
 st.rerun()

SCHEMA_SQL = "-- Supabase SQL Editor에서 한 번 실행하세요.\ncreate table public.families (\n id text primary key,\n salt text not null,\n password_hash text not null,\n data jsonb not null default '{}'::jsonb,\n revision bigint not null default 0\n);\nalter table public.families enable row level security;\n-- 클라이언트용 정책을 만들지 않습니다. 서버의 service_role만 접근합니다.\nrevoke all on public.families from anon, authenticated;\n"

with st.expander("⚙️ 처음 실행할 때: 연결·배포 안내"):
 st.markdown("""1. Supabase에서 전용 프로젝트를 만들고 아래 SQL을 SQL Editor에서 한 번 실행하세요.
2. GitHub 저장소에 **app.py**, **requirements.txt** 두 파일을 올리세요.
3. Streamlit Community Cloud에서 저장소를 연결하고 진입 파일을 `app.py`로 선택하세요.
4. 배포 설정의 Secrets에 아래 형식으로 URL과 서버 전용 키를 입력하세요. **실제 키를 GitHub에 올리지 마세요.**
5. 배포한 앱에서 가족 공간을 만들고 주소·공간 코드·비밀번호를 가족에게 공유하세요.

로컬 실행: `pip install -r requirements.txt` 실행 후, `.streamlit/secrets.toml`에 같은 연결 정보를 넣고 `streamlit run app.py`를 실행하세요.

공유 비밀번호를 아는 가족은 모든 데이터를 수정할 수 있습니다. 개인 인증·암호 재설정·접속 속도 제한은 없는 가족용 시제품입니다. 공개 서비스 운영용은 아닙니다.
""")
 st.code('SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"\nSUPABASE_SERVICE_ROLE_KEY = "YOUR_SERVER_SIDE_SERVICE_ROLE_KEY"', language='toml')
 st.code(SCHEMA_SQL, language='sql')
 st.caption('SQL은 처음 한 번만 실행합니다. 데이터는 GitHub가 아닌 Supabase에 저장되며, 열린 화면은 새로고침 버튼으로 갱신합니다.')
try:
 configured = bool(st.secrets.get('SUPABASE_URL')) and bool(st.secrets.get('SUPABASE_SERVICE_ROLE_KEY'))
except Exception:
 configured = False
if not configured:
 st.info('처음 실행하셨나요? 위 연결·배포 안내를 열어 저장소와 비공개 연결 정보를 설정해주세요.')
 st.stop()

if 'room' not in st.session_state:
 st.info('가족 공간을 만들고 공간 코드와 비밀번호를 가족에게 공유하세요.')
 with st.form('login'):
  mode=st.radio('시작하기',['가족 공간 입장','새 가족 공간 만들기'],horizontal=True)
  code=st.text_input('가족 공간 코드',help='영문·숫자 8자 이상. 추측하기 어려운 코드를 사용하세요.').strip()
  password=st.text_input('공유 비밀번호',type='password')
  if st.form_submit_button('시작하기',type='primary'):
   if len(code)<8 or not code.isascii() or not code.isalnum() or len(password)<10:
    st.error('공간 코드는 영문·숫자 8자 이상, 비밀번호는 10자 이상으로 입력하세요.')
   else:
    room=hashlib.sha256(code.encode()).hexdigest()
    try:
     rows=api('GET','?id=eq.'+room)
     if mode=='새 가족 공간 만들기':
      if rows: st.error('이미 사용 중인 코드입니다.')
      else:
       salt=secrets.token_hex(16)
       api('POST',json={'id':room,'salt':salt,'password_hash':pw_hash(password,salt),'data':{'members':{},'pantry':[],'plan':{},'votes':{},'checked':[]},'revision':0})
       st.session_state.room=room; st.rerun()
     elif rows and hmac.compare_digest(rows[0]['password_hash'],pw_hash(password,rows[0]['salt'])):
      st.session_state.room=room; st.rerun()
     else: st.error('공간 코드 또는 비밀번호가 일치하지 않습니다.')
    except requests.RequestException:
     st.error('저장소에 연결하지 못했습니다. 관리자에게 설정 확인을 요청하세요.')
 st.caption('이 앱은 소규모 가족용 시제품입니다. 의료정보·실명 대신 별명을 사용하세요.')
 st.stop()

try: row=load()
except (requests.RequestException,RuntimeError,KeyError):
 st.error('가족 데이터를 불러오지 못했습니다. 저장소 설정을 확인한 뒤 새로고침하세요.');st.stop()
d=row['data']
with st.sidebar:
 st.header('우리 가족')
 if st.button('🔄 최신 내용 불러오기'): st.rerun()
 if st.button('로그아웃'):
  st.session_state.clear();st.rerun()
 st.caption('공유 비밀번호를 아는 사람은 가족 데이터 전체를 수정할 수 있습니다.')
st.warning('알레르기 필터는 등록된 주재료만 비교합니다. 소스·가공식품·교차접촉을 보장하지 않으므로 성분표를 직접 확인하세요. 의료용 식단이 아닙니다.')
t1,t2,t3,t4=st.tabs(['👨‍👩‍👧 가족·냉장고','🗳️ 메뉴 투표','📅 주간 식단','🛒 장보기'])
with t1:
 st.subheader('가족별 취향')
 with st.form('member'):
  name=st.text_input('별명 (같은 별명으로 저장하면 수정됩니다)',max_chars=20).strip()
  allergies=st.multiselect('피해야 할 알레르기 항목',ALLERGENS)
  dislikes=st.text_input('싫어하는 재료 (쉼표로 구분)',max_chars=200)
  if st.form_submit_button('가족 저장'):
   if not name: st.error('별명을 입력하세요.')
   else:
    d['members'][name]={'allergies':allergies,'dislikes':[x.strip() for x in dislikes.split(',') if x.strip()]};save(row,d)
 for n,m in d['members'].items():
  st.write(f"**{n}** · 알레르기: {', '.join(m['allergies']) or '없음'} · 기피: {', '.join(m['dislikes']) or '없음'}")
 with st.form('pantry'):
  pantry=st.text_input('집에 있는 재료 (쉼표로 구분)',value=', '.join(d['pantry']))
  st.caption('재료 보유 여부만 기록하며 실제 수량은 관리하지 않습니다.')
  if st.form_submit_button('냉장고 저장'):
   d['pantry']=list(dict.fromkeys(x.strip() for x in pantry.split(',') if x.strip()));save(row,d)

avoid=set(a for m in d['members'].values() for a in m['allergies'])
dislikes=set(a for m in d['members'].values() for a in m['dislikes'])
allowed=[r for r in RECIPES if not avoid.intersection(r['allergens']) and not dislikes.intersection(r['ingredients'])]
allowed.sort(key=lambda r:(-len(set(r['ingredients']) & set(d['pantry'])),-len(d['votes'].get(r['name'],[])),r['minutes']))
with t2:
 st.subheader('저녁 메뉴 후보')
 st.caption('냉장고 재료 활용도 → 가족 투표 수 → 조리시간 순서입니다. 투표는 공동 후보 목록에 계속 유지됩니다.')
 if not d['members']: st.info('가족·냉장고 탭에서 가족을 먼저 등록하세요.')
 else:
  voter=st.selectbox('누구의 투표인가요?',list(d['members']))
  max_time=st.select_slider('조리시간 상한',options=[15,20,25,30],value=30)
  for r in [r for r in allowed if r['minutes']<=max_time]:
   with st.container(border=True):
    st.markdown(f"### {r['name']}")
    votes=d['votes'].get(r['name'],[])
    st.write(f"약 {r['minutes']}분 · {len(votes)}표 · 재료: {', '.join(r['ingredients'])}")
    st.caption('투표: '+(', '.join(votes) or '아직 없음'))
    if st.button('투표 취소' if voter in votes else '👍 이 메뉴 좋아요',key='vote_'+r['name']):
     if voter in votes: votes.remove(voter)
     else: votes.append(voter)
     d['votes'][r['name']]=votes;save(row,d)
 if not allowed: st.info('현재 조건에 맞는 메뉴가 없습니다. 알레르기 조건을 임의로 완화하지 말고 별도 메뉴를 준비하세요.')

with t3:
 st.subheader('일주일 저녁 식단')
 anchor=st.date_input('보고 싶은 주',date.today())
 monday=anchor-timedelta(days=anchor.weekday())
 names=[r['name'] for r in allowed]
 st.caption('새로 등록한 알레르기는 기존 식단에도 확인이 필요합니다. 자동 추천은 같은 메뉴를 반복할 수 있습니다.')
 if st.button('✨ 빈 날짜에 추천 채우기',disabled=not names):
  ranked=sorted(allowed,key=lambda r:(-len(d['votes'].get(r['name'],[])),-len(set(r['ingredients'])&set(d['pantry']))))
  for i in range(7): d['plan'].setdefault(str(monday+timedelta(days=i)),ranked[i%len(ranked)]['name'])
  d['checked']=[];save(row,d)
 with st.form('weekly'):
  edited={}
  for i in range(7):
   day=str(monday+timedelta(days=i));current=d['plan'].get(day,'미정')
   options=['미정','외식 / 각자 식사']+names
   if current not in options:
    st.error(f'{day}: 기존 메뉴 {current}는 현재 가족의 제외 조건에 해당합니다.')
    options.append(current)
   edited[day]=st.selectbox(f'{day} · {"월화수목금토일"[i]}',options,index=options.index(current),key='day_'+day)
  if st.form_submit_button('이번 주 식단 저장',type='primary'):
   d['plan'].update(edited);d['checked']=[];save(row,d)

with t4:
 st.subheader('장보기 목록')
 start=st.date_input('장볼 주의 아무 날짜',date.today(),key='shopping_week')
 start=start-timedelta(days=start.weekday())
 st.caption('기본 레시피는 약 2인분이며 수량은 구매용 참고 묶음입니다. 1 = 1팩·1개 등 재료마다 다릅니다. 가족 인원과 제품 용량에 맞게 조절하세요.')
 recipes={r['name']:r for r in RECIPES};totals={}
 for i in range(7):
  r=recipes.get(d['plan'].get(str(start+timedelta(days=i))))
  if r:
   for ingredient,qty in r['ingredients'].items():totals[ingredient]=totals.get(ingredient,0)+qty
 missing={k:v for k,v in totals.items() if k not in d['pantry']}
 if not totals: st.info('주간 식단을 먼저 저장하세요.')
 elif not missing: st.success('등록된 주재료가 모두 냉장고에 있습니다. 실제 수량과 양념은 따로 확인하세요.')
 else:
  st.caption('냉장고에 있다고 등록한 재료는 수량과 무관하게 제외됩니다. 소금·식용유·간장 등 기본 양념은 별도 확인하세요.')
  with st.form('shopping'):
   selected=[]
   for item,qty in sorted(missing.items()):
    token=str(start)+'|'+item
    if st.checkbox(f'{item} · 참고 수량 {qty}',value=token in d['checked'],key='check_'+token):selected.append(token)
   if st.form_submit_button('구매 체크 공유 저장'):
    prefix=str(start)+'|';d['checked']=[x for x in d['checked'] if not x.startswith(prefix)]+selected;save(row,d)
  text='장보기 목록 ('+str(start)+')\n'+'\n'.join(f'{k}: 참고 수량 {v}' for k,v in sorted(missing.items()))
  st.download_button('목록 내려받기',text,'shopping.txt',mime='text/plain')
