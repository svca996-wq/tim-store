import sqlite3,os,secrets,datetime,random,string,time,json,traceback,base64,re
from datetime import timedelta
from flask import Flask,request,redirect,session,send_from_directory,Response
from collections import defaultdict
app=Flask(__name__);app.secret_key="tim-shop-2026";app.permanent_session_lifetime=timedelta(days=30)
UPLOAD_FOLDER="uploads";os.makedirs(UPLOAD_FOLDER,exist_ok=True);NL=chr(10)
RL=defaultdict(list);BL={};MAX_REQ=40;BLOCK_TIME=600
ADMIN_USER="admim11";ADMIN_PASS="123456789"
TH_MONTHS={1:"ม.ค.",2:"ก.พ.",3:"มี.ค.",4:"เม.ย.",5:"พ.ค.",6:"มิ.ย.",7:"ก.ค.",8:"ส.ค.",9:"ก.ย.",10:"ต.ค.",11:"พ.ย.",12:"ธ.ค."}
def is_valid_tm_envelope(url):
 s=(url or "").strip()
 return bool(re.match(r"^https?://gift\.truemoney\.com/[a-zA-Z0-9_-]+/?(?:\?.*)?$",s))
def db():
 c=sqlite3.connect("shop.db");c.row_factory=sqlite3.Row;return c
def sf(r,k,d=""):
 try:
  v=r[k];return v if v is not None else d
 except:return d
def cur():
 if 'uid' not in session:return None
 c=db();u=c.execute("SELECT * FROM users WHERE id=?",(session['uid'],)).fetchone();c.close();return u
def is_admin(u):return u and u['username']==ADMIN_USER
def stg():
 c=db()
 try:s=c.execute("SELECT * FROM settings WHERE id=1").fetchone()
 except:s=None
 c.close();return s
def maintenance_page(st):
 sn=sf(st,'shop_name','timstore')
 msg=sf(st,'maintenance_msg','กำลังปิดปรับปรุงระบบและอัปเดตเว็บไซต์ชั่วคราว ขออภัยในความไม่สะดวกครับ')
 return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{sn} · ปิดปรับปรุงระบบ</title><style>
 *{{box-sizing:border-box}}
 body{{margin:0;min-height:100vh;background:#050507;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;padding:18px}}
 .m-card{{width:100%;max-width:460px;background:linear-gradient(180deg,#17070c,#0b0b0f);border:1px solid rgba(225,29,72,.45);border-radius:24px;padding:28px 20px;text-align:center;box-shadow:0 16px 40px rgba(0,0,0,.6)}}
 .m-badge{{display:inline-block;background:rgba(225,29,72,.18);border:1px solid rgba(225,29,72,.45);color:#ff4d6d;font-size:12px;font-weight:bold;padding:5px 12px;border-radius:999px;margin-bottom:14px}}
 .m-ico{{font-size:48px;margin-bottom:10px}}
 h1{{margin:0 0 10px;font-size:24px;font-weight:900}}
 p{{margin:0 0 20px;color:#cbd5e1;font-size:14px;line-height:1.65;white-space:pre-line}}
 .m-btn{{display:inline-block;background:#14151c;border:1px solid #2b2d3a;color:#ff6b86;padding:10px 18px;border-radius:12px;font-size:13px;font-weight:bold;text-decoration:none}}
 </style></head><body>
  <div class='m-card'>
   <div class='m-badge'>🛠️ MAINTENANCE MODE</div>
   <div class='m-ico'>🚧</div>
   <h1>{sn} กำลังอัปเดตระบบ</h1>
   <p>{msg}</p>
   <a href='/login' class='m-btn'>เข้าสู่ระบบแอดมิน</a>
  </div>
 </body></html>""",503
@app.before_request
def dd():
 if request.path.startswith(('/static','/uploads')):return
 ip=request.remote_addr or 'x';now=time.time()
 if ip in BL:
  if now<BL[ip]:return f"<h1>โดนบล็อก รอ {int(BL[ip]-now)} วิ</h1>",429
  del BL[ip]
 RL[ip]=[t for t in RL[ip] if now-t<60];RL[ip].append(now)
 if len(RL[ip])>MAX_REQ:BL[ip]=now+BLOCK_TIME;return "<h1>ยิงเว็บ โดนบล็อก 10 นาที</h1>",429
 if request.path not in ('/login','/logout','/reset-admin-tim123'):
  st=stg()
  if st and sf(st,'maintenance_on',0)==1:
   u=cur()
   if not is_admin(u):
    return maintenance_page(st)
@app.errorhandler(500)
def e500(e):tb=traceback.format_exc();print(tb);return f"<h1>error</h1><pre>{tb}</pre>",500
def pp(v):
 try:
  s=str(v).replace(',','').strip()
  if '-' in s:s=s.split('-')[0].strip()
  return float(s) if s not in ('','-') else 0
 except:return 0
def fp(v):
 try:
  f=float(v);return str(int(f)) if f==int(f) else str(f)
 except:return "0"
def fmt_th_date(dt_str):
 try:
  s=str(dt_str or '').strip().replace('T',' ')[:19]
  dt=datetime.datetime.fromisoformat(s)
  return f"{dt.day} {TH_MONTHS.get(dt.month,'')} {dt.year+543}"
 except:return str(dt_str or '-')[:10]
def init():
 c=db()
 T=[("users","id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT DEFAULT '', password TEXT, coin REAL DEFAULT 0, role TEXT DEFAULT 'user', avatar TEXT DEFAULT '', last_login TEXT DEFAULT '', date TEXT"),("zones","id INTEGER PRIMARY KEY, name TEXT, icon TEXT DEFAULT '🔥', order_num INTEGER DEFAULT 0, img TEXT DEFAULT ''"),("categories","id INTEGER PRIMARY KEY, name TEXT UNIQUE, icon TEXT DEFAULT '📦', order_num INTEGER DEFAULT 0"),("products","id INTEGER PRIMARY KEY, zone_id INTEGER, category_id INTEGER DEFAULT 0, name TEXT, price REAL, agent_price REAL DEFAULT 0, desc TEXT, img TEXT DEFAULT '', stock TEXT DEFAULT '', date TEXT"),("variants","id INTEGER PRIMARY KEY, product_id INTEGER, name TEXT, price REAL, agent_price REAL DEFAULT 0, stock TEXT DEFAULT '', date TEXT"),("settings","id INTEGER PRIMARY KEY, logo TEXT DEFAULT '', banner TEXT DEFAULT '', shop_name TEXT DEFAULT 'timstore', promptpay TEXT DEFAULT '', truemoney_phone TEXT DEFAULT '', bank_name TEXT DEFAULT 'ธนาคารกสิกรไทย', bank_acc_name TEXT DEFAULT 'แอดมิน timstore', bank_acc_no TEXT DEFAULT '', auto_check INTEGER DEFAULT 1, disc_on INTEGER DEFAULT 0, disc_type TEXT DEFAULT 'percent', disc_val REAL DEFAULT 0, maintenance_on INTEGER DEFAULT 0, maintenance_msg TEXT DEFAULT 'กำลังปิดปรับปรุงระบบและอัปเดตเว็บไซต์ชั่วคราว ขออภัยในความไม่สะดวกครับ'"),("topups","id INTEGER PRIMARY KEY, username TEXT, amount REAL, method TEXT, slip TEXT DEFAULT '', envelope_link TEXT DEFAULT '', phone TEXT DEFAULT '', status TEXT DEFAULT 'pending', date TEXT"),("credit_codes","id INTEGER PRIMARY KEY, code TEXT UNIQUE, amount REAL, used_by TEXT DEFAULT '', used INTEGER DEFAULT 0"),("agent_keys","id INTEGER PRIMARY KEY, code TEXT UNIQUE, discount INTEGER DEFAULT 10, days INTEGER DEFAULT 30, price REAL DEFAULT 0, created_by TEXT DEFAULT 'admin', used_by TEXT DEFAULT '', used INTEGER DEFAULT 0, date TEXT"),("agents","id INTEGER PRIMARY KEY, username TEXT UNIQUE, discount INTEGER DEFAULT 10, expire TEXT, renewed_cycle TEXT DEFAULT '', date TEXT"),("orders","id INTEGER PRIMARY KEY, username TEXT, product_name TEXT, product_img TEXT DEFAULT '', qty INTEGER, total REAL, codes TEXT, date TEXT"),("notifications","id INTEGER PRIMARY KEY, type TEXT, username TEXT, amount REAL, message TEXT, detail TEXT, link TEXT, is_read INTEGER DEFAULT 0, date TEXT"),("coupons","id INTEGER PRIMARY KEY, code TEXT UNIQUE, value REAL, type TEXT DEFAULT 'percent', max_use INTEGER DEFAULT 0, used INTEGER DEFAULT 0, active INTEGER DEFAULT 1")]
 for n,s in T:c.execute(f"CREATE TABLE IF NOT EXISTS {n}({s})")
 NEED={'users':[('email',"TEXT DEFAULT ''"),('password',"TEXT DEFAULT '1234'"),('coin',"REAL DEFAULT 0"),('role',"TEXT DEFAULT 'user'"),('avatar',"TEXT DEFAULT ''"),('last_login',"TEXT DEFAULT ''"),('date',"TEXT")],'zones':[('icon',"TEXT DEFAULT '🔥'"),('order_num',"INTEGER DEFAULT 0"),('img',"TEXT DEFAULT ''")],'categories':[('icon',"TEXT DEFAULT '📦'"),('order_num',"INTEGER DEFAULT 0")],'products':[('category_id',"INTEGER DEFAULT 0"),('agent_price',"REAL DEFAULT 0"),('desc',"TEXT DEFAULT ''"),('img',"TEXT DEFAULT ''"),('stock',"TEXT DEFAULT ''"),('date',"TEXT")],'variants':[('agent_price',"REAL DEFAULT 0"),('stock',"TEXT DEFAULT ''"),('date',"TEXT")],'settings':[('logo',"TEXT DEFAULT ''"),('banner',"TEXT DEFAULT ''"),('shop_name',"TEXT DEFAULT 'timstore'"),('promptpay',"TEXT DEFAULT ''"),('truemoney_phone',"TEXT DEFAULT ''"),('bank_name',"TEXT DEFAULT 'ธนาคารกสิกรไทย'"),('bank_acc_name',"TEXT DEFAULT 'แอดมิน timstore'"),('bank_acc_no',"TEXT DEFAULT ''"),('auto_check',"INTEGER DEFAULT 1"),('disc_on',"INTEGER DEFAULT 0"),('disc_type',"TEXT DEFAULT 'percent'"),('disc_val',"REAL DEFAULT 0"),('maintenance_on',"INTEGER DEFAULT 0"),('maintenance_msg',"TEXT DEFAULT 'กำลังปิดปรับปรุงระบบและอัปเดตเว็บไซต์ชั่วคราว ขออภัยในความไม่สะดวกครับ'")],'topups':[('slip',"TEXT DEFAULT ''"),('envelope_link',"TEXT DEFAULT ''"),('phone',"TEXT DEFAULT ''"),('status',"TEXT DEFAULT 'pending'")],'credit_codes':[('used_by',"TEXT DEFAULT ''"),('used',"INTEGER DEFAULT 0")],'agent_keys':[('discount',"INTEGER DEFAULT 10"),('days',"INTEGER DEFAULT 30"),('price',"REAL DEFAULT 0")],'agents':[('renewed_cycle',"TEXT DEFAULT ''")],'orders':[('product_img',"TEXT DEFAULT ''")],'coupons':[('type',"TEXT DEFAULT 'percent'"),('max_use',"INTEGER DEFAULT 0"),('used',"INTEGER DEFAULT 0"),('active',"INTEGER DEFAULT 1")]}
 for tbl,cols in NEED.items():
  try:
   have=[r[1] for r in c.execute(f"PRAGMA table_info({tbl})").fetchall()]
   for col,typ in cols:
    if col not in have:c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {typ}")
  except:pass
 if not c.execute("SELECT * FROM categories").fetchone():
  for idx,(nm,ic) in enumerate([("ไอดีเกม","🎮"),("สคริปต์ / ตัวรัน","⚡"),("เติมเกม / โค้ด","💎")]):
   try:c.execute("INSERT OR IGNORE INTO categories(name,icon,order_num) VALUES(?,?,?)",(nm,ic,idx))
   except:pass
 if not c.execute("SELECT * FROM settings WHERE id=1").fetchone():c.execute("INSERT INTO settings(id,shop_name) VALUES(1,'timstore')")
 if not c.execute("SELECT * FROM users WHERE username=?",(ADMIN_USER,)).fetchone():c.execute("INSERT INTO users(username,email,password,coin,role,last_login,date) VALUES(?,?,?,999999,'owner',?,?)",(ADMIN_USER,"",ADMIN_PASS,str(datetime.datetime.now()),str(datetime.datetime.now())))
 else:c.execute("UPDATE users SET password=?, role='owner', coin=999999 WHERE username=?",(ADMIN_PASS,ADMIN_USER))
 c.execute("UPDATE users SET role='user' WHERE username!=? AND role IN ('admin','owner')",(ADMIN_USER,))
 c.commit();c.close()
def role_th(role):
 m={'owner':'เจ้าของร้าน','admin':'แอดมิน','agent':'ตัวแทน','user':'Member'}
 return m.get(str(role or 'user').lower(),'Member')
def user_badges_html(u,ag=None):
 if not u:return ""
 r_raw=str(sf(u,'role','user')).lower()
 main_lbl='Member' if r_raw in ('user','agent') else role_th(r_raw)
 h=f"<span class='role-pill'>👤 {main_lbl}</span>"
 if ag or r_raw=='agent':
  h+="<span class='agent-pill'>🤝 Reseller</span>"
 return f"<div class='badge-row'>{h}</div>"
def agent_7d_topup(c,username):
 try:
  cutoff=(datetime.datetime.now()-datetime.timedelta(days=7)).isoformat(' ')
  rows=c.execute("SELECT amount, date FROM topups WHERE username=? AND status='approved'",(username,)).fetchall()
  tot=0.0
  for r in rows:
   dt_s=str(sf(r,'date','')).replace('T',' ')[:19]
   if not dt_s or dt_s>=cutoff[:19]:
    tot+=float(sf(r,'amount',0) or 0)
  return tot
 except:return 0.0
def check_auto_renew_agent(c,username):
 ag=c.execute("SELECT * FROM agents WHERE username=?",(username,)).fetchone()
 if not ag:return False
 top7=agent_7d_topup(c,username)
 if top7<50.0:return False
 now=datetime.datetime.now()
 cycle_tag=now.strftime("%Y-W%W")
 if sf(ag,'renewed_cycle','')==cycle_tag:return False
 base_dt=now
 try:
  exp_s=str(sf(ag,'expire','')).strip()
  if exp_s:
   exp_dt=datetime.datetime.fromisoformat(exp_s)
   if exp_dt>now:base_dt=exp_dt
 except:pass
 new_exp=(base_dt+datetime.timedelta(days=7)).isoformat(' ')
 c.execute("UPDATE agents SET expire=?, renewed_cycle=? WHERE username=?",(new_exp,cycle_tag,username))
 u_row=c.execute("SELECT role FROM users WHERE username=?",(username,)).fetchone()
 if u_row and str(sf(u_row,'role','user')).lower()=='user':
  c.execute("UPDATE users SET role='agent' WHERE username=?",(username,))
 c.commit()
 return True
def active_agent(c,u):
 if not u:return None
 check_auto_renew_agent(c,u['username'])
 ag=c.execute("SELECT * FROM agents WHERE username=?",(u['username'],)).fetchone()
 u_role=str(sf(u,'role','user')).lower()
 if not ag:
  if u_role=='agent':
   c.execute("UPDATE users SET role='user' WHERE username=? AND role='agent'",(u['username'],));c.commit()
  return None
 try:
  exp=str(sf(ag,'expire','')).strip()
  if exp and datetime.datetime.fromisoformat(exp)<datetime.datetime.now():
   if u_role=='agent':
    c.execute("UPDATE users SET role='user' WHERE username=? AND role='agent'",(u['username'],));c.commit()
   return None
 except:pass
 if u_role=='user':
  c.execute("UPDATE users SET role='agent' WHERE username=?",(u['username'],));c.commit()
 return ag
def agent_rem_text(ag):
 if not ag:return "0 วัน 0 ชม."
 try:
  exp=str(sf(ag,'expire','')).strip()
  if not exp:return "ถาวร"
  diff=datetime.datetime.fromisoformat(exp)-datetime.datetime.now()
  if diff.total_seconds()<=0:return "0 วัน 0 ชม."
  days=diff.days
  hrs=diff.seconds//3600
  return f"{days} วัน {hrs} ชม."
 except:return "-"
def noti(t,u,a,m,d="",l="/admin"):
 c=db();c.execute("INSERT INTO notifications(type,username,amount,message,detail,link,is_read,date) VALUES(?,?,?,?,?,?,0,?)",(t,u,a,m,d,l,str(datetime.datetime.now())));c.commit();c.close()
def unread():
 c=db()
 try:n=c.execute("SELECT COUNT(*) FROM notifications WHERE is_read=0").fetchone()[0]
 except:n=0
 c.close();return n
def up(f):
 if f and f.filename:
  fn=secrets.token_hex(4)+"_"+f.filename;f.save(os.path.join(UPLOAD_FOLDER,fn));return fn
 return ""
def build_backup_payload(c=None):
 own_conn=False
 if c is None:
  c=db();own_conn=True
 data={'saved_at':str(datetime.datetime.now()),'files':{}}
 for t in ['settings','categories','zones','products','variants','coupons','credit_codes','agent_keys','agents','topups']:
  data[t]=[dict(r) for r in c.execute(f"SELECT * FROM {t}").fetchall()]
 if own_conn:
  c.close()
 for fn in os.listdir(UPLOAD_FOLDER):
  fpth=os.path.join(UPLOAD_FOLDER,fn)
  if os.path.isfile(fpth):
   try:
    with open(fpth,'rb') as rf:data['files'][fn]=base64.b64encode(rf.read()).decode('ascii')
   except:pass
 return json.dumps(data,ensure_ascii=False)
def write_auto_backup(c=None):
 js=build_backup_payload(c)
 for target in ['backup_timshop.json','/sdcard/Download/backup_timshop.json']:
  try:
   if os.path.dirname(target) and not os.path.exists(os.path.dirname(target)):continue
   with open(target,'w',encoding='utf-8') as f:f.write(js)
  except:pass
 return js
def disc_price(price,ag=None):
 if ag:
  try:
   pct=float(sf(ag,'discount',0) or 0)
   if pct>0:return max(0,round(float(price)*(100-pct)/100,2))
  except:pass
  return round(float(price),2)
 try:
  st=stg();on=sf(st,'disc_on',0);typ=sf(st,'disc_type','percent');val=float(sf(st,'disc_val',0) or 0)
  if not on or val<=0:return float(price)
  if typ=='percent':return max(0,round(float(price)*(100-val)/100,2))
  if typ=='baht':return max(0,round(float(price)-val,2))
 except:pass
 return float(price)
def disc_label():
 try:
  st=stg()
  if not sf(st,'disc_on',0):return ""
  return f"ลด {sf(st,'disc_val',0)} {'%' if sf(st,'disc_type','percent')=='percent' else 'บาท'}"
 except:return ""
def prod_stock_count(c,pid):
 stk=[x for x in sf(c.execute("SELECT stock FROM products WHERE id=?",(pid,)).fetchone(),'stock','').split(NL) if x.strip()]
 if stk:return len(stk)
 vs=c.execute("SELECT stock FROM variants WHERE product_id=?",(pid,)).fetchall()
 if vs:
  return sum(len([x for x in sf(v,'stock','').split(NL) if x.strip()]) for v in vs)
 return 0
def prod_sold_count(c,prod_name):
 try:
  nm=str(prod_name or '').strip()
  if not nm:return 0
  r=c.execute("SELECT COALESCE(SUM(qty),0) FROM orders WHERE product_name=? OR product_name LIKE ?",(nm,f"{nm} - %")).fetchone()
  return int(float(r[0] or 0))
 except:return 0
def item_agent_price(row, base_price):
 try:
  ap=float(sf(row,'agent_price',0) or 0)
  if ap>0:return round(ap,2)
 except:pass
 return None
def resolve_item_price(row, base_price, ag=None):
 bp=float(base_price or 0)
 if ag:
  ap=item_agent_price(row,bp)
  if ap is not None:return ap
  try:
   pct=float(sf(ag,'discount',0) or 0)
   if pct>0:return max(0,round(bp*(100-pct)/100,2))
  except:pass
  return round(bp,2)
 return disc_price(bp,ag)
def prod_agent_badge_text(c,p):
 try:
  vs=c.execute("SELECT price, agent_price FROM variants WHERE product_id=?",(p['id'],)).fetchall()
  if vs:
   ag_vals=[]
   for v in vs:
    ap=item_agent_price(v,v['price'])
    if ap is not None:ag_vals.append(ap)
   if ag_vals:
    lo,hi=min(ag_vals),max(ag_vals)
    return f"฿{fp(lo)} - ฿{fp(hi)}" if lo!=hi else f"฿{fp(lo)}"
  ap=item_agent_price(p,p['price'])
  if ap is not None:return f"฿{fp(ap)}"
 except:pass
 return ""
def prod_price_text(c,p,ag=None):
 vs=c.execute("SELECT * FROM variants WHERE product_id=?",(p['id'],)).fetchall()
 if vs:
  prices=[resolve_item_price(v,v['price'],ag) for v in vs]
  lo,hi=min(prices),max(prices)
  if lo!=hi:return f"฿{fp(lo)} - ฿{fp(hi)}"
  return f"฿{fp(lo)}"
 return f"฿{fp(resolve_item_price(p,p['price'],ag))}"
def render_prod_card(c,p,slide=False,ag=None):
 cnt=prod_stock_count(c,p['id'])
 sold_cnt=prod_sold_count(c,p['name'])
 is_out=(cnt<=0)
 pr_txt=prod_price_text(c,p,ag)
 ag_txt=prod_agent_badge_text(c,p) if ag else ""
 im=sf(p,'img','')
 img_h="142px" if not slide else "138px"
 img_blur="filter:blur(3px) brightness(.45);" if is_out else ""
 ih=f"<img src='/uploads/{im}' style='width:100%;height:{img_h};object-fit:contain;border-radius:12px;display:block;background:#08080a;{img_blur}'>" if im else f"<div style='width:100%;height:{img_h};border-radius:12px;background:#14151c;display:flex;align-items:center;justify-content:center;font-size:32px;{img_blur}'>📦</div>"
 out_ov="<div style='position:absolute;inset:0;background:rgba(5,5,8,.68);border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;z-index:2'><div style='width:42px;height:42px;border-radius:50%;border:2.5px solid #ef4444;color:#ef4444;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px'>⊘</div><div style='color:#f3f4f6;font-weight:bold;font-size:13px'>สินค้าหมด</div></div>" if is_out else ""
 sold_badge=f"<div style='position:absolute;top:7px;right:7px;z-index:3;background:rgba(12,12,16,.9);border:1px solid rgba(225,29,72,.5);color:#ff6b86;font-size:10px;font-weight:800;padding:3px 8px;border-radius:999px;backdrop-filter:blur(4px)'>🔥 ขายแล้ว {sold_cnt:,}</div>"
 ag_badge=f"<div style='display:inline-flex;align-items:center;gap:5px;background:#0d2620;border:1px solid #195c4c;border-radius:999px;padding:3px 7px;margin-bottom:6px;max-width:100%'><span style='background:#10b981;color:#04130f;font-size:10px;font-weight:900;padding:1px 6px;border-radius:999px;flex-shrink:0'>ตัวแทน</span><span style='color:#34d399;font-size:11px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{ag_txt}</span></div>" if ag_txt else ""
 st_dot="<span style='color:#9ca3af;font-size:11px'>● สินค้าหมด</span>" if is_out else f"<span style='color:#ef4444;font-size:11px'>● มีสินค้า</span> <span style='color:#9ca3af;font-size:11px'>· คงเหลือ {cnt}</span>"
 btn_html="<button disabled style='background:#181920;color:#6b7280;border:1px solid #262833;cursor:not-allowed;font-size:12px;padding:10px 8px'>⊘ สินค้าหมด</button>" if is_out else f"<a href='/product/{p['id']}'><button style='background:linear-gradient(90deg,#e11d48,#b91c1c);font-size:13px;padding:10px 8px'>🛒 ซื้อเลย &gt;</button></a>"
 cls="box prod-slide" if slide else "box prod-grid-card"
 return f"<div class='{cls}' style='padding:10px;display:flex;flex-direction:column;min-width:0'><div style='position:relative'>{ih}{sold_badge}{out_ov}</div><div style='font-weight:bold;font-size:14px;margin-top:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{p['name']}</div><div style='color:#ff2a55;font-weight:900;font-size:15px;margin:4px 0 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{pr_txt}</div>{ag_badge}<div style='margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{st_dot}</div><div style='margin-top:auto'>{btn_html}</div></div>"
def base(body):
 u=cur();st=stg();sn=sf(st,'shop_name','timstore');lg=sf(st,'logo','')
 lh=f"<img src='/uploads/{lg}' style='width:38px;height:38px;border-radius:50%;object-fit:cover;display:block;border:1px solid rgba(225,29,72,.5)'>" if lg else "<div style='width:38px;height:38px;border-radius:12px;background:#1a080c;border:1px solid #e11d48;display:flex;align-items:center;justify-content:center;font-weight:900;color:#ff2a55'>TS</div>"
 if u:
  c_ag=db();ag_side=active_agent(c_ag,u);c_ag.close()
  av=sf(u,'avatar','');ah=f"<img src='/uploads/{av}' style='width:48px;height:48px;border-radius:50%;object-fit:cover;border:2px solid #e11d48'>" if av else "<div style='width:48px;height:48px;border-radius:50%;background:#1e090e;border:2px solid #e11d48;display:flex;align-items:center;justify-content:center;font-size:22px'>👤</div>"
  ub=f"<a href='/profile' style='display:flex;align-items:center;gap:6px;color:#fff;font-size:13px;font-weight:bold'>{ah.replace('48px','30px')} <span>฿{int(u['coin'])}</span></a>"
  su=f"""
  <div class='side-user-card'>
   {ah}
   <div style='flex:1;min-width:0'>
    <div style='font-weight:900;font-size:16px;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{u['username'].upper()}</div>
    {user_badges_html(u,ag_side)}
   </div>
  </div>
  <div class='side-bal-card'>
   <div>
    <div style='font-size:11px;color:#9ca3af'>ยอดเงิน</div>
    <div style='font-size:22px;font-weight:900;color:#fff'>฿{float(u['coin']):.2f}</div>
   </div>
   <a href='/topup' class='btn-red-sm'>+ เติมเงิน</a>
  </div>
  """
 else:
  ub="<a href='/login' style='color:#ff4d6d;font-size:13px;font-weight:bold'>เข้าสู่ระบบ</a>"
  su="<div class='side-user-card'><div style='font-size:14px;color:#d1d5db'>ยังไม่ได้เข้าสู่ระบบ<br><a href='/login' style='color:#ff4d6d;font-weight:bold'>เข้าสู่ระบบ</a> · <a href='/register' style='color:#fff;font-weight:bold'>สมัครสมาชิก</a></div></div>"
 bell="";admin_menu=""
 if is_admin(u):
  n=unread();badge=f"<span id='bell-badge' style='background:#ef4444;color:#fff;font-size:10px;padding:2px 6px;border-radius:20px;position:absolute;top:-6px;right:-6px'>{n}</span>" if n>0 else "<span id='bell-badge' style='display:none'></span>"
  bell=f"<a href='/notifications' style='position:relative;font-size:19px;color:#fff'>🔔{badge}</a>"
  admin_menu="<a class='m-card' href='/admin' style='border-color:rgba(225,29,72,.55);background:linear-gradient(90deg,rgba(225,29,72,.22),rgba(20,8,12,.9))'><div class='m-ico'>⚙️</div><div><div class='m-t'>แอดมิน (เห็นแค่มึง)</div><div class='m-s'>จัดการร้าน สินค้า เติมเงิน สมาชิก</div></div></a><a class='m-card' href='/notifications'><div class='m-ico'>🔔</div><div><div class='m-t'>แจ้งเตือน</div><div class='m-s'>รายการสั่งซื้อและเติมเงินใหม่</div></div></a>"
 maint_banner="<div style='background:rgba(245,158,11,.16);border:1px solid #f59e0b;color:#fbbf24;text-align:center;padding:8px;border-radius:12px;font-weight:bold;margin:10px 0'>🚧 โหมดปิดปรับปรุงเว็บไซต์กำลังเปิดอยู่ (แอดมินเห็นได้คนเดียว)</div>" if (is_admin(u) and sf(st,'maintenance_on',0)==1) else ""
 disc=disc_label();disc_bar=f"<div style='background:#e11d48;color:#fff;text-align:center;padding:8px;border-radius:12px;font-weight:bold;margin:12px 0'>🔥 ลดทั้งร้าน {disc} !!</div>" if disc else ""
 return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{sn}</title><style>
 *{{box-sizing:border-box}}
 body{{background:#050506;color:#fff;font-family:sans-serif;margin:0;overflow-x:hidden}}
 a{{color:#ff4d6d;text-decoration:none}}
 .top-notice{{background:#0b0608;color:#d1d5db;font-size:12px;padding:7px 14px;border-bottom:1px solid #1a0b0e;display:flex;justify-content:space-between;gap:14px;white-space:nowrap;overflow:hidden}}
 .top{{background:#070709;padding:11px 14px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100;border-bottom:1px solid #180b0e}}
 .sidebar{{position:fixed;top:0;left:-320px;width:295px;max-width:86vw;height:100vh;background:#0a090b;z-index:200;transition:.25s;padding:16px;border-right:1px solid #261016;overflow-y:auto}}
 .sidebar.open{{left:0}}
 .overlay{{position:fixed;inset:0;background:rgba(0,0,0,.72);display:none;z-index:150}}
 .overlay.show{{display:block}}
 .side-user-card{{display:flex;align-items:center;gap:12px;background:linear-gradient(135deg,#24090f,#110a0c);border:1px solid rgba(225,29,72,.35);border-radius:16px;padding:12px;margin:12px 0}}
 .badge-row{{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:6px;margin-top:6px}}
 .side-user-card .badge-row{{justify-content:flex-start;margin-top:4px}}
 .role-pill{{display:inline-block;background:rgba(225,29,72,.18);color:#ff6b86;border:1px solid rgba(225,29,72,.45);font-size:11px;font-weight:bold;padding:3px 10px;border-radius:999px}}
 .agent-pill{{display:inline-block;background:rgba(139,92,246,.22);color:#c4b5fd;border:1px solid rgba(167,139,250,.5);font-size:11px;font-weight:bold;padding:3px 10px;border-radius:999px}}
 .side-bal-card{{display:flex;justify-content:space-between;align-items:center;background:#111114;border:1px solid #22232a;border-radius:16px;padding:12px;margin-bottom:12px}}
 .btn-red-sm{{background:#e11d48;color:#fff;padding:8px 12px;border-radius:10px;font-size:12px;font-weight:bold}}
 .m-card{{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:14px;color:#fff;margin:6px 0;background:#101014;border:1px solid #1c1d24}}
 .m-card.active-red{{background:linear-gradient(90deg,rgba(225,29,72,.24),rgba(18,8,11,.95));border-color:rgba(225,29,72,.55)}}
 .m-ico{{width:34px;height:34px;border-radius:10px;background:#181920;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}}
 .m-t{{font-size:14px;font-weight:bold;color:#fff}}
 .m-s{{font-size:11px;color:#8e929e;margin-top:2px}}
 .box{{background:#0e0e12;border:1px solid #1e1f26;border-radius:18px;padding:16px;margin:12px 0}}
 input,select,textarea{{width:100%;padding:12px;background:#14151b;border:1px solid #262833;color:#fff;border-radius:12px;margin:6px 0}}
 button{{background:#e11d48;color:#fff;border:none;padding:11px;border-radius:12px;font-weight:bold;cursor:pointer;width:100%;margin-top:4px}}
 .hero-box{{padding:18px 4px 10px}}
 .hero-pill{{display:inline-flex;align-items:center;gap:6px;background:#1b090d;border:1px solid rgba(225,29,72,.55);color:#ff4d6d;font-size:13px;font-weight:bold;padding:7px 14px;border-radius:999px;margin-bottom:14px}}
 .hero-title{{font-size:32px;font-weight:900;line-height:1.22;margin:0 0 12px;color:#fff}}
 .hero-sub{{font-size:15px;line-height:1.65;color:#b8bcc8;margin:4px 0}}
 .hero-btns{{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 10px}}
 .btn-hero-red{{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(90deg,#e11d48,#be123c);color:#fff;padding:12px 20px;border-radius:14px;font-weight:bold;font-size:15px;box-shadow:0 8px 24px rgba(225,29,72,.28)}}
 .btn-hero-dark{{display:inline-flex;align-items:center;gap:8px;background:#101116;border:1px solid #262833;color:#e5e7eb;padding:12px 18px;border-radius:14px;font-weight:bold;font-size:15px}}
 .stat-card-tl{{display:flex;align-items:center;gap:10px;background:#0b0b0e;border:1px solid #221116;border-radius:16px;padding:12px;min-width:0}}
 .stat-ico-tl{{width:42px;height:42px;border-radius:12px;background:#1a070b;border:1px solid rgba(225,29,72,.45);color:#ff335b;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0}}
 .stat-lbl-tl{{color:#9ca3af;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
 .stat-val-tl{{font-size:20px;font-weight:900;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
 .stat-unit-tl{{font-size:11px;color:#8e929e;font-weight:normal}}
 .how-modal{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.78);z-index:300;padding:14px;align-items:center;justify-content:center;overflow-y:auto}}
 .how-modal.show{{display:flex}}
 .tp-sheet{{width:100%;max-width:440px;background:#09090c;border:1px solid #261218;border-radius:24px;padding:18px;max-height:92vh;overflow-y:auto}}
 .tp-hdr{{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;padding-bottom:14px;border-bottom:1px solid #1a1b22}}
 .tp-ico{{width:46px;height:46px;border-radius:14px;background:#16171e;border:1px solid #282a36;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}}
 .tp-x{{background:transparent;border:none;color:#9ca3af;font-size:20px;width:auto;margin:0;padding:2px 6px}}
 .tp-warn{{background:rgba(225,29,72,.12);border:1px solid rgba(225,29,72,.42);border-radius:14px;padding:12px 14px;margin:12px 0}}
 .tp-link-row{{display:flex;gap:8px;align-items:center;margin:8px 0 12px}}
 .tp-link-row input{{margin:0;flex:1;padding-left:38px}}
 .tp-paste-btn{{width:auto;margin:0;background:#15161d;border:1px solid #2a2c38;color:#e5e7eb;padding:12px 14px;border-radius:12px;white-space:nowrap}}
 .tp-guide{{background:rgba(127,29,29,.18);border:1px solid rgba(225,29,72,.35);border-radius:16px;padding:14px;margin:12px 0}}
 .tp-step{{display:flex;gap:10px;align-items:flex-start;margin:10px 0;font-size:13px;color:#d1d5db;line-height:1.5}}
 .tp-num{{width:22px;height:22px;border-radius:50%;background:rgba(225,29,72,.22);border:1px solid rgba(225,29,72,.5);color:#ff4d6d;font-size:11px;font-weight:bold;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}}
 .tp-bank-box{{background:#101116;border:1px solid #222430;border-radius:16px;overflow:hidden;margin:12px 0}}
 .tp-bank-row{{display:flex;justify-content:space-between;align-items:center;padding:13px 14px;border-bottom:1px solid #1b1d27;font-size:14px;gap:8px}}
 .tp-bank-row:last-child{{border-bottom:none}}
 .tp-drop{{display:block;border:1px dashed #2e303d;background:#0e0f14;border-radius:16px;padding:22px 14px;text-align:center;cursor:pointer;margin:12px 0}}
 .tp-amber{{background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.35);color:#fbbf24;border-radius:12px;padding:11px 14px;font-size:13px;display:flex;align-items:center;gap:8px;margin:12px 0}}
 .tp-foot{{display:grid;grid-template-columns:1fr 1.5fr;gap:10px;margin-top:14px}}
 .tp-cancel{{background:#121318;border:1px solid #252733;color:#e5e7eb;padding:13px;border-radius:14px;margin:0}}
 .tp-submit{{background:linear-gradient(90deg,#e11d48,#be123c);color:#fff;padding:13px;border-radius:14px;margin:0}}
 .zone-grid{{display:grid;grid-template-columns:1fr;gap:14px;margin:12px 0}}
 .zone-card{{background:#0e0e12;border-radius:18px;overflow:hidden;text-align:left;border:1px solid #221217}}
 .zone-card.active-zone{{border-color:#e11d48;box-shadow:0 0 0 1px rgba(225,29,72,.45)}}
 .zone-card img{{width:100%;height:auto;object-fit:contain;background:#000;display:block}}
 .zone-card .ztitle{{padding:12px 14px 2px;font-size:18px;font-weight:bold;color:#fff}}
 .zone-card .zsub{{padding:0 14px 14px;font-size:13px;color:#9ca3af}}
 .cat-sec-hdr{{display:flex;justify-content:space-between;align-items:baseline;margin:18px 0 8px;gap:8px}}
 .cat-sec-title{{font-size:18px;font-weight:900;color:#fff;line-height:1.3}}
 .cat-sec-title span{{color:#ff2a55}}
 .cat-all-link{{font-size:12px;color:#ff4d6d;white-space:nowrap;flex-shrink:0}}
 .prod-grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:6px 0 14px}}
 .prod-grid-card{{margin:0}}
 .prod-scroll{{display:flex;gap:12px;overflow-x:auto;padding:2px 0 10px;scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch}}
 .prod-slide{{width:185px;min-width:185px;max-width:185px;flex-shrink:0;scroll-snap-align:start;margin:0}}
 .qty-box{{display:inline-flex;align-items:center;background:#14151b;border:1px solid #262833;border-radius:12px;overflow:hidden;margin:6px 0}}
 .qty-btn{{width:38px;height:40px;margin:0;border-radius:0;background:#1a1b24;font-size:18px;padding:0}}
 .qty-inp{{width:58px;height:40px;margin:0;border:none;background:transparent;text-align:center;font-weight:bold;padding:0}}
 .live-total-box{{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(90deg,rgba(225,29,72,.16),rgba(18,8,12,.92));border:1px solid rgba(225,29,72,.45);border-radius:14px;padding:12px 14px;margin:10px 0}}
 .coupon-row{{display:flex;gap:8px;align-items:center;margin:8px 0}}
 .coupon-row input{{margin:0;flex:1}}
 .coupon-row button{{width:auto;margin:0;padding:12px 16px;white-space:nowrap}}
 .agent-box{{background:linear-gradient(135deg,rgba(127,29,29,.26),rgba(20,8,12,.92));border:1px solid rgba(225,29,72,.5);border-radius:14px;padding:12px 14px;margin:10px 0}}
 .agent-title{{display:flex;align-items:center;gap:8px;color:#ff4d6d;font-weight:bold;font-size:14px}}
 .agent-dot{{width:10px;height:10px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444;flex-shrink:0}}
 .agent-sub{{color:#d1d5db;font-size:12px;margin-top:4px;line-height:1.5}}
 .cf-card{{background:#0d0d11;border:1px solid #241217;border-radius:22px;padding:16px;margin:12px 0}}
 .cf-top{{display:flex;justify-content:space-between;align-items:center;padding-bottom:12px;border-bottom:1px solid #1d1e26}}
 .cf-close{{width:32px;height:32px;border-radius:50%;background:#181920;border:1px solid #2a2c37;color:#9ca3af;display:flex;align-items:center;justify-content:center;font-size:14px}}
 .cf-prod{{display:flex;align-items:center;gap:12px;background:#13141a;border:1px solid #222430;border-radius:16px;padding:12px;margin:14px 0}}
 .cf-pill{{display:inline-block;margin-top:6px;background:rgba(225,29,72,.18);border:1px solid rgba(225,29,72,.45);color:#ff4d6d;font-size:11px;font-weight:bold;padding:3px 10px;border-radius:8px;text-transform:uppercase}}
 .cf-tbl{{background:#121319;border:1px solid #20222d;border-radius:16px;overflow:hidden;margin:12px 0}}
 .cf-row{{display:flex;justify-content:space-between;align-items:center;padding:13px 14px;border-bottom:1px solid #1d1f29;font-size:14px}}
 .cf-row:last-child{{border-bottom:none}}
 .cf-total{{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(90deg,rgba(225,29,72,.18),rgba(120,12,32,.22));border:1px solid rgba(225,29,72,.45);border-radius:16px;padding:16px;margin:12px 0}}
 .cf-warn{{background:rgba(225,29,72,.08);border:1px solid rgba(225,29,72,.3);border-radius:14px;padding:12px 14px;color:#d1d5db;font-size:12px;line-height:1.5;margin:12px 0}}
 .cf-btns{{display:grid;grid-template-columns:1fr 1.6fr;gap:10px;margin-top:14px}}
 .tab-bar{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;background:#0d0d11;border:1px solid #1e1f26;border-radius:16px;padding:8px;margin:12px 0}}
 .tab-btn{{padding:10px 6px;text-align:center;border-radius:12px;font-size:13px;font-weight:bold;color:#a1a1aa;display:flex;flex-direction:column;align-items:center;gap:4px}}
 .tab-btn.active{{background:linear-gradient(180deg,#f43f5e,#be123c);color:#fff;box-shadow:0 4px 14px rgba(225,29,72,.35)}}
 .stat-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:14px 0}}
 .stat-card{{background:#0e0e12;border:1px solid #1e1f26;border-radius:16px;padding:14px}}
 .lnk-card{{display:flex;align-items:center;gap:14px;background:#0d0d11;border:1px solid #1f1619;border-radius:18px;padding:14px 16px;margin:10px 0;color:#fff}}
 .lnk-ico{{width:44px;height:44px;border-radius:13px;background:#16171e;border:1px solid #262834;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0}}
 .ag-panel{{background:#0c0c10;border:1px solid #241217;border-radius:22px;padding:18px;margin:12px 0}}
 .ag-stat-box{{display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#24080e,#12090c);border:1px solid rgba(225,29,72,.45);border-radius:16px;padding:16px;margin:14px 0}}
 .ag-prog-bg{{width:100%;height:7px;background:#1d1e26;border-radius:999px;overflow:hidden;margin:10px 0}}
 .ag-prog-fill{{height:100%;background:linear-gradient(90deg,#e11d48,#ff4d6d);border-radius:999px}}
 .ag-warn{{display:flex;align-items:center;gap:8px;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.35);color:#fbbf24;border-radius:12px;padding:11px 14px;font-size:13px;margin-top:12px}}
 .acc-tbl{{background:#0c0c10;border:1px solid #221217;border-radius:20px;padding:18px;margin:12px 0}}
 .acc-row{{display:flex;justify-content:space-between;align-items:center;padding:16px 4px;border-bottom:1px solid #191a22;gap:12px;font-size:14px}}
 .acc-row:last-child{{border-bottom:none;padding-bottom:4px}}
 .dc-card{{display:flex;justify-content:space-between;align-items:center;background:#0c0c10;border:1px solid #221217;border-radius:20px;padding:16px;margin:12px 0;gap:12px}}
 .dc-btn{{width:auto;margin:0;padding:10px 18px;background:#5865f2;color:#fff;border-radius:12px;font-size:13px;font-weight:bold;white-space:nowrap}}
 .pw-eye-wrap{{position:relative;margin:6px 0 12px}}
 .pw-eye-wrap input{{margin:0;padding-right:42px}}
 .pw-eye-ico{{position:absolute;right:12px;top:50%;transform:translateY(-50%);color:#9ca3af;cursor:pointer;font-size:16px;user-select:none}}
 .env-box{{background:#111218;border:1px solid #272936;border-radius:12px;padding:10px 12px;margin:8px 0;display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}}
 .copy-env-btn{{width:auto;margin:0;padding:7px 12px;background:#1b1d28;border:1px solid #323548;border-radius:10px;font-size:12px;color:#fff}}
 .ord-card{{background:#0c0c10;border:1px solid #221217;border-radius:20px;padding:14px;margin:12px 0}}
 .ord-top{{display:flex;align-items:center;gap:12px;padding-bottom:12px;border-bottom:1px solid #191a21}}
 .ord-thumb{{width:64px;height:64px;border-radius:14px;background:#15161d;border:1px solid #252733;display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0}}
 .ord-pill{{display:inline-block;margin-top:5px;background:rgba(225,29,72,.18);border:1px solid rgba(225,29,72,.45);color:#ff4d6d;font-size:11px;font-weight:bold;padding:3px 10px;border-radius:8px;text-transform:uppercase}}
 .ord-foot{{display:flex;justify-content:space-between;align-items:center;padding-top:12px;gap:10px}}
 .ord-btn{{width:auto;margin:0;padding:10px 16px;background:#121318;border:1px solid #252733;border-radius:12px;color:#e5e7eb;font-size:13px;font-weight:bold;white-space:nowrap}}
 .shop-foot{{margin-top:28px;padding:22px 16px;background:#09090c;border-top:1px solid #1a1014;border-radius:20px 20px 0 0}}
 .pay-row{{display:flex;align-items:center;gap:14px;background:#0e0e12;border:1px solid #1e1f26;border-radius:18px;padding:16px;margin:12px 0;color:#fff}}
 .pay-badge{{width:54px;height:54px;border-radius:16px;background:#16171d;border:1px solid #272934;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0}}
 .auth-card{{background:linear-gradient(180deg,#16070b,#0b0b0e);border:1px solid rgba(225,29,72,.35);border-radius:24px;padding:22px 18px;margin:18px 0}}
 .auth-tabs{{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid #22232b;margin:14px 0}}
 .auth-tab{{text-align:center;padding:10px;font-weight:bold;color:#9ca3af;border-bottom:2px solid transparent}}
 .auth-tab.active{{color:#fff;border-bottom-color:#e11d48}}
 .inp-wrap{{position:relative;margin:8px 0}}
 .inp-wrap input{{margin:0;padding-left:40px;padding-right:40px}}
 .inp-ico{{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:#9ca3af;font-size:15px;pointer-events:none}}
 .eye-btn{{position:absolute;right:12px;top:50%;transform:translateY(-50%);color:#9ca3af;cursor:pointer;font-size:15px;user-select:none}}
 .verify-box{{display:flex;justify-content:space-between;align-items:center;background:#13141a;border:1px solid #262834;border-radius:14px;padding:14px;margin:12px 0}}
 .variant-opt{{display:flex;justify-content:space-between;align-items:center;background:#14151b;border:1px solid #262833;border-radius:12px;padding:12px;margin:6px 0;cursor:pointer}}
 .variant-opt.active{{border-color:#e11d48;background:rgba(225,29,72,.08)}}
 .variant-opt.disabled{{opacity:.5;cursor:not-allowed}}
 .snowflake{{position:fixed;top:-20px;color:#fff;pointer-events:none;z-index:9999;text-shadow:0 0 8px #fff,0 0 12px #aee2ff;animation:fall linear forwards}}
 @keyframes fall{{to{{transform:translateY(110vh) rotate(360deg)}}}}
 </style></head><body>
 <div class='top-notice'><span>🔔 หากพบปัญหากรุณาติดต่อแอดมิน</span><span>🔔 ยินดีต้อนรับสู่ {sn}</span></div>
 <div class='top'>
  <div style='display:flex;align-items:center;gap:10px'>
   <span onclick="document.getElementById('side').classList.add('open');document.getElementById('ov').classList.add('show')" style='font-size:22px;cursor:pointer'>☰</span>
   <a href='/' style='display:flex;align-items:center;gap:8px;color:#fff'>{lh}<b style='font-size:17px'>{sn}</b></a>
  </div>
  <div style='display:flex;gap:12px;align-items:center'>{bell}{ub}</div>
 </div>
 <div class='sidebar' id='side'>
  <div style='display:flex;justify-content:space-between;align-items:center'>
   <div style='display:flex;align-items:center;gap:8px'>{lh}<b>{sn}</b></div>
   <span onclick="document.getElementById('side').classList.remove('open');document.getElementById('ov').classList.remove('show')" style='cursor:pointer;color:#9ca3af;font-size:18px'>✕</span>
  </div>
  {su}
  <a class='m-card active-red' href='/'><div class='m-ico'>🏪</div><div><div class='m-t'>ร้านค้า</div><div class='m-s'>ดูสินค้าทั้งหมด</div></div></a>
  <a class='m-card' href='/topup'><div class='m-ico'>💳</div><div><div class='m-t'>เติมเงิน</div><div class='m-s'>เพิ่มเครดิตเข้าบัญชี</div></div></a>
  <a class='m-card' href='/history'><div class='m-ico'>🕒</div><div><div class='m-t'>ประวัติการซื้อ</div><div class='m-s'>ดูออเดอร์ทั้งหมด</div></div></a>
  <a class='m-card' href='/profile?tab=topups'><div class='m-ico'>🧾</div><div><div class='m-t'>ประวัติการเติมเงิน</div><div class='m-s'>รายการเติมเงินทั้งหมด</div></div></a>
  <a class='m-card' href='/profile'><div class='m-ico'>👤</div><div><div class='m-t'>โปรไฟล์</div><div class='m-s'>บัญชีและรหัสผ่าน</div></div></a>
  {admin_menu}
  {'<a class="m-card" href="/logout" style="border-color:rgba(239,68,68,.3)"><div class="m-ico">↪️</div><div><div class="m-t" style="color:#ff5555">ออกจากระบบ</div><div class="m-s">ออกจากบัญชีของคุณ</div></div></a>' if u else ''}
 </div>
 <div class='overlay' id='ov' onclick="document.getElementById('side').classList.remove('open');this.classList.remove('show')"></div>
 <div class='how-modal' id='how_modal' onclick="if(event.target===this)this.classList.remove('show')">
  <div class='box' style='width:100%;max-width:460px;margin:0'>
   <div style='display:flex;justify-content:space-between;align-items:center'><h3 style='margin:0'>📖 วิธีการสั่งซื้อสินค้า</h3><span onclick="document.getElementById('how_modal').classList.remove('show')" style='cursor:pointer;color:#9ca3af;font-size:18px'>✕</span></div>
   <p style='color:#d1d5db;font-size:14px;line-height:1.7;margin:12px 0'>1. เข้าสู่ระบบหรือสมัครสมาชิก<br>2. ไปที่เมนู <b>เติมเงิน</b> เพื่อเพิ่มยอดเงินเข้าระบบ<br>3. เลือกสินค้าและตัวเลือกที่ต้องการ กด <b>ซื้อเลย</b> และกด <b>ยืนยันชำระเงิน</b><br>4. รับโค้ด/สินค้าได้ทันทีในหน้าสำเร็จและ <b>ประวัติการซื้อ</b></p>
   <button onclick="document.getElementById('how_modal').classList.remove('show')">เข้าใจแล้ว</button>
  </div>
 </div>
 <div class='how-modal' id='key_modal' onclick="if(event.target===this)this.classList.remove('show')">
  <div class='box' style='width:100%;max-width:440px;margin:0'>
   <div style='display:flex;justify-content:space-between;align-items:center'><h3 style='margin:0' id='km_title'>🔑 คีย์ใช้งาน</h3><span onclick="document.getElementById('key_modal').classList.remove('show')" style='cursor:pointer;color:#9ca3af;font-size:18px'>✕</span></div>
   <div style='color:#9ca3af;font-size:12px;margin-top:6px' id='km_meta'></div>
   <textarea id='km_codes' rows='4' readonly style='margin-top:10px'></textarea>
   <button onclick="navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('km_codes').value);this.innerText='✅ คัดลอกแล้ว'">📋 คัดลอกคีย์ทั้งหมด</button>
  </div>
 </div>
 <div style='max-width:900px;margin:0 auto;padding:0 12px 40px'>
  {maint_banner}{disc_bar}{body}
  <div class='shop-foot'>
   <div style='display:flex;align-items:center;gap:12px'>
    {lh}
    <div>
     <div style='font-weight:900;font-size:18px'>{sn}</div>
     <div style='font-size:12px;color:#22c55e;margin-top:2px'>● ONLINE</div>
    </div>
   </div>
   <div style='color:#9ca3af;font-size:13px;line-height:1.6;margin-top:10px'>ร้านค้าออนไลน์คุณภาพ สะดวก เติมเงินและจัดส่งรวดเร็ว</div>
  </div>
 </div>
 <script>
 function fmtMoney(n){{
  let num=Number(n)||0;
  return '฿'+num.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}});
 }}
 function updateProdTotal(){{
  let totEl=document.getElementById('live_total');
  let qtyEl=document.getElementById('qty_inp');
  if(!totEl||!qtyEl)return;
  let checked=document.querySelector('input[name="variant_id"]:checked');
  let unitPrice=checked ? parseFloat(checked.dataset.price||'0') : parseFloat(totEl.dataset.basePrice||'0');
  let maxStock=checked ? parseInt(checked.dataset.stock||'999999',10) : parseInt(totEl.dataset.baseStock||'999999',10);
  if(maxStock<1)maxStock=1;
  let q=parseInt(qtyEl.value,10);
  if(isNaN(q)||q<1)q=1;
  if(q>maxStock)q=maxStock;
  qtyEl.value=q;
  qtyEl.max=maxStock;
  totEl.innerText=fmtMoney(unitPrice*q);
 }}
 function setVar(el){{
  let inp=el.querySelector('input[name="variant_id"]');
  if(inp&&inp.disabled)return;
  document.querySelectorAll('.variant-opt').forEach(e=>e.classList.remove('active'));
  el.classList.add('active');
  if(inp)inp.checked=true;
  updateProdTotal();
 }}
 function chgQty(d){{
  let i=document.getElementById('qty_inp');
  if(!i)return;
  let v=(parseInt(i.value,10)||1)+d;
  if(v<1)v=1;
  i.value=v;
  updateProdTotal();
 }}
 function toggleEye(id){{let i=document.getElementById(id);if(i)i.type=(i.type==='password'?'text':'password');}}
 function openKeyModal(title,meta,codes){{document.getElementById('km_title').innerText='🔑 '+title;document.getElementById('km_meta').innerText=meta;document.getElementById('km_codes').value=codes||'ไม่มีข้อมูลคีย์';document.getElementById('key_modal').classList.add('show');}}
 function filterOrders(q){{q=(q||'').toLowerCase().trim();document.querySelectorAll('.ord-card').forEach(el=>{{el.style.display=(!q||el.dataset.search.includes(q))?'':'none';}});}}
 function copyText(txt,btn){{if(!txt)return;const done=()=>{{if(btn){{const old=btn.innerText;btn.innerText='✅ คัดลอกแล้ว';setTimeout(()=>btn.innerText=old,1500);}}}};if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(txt).then(done).catch(()=>{{fallbackCopy(txt);done();}});}}else{{fallbackCopy(txt);done();}}}}
 function fallbackCopy(txt){{const ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove();}}
 updateProdTotal();
 setInterval(()=>{{fetch('/api/unread').then(r=>r.json()).then(d=>{{let b=document.getElementById('bell-badge');if(!b)return;if(d.unread>0){{b.style.display='inline';b.innerText=d.unread;}}else{{b.style.display='none';}}}})}},15000);
 function makeSnow(){{let s=document.createElement('div');s.className='snowflake';s.innerText='❄';let size=Math.random()*14+8;s.style.left=Math.random()*100+'vw';s.style.fontSize=size+'px';s.style.opacity=(Math.random()*0.7+0.3).toFixed(2);s.style.animationDuration=(Math.random()*5+5)+'s';document.body.appendChild(s);setTimeout(()=>s.remove(),11000);}}
 setInterval(makeSnow,120);for(let i=0;i<30;i++)setTimeout(makeSnow,i*100);
 </script></body></html>"""
@app.route('/uploads/<path:f>')
def uploads(f):return send_from_directory(UPLOAD_FOLDER,f)
@app.route('/reset-admin-tim123')
def reset_admin():
 c=db();c.execute("INSERT OR REPLACE INTO users(username,email,password,coin,role,last_login,date) VALUES(?,?,?,999999,'owner',?,?)",(ADMIN_USER,"",ADMIN_PASS,str(datetime.datetime.now()),str(datetime.datetime.now())));c.execute("UPDATE users SET role='user' WHERE username!=? AND role IN ('admin','owner')",(ADMIN_USER,));c.commit();c.close();return f"รีเซ็ตแล้ว! ชื่อ: {ADMIN_USER} รหัส: {ADMIN_PASS} <a href='/login'>ไปล็อกอิน</a>"
@app.route('/')
def index():
 c=db();u=cur();ag=active_agent(c,u);st=stg();zones=c.execute("SELECT * FROM zones ORDER BY order_num, id").fetchall();cats=c.execute("SELECT * FROM categories ORDER BY order_num, id").fetchall();bn=sf(st,'banner','');sn=sf(st,'shop_name','timstore')
 u_cnt=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
 p_cnt=c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
 o_cnt=c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
 o_sum=c.execute("SELECT COALESCE(SUM(qty),0) FROM orders").fetchone()[0]
 stk_sum=0
 for r in c.execute("SELECT stock FROM products").fetchall():
  stk_sum+=len([x for x in sf(r,'stock','').split(NL) if x.strip()])
 for r in c.execute("SELECT stock FROM variants").fetchall():
  stk_sum+=len([x for x in sf(r,'stock','').split(NL) if x.strip()])
 b=f"""
 <div class='hero-box'>
  <div class='hero-pill'>⚡ {sn}</div>
  <h1 class='hero-title'>ยินดีต้อนรับสู่ร้าน {sn}</h1>
  <p class='hero-sub'>ร้านจำหน่ายสินค้าและบริการดิจิทัล 24 ชั่วโมง</p>
  <p class='hero-sub'>สินค้าราคาถูกแอดมินบริการดีที่ {sn} เท่านั้น</p>
  <div class='hero-btns'>
   <a href='#shop_content' class='btn-hero-red'>🔒 เริ่มต้นใช้งาน</a>
   <a href='javascript:void(0)' onclick="document.getElementById('how_modal').classList.add('show')" class='btn-hero-dark'>วิธีการสั่งซื้อ &rarr;</a>
  </div>
 </div>
 """
 if bn:
  b+=f"<img src='/uploads/{bn}' style='width:100%;border-radius:18px;margin:14px 0;height:auto;object-fit:contain;display:block;background:#000'>"
 b+=f"""
 <div class='stat-grid'>
  <div class='stat-card-tl'><div class='stat-ico-tl'>👥</div><div style='min-width:0;flex:1'><div class='stat-lbl-tl'>ผู้ใช้งาน</div><div class='stat-val-tl'>{u_cnt:,} <span class='stat-unit-tl'>คน</span></div></div></div>
  <div class='stat-card-tl'><div class='stat-ico-tl'>🛍️</div><div style='min-width:0;flex:1'><div class='stat-lbl-tl'>สินค้า</div><div class='stat-val-tl'>{p_cnt:,} <span class='stat-unit-tl'>รายการ</span></div></div></div>
  <div class='stat-card-tl'><div class='stat-ico-tl'>📦</div><div style='min-width:0;flex:1'><div class='stat-lbl-tl'>คลังสินค้า</div><div class='stat-val-tl'>{stk_sum:,} <span class='stat-unit-tl'>ชิ้น</span></div></div></div>
  <div class='stat-card-tl'><div class='stat-ico-tl'>✅</div><div style='min-width:0;flex:1'><div class='stat-lbl-tl'>ขายแล้ว</div><div class='stat-val-tl'>{(o_sum if o_sum else o_cnt):,} <span class='stat-unit-tl'>ชิ้น</span></div></div></div>
 </div>
 <h3 style='margin:20px 0 8px'>ทำไมต้องเลือก <span style='color:#ff2a55'>{sn}</span></h3>
 <div class='box' style='display:flex;gap:12px;align-items:flex-start'><div class='pay-badge'>🛡️</div><div><div style='font-weight:bold;font-size:16px'>ปลอดภัย รวดเร็ว</div><div style='color:#9ca3af;font-size:13px;margin-top:4px'>ใส่ใจในคุณภาพของสินค้าและบริการ ด้วยระบบรักษาความปลอดภัยที่ทันสมัย พร้อมบริการรวดเร็วตลอด 24 ชั่วโมง</div></div></div>
 <div id='shop_content'></div>
 """
 zid=request.args.get('zone','');cid=request.args.get('cat','')
 if zones:
  b+="<div class='cat-sec-hdr'><div class='cat-sec-title'>โซน<span>สินค้า</span></div>"
  if zid:b+="<a href='/' class='cat-all-link'>แสดงทุกโซน &rarr;</a>"
  b+="</div><div class='zone-grid'>"
  for z in zones:
   im=sf(z,'img','');ic=sf(z,'icon','🔥')
   ih=f"<img src='/uploads/{im}' style='width:100%;height:auto;object-fit:contain;background:#000;display:block'>" if im else f"<div style='height:120px;background:#14151b;display:flex;align-items:center;justify-content:center;font-size:36px'>{ic}</div>"
   act_cls=" active-zone" if str(z['id'])==str(zid) else ""
   cq=f"&cat={cid}" if cid else ""
   b+=f"<a href='/?zone={z['id']}{cq}#shop_content'><div class='zone-card{act_cls}'>{ih}<div class='ztitle'>{ic} {z['name']}</div><div class='zsub'>รวมสินค้าและบริการยอดนิยมสำหรับคุณ</div></div></a>"
  b+="</div>"
 if zid or cid:
  if zid and cid:prods=c.execute("SELECT * FROM products WHERE zone_id=? AND category_id=? ORDER BY id DESC",(zid,cid)).fetchall()
  elif zid:prods=c.execute("SELECT * FROM products WHERE zone_id=? ORDER BY id DESC",(zid,)).fetchall()
  else:prods=c.execute("SELECT * FROM products WHERE category_id=? ORDER BY id DESC",(cid,)).fetchall()
  b+="<div class='cat-sec-hdr'><div class='cat-sec-title'>สินค้าที่<span>เลือก</span></div><a href='/' class='cat-all-link'>ดูทั้งหมด &rarr;</a></div><div class='prod-grid-2'>"
  for p in prods:b+=render_prod_card(c,p,slide=False,ag=ag)
  if not prods:b+="<div class='box' style='grid-column:1/-1;color:#9ca3af'>ยังไม่มีสินค้าในหมวด/โซนนี้</div>"
  b+="</div>"
 else:
  for ct in cats:
   cprods=c.execute("SELECT * FROM products WHERE category_id=? ORDER BY id DESC",(ct['id'],)).fetchall()
   if not cprods:continue
   b+=f"<div class='cat-sec-hdr'><div class='cat-sec-title'>หมวดหมู่ : <span>{ct['name']}</span></div><a href='/?cat={ct['id']}#shop_content' class='cat-all-link'>ดูทั้งหมด &rarr;</a></div><div class='prod-grid-2'>"
   for p in cprods:b+=render_prod_card(c,p,slide=False,ag=ag)
   b+="</div>"
  un_prods=c.execute("SELECT * FROM products WHERE category_id=0 OR category_id IS NULL ORDER BY id DESC").fetchall()
  if un_prods:
   b+="<div class='cat-sec-hdr'><div class='cat-sec-title'>หมวดหมู่ : <span>สินค้าทั้งหมด</span></div><a href='/' class='cat-all-link'>ดูทั้งหมด &rarr;</a></div><div class='prod-grid-2'>"
   for p in un_prods:b+=render_prod_card(c,p,slide=False,ag=ag)
   b+="</div>"
 c.close();return base(b)
@app.route('/product/<int:pid>',methods=['GET','POST'])
def product(pid):
 c=db();u=cur();ag=active_agent(c,u);p=c.execute("SELECT * FROM products WHERE id=?",(pid,)).fetchone()
 if not p:c.close();return "ไม่เจอสินค้า"
 p_img_fn=sf(p,'img','')
 if request.method=='POST':
  if not u:c.close();return redirect('/login')
  vid=request.form.get('variant_id','');qty=int(float(request.form.get('qty',1) or 1));ccode="" if ag else request.form.get('coupon_code','').strip().upper();step=request.form.get('step','confirm')
  if qty<1:qty=1
  if vid:
   v=c.execute("SELECT * FROM variants WHERE id=?",(vid,)).fetchone()
   if not v:c.close();return base("<div class='box'>❌ ไม่เจอช่องนี้</div>")
   upr=resolve_item_price(v,v['price'],ag);vlabel=v['name'];unm=f"{p['name']} - {v['name']}";stk=[x for x in sf(v,'stock','').split(NL) if x.strip()]
  else:upr=resolve_item_price(p,p['price'],ag);vlabel="มาตรฐาน";unm=p['name'];stk=[x for x in sf(p,'stock','').split(NL) if x.strip()]
  total=upr*qty;disc=0
  if ccode and not ag:
   cp=c.execute("SELECT * FROM coupons WHERE code=? AND active=1",(ccode,)).fetchone()
   if not cp:c.close();return base("<div class='box'>❌ โค้ดไม่ถูก</div>")
   if cp['max_use']>0 and cp['used']>=cp['max_use']:c.close();return base("<div class='box'>❌ โค้ดหมดแล้ว</div>")
   disc=total*cp['value']/100 if cp['type']=='percent' else cp['value'];total=max(0,total-disc)
  if len(stk)<qty:c.close();return base("<div class='box'>❌ ของหมด</div>")
  if step!='pay':
   st=stg();sn=sf(st,'shop_name','timstore');lg=sf(st,'logo','')
   lh=f"<img src='/uploads/{lg}' style='width:42px;height:42px;border-radius:12px;object-fit:cover;border:1px solid rgba(225,29,72,.5)'>" if lg else "<div style='width:42px;height:42px;border-radius:12px;background:#1c070c;border:1px solid #e11d48;display:flex;align-items:center;justify-content:center;font-weight:900;color:#ff2a55'>TS</div>"
   cat_row=c.execute("SELECT name FROM categories WHERE id=?",(sf(p,'category_id',0),)).fetchone()
   cat_nm=cat_row['name'] if cat_row else "สินค้าทั่วไป"
   pih=f"<img src='/uploads/{p_img_fn}' style='width:62px;height:62px;border-radius:12px;object-fit:cover;background:#000'>" if p_img_fn else "<div style='width:62px;height:62px;border-radius:12px;background:#1b1c24;display:flex;align-items:center;justify-content:center;font-size:24px'>📦</div>"
   disc_row=f"<div class='cf-row'><span style='color:#9ca3af'>ส่วนลด ({ccode})</span><b style='color:#22c55e'>-฿{float(disc):.2f}</b></div>" if disc>0 else ""
   ag_cf="<div class='agent-box'><div class='agent-title'><span class='agent-dot'></span><span>คุณได้รับราคาตัวแทนจำหน่ายแล้ว</span></div><div class='agent-sub'>(ระบบล็อกราคาพิเศษแล้ว ไม่สามารถใช้คูปองร่วมได้)</div></div>" if ag else ""
   c.close()
   return base(f"""
   <div class='cf-card'>
    <div class='cf-top'>
     <div style='display:flex;align-items:center;gap:10px'>
      {lh}
      <div>
       <div style='font-weight:900;font-size:17px'>{sn}</div>
       <div style='font-size:11px;color:#9ca3af'>ยืนยันคำสั่งซื้อ · ตรวจสอบข้อมูลก่อนชำระเงิน</div>
      </div>
     </div>
     <a href='/product/{pid}' class='cf-close'>✕</a>
    </div>
    <div class='cf-prod'>
     {pih}
     <div style='min-width:0;flex:1'>
      <div style='font-weight:900;font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{p['name']}</div>
      <span class='cf-pill'>{vlabel}</span>
     </div>
    </div>
    {ag_cf}
    <div style='font-size:12px;color:#9ca3af;margin:8px 0 4px'>สรุปรายละเอียด</div>
    <div class='cf-tbl'>
     <div class='cf-row'><span style='color:#9ca3af'>หมวดหมู่</span><b>{cat_nm}</b></div>
     <div class='cf-row'><span style='color:#9ca3af'>ตัวเลือก</span><b>{vlabel}</b></div>
     <div class='cf-row'><span style='color:#9ca3af'>ราคาต่อชิ้น</span><b>฿{float(upr):.2f}</b></div>
     <div class='cf-row'><span style='color:#9ca3af'>จำนวนสั่งซื้อ</span><b>{qty} ชิ้น</b></div>
     {disc_row}
    </div>
    <div class='cf-total'>
     <span style='font-weight:bold;color:#e5e7eb'>ยอดชำระเงินทั้งหมด</span>
     <b style='font-size:24px;font-weight:900;color:#ff2a55'>฿{float(total):.2f}</b>
    </div>
    <div class='cf-warn'>⚠️ โปรดตรวจสอบข้อมูลสินค้าให้ถูกต้องก่อนกดยืนยันคำสั่งซื้อ เมื่อทำรายการสำเร็จแล้วไม่สามารถเปลี่ยนคืนได้</div>
    <form method='post'>
     <input type='hidden' name='step' value='pay'>
     <input type='hidden' name='variant_id' value='{vid}'>
     <input type='hidden' name='qty' value='{qty}'>
     <input type='hidden' name='coupon_code' value='{ccode}'>
     <div class='cf-btns'>
      <a href='/product/{pid}' style='display:block;text-align:center;background:#16171f;border:1px solid #282a36;color:#fff;padding:13px;border-radius:12px;font-weight:bold'>ยกเลิก</a>
      <button style='margin:0;background:linear-gradient(90deg,#e11d48,#b91c1c);padding:13px'>🛒 ยืนยันชำระเงิน</button>
     </div>
    </form>
   </div>
   """)
  if u['coin']<total:c.close();return base("<div class='box'>❌ coin ไม่พอ <a href='/topup'>เติมเงิน</a></div>")
  codes=stk[:qty];rest=NL.join(stk[qty:])
  c.execute("UPDATE users SET coin=coin-? WHERE id=?",(total,u['id']))
  if vid:c.execute("UPDATE variants SET stock=? WHERE id=?",(rest,vid))
  else:c.execute("UPDATE products SET stock=? WHERE id=?",(rest,pid))
  if ccode and not ag:c.execute("UPDATE coupons SET used=used+1 WHERE code=?",(ccode,))
  c.execute("INSERT INTO orders(username,product_name,product_img,qty,total,codes,date) VALUES(?,?,?,?,?,?,?)",(u['username'],unm,p_img_fn,qty,total,NL.join(codes),str(datetime.datetime.now())));c.commit();c.close()
  noti('order',u['username'],total,f"🛒 ซื้อ! {unm} x{qty}",f"ยอด {int(total)} ลด {int(disc)}")
  return base(f"<div class='box'><h2>✅ ซื้อสำเร็จ!</h2><p>จ่าย {int(total)} บาท (ลด {int(disc)})</p><textarea>{NL.join(codes)}</textarea><a href='/history'><button>ดูประวัติ</button></a></div>")
 vs=c.execute("SELECT * FROM variants WHERE product_id=?",(pid,)).fetchall()
 sold_cnt=prod_sold_count(c,p['name'])
 ih=f"<img src='/uploads/{p_img_fn}' style='width:100%;border-radius:12px;height:auto;object-fit:contain;display:block;background:#000'>" if p_img_fn else ""
 vh=""
 first_price=0.0
 first_stock=1
 if vs:
  picked_first=False
  for v in vs:
   left=len([x for x in sf(v,'stock','').split(NL) if x.strip()])
   is_v_out=(left<=0)
   ch=""
   act_cls=""
   if not is_v_out and not picked_first:
    ch="checked";act_cls=" active";picked_first=True
    first_price=resolve_item_price(v,v['price'],ag)
    first_stock=left
   np=resolve_item_price(v,v['price'],ag);old=f"<span style='text-decoration:line-through;color:#888'>฿{fp(v['price'])}</span> " if np!=float(v['price']) else ""
   vap=item_agent_price(v,v['price']) if ag else None
   v_ag_tag=f" <span style='background:#0d2620;color:#34d399;border:1px solid #195c4c;font-size:11px;padding:1px 7px;border-radius:999px'>ตัวแทน ฿{fp(vap)}</span>" if vap is not None else ""
   rem_txt="<span style='color:#ef4444;font-size:12px;font-weight:bold'>หมด</span>" if is_v_out else f"<span style='color:#9ca3af;font-size:12px'>รับสินค้าทันที · เหลือ {left} ชิ้น</span>"
   dis_attr="disabled" if is_v_out else ""
   dis_cls=" disabled" if is_v_out else ""
   vh+=f"<label class='variant-opt{act_cls}{dis_cls}' onclick='setVar(this)'><span><input type='radio' name='variant_id' value='{v['id']}' data-price='{np}' data-stock='{left}' {ch} {dis_attr} onchange='updateProdTotal()' style='width:auto'> <b>{v['name']}</b><br>{rem_txt}{v_ag_tag}</span><b style='color:#ff4d6d'>{old}฿{float(np):.2f}</b></label>"
  if not picked_first:
   first_price=resolve_item_price(vs[0],vs[0]['price'],ag)
   first_stock=1
 else:
  left=len([x for x in sf(p,'stock','').split(NL) if x.strip()])
  first_stock=max(1,left)
  np=resolve_item_price(p,p['price'],ag);first_price=np
  old=f"<span style='text-decoration:line-through;color:#888'>฿{fp(p['price'])}</span> " if np!=float(p['price']) else ""
  pap=item_agent_price(p,p['price']) if ag else None
  p_ag_tag=f" <span style='background:#0d2620;color:#34d399;border:1px solid #195c4c;font-size:12px;padding:2px 8px;border-radius:999px;margin-left:6px'>ตัวแทน ฿{fp(pap)}</span>" if pap is not None else ""
  vh=f"<p style='margin:6px 0'>ราคาต่อชิ้น: {old}<b style='color:#ff4d6d;font-size:18px'>฿{float(np):.2f}</b> <span style='color:#9ca3af;font-size:12px'>· คงเหลือ {left} ชิ้น</span>{p_ag_tag}</p>"
 if ag:
  side_ctl="<div class='agent-box'><div class='agent-title'><span class='agent-dot'></span><span>คุณได้รับราคาตัวแทนจำหน่ายแล้ว</span></div><div class='agent-sub'>(ระบบล็อกราคาพิเศษแล้ว ไม่สามารถใช้คูปองร่วมได้)</div></div>"
 else:
  side_ctl="<div style='flex:1;min-width:190px'><div style='font-size:12px;color:#9ca3af'>🎟️ โค้ดส่วนลด</div><div class='coupon-row'><input name='coupon_code' placeholder='โค้ดส่วนลด (ถ้ามี)'><button type='button' onclick=\"this.previousElementSibling.focus()\" style='background:#1a1b24;border:1px solid #2b2d3a'>ใช้โค้ด</button></div></div>"
 c.close();return base(f"""
 <div class='box'>{ih}
  <div style='display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:12px;flex-wrap:wrap'>
   <h2 style='margin:0'>{p['name']}</h2>
   <span style='background:rgba(225,29,72,.16);border:1px solid rgba(225,29,72,.45);color:#ff6b86;font-size:12px;font-weight:bold;padding:4px 10px;border-radius:999px'>🔥 ขายแล้ว {sold_cnt:,} ชิ้น</span>
  </div>
  <div style='margin-top:8px'>{vh}</div>
  <form method='post'>
   <input type='hidden' name='step' value='confirm'>
   <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap'>
    <div><div style='font-size:12px;color:#9ca3af'>จำนวน</div><div class='qty-box'><button type='button' class='qty-btn' onclick='chgQty(-1)'>-</button><input id='qty_inp' class='qty-inp' type='number' name='qty' value='1' min='1' max='{first_stock}' oninput='updateProdTotal()'><button type='button' class='qty-btn' onclick='chgQty(1)'>+</button></div></div>
    {side_ctl}
   </div>
   <div class='live-total-box'>
    <div>
     <div style='font-size:12px;color:#d1d5db'>ยอดรวมตามจำนวนที่เลือก</div>
     <div style='font-size:11px;color:#9ca3af'>คำนวณอัตโนมัติตามราคาตัวเลือก × จำนวน</div>
    </div>
    <b id='live_total' data-base-price='{first_price}' data-base-stock='{first_stock}' style='font-size:22px;font-weight:900;color:#ff2a55'>฿{float(first_price):.2f}</b>
   </div>
   <button style='background:linear-gradient(90deg,#e11d48,#b91c1c);padding:13px'>🛒 ซื้อเลย &rarr;</button>
   <div style='display:flex;justify-content:center;gap:14px;font-size:11px;color:#9ca3af;margin-top:8px'><span>🔒 ชำระเงินปลอดภัย</span><span>⚡ ส่งทันทีหลังสั่งซื้อ</span></div>
  </form>
 </div>
 <div class='box'><h3 style='margin-top:0'>☰ รายละเอียด</h3><p style='color:#d1d5db;white-space:pre-line;line-height:1.6;margin:0'>{sf(p,'desc','ไม่มีรายละเอียดเพิ่มเติม')}</p></div>
 """)
def auth_shell(mode,sn,lg,err_msg=""):
 lh=f"<img src='/uploads/{lg}' style='width:68px;height:68px;border-radius:18px;object-fit:cover;display:block;margin:0 auto 10px;border:1px solid rgba(225,29,72,.5)'>" if lg else "<div style='width:68px;height:68px;border-radius:18px;background:#1c070c;border:1px solid #e11d48;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:24px;color:#ff2a55;margin:0 auto 10px'>TS</div>"
 err_html=f"<div style='background:rgba(239,68,68,.16);border:1px solid #ef4444;color:#ff7b8a;padding:10px 12px;border-radius:12px;margin-bottom:12px;font-size:13px'>{err_msg}</div>" if err_msg else ""
 t_in="active" if mode=="login" else "";t_up="active" if mode=="register" else ""
 if mode=="register":
  form_html="""
  <form method='post' enctype='multipart/form-data'>
   <div class='inp-wrap'><span class='inp-ico'>👤</span><input name='username' placeholder='ชื่อผู้ใช้ (อย่างน้อย 4 ตัว)' required></div>
   <div class='inp-wrap'><span class='inp-ico'>✉️</span><input name='email' type='email' placeholder='อีเมล (ไม่บังคับ)'></div>
   <div class='inp-wrap'><span class='inp-ico'>🔒</span><input id='reg_pw' name='password' type='password' placeholder='รหัสผ่าน (อย่างน้อย 4 ตัว)' required><span class='eye-btn' onclick="toggleEye('reg_pw')">👁</span></div>
   <div class='inp-wrap'><span class='inp-ico'>🔒</span><input id='reg_pw2' name='password2' type='password' placeholder='ยืนยันรหัสผ่าน' required><span class='eye-btn' onclick="toggleEye('reg_pw2')">👁</span></div>
   <div class='verify-box'>
    <div style='display:flex;align-items:center;gap:10px'>
     <input type='checkbox' id='chk_human' required style='width:18px;height:18px;margin:0'>
     <label for='chk_human' style='font-size:13px;color:#e5e7eb;cursor:pointer'>ยืนยันตัวตนก่อนสมัครสมาชิก</label>
    </div>
    <div style='text-align:right;font-size:10px;color:#9ca3af'><b style='color:#f59e0b;font-size:11px'>VERIFY</b><br>ความเป็นส่วนตัว · ช่วยเหลือ</div>
   </div>
   <button>สมัครสมาชิก →</button>
  </form>
  """
  title_txt="สร้างบัญชีใหม่";sub_txt=f"เริ่มต้นใช้งาน {sn}";badge_txt="สมัครสมาชิก"
 else:
  form_html="""
  <form method='post'>
   <div class='inp-wrap'><span class='inp-ico'>👤</span><input name='username' placeholder='ชื่อผู้ใช้หรืออีเมล' required></div>
   <div class='inp-wrap'><span class='inp-ico'>🔒</span><input id='log_pw' name='password' type='password' placeholder='รหัสผ่าน' required><span class='eye-btn' onclick="toggleEye('log_pw')">👁</span></div>
   <div class='verify-box'>
    <div style='display:flex;align-items:center;gap:10px'>
     <input type='checkbox' id='chk_login' required style='width:18px;height:18px;margin:0'>
     <label for='chk_login' style='font-size:13px;color:#e5e7eb;cursor:pointer'>ยืนยันตัวตนก่อนเข้าสู่ระบบ</label>
    </div>
    <div style='text-align:right;font-size:10px;color:#9ca3af'><b style='color:#f59e0b;font-size:11px'>VERIFY</b><br>ความเป็นส่วนตัว · ช่วยเหลือ</div>
   </div>
   <button>เข้าสู่ระบบ →</button>
  </form>
  """
  title_txt="ยินดีต้อนรับกลับมา";sub_txt=f"ลงชื่อเข้าใช้ {sn}";badge_txt="เข้าสู่ระบบ"
 return base(f"""
 <div class='auth-card'>
  <div style='text-align:right'><a href='/' style='color:#9ca3af;font-size:18px'>✕</a></div>
  {lh}
  <div style='text-align:center;color:#ff4d6d;font-size:12px;font-weight:bold'>{badge_txt}</div>
  <h2 style='text-align:center;margin:6px 0 4px;font-size:24px'>{title_txt}</h2>
  <div style='text-align:center;color:#9ca3af;font-size:13px'>{sub_txt}</div>
  <div class='auth-tabs'>
   <a href='/login' class='auth-tab {t_in}'>เข้าสู่ระบบ</a>
   <a href='/register' class='auth-tab {t_up}'>สมัครสมาชิก</a>
  </div>
  {err_html}
  {form_html}
 </div>
 """)
@app.route('/register',methods=['GET','POST'])
def register():
 st=stg();lg=sf(st,'logo','');sn=sf(st,'shop_name','timstore')
 if request.method=='POST':
  un=request.form.get('username','').strip();em=request.form.get('email','').strip();pw=request.form.get('password','').strip();pw2=request.form.get('password2','').strip()
  if not un or not pw:return auth_shell("register",sn,lg,"❌ กรุณากรอกข้อมูลให้ครบ")
  if ' ' in un or len(un)<4:return auth_shell("register",sn,lg,"❌ ชื่อผู้ใช้ต้องอย่างน้อย 4 ตัวอักษรและห้ามมีช่องว่าง")
  if len(pw)<4:return auth_shell("register",sn,lg,"❌ รหัสผ่านต้องอย่างน้อย 4 ตัวอักษร")
  if pw!=pw2:return auth_shell("register",sn,lg,"❌ รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
  c=db()
  if c.execute("SELECT * FROM users WHERE username=?",(un,)).fetchone():c.close();return auth_shell("register",sn,lg,f"❌ ชื่อผู้ใช้ {un} มีอยู่ในระบบแล้ว")
  now_s=str(datetime.datetime.now())
  cur_=c.execute("INSERT INTO users(username,email,password,coin,role,avatar,last_login,date) VALUES(?,?,?,0,'user','',?,?)",(un,em,pw,now_s,now_s));c.commit();uid=cur_.lastrowid;c.close();noti('register',un,0,f"👤 สมัครใหม่! {un}",f"อีเมล: {em or '-'}");session.permanent=True;session['uid']=uid
  return base(f"<div class='box' style='text-align:center'><h2>✅ สมัครสำเร็จ!</h2><p>ยินดีต้อนรับ <b>{un}</b></p><a href='/'><button>เข้าเว็บเลย</button></a></div>")
 return auth_shell("register",sn,lg)
@app.route('/login',methods=['GET','POST'])
def login():
 st=stg();lg=sf(st,'logo','');sn=sf(st,'shop_name','timstore')
 if request.method=='POST':
  ident=request.form.get('username','').strip();pw=request.form.get('password','').strip()
  c=db();u=c.execute("SELECT * FROM users WHERE (username=? OR (email!='' AND email=?)) AND password=?",(ident,ident,pw)).fetchone()
  if u:
   c.execute("UPDATE users SET last_login=? WHERE id=?",(str(datetime.datetime.now()),u['id']));c.commit();c.close()
   session.permanent=True;session['uid']=u['id'];return redirect('/')
  c.close()
  return auth_shell("login",sn,lg,"❌ ชื่อผู้ใช้ อีเมล หรือรหัสผ่านไม่ถูกต้อง")
 return auth_shell("login",sn,lg)
@app.route('/logout')
def logout():session.pop('uid',None);return redirect('/')
@app.route('/topup',methods=['GET','POST'])
def topup_page():
 u=cur()
 if not u:return redirect('/login')
 c=db()
 if request.method=='POST':
  act=request.form.get('act','topup')
  if act=='redeem_code':
   code=request.form.get('code','').strip()
   cc=c.execute("SELECT * FROM credit_codes WHERE code=? AND used=0",(code,)).fetchone()
   if cc:
    c.execute("UPDATE users SET coin=coin+? WHERE id=?",(cc['amount'],u['id']))
    c.execute("UPDATE credit_codes SET used=1, used_by=? WHERE code=?",(u['username'],code))
    c.commit();c.close()
    noti('credit',u['username'],cc['amount'],f"🎫 กรอกโค้ดฟรี {code}",f"ได้ {int(cc['amount'])} บาท")
    return base(f"<div class='box' style='text-align:center'><h2>✅ รับเครดิตสำเร็จ!</h2><p>ได้รับเงินฟรี <b>฿{float(cc['amount']):.2f}</b> เข้าบัญชีแล้ว</p><a href='/topup'><button>กลับหน้าเติมเงิน</button></a></div>")
   cp=c.execute("SELECT * FROM coupons WHERE code=? AND active=1",(code.upper(),)).fetchone()
   if cp and (cp['max_use']==0 or cp['used']<cp['max_use']) and cp['type']=='baht':
    c.execute("UPDATE users SET coin=coin+? WHERE id=?",(cp['value'],u['id']))
    c.execute("UPDATE coupons SET used=used+1 WHERE id=?",(cp['id'],))
    c.commit();c.close()
    noti('credit',u['username'],cp['value'],f"🎟️ ใช้โค้ด {cp['code']}",f"ได้ {int(cp['value'])} บาท")
    return base(f"<div class='box' style='text-align:center'><h2>✅ รับเครดิตสำเร็จ!</h2><p>ได้รับเงินฟรี <b>฿{float(cp['value']):.2f}</b> เข้าบัญชีแล้ว</p><a href='/topup'><button>กลับหน้าเติมเงิน</button></a></div>")
   c.close()
   return base("<div class='box' style='text-align:center'><h2>❌ โค้ดไม่ถูกต้องหรือถูกใช้งานไปแล้ว</h2><a href='/topup'><button>ลองใหม่อีกครั้ง</button></a></div>")
  if act=='envelope':
   env=request.form.get('envelope_link','').strip()
   amt=float(request.form.get('amount',0) or 0)
   if not is_valid_tm_envelope(env):
    c.close()
    return base("<div class='box' style='text-align:center'><h2>❌ ลิงก์ซองไม่ถูกต้อง</h2><p style='color:#9ca3af'>ต้องเป็นลิงก์ซองอั่งเปา TrueMoney (gift.truemoney.com) เท่านั้น เงินจะไม่ถูกเพิ่มเข้าระบบ</p><a href='/topup'><button>กลับหน้าเติมเงิน</button></a></div>")
   if amt<10:
    c.close()
    return base("<div class='box' style='text-align:center'><h2>❌ จำนวนเงินขั้นต่ำ 10 บาท</h2><a href='/topup'><button>กลับหน้าเติมเงิน</button></a></div>")
   if c.execute("SELECT 1 FROM topups WHERE envelope_link=?",(env,)).fetchone():
    c.close()
    return base("<div class='box' style='text-align:center'><h2>❌ ลิงก์ซองนี้ถูกใช้งานไปแล้ว</h2><a href='/topup'><button>กลับหน้าเติมเงิน</button></a></div>")
   net_amt=round(amt*(1-0.029),2)
   now_s=str(datetime.datetime.now())
   c.execute("UPDATE users SET coin=coin+? WHERE id=?",(net_amt,u['id']))
   c.execute("INSERT INTO topups(username,amount,method,slip,envelope_link,phone,status,date) VALUES(?,?,?,?,?,?, 'approved',?)",(u['username'],net_amt,'ซองอั่งเปา TrueMoney','',env,sf(stg(),'truemoney_phone',''),now_s))
   c.commit()
   renewed=check_auto_renew_agent(c,u['username'])
   c.close()
   noti('envelope',u['username'],net_amt,f"🎁 รับซองอัตโนมัติ! {u['username']} (+฿{net_amt:.2f} จาก ฿{amt:.2f})",env,"/notifications")
   if renewed:
    noti('agent',u['username'],7,f"🤝 ต่ออายุตัวแทนอัตโนมัติ +7 วัน! {u['username']}","ทำยอดครบ 50.00 ฿ ในรอบ 7 วัน")
   return base(f"<div class='box' style='text-align:center'><h2>✅ เติมเงินสำเร็จ!</h2><p>ยอดซอง <b>฿{amt:.2f}</b> (หัก 2.9% เข้าบัญชี <b>฿{net_amt:.2f}</b>)</p><a href='/topup'><button>กลับหน้าเติมเงิน</button></a></div>")
  amt=float(request.form.get('amount',0) or 0)
  slip_fn=up(request.files.get('slip'))
  if amt<=0 and slip_fn:amt=10
  if amt<=0:c.close();return base("<div class='box'>❌ ใส่จำนวนเงินหรือแนบสลิปก่อน</div><a href='/topup'><button>กลับ</button></a>")
  method=request.form.get('method','โอนผ่านธนาคาร')
  env_link=request.form.get('envelope_link','').strip()
  c.execute("INSERT INTO topups(username,amount,method,slip,envelope_link,phone,status,date) VALUES(?,?,?,?,?,?, 'pending',?)",(u['username'],amt,method,slip_fn,env_link,request.form.get('phone',''),str(datetime.datetime.now())))
  c.commit();c.close()
  detail_txt=env_link if env_link else "รอตรวจ"
  noti('envelope' if env_link else 'topup',u['username'],amt,f"💰 เติมเงิน {amt} ({method})",detail_txt,"/notifications")
  return base("<div class='box' style='text-align:center'><h2>✅ ยืนยันรายการเรียบร้อย!</h2><p style='color:#9ca3af'>ส่งข้อมูลให้แอดมินตรวจสอบแล้ว</p><a href='/topup'><button>กลับหน้าเติมเงิน</button></a></div>")
 st=c.execute("SELECT * FROM settings WHERE id=1").fetchone();c.close()
 bank_nm=sf(st,'bank_name','ธนาคารกสิกรไทย')
 acc_nm=sf(st,'bank_acc_name','แอดมิน timstore')
 acc_no=sf(st,'bank_acc_no','') or sf(st,'promptpay','ยังไม่ได้ตั้งค่าเลขบัญชี')
 tm_ph=sf(st,'truemoney_phone','-')
 paste_js="navigator.clipboard&&navigator.clipboard.readText().then(t=>{if(t)document.getElementById('env_inp').value=t}).catch(()=>document.getElementById('env_inp').focus())"
 copy_js="navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('copy_acc_txt').innerText)"
 return base(f"""
 <div style='text-align:center;margin:18px 0 14px'>
  <div style='font-size:28px;font-weight:900'>เติมเงิน<span style='color:#ff2a55'>เข้าระบบ</span></div>
  <div style='font-size:13px;color:#9ca3af;margin-top:6px'>เลือกช่องทางที่สะดวก · ยอดเข้าทันที · อัตโนมัติ 24 ชม.</div>
 </div>
 <a href='javascript:void(0)' onclick="document.getElementById('modal_bank').classList.add('show')" class='pay-row'><div class='pay-badge'>🧾</div><div style='flex:1'><div style='font-size:11px;color:#ff4d6d;letter-spacing:1px'>BANK TRANSFER</div><div style='font-size:18px;font-weight:bold'>โอนผ่านธนาคาร</div><div style='font-size:13px;color:#9ca3af'>พร้อมเพย์/บัญชี: {acc_no} · แนบสลิปตรวจสอบ</div></div><span style='color:#6b7280;font-size:20px'>></span></a>
 <a href='javascript:void(0)' onclick="document.getElementById('modal_tm').classList.add('show')" class='pay-row'><div class='pay-badge' style='background:#fff;color:#e11d48;font-weight:900'>TM</div><div style='flex:1'><div style='font-size:11px;color:#ff4d6d;letter-spacing:1px'>TRUEMONEY</div><div style='font-size:18px;font-weight:bold'>ซองอั่งเปา / ทรูมันนี่</div><div style='font-size:13px;color:#9ca3af'>เบอร์: {tm_ph} · วางลิงก์ซองของขวัญ</div></div><span style='color:#6b7280;font-size:20px'>></span></a>
 <a href='javascript:void(0)' onclick="document.getElementById('modal_code').classList.add('show')" class='pay-row'><div class='pay-badge'>🪙</div><div style='flex:1'><div style='font-size:11px;color:#ff4d6d;letter-spacing:1px'>REDEEM</div><div style='font-size:18px;font-weight:bold'>กรอกโค้ดฟรี</div><div style='font-size:13px;color:#9ca3af'>กรอกโค้ดเพื่อรับเงินฟรีทันที</div></div><span style='color:#6b7280;font-size:20px'>></span></a>
 <div class='box' style='border-color:rgba(225,29,72,.35);background:#12080b'>
  <div style='display:flex;align-items:center;gap:12px'>
   <div style='width:42px;height:42px;border-radius:12px;background:#240910;display:flex;align-items:center;justify-content:center;color:#ff4d6d;font-weight:bold'>⚠️</div>
   <div><div style='font-weight:bold;color:#ff6b86'>ไม่มีนโยบายคืนเงิน</div><div style='font-size:12px;color:#9ca3af'>ตรวจสอบยอดให้ถูกต้องก่อนเติม · ระบบไม่สามารถคืนเงินได้ทุกกรณี</div></div>
  </div>
 </div>
 <div class='how-modal' id='modal_tm' onclick="if(event.target===this)this.classList.remove('show')">
  <div class='tp-sheet'>
   <div class='tp-hdr'>
    <div style='display:flex;align-items:center;gap:12px'>
     <div class='tp-ico' style='background:#fff;color:#e11d48;font-weight:900'>TM</div>
     <div><div style='font-size:18px;font-weight:900'>ซองอั่งเปา TrueMoney</div><div style='font-size:12px;color:#9ca3af'>วางลิงก์ซองจาก TrueMoney Wallet</div></div>
    </div>
    <button type='button' class='tp-x' onclick="document.getElementById('modal_tm').classList.remove('show')">✕</button>
   </div>
   <form method='post'>
    <input type='hidden' name='act' value='envelope'>
    <div style='font-size:13px;color:#d1d5db;margin-top:12px'>จำนวนเงินในซอง (ขั้นต่ำ 10 บาท)</div>
    <input name='amount' type='number' step='0.01' min='10' placeholder='กรอกยอดเงินในซอง (เช่น 50)' required>
    <div style='font-size:13px;color:#d1d5db;margin-top:8px'>ลิงก์ซองของขวัญ</div>
    <div class='tp-warn'>
     <div style='font-weight:bold;color:#ff4d6d;font-size:13px'>&#9432; ช่องทางนี้มีค่าธรรมเนียม 2.9%</div>
     <div style='font-size:12px;color:#d1d5db;margin-top:3px'>ต้องเป็นลิงก์ซอง TrueMoney เท่านั้น · ยอดเงินจะถูกหัก 2.9% อัตโนมัติหลังเติมสำเร็จ</div>
    </div>
    <div class='tp-link-row'>
     <div style='position:relative;flex:1'>
      <span style='position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#9ca3af'>&#128279;</span>
      <input id='env_inp' name='envelope_link' placeholder='https://gift.truemoney.com/campaign/?v=...' required>
     </div>
     <button type='button' class='tp-paste-btn' onclick="{paste_js}">วาง</button>
    </div>
    <div class='tp-guide'>
     <div style='font-weight:bold;color:#ff4d6d;font-size:13px;margin-bottom:8px'>&#128205; วิธีเติมผ่านซองอั่งเปา</div>
     <div class='tp-step'><span class='tp-num'>1</span><span>เปิดแอป TrueMoney Wallet แล้วสร้างซองตามยอดที่ต้องการ</span></div>
     <div class='tp-step'><span class='tp-num'>2</span><span>กดแชร์ซอง &rarr; คัดลอกลิงก์ &rarr; กด <b>วาง</b> หรือวางในช่องด้านบน</span></div>
     <div class='tp-step'><span class='tp-num'>3</span><span>กรอกยอดเงินในซองแล้วกด <b>เติมเงิน</b> ยอดเข้าบัญชีทันที</span></div>
    </div>
    <div style='text-align:center;font-size:11px;color:#6b7280;margin:8px 0'>ลิงก์ใช้ได้ครั้งเดียว · ขั้นต่ำ 10 บาท</div>
    <div class='tp-foot'>
     <button type='button' class='tp-cancel' onclick="document.getElementById('modal_tm').classList.remove('show')">ยกเลิก</button>
     <button type='submit' class='tp-submit'>เติมเงิน &rarr;</button>
    </div>
   </form>
  </div>
 </div>
 <div class='how-modal' id='modal_bank' onclick="if(event.target===this)this.classList.remove('show')">
  <div class='tp-sheet'>
   <div class='tp-hdr'>
    <div style='display:flex;align-items:center;gap:12px'>
     <div class='tp-ico'>🧾</div>
     <div><div style='font-size:18px;font-weight:900'>โอนผ่านธนาคาร</div><div style='font-size:12px;color:#9ca3af'>โอนเงินแล้วอัปโหลดสลิปตรวจสอบ</div></div>
    </div>
    <button type='button' class='tp-x' onclick="document.getElementById('modal_bank').classList.remove('show')">✕</button>
   </div>
   <form method='post' enctype='multipart/form-data'>
    <input type='hidden' name='act' value='topup'>
    <input type='hidden' name='method' value='โอนผ่านธนาคาร'>
    <div class='tp-bank-box'>
     <div class='tp-bank-row'><span style='color:#9ca3af'>ชื่อบัญชี</span><b style='text-align:right'>{acc_nm}</b></div>
     <div class='tp-bank-row'><span style='color:#9ca3af'>เลขบัญชีธนาคาร</span><span style='display:flex;align-items:center;gap:8px'><b id='copy_acc_txt'>{acc_no}</b><button type='button' onclick="{copy_js}" style='width:auto;margin:0;padding:5px 8px;background:#1b1d27;border:1px solid #2d3040;border-radius:8px;font-size:12px'>&#128203;</button></span></div>
     <div class='tp-bank-row'><span style='color:#9ca3af'>ธนาคาร</span><b>{bank_nm}</b></div>
    </div>
    <input name='amount' type='number' step='0.01' placeholder='จำนวนเงินที่โอน (เช่น 100)' required>
    <label class='tp-drop' for='slip_file_inp'>
     <div style='font-size:24px;color:#9ca3af'>&#9729;&#65039;</div>
     <div id='slip_file_lbl' style='font-size:15px;font-weight:bold;color:#e5e7eb;margin-top:6px'>คลิกเพื่อเลือกไฟล์สลิป</div>
     <div style='font-size:11px;color:#6b7280;margin-top:4px'>JPG PNG WEBP · ให้เห็นข้อมูลชัดเจน</div>
     <input id='slip_file_inp' type='file' name='slip' accept='image/*' style='display:none' onchange="document.getElementById('slip_file_lbl').innerText=this.files[0]?this.files[0].name:'คลิกเพื่อเลือกไฟล์สลิป'">
    </label>
    <div style='font-size:12px;color:#9ca3af;line-height:1.65'>
     โอนเงินเข้าบัญชีด้านบนตามยอดที่ต้องการเติม<br>
     แคปสลิปจากแอปธนาคารให้เห็นยอดและวันที่ชัดเจน<br>
     อัปโหลดสลิปแล้วกด "ยืนยันสลิป" ส่งให้แอดมินตรวจสอบ
    </div>
    <div class='tp-amber'><span>&#9200;</span><span><b>โปรดแนบสลิป ภายใน 1 ชั่วโมง</b> หลังโอน</span></div>
    <div class='tp-foot'>
     <button type='button' class='tp-cancel' onclick="document.getElementById('modal_bank').classList.remove('show')">ยกเลิก</button>
     <button type='submit' class='tp-submit'>ยืนยันสลิป &rarr;</button>
    </div>
   </form>
  </div>
 </div>
 <div class='how-modal' id='modal_code' onclick="if(event.target===this)this.classList.remove('show')">
  <div class='tp-sheet'>
   <div class='tp-hdr'>
    <div style='display:flex;align-items:center;gap:12px'>
     <div class='tp-ico' style='background:rgba(245,158,11,.15);border-color:rgba(245,158,11,.4)'>🪙</div>
     <div><div style='font-size:18px;font-weight:900'>กรอกโค้ดฟรี</div><div style='font-size:12px;color:#9ca3af'>กรอกโค้ดเพื่อรับเครดิตทันที ไม่ต้องโอนเงิน</div></div>
    </div>
    <button type='button' class='tp-x' onclick="document.getElementById('modal_code').classList.remove('show')">✕</button>
   </div>
   <form method='post'>
    <input type='hidden' name='act' value='redeem_code'>
    <div style='font-size:13px;color:#d1d5db;margin:14px 0 4px'>โค้ดคูปอง</div>
    <input name='code' placeholder='กรอกโค้ดคูปองที่นี่' required>
    <div class='tp-foot'>
     <button type='button' class='tp-cancel' onclick="document.getElementById('modal_code').classList.remove('show')">ยกเลิก</button>
     <button type='submit' class='tp-submit'>ยืนยันโค้ด &rarr;</button>
    </div>
   </form>
  </div>
 </div>
 """)
def admin_html(u):
 c=db();td=str(datetime.datetime.now().date());tu=c.execute("SELECT COUNT(*) FROM users").fetchone()[0];to=c.execute("SELECT COUNT(*) FROM orders").fetchone()[0];ts=c.execute("SELECT COALESCE(SUM(total),0) FROM orders").fetchone()[0];tst=c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE date LIKE ?",(f"%{td}%",)).fetchone()[0];st=c.execute("SELECT * FROM settings WHERE id=1").fetchone();ch="checked" if sf(st,'auto_check',1)==1 else ""
 m_on="checked" if sf(st,'maintenance_on',0)==1 else ""
 m_msg=sf(st,'maintenance_msg','กำลังปิดปรับปรุงระบบและอัปเดตเว็บไซต์ชั่วคราว ขออภัยในความไม่สะดวกครับ')
 saved_bar="<div class='box' style='border:2px solid #22c55e;background:rgba(34,197,94,.12);color:#4ade80;font-weight:bold;text-align:center'>✅ บันทึกทุกอย่างที่ตั้งไว้ในเว็บและอัปเดตไฟล์สำรองเรียบร้อยแล้ว!</div>" if request.args.get('saved')=='1' else ""
 lp=f"<img src='/uploads/{sf(st,'logo','')}' style='width:80px;height:80px;border-radius:50%;object-fit:cover'>" if sf(st,'logo','') else "ยังไม่มีโลโก้";bp=f"<img src='/uploads/{sf(st,'banner','')}' style='width:100%;height:100px;object-fit:contain;border-radius:12px;display:block;background:#000'>" if sf(st,'banner','') else "ยังไม่มีแบนเนอร์"
 b=saved_bar+f"<div class='box'><h3>📊 แดชบอร์ด</h3><p>👥 สมาชิก {tu} | 🛒 ออเดอร์ {to} | 💰 ยอดขายรวม {int(ts)} | วันนี้ {int(tst)}</p></div>"
 b+=f"""
 <div class='box' style='border:2px solid #f59e0b'>
  <h3>🚧 ระบบปิดเว็บไซต์อัปเดตเว็บไซต์</h3>
  <form method='post' action='/admin'>
   <input type='hidden' name='act' value='set_maintenance'>
   <label><input type='checkbox' name='maintenance_on' {m_on} style='width:auto'> เปิดโหมดปิดปรับปรุงเว็บไซต์ (คนทั่วไปเข้าไม่ได้ ยกเว้นแอดมิน)</label>
   <textarea name='maintenance_msg' rows='2' placeholder='ข้อความแจ้งเตือนหน้าปิดปรับปรุง'>{m_msg}</textarea>
   <button style='background:linear-gradient(90deg,#f59e0b,#d97706);color:#000'>💾 บันทึกสถานะปิดปรับปรุงเว็บ</button>
  </form>
 </div>
 """
 b+=f"""
 <form id='admin_save_all_form' method='post' action='/admin' enctype='multipart/form-data'>
  <input type='hidden' name='act' value='save_all'>
  <div class='box' style='border:2px solid #e11d48'>
   <h3>🔥 โลโก้ + แบนเนอร์ + บัญชีรับเงิน</h3>
   <p>โลโก้ตอนนี้:</p>{lp}
   <p>แบนเนอร์ตอนนี้:</p>{bp}
   ชื่อร้าน <input name='shop_name' value='{sf(st,'shop_name','timstore')}'>
   ธนาคาร <input name='bank_name' value='{sf(st,'bank_name','ธนาคารกสิกรไทย')}'>
   ชื่อบัญชีธนาคาร <input name='bank_acc_name' value='{sf(st,'bank_acc_name','')}'>
   เลขบัญชีธนาคาร <input name='bank_acc_no' value='{sf(st,'bank_acc_no','')}'>
   พร้อมเพย์ <input name='promptpay' value='{sf(st,'promptpay','')}'>
   ทรูมันนี่ <input name='truemoney_phone' value='{sf(st,'truemoney_phone','')}'>
   <label><input type='checkbox' name='auto_check' {ch} style='width:auto'> ตรวจเงินอัตโนมัติ</label>
   โลโก้ <input type='file' name='logo'>
   แบนเนอร์ <input type='file' name='banner'>
   <button type='submit' style='background:linear-gradient(90deg,#22c55e,#16a34a);color:#fff;font-size:16px;padding:14px;margin-top:12px;box-shadow:0 6px 20px rgba(34,197,94,.28)'>💾 บันทึกตั้งค่าร้าน (save_all)</button>
  </div>
 </form>
 """
 b+=f"<div class='box' style='border:3px solid red'><h3>🔥 บังคับเปลี่ยนหมดทุกคนตามที่กูตั้ง</h3><form method='post' action='/admin' enctype='multipart/form-data'><input type='hidden' name='act' value='force_all'>📷 รูปที่จะให้ทุกคนใช้ <input type='file' name='force_avatar'>💰 coin ให้ทุกคน (ว่าง=ไม่เปลี่ยน) <input name='force_coin' type='number' placeholder='เช่น 100'>👑 ยศให้ทุกคน <select name='force_role'><option value=''>ไม่เปลี่ยนยศ</option><option value='user'>สมาชิกทั้งหมด</option><option value='admin'>แอดมินทั้งหมด</option><option value='agent'>ตัวแทนทั้งหมด</option></select><button style='background:#ff0000'>🔥 บังคับเปลี่ยนหมดทุกคน</button></form></div>"
 b+="<div class='box'><h3>🗂️ เพิ่มหมวดหมู่</h3><form method='post' action='/admin'><input type='hidden' name='act' value='add_cat'><input name='cat_name' placeholder='ชื่อหมวดหมู่'><input name='cat_icon' placeholder='ไอคอน 📦'><input name='cat_order' type='number' placeholder='ลำดับ'><button>เพิ่มหมวดหมู่</button></form>"
 for ct in c.execute("SELECT * FROM categories ORDER BY order_num, id").fetchall():
  b+=f"<p style='display:flex;justify-content:space-between;align-items:center;gap:8px'><span>{sf(ct,'icon','📦')} <b>{ct['name']}</b></span><form method='post' action='/admin' style='display:inline;margin:0'><input type='hidden' name='act' value='del_cat'><input type='hidden' name='cat_id' value='{ct['id']}'><button style='width:auto;background:#ef4444;padding:6px 10px;margin:0'>ลบ</button></form></p>"
 b+="</div>"
 b+="<div class='box'><h3>➕ เพิ่มโซน</h3><form method='post' action='/admin' enctype='multipart/form-data'><input type='hidden' name='act' value='add_zone'><input name='zone_name' placeholder='ชื่อโซน'><input name='zone_icon' placeholder='ไอคอน 🔥'><input name='zone_order' type='number' placeholder='ลำดับ'><input type='file' name='zone_img'><button>เพิ่มโซน</button></form></div>"
 for z in c.execute("SELECT * FROM zones ORDER BY order_num").fetchall():
  b+=f"<div class='box'><b>{z['name']}</b><form method='post' action='/admin' enctype='multipart/form-data'><input type='hidden' name='act' value='edit_zone'><input type='hidden' name='zone_id' value='{z['id']}'><input type='hidden' name='zone_name' value='{z['name']}'><input type='hidden' name='zone_icon' value='{sf(z,'icon','🔥')}'><input type='hidden' name='zone_order' type='number' value='{z['order_num']}'><input type='file' name='zone_img'><button>แก้ไขโซน</button></form><form method='post' action='/admin'><input type='hidden' name='act' value='del_zone'><input type='hidden' name='zone_id' value='{z['id']}'><button style='background:#ef4444'>ลบโซน</button></form></div>"
 cat_opts="".join([f"<option value='{ct['id']}'>{ct['name']}</option>" for ct in c.execute("SELECT * FROM categories ORDER BY order_num, id").fetchall()])
 b+="<div class='box'><h3>➕ เพิ่มสินค้า</h3><form method='post' action='/admin' enctype='multipart/form-data'><input type='hidden' name='act' value='add_product'><select name='zone_id'>"+"".join([f"<option value='{z['id']}'>{z['name']}</option>" for z in c.execute("SELECT * FROM zones").fetchall()])+"</select><select name='category_id'><option value='0'>-- เลือกหมวดหมู่ --</option>"+cat_opts+"</select><input name='pname' placeholder='ชื่อสินค้า'><input name='price' placeholder='ราคาปกติ (บาท)'><input name='agent_price' placeholder='ราคาตัวแทนแยกชิ้น (ว่าง = ใช้ส่วนลดคีย์)'><textarea name='desc' placeholder='รายละเอียด'></textarea><textarea name='stock' placeholder='สต็อก 1 บรรทัด = 1 โค้ด'></textarea><input type='file' name='pimg'><button>เพิ่มสินค้า</button></form></div>"
 for p in c.execute("SELECT * FROM products").fetchall():
  p_ap=float(sf(p,'agent_price',0) or 0)
  p_ap_lbl=f" | <span style='color:#34d399'>ตัวแทน ฿{fp(p_ap)}</span>" if p_ap>0 else ""
  b+=f"<div class='box'><b>{p['name']} - ฿{fp(p['price'])}</b>{p_ap_lbl}<form method='post' action='/admin' style='display:flex;gap:6px;align-items:center;margin:8px 0'><input type='hidden' name='act' value='set_product_agent_price'><input type='hidden' name='pid' value='{p['id']}'><input name='agent_price' type='number' step='0.01' value='{fp(p_ap) if p_ap>0 else ''}' placeholder='ราคาตัวแทน (0=ปิด)' style='margin:0;flex:1'><button style='width:auto;margin:0;padding:10px 12px;background:#059669;white-space:nowrap'>บันทึกราคาตัวแทน</button></form><form method='post' action='/admin'><input type='hidden' name='act' value='del_product'><input type='hidden' name='pid' value='{p['id']}'><button style='background:#ef4444'>ลบสินค้า</button></form><form method='post' action='/admin'><input type='hidden' name='act' value='add_variant'><input type='hidden' name='pid' value='{p['id']}'><input name='vname' placeholder='ชื่อตัวเลือก'><input name='vprice' placeholder='ราคาปกติ'><input name='vagent_price' placeholder='ราคาตัวแทนตัวเลือก (ว่าง=ไม่ตั้ง)'><textarea name='vstock' placeholder='สต็อก'></textarea><button>เพิ่มตัวเลือก</button></form></div>"
  for v in c.execute("SELECT * FROM variants WHERE product_id=?",(p['id'],)).fetchall():
   v_ap=float(sf(v,'agent_price',0) or 0)
   v_ap_lbl=f" <span style='color:#34d399'>(ตัวแทน ฿{fp(v_ap)})</span>" if v_ap>0 else ""
   b+=f"<p>📂 {v['name']} - ฿{fp(v['price'])}{v_ap_lbl} <form method='post' action='/admin' style='display:inline'><input type='hidden' name='act' value='del_variant'><input type='hidden' name='vid' value='{v['id']}'><button style='width:auto;background:#ef4444'>ลบ</button></form></p>"
 b+="<div class='box'><h3>💰 เติมเงินรอตรวจ</h3>"
 for t in c.execute("SELECT * FROM topups WHERE status='pending' ORDER BY id DESC").fetchall():
  slip=f"<a href='/uploads/{t['slip']}' target='_blank'>ดูสลิป</a>" if t['slip'] else ""
  env_raw=sf(t,'envelope_link','')
  env_js=json.dumps(env_raw)
  env=f"<div class='env-box'><span style='color:#ff4d6d;font-size:12px;word-break:break-all'>🎁 ซองวอ: {env_raw}</span><button type='button' class='copy-env-btn' onclick='copyText({env_js},this)'>📋 คัดลอกซองวอ</button></div>" if env_raw else ""
  b+=f"<div style='border-bottom:1px solid #1e1f26;padding:8px 0'><p style='margin:4px 0'><b>{t['username']}</b> {int(t['amount'])} บาท - {t['method']} - {t['status']} {slip}</p>{env}<form method='post' action='/admin' style='display:inline'><input type='hidden' name='act' value='topup_action'><input type='hidden' name='tid' value='{t['id']}'><input type='hidden' name='action' value='approve'><button style='width:auto;background:#00c853;padding:6px 10px'>อนุมัติ</button></form><form method='post' action='/admin' style='display:inline'><input type='hidden' name='act' value='topup_action'><input type='hidden' name='tid' value='{t['id']}'><input type='hidden' name='action' value='reject'><button style='width:auto;background:#ef4444;padding:6px 10px'>ปฏิเสธ</button></form></div>"
 b+="""</div><div class='box' style='border:1px solid rgba(16,185,129,.45)'><h3>สร้างคีย์ตัวแทน (แบบง่าย)</h3><p style='color:#9ca3af;font-size:12px;margin:0 0 8px'>ปล่อยว่างทุกช่องได้เลย ระบบจะสุ่มคีย์ + ใช้ราคาตัวแทนแยกตามสินค้า + อายุ 30 วันให้อัตโนมัติ (หรือกรอก % ลดเพิ่มเฉพาะคีย์ก็ได้)</p><form method='post' action='/admin'><input type='hidden' name='act' value='add_agent_key'><input name='code' placeholder='คีย์ (ว่าง = สุ่มให้เองอัตโนมัติ)'><input name='discount' type='number' placeholder='ส่วนลดสำรอง % (ว่าง = ใช้ราคาตัวแทนรายชิ้นเป็นหลัก)'><input name='days' type='number' placeholder='กี่วัน (ว่าง = 30 วัน)'><input name='price' placeholder='ราคาคีย์ (ว่าง = 0)'><button style='background:linear-gradient(90deg,#10b981,#059669)'>สร้างคีย์ตัวแทนทันที</button></form>"""
 for ak in c.execute("SELECT * FROM agent_keys ORDER BY id DESC").fetchall():
  ak_d=int(sf(ak,'discount',0) or 0)
  ak_mode_txt="ราคาตัวแทนรายชิ้น" if ak_d<=0 else f"ราคาตัวแทนรายชิ้น / ลด {ak_d}%"
  b+=f"<p><b>{ak['code']}</b> · {ak_mode_txt} · {ak['days']} วัน · {'ใช้แล้ว' if ak['used'] else 'ยังไม่ใช้'} <form method='post' action='/admin' style='display:inline'><input type='hidden' name='act' value='del_agent_key'><input type='hidden' name='kid' value='{ak['id']}'><button style='width:auto;background:#ef4444'>ลบ</button></form></p>"
 b+="</div><div class='box'><h3>🎫 โค้ดเครดิต</h3><form method='post' action='/admin'><input type='hidden' name='act' value='add_credit'><input name='code' placeholder='โค้ด'><input name='amount' placeholder='coin'><button>สร้างโค้ด</button></form>"
 for cc in c.execute("SELECT * FROM credit_codes ORDER BY id DESC").fetchall():b+=f"<p>{cc['code']} = {int(cc['amount'])} coin <form method='post' action='/admin' style='display:inline'><input type='hidden' name='act' value='del_credit'><input type='hidden' name='cid' value='{cc['id']}'><button style='width:auto;background:#ef4444'>ลบ</button></form></p>"
 b+="</div><div class='box' style='border:2px solid #ffaa00'><h3>🎟️ โค้ดส่วนลด</h3><form method='post' action='/admin'><input type='hidden' name='act' value='add_coupon'><input name='coupon_code' placeholder='โค้ด เช่น TIM10'><select name='coupon_type'><option value='percent'>ลดเป็น %</option><option value='baht'>ลดเป็น บาท</option></select><input name='coupon_value' type='number' value='10'><input name='coupon_max_use' type='number' value='0' placeholder='ใช้ได้กี่ครั้ง 0=ไม่จำกัด'><button style='background:#ffaa00;color:#000'>สร้างโค้ด</button></form>"
 for cp in c.execute("SELECT * FROM coupons ORDER BY id DESC").fetchall():
  lb=f"{int(cp['value'])}%" if cp['type']=='percent' else f"{int(cp['value'])} บาท";b+=f"<p>🎟️ <b>{cp['code']}</b> - ลด {lb} | {cp['used']}/{cp['max_use'] or '∞'} | {'✅' if cp['active'] else '❌'} <form method='post' action='/admin' style='display:inline'><input type='hidden' name='act' value='toggle_coupon'><input type='hidden' name='coupon_id' value='{cp['id']}'><button style='width:auto'>เปิด/ปิด</button></form> <form method='post' action='/admin' style='display:inline'><input type='hidden' name='act' value='del_coupon'><input type='hidden' name='coupon_id' value='{cp['id']}'><button style='width:auto;background:#ef4444'>ลบ</button></form></p>"
 b+="</div><div class='box' style='border:2px solid #00ff88'><h3>📦 เติมของ</h3><form method='post' action='/admin'><input type='hidden' name='act' value='add_stock_all'><select name='item_id' onchange=\"document.getElementById('rk').value=this.options[this.selectedIndex].dataset.kind\">"
 for p in c.execute("SELECT * FROM products").fetchall():b+=f"<option value='{p['id']}' data-kind='product'>🛒 {p['name']} - เหลือ {len([x for x in sf(p,'stock','').split(NL) if x.strip()])}</option>"
 for v in c.execute("SELECT variants.*, products.name as pname FROM variants JOIN products ON variants.product_id=products.id").fetchall():b+=f"<option value='{v['id']}' data-kind='variant'>📂 {v['pname']} - {v['name']} - เหลือ {len([x for x in sf(v,'stock','').split(NL) if x.strip()])}</option>"
 b+="</select><input type='hidden' name='kind' id='rk' value='product'><textarea name='add_stock' placeholder='ใส่สต็อก'></textarea><button style='background:#00c853'>+ เติมสต็อก</button></form></div>"
 b+="<div class='box'><h3>👥 สมาชิก - แอดมินแก้ได้ทุกคน</h3>"
 for us in c.execute("SELECT * FROM users ORDER BY id DESC").fetchall():
  b+=f"<form method='post' action='/admin' enctype='multipart/form-data'><input type='hidden' name='act' value='edit_user'><input type='hidden' name='uid' value='{us['id']}'><b>{us['username']}</b> - {int(us['coin'])} coin - {role_th(us['role'])}<input name='new_username' value='{us['username']}'><input name='new_password' value='{us['password']}'><input name='new_coin' type='number' value='{int(us['coin'])}'><select name='new_role'><option value='user' {'selected' if us['role']=='user' else ''}>สมาชิก</option><option value='admin' {'selected' if us['role']=='admin' else ''}>แอดมิน</option><option value='owner' {'selected' if us['role']=='owner' else ''}>เจ้าของร้าน</option><option value='agent' {'selected' if us['role']=='agent' else ''}>ตัวแทน</option></select><input type='file' name='new_avatar'><button>บันทึกคนนี้</button></form>"
 b+="</div>"
 b+="<div class='box'><h3>💾 สำรอง / กู้ข้อมูลทั้งหมด</h3><p style='color:#9ca3af;font-size:12px'>สำรองตั้งค่าร้าน หมวดหมู่ โซน สินค้า รูปภาพ คูปอง และรายการเติมเงินทั้งหมดในไฟล์เดียว</p><a href='/backup'><button>💾 สำรองข้อมูลทั้งหมด (ดาวน์โหลดไฟล์)</button></a><form method='post' action='/admin' enctype='multipart/form-data' style='margin-top:8px'><input type='hidden' name='act' value='restore_all'><input type='file' name='backup_file' accept='.json'><button style='background:#ffaa00;color:#000'>♻️ กู้ข้อมูลจาก backup</button></form></div>"
 b+=f"""
 <div class='box' style='border:2px solid #facc15;background:linear-gradient(135deg,rgba(250,204,21,.12),rgba(14,14,18,.96));margin-top:16px'>
  <form id='admin_promo_form' method='post' action='/admin'>
   <input type='hidden' name='act' value='set_discount'>
   <h3 style='margin-top:0;color:#facc15'>🔥 โปรโมชั่นลดทั้งร้าน (ตั้งค่าด้านล่างสุด)</h3>
   <label><input type='checkbox' name='disc_on' {'checked' if sf(st,'disc_on',0)==1 else ''} style='width:auto'> เปิดใช้งานโปรโมชั่นลดทั้งร้าน</label>
   <select name='disc_type'>
    <option value='percent' {'selected' if sf(st,'disc_type','percent')=='percent' else ''}>ลดเป็น %</option>
    <option value='baht' {'selected' if sf(st,'disc_type','percent')=='baht' else ''}>ลดเป็น บาท</option>
   </select>
   <input name='disc_val' type='number' step='0.01' value='{sf(st,'disc_val',0)}' placeholder='ใส่ส่วนลด เช่น 10'>
   <p style='color:#d1d5db;font-size:12px;margin:4px 0 12px'>สถานะปัจจุบัน: <b>{'ปิดอยู่' if sf(st,'disc_on',0)!=1 else 'ลด '+str(sf(st,'disc_val',0))+' '+('%' if sf(st,'disc_type','percent')=='percent' else 'บาท')+' ทุกชิ้น'}</b></p>
   <button type='submit' style='background:linear-gradient(90deg,#facc15,#eab308);color:#000;font-size:16px;padding:15px;box-shadow:0 8px 24px rgba(250,204,21,.28)'>🔥 บันทึกโปรโมชั่นลดทั้งร้าน</button>
  </form>
 </div>
 <div class='box' style='border:2px solid #22c55e;background:linear-gradient(135deg,rgba(34,197,94,.14),rgba(14,14,18,.98));margin-top:12px'>
  <form id='admin_save_everything_form' method='post' action='/admin' onsubmit='syncSaveEverything()'>
   <input type='hidden' name='act' value='save_everything'>
   <input type='hidden' id='se_disc_on' name='disc_on' value='{1 if sf(st,'disc_on',0)==1 else 0}'>
   <input type='hidden' id='se_disc_type' name='disc_type' value='{sf(st,'disc_type','percent')}'>
   <input type='hidden' id='se_disc_val' name='disc_val' value='{sf(st,'disc_val',0)}'>
   <input type='hidden' id='se_shop_name' name='shop_name' value='{sf(st,'shop_name','timstore')}'>
   <input type='hidden' id='se_bank_name' name='bank_name' value='{sf(st,'bank_name','ธนาคารกสิกรไทย')}'>
   <input type='hidden' id='se_bank_acc_name' name='bank_acc_name' value='{sf(st,'bank_acc_name','')}'>
   <input type='hidden' id='se_bank_acc_no' name='bank_acc_no' value='{sf(st,'bank_acc_no','')}'>
   <input type='hidden' id='se_promptpay' name='promptpay' value='{sf(st,'promptpay','')}'>
   <input type='hidden' id='se_truemoney_phone' name='truemoney_phone' value='{sf(st,'truemoney_phone','')}'>
   <input type='hidden' id='se_auto_check' name='auto_check' value='{1 if sf(st,'auto_check',1)==1 else 0}'>
   <div style='font-size:13px;color:#bbf7d0;margin-bottom:8px;text-align:center'>กดปุ่มเดียวเพื่อบันทึกค่าที่ปรับไว้บนหน้านี้ทั้งหมด + สำรองข้อมูลอัตโนมัติ</div>
   <button type='submit' style='background:linear-gradient(90deg,#16a34a,#22c55e);color:#fff;font-size:16px;padding:15px;box-shadow:0 8px 24px rgba(34,197,94,.3)'>💾 บันทึกทุกอย่างที่ตั้งไว้ในเว็บ</button>
  </form>
 </div>
 <script>
 function syncSaveEverything(){{
  let pf=document.getElementById('admin_promo_form');
  if(pf){{
   let don=pf.querySelector('[name="disc_on"]');
   let dt=pf.querySelector('[name="disc_type"]');
   let dv=pf.querySelector('[name="disc_val"]');
   if(don)document.getElementById('se_disc_on').value=don.checked?'1':'0';
   if(dt)document.getElementById('se_disc_type').value=dt.value;
   if(dv)document.getElementById('se_disc_val').value=dv.value;
  }}
  let sfrm=document.getElementById('admin_save_all_form');
  if(sfrm){{
   ['shop_name','bank_name','bank_acc_name','bank_acc_no','promptpay','truemoney_phone'].forEach(k=>{{
    let src=sfrm.querySelector('[name="'+k+'"]');
    let dst=document.getElementById('se_'+k);
    if(src&&dst)dst.value=src.value;
   }});
   let ac=sfrm.querySelector('[name="auto_check"]');
   if(ac)document.getElementById('se_auto_check').value=ac.checked?'1':'0';
  }}
 }}
 </script>
 """
 c.close();return b
@app.route('/profile',methods=['GET','POST'])
def profile():
 u=cur()
 if not u:return redirect('/login')
 c=db()
 msg_html=""
 if request.method=='POST':
  act=request.form.get('act')
  if act=='redeem_credit':
   code=request.form.get('code','').strip();cc=c.execute("SELECT * FROM credit_codes WHERE code=? AND used=0",(code,)).fetchone()
   if not cc:c.close();return base("<div class='box'>❌ โค้ดผิด / ใช้แล้ว</div>")
   c.execute("UPDATE users SET coin=coin+? WHERE id=?",(cc['amount'],u['id']));c.execute("UPDATE credit_codes SET used=1, used_by=? WHERE code=?",(u['username'],code));c.commit();c.close();return base(f"<div class='box'>✅ ได้ {int(cc['amount'])} coin</div>")
  if act=='use_agent_key':
   code=request.form.get('code','').strip();ak=c.execute("SELECT * FROM agent_keys WHERE code=?",(code,)).fetchone()
   if not ak or ak['used']==1:
    c.close()
    return base("<div class='box' style='text-align:center'><h2>❌ คีย์ไม่ถูกต้องหรือถูกใช้งานแล้ว</h2><a href='/profile?tab=agent'><button>กลับไปลองใหม่</button></a></div>")
   days_val=int(ak['days'] or 30)
   disc_val=int(ak['discount'] or 0)
   exp=str(datetime.datetime.now()+datetime.timedelta(days=days_val))
   c.execute("INSERT OR REPLACE INTO agents(username,discount,expire,renewed_cycle,date) VALUES(?,?,?,'',?)",(u['username'],disc_val,exp,str(datetime.datetime.now())))
   c.execute("UPDATE agent_keys SET used=1, used_by=? WHERE id=?",(u['username'],ak['id']))
   if not is_admin(u):
    c.execute("UPDATE users SET role='agent' WHERE id=?",(u['id'],))
   c.commit();c.close()
   return redirect('/profile?tab=agent&activated=1')
  if act=='change_pw':
   cur_pw=request.form.get('cur_pw','').strip()
   new_pw=request.form.get('new_pw','').strip()
   new_pw2=request.form.get('new_pw2','').strip()
   if cur_pw!=str(sf(u,'password','')):
    msg_html="<div class='box' style='border-color:#ef4444;color:#ff7b8a'>❌ รหัสผ่านปัจจุบันไม่ถูกต้อง</div>"
   elif len(new_pw)<4:
    msg_html="<div class='box' style='border-color:#ef4444;color:#ff7b8a'>❌ รหัสผ่านใหม่ต้องอย่างน้อย 4 ตัวอักษร</div>"
   elif new_pw!=new_pw2:
    msg_html="<div class='box' style='border-color:#ef4444;color:#ff7b8a'>❌ ยืนยันรหัสผ่านใหม่ไม่ตรงกัน</div>"
   else:
    c.execute("UPDATE users SET password=? WHERE id=?",(new_pw,u['id']));c.commit()
    u=c.execute("SELECT * FROM users WHERE id=?",(u['id'],)).fetchone()
    msg_html="<div class='box' style='border-color:#22c55e;color:#4ade80'>✅ เปลี่ยนรหัสผ่านเรียบร้อยแล้ว</div>"
  if act=='avatar':
   fn=up(request.files.get('avatar'))
   if fn:c.execute("UPDATE users SET avatar=? WHERE id=?",(fn,u['id']));c.commit()
   c.close();return redirect('/profile')
 tab=request.args.get('tab','summary')
 my=c.execute("SELECT * FROM topups WHERE username=? ORDER BY id DESC",(u['username'],)).fetchall()
 ord_cnt=c.execute("SELECT COUNT(*) FROM orders WHERE username=?",(u['username'],)).fetchone()[0]
 ord_sum=c.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE username=?",(u['username'],)).fetchone()[0]
 ag_info=active_agent(c,u)
 u=c.execute("SELECT * FROM users WHERE id=?",(u['id'],)).fetchone()
 rem_txt=agent_rem_text(ag_info)
 top7=agent_7d_topup(c,u['username'])
 c.close()
 av=sf(u,'avatar','')
 cam_btn="<label for='pro_av_inp' title='เปลี่ยนรูปโปรไฟล์' style='position:absolute;right:0;bottom:0;width:30px;height:30px;border-radius:50%;background:#e11d48;color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;cursor:pointer;border:2px solid #0e0e12'>📷</label><form id='pro_av_frm' method='post' enctype='multipart/form-data' style='display:none'><input type='hidden' name='act' value='avatar'><input id='pro_av_inp' type='file' name='avatar' accept='image/*' onchange='document.getElementById(\"pro_av_frm\").submit()'></form>"
 ah_inner=f"<img src='/uploads/{av}' style='width:96px;height:96px;border-radius:50%;object-fit:cover;border:2px solid #e11d48;display:block'>" if av else "<div style='width:96px;height:96px;border-radius:50%;background:#1e090e;border:2px solid #e11d48;display:flex;align-items:center;justify-content:center;font-size:42px'>👤</div>"
 ah=f"<div style='position:relative;width:96px;height:96px;margin:0 auto'>{ah_inner}{cam_btn}</div>"
 head_card=f"""
 <div class='box' style='text-align:center;padding:24px 16px'>
  {ah}
  <h2 style='margin:14px 0 6px;font-size:24px'>{u['username'].upper()}</h2>
  {user_badges_html(u,ag_info)}
 </div>
 <div class='tab-bar'>
  <a href='/profile?tab=summary' class='tab-btn {'active' if tab=='summary' else ''}'><span>🏠</span><span>สรุป</span></a>
  <a href='/profile?tab=account' class='tab-btn {'active' if tab=='account' else ''}'><span>👤</span><span>บัญชี</span></a>
  <a href='/profile?tab=security' class='tab-btn {'active' if tab=='security' else ''}'><span>🔒</span><span>รหัสผ่าน</span></a>
  <a href='/profile?tab=agent' class='tab-btn {'active' if tab=='agent' else ''}'><span>🤝</span><span>ตัวแทน</span></a>
 </div>
 """
 if tab=='agent':
  if ag_info:
   pct_ag=int(sf(ag_info,'discount',0) or 0)
   pct_bar=min(100,int((top7/50.0)*100)) if top7>0 else 0
   act_note="<div class='box' style='border-color:#22c55e;background:rgba(34,197,94,.12);color:#4ade80;font-weight:bold;text-align:center'>✅ เปิดใช้งานตัวแทนและรับยศ Reseller พร้อมส่วนลดสินค้าเรียบร้อยแล้ว!</div>" if request.args.get('activated')=='1' else ""
   body_tab=f"""
   {act_note}
   <div class='ag-panel'>
    <div style='font-size:20px;font-weight:900'>ระบบตัวแทนจำหน่าย</div>
    <div style='color:#9ca3af;font-size:13px;margin-top:4px'>สถานะโควต้าและสิทธิ์ราคาพิเศษ {f'(ลดราคาสินค้า {pct_ag}%)' if pct_ag>0 else ''}</div>
    <div class='ag-stat-box'>
     <div><div style='color:#9ca3af;font-size:12px'>สถานะ</div><div style='color:#ff2a55;font-size:24px;font-weight:900;margin-top:4px'>Active</div></div>
     <div style='text-align:right'><div style='color:#9ca3af;font-size:12px'>เหลือเวลา</div><div style='color:#fff;font-size:20px;font-weight:900;margin-top:4px'>{rem_txt}</div></div>
    </div>
    <div style='display:flex;justify-content:space-between;align-items:center;font-size:13px;margin-top:12px'>
     <span style='color:#d1d5db'>ยอดเติมในรอบ 7 วัน</span>
     <b>{top7:.2f} / 50.00 ฿</b>
    </div>
    <div class='ag-prog-bg'><div class='ag-prog-fill' style='width:{pct_bar}%'></div></div>
    <div class='ag-warn'><span>&#9888;&#65039;</span><span>ทำยอดให้ถึง <b>50.00 ฿</b> ก่อนหมดเวลา</span></div>
   </div>
   """
  else:
   body_tab="""
   <div class='ag-panel'>
    <div style='font-size:20px;font-weight:900'>ระบบตัวแทนจำหน่าย</div>
    <div style='color:#9ca3af;font-size:13px;margin-top:4px'>สถานะโควต้าและสิทธิ์ราคาพิเศษ</div>
    <form method='post' style='margin-top:18px'>
     <input type='hidden' name='act' value='use_agent_key'>
     <div style='font-size:14px;color:#e5e7eb;margin-bottom:6px'>คีย์ตัวแทนจำหน่าย</div>
     <input name='code' placeholder='กรอกคีย์ที่นี่' required>
     <button style='background:linear-gradient(90deg,#f43f5e,#be123c);padding:13px;font-size:15px;margin-top:8px'>เปิดใช้งานตัวแทน</button>
    </form>
   </div>
   """
 elif tab=='account':
  em_txt=sf(u,'email','') or "ยังไม่ได้เชื่อมต่อ"
  reg_txt=fmt_th_date(sf(u,'date',''))
  last_txt=fmt_th_date(sf(u,'last_login','') or sf(u,'date',''))
  body_tab=f"""
  <div class='acc-tbl'>
   <div style='font-size:20px;font-weight:900;margin-bottom:6px'>ข้อมูลบัญชี</div>
   <div class='acc-row'><span style='color:#9ca3af'>ชื่อผู้ใช้</span><b>{u['username']}</b></div>
   <div class='acc-row'><span style='color:#9ca3af'>อีเมล</span><b>{em_txt}</b></div>
   <div class='acc-row'><span style='color:#9ca3af'>สมัครเมื่อ</span><b>{reg_txt}</b></div>
   <div class='acc-row'><span style='color:#9ca3af'>เข้าสู่ระบบล่าสุด</span><b>{last_txt}</b></div>
  </div>
  <div class='dc-card'>
   <div style='display:flex;align-items:center;gap:14px'>
    <div class='lnk-ico' style='background:#181b2e;border-color:#2b3157;color:#818cf8;font-size:22px'>🎮</div>
    <div>
     <div style='font-weight:bold;font-size:16px'>Discord</div>
     <div style='color:#9ca3af;font-size:13px;margin-top:2px'>ยังไม่ได้เชื่อมต่อ</div>
    </div>
   </div>
   <button type='button' class='dc-btn' onclick="alert('พร้อมเชื่อมต่อ Discord เร็วๆ นี้')">เชื่อมต่อ</button>
  </div>
  <div class='box'><h3>🎫 กรอกโค้ดรับเงินฟรี</h3><form method='post'><input type='hidden' name='act' value='redeem_credit'><input name='code' placeholder='กรอกโค้ดเครดิต'><button>รับเงินฟรีทันที</button></form></div>
  """
 elif tab=='security':
  body_tab=f"""
  {msg_html}
  <div class='acc-tbl'>
   <div style='font-size:20px;font-weight:900'>เปลี่ยนรหัสผ่าน</div>
   <div style='color:#9ca3af;font-size:13px;margin:4px 0 14px'>กรอกรหัสผ่านปัจจุบันและรหัสผ่านใหม่</div>
   <form method='post'>
    <input type='hidden' name='act' value='change_pw'>
    <div style='font-size:13px;color:#e5e7eb'>รหัสผ่านปัจจุบัน</div>
    <div class='pw-eye-wrap'><input id='cpw1' type='password' name='cur_pw' placeholder='••••••••' required><span class='pw-eye-ico' onclick="toggleEye('cpw1')">👁</span></div>
    <div style='font-size:13px;color:#e5e7eb'>รหัสผ่านใหม่</div>
    <div class='pw-eye-wrap'><input id='cpw2' type='password' name='new_pw' placeholder='••••••••' required><span class='pw-eye-ico' onclick="toggleEye('cpw2')">👁</span></div>
    <div style='font-size:13px;color:#e5e7eb'>ยืนยันรหัสผ่านใหม่</div>
    <div class='pw-eye-wrap'><input id='cpw3' type='password' name='new_pw2' placeholder='••••••••' required><span class='pw-eye-ico' onclick="toggleEye('cpw3')">👁</span></div>
    <button style='background:linear-gradient(90deg,#f43f5e,#be123c);padding:13px;font-size:15px;margin-top:10px'>บันทึกรหัสผ่านใหม่</button>
   </form>
  </div>
  """
 else:
  ag_sub_txt=f"Active · เหลือ {rem_txt}" if ag_info else "จัดการสิทธิ์และรับราคาตัวแทน"
  body_tab=f"""
  <div class='box' style='border-color:rgba(225,29,72,.35);background:linear-gradient(145deg,#1b070c,#0e0e12)'>
   <div style='color:#9ca3af;font-size:13px'>ยอดคงเหลือ</div>
   <div style='display:flex;justify-content:space-between;align-items:center;margin-top:8px'>
    <div style='font-size:32px;font-weight:900;color:#ff2a55'>฿{float(u['coin']):.2f}</div>
    <a href='/topup' class='btn-red-sm' style='padding:10px 14px;font-size:14px'>+ เติมเงิน</a>
   </div>
  </div>
  <div class='stat-grid'>
   <div class='stat-card'><div style='color:#9ca3af;font-size:13px'>🛍️ คำสั่งซื้อ</div><div style='font-size:28px;font-weight:900;margin-top:8px'>{ord_cnt}</div><div style='color:#6b7280;font-size:12px'>รายการ</div></div>
   <div class='stat-card'><div style='color:#9ca3af;font-size:13px'>💵 ยอดซื้อรวม</div><div style='font-size:26px;font-weight:900;color:#ff2a55;margin-top:8px'>฿{float(ord_sum):.2f}</div><div style='color:#6b7280;font-size:12px'>บาท</div></div>
  </div>
  <a href='/history' class='lnk-card'><div class='lnk-ico'>🧾</div><div style='flex:1'><div style='font-weight:bold;font-size:16px'>ประวัติการซื้อ</div><div style='color:#9ca3af;font-size:12px;margin-top:2px'>ดูคำสั่งซื้อทั้งหมด</div></div><span style='color:#6b7280;font-size:18px'>&gt;</span></a>
  <a href='/' class='lnk-card'><div class='lnk-ico'>🏪</div><div style='flex:1'><div style='font-weight:bold;font-size:16px'>ไปหน้าร้านค้า</div><div style='color:#9ca3af;font-size:12px;margin-top:2px'>เลือกซื้อสินค้า</div></div><span style='color:#6b7280;font-size:18px'>&gt;</span></a>
  <a href='/profile?tab=agent' class='lnk-card'><div class='lnk-ico'>🤝</div><div style='flex:1'><div style='font-weight:bold;font-size:16px'>ระบบตัวแทน</div><div style='color:#9ca3af;font-size:12px;margin-top:2px'>{ag_sub_txt}</div></div><span style='color:#6b7280;font-size:18px'>&gt;</span></a>
  """
 if is_admin(u):
  body_tab+=admin_html(u)
 elif tab=='topups':
  body_tab="<div class='box'><h3>🧾 ประวัติการเติมเงิน</h3>"
  for t in my:body_tab+=f"<p>💰 {int(t['amount'])} บาท - {t['method']} - {t['status']}</p>"
  body_tab+="<a href='/history'><button>ดูประวัติการซื้อ</button></a></div>"
 return base(head_card+body_tab)
@app.route('/history')
def history():
 u=cur()
 if not u:return redirect('/login')
 c=db()
 o=c.execute("SELECT * FROM orders WHERE username=? ORDER BY id DESC",(u['username'],)).fetchall()
 prod_imgs={}
 for p in c.execute("SELECT name, img FROM products").fetchall():
  if sf(p,'img',''):prod_imgs[p['name']]=sf(p,'img','')
 c.close()
 b="""
 <div style='display:flex;align-items:center;gap:12px;margin:16px 0 6px'>
  <div class='lnk-ico' style='background:#1e080e;border-color:rgba(225,29,72,.45);color:#ff4d6d'>↺</div>
  <div>
   <h2 style='margin:0;font-size:24px'>ประวัติ<span style='color:#ff2a55'>การซื้อ</span></h2>
   <div style='color:#9ca3af;font-size:12px;margin-top:2px'>ตรวจสอบประวัติรายการ คีย์ และรายละเอียดคู่มือการใช้งานทั้งหมดของคุณ</div>
  </div>
 </div>
 <input placeholder='ค้นหาชื่อสินค้าหรือตัวเลือก...' oninput='filterOrders(this.value)'>
 """
 for x in o:
  raw_nm=sf(x,'product_name','')
  base_nm=raw_nm.split(' - ')[0].strip() if ' - ' in raw_nm else raw_nm
  var_nm=raw_nm.split(' - ',1)[1].strip() if ' - ' in raw_nm else f"{x['qty']} ชิ้น"
  im=sf(x,'product_img','') or prod_imgs.get(base_nm,'') or prod_imgs.get(raw_nm,'')
  th=f"<img src='/uploads/{im}' class='ord-thumb' style='object-fit:cover'>" if im else "<div class='ord-thumb'>📦</div>"
  ord_no=f"#ORD{8000+int(x['id'])}"
  dt_s=str(sf(x,'date',''))[:16].replace('T',' ')
  codes_raw=sf(x,'codes','')
  codes_js=json.dumps(codes_raw)
  meta_js=json.dumps(f"{raw_nm} ({x['qty']} ชิ้น) · {ord_no} · {dt_s}")
  title_js=json.dumps(base_nm)
  srch=(raw_nm+" "+ord_no+" "+dt_s).lower().replace("'","")
  b+=f"""
  <div class='ord-card' data-search='{srch}'>
   <div class='ord-top'>
    {th}
    <div style='min-width:0;flex:1'>
     <div style='font-weight:900;font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{base_nm}</div>
     <span class='ord-pill'>{var_nm} · {x['qty']} ชิ้น</span>
     <div style='color:#9ca3af;font-size:12px;margin-top:6px'><b>{ord_no}</b> · 📅 {dt_s}</div>
    </div>
   </div>
   <div class='ord-foot'>
    <div>
     <div style='color:#9ca3af;font-size:11px'>ราคาชำระ</div>
     <div style='color:#ff2a55;font-size:20px;font-weight:900;margin-top:2px'>฿{float(x['total']):.2f}</div>
    </div>
    <button type='button' class='ord-btn' onclick='openKeyModal({title_js},{meta_js},{codes_js})'>ดูคีย์ใช้งาน &gt;</button>
   </div>
  </div>
  """
 if not o:b+="<div class='box'>ยังไม่มีประวัติ</div>"
 return base(b)
@app.route('/notifications')
def notifications():
 u=cur()
 if not is_admin(u):return redirect('/')
 c=db();ns=c.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 50").fetchall();c.close();b="<div class='box'><h2>🔔 แจ้งเตือนเจ้าของ</h2><form method='post' action='/notifications/read_all'><button>✅ อ่านทั้งหมดแล้ว</button></form></div>"
 for n in ns:
  ic="💰" if n['type']=='topup' else ("🎁" if n['type']=='envelope' else ("🎫" if n['type']=='credit' else ("🛒" if n['type']=='order' else "🔔")));bg="#1a1a1a" if n['is_read']==1 else "#1e2a3a"
  det=sf(n,'detail','')
  env_copy=""
  if n['type']=='envelope' or ('gift.truemoney.com' in det) or det.startswith('http'):
   det_js=json.dumps(det)
   env_copy=f"<div class='env-box'><span style='color:#ff4d6d;font-size:12px;word-break:break-all'>🎁 ซองวอ: {det}</span><button type='button' class='copy-env-btn' onclick='copyText({det_js},this)'>📋 คัดลอกซองวอ</button></div>"
  b+=f"<div class='box' style='background:{bg}'><b>{ic} {n['message']}</b>{env_copy}<p style='color:#aaa;font-size:13px'>{det} | {n['date']}</p><a href='{n['link']}'><button>ไปจัดการ →</button></a><form method='post' action='/notifications/read/{n['id']}'><button style='background:#222'>อ่านแล้ว</button></form></div>"
 if not ns:b+="<div class='box'>ยังไม่มีแจ้งเตือน</div>"
 return base(b)
@app.route('/notifications/read/<int:nid>',methods=['POST'])
def read_one(nid):
 u=cur()
 if not is_admin(u):return redirect('/')
 c=db();c.execute("UPDATE notifications SET is_read=1 WHERE id=?",(nid,));c.commit();c.close();return redirect('/notifications')
@app.route('/notifications/read_all',methods=['POST'])
def read_all():
 u=cur()
 if not is_admin(u):return redirect('/')
 c=db();c.execute("UPDATE notifications SET is_read=1");c.commit();c.close();return redirect('/notifications')
@app.route('/api/unread')
def api_unread():
 u=cur()
 if not is_admin(u):return {"unread":0}
 return {"unread":unread()}
@app.route('/admin',methods=['GET','POST'])
def admin():
 u=cur()
 if not is_admin(u):return redirect('/login')
 c=db()
 if request.method=='POST':
  act=request.form.get('act')
  if act=='set_maintenance':
   m_on=1 if request.form.get('maintenance_on') else 0
   m_msg=(request.form.get('maintenance_msg','') or '').strip() or 'กำลังปิดปรับปรุงระบบและอัปเดตเว็บไซต์ชั่วคราว ขออภัยในความไม่สะดวกครับ'
   c.execute("UPDATE settings SET maintenance_on=?, maintenance_msg=? WHERE id=1",(m_on,m_msg))
   c.commit();write_auto_backup(c);c.close();return redirect('/profile?saved=1')
  if act=='save_all':
   c.execute("UPDATE settings SET shop_name=?, promptpay=?, truemoney_phone=?, bank_name=?, bank_acc_name=?, bank_acc_no=?, auto_check=? WHERE id=1",(request.form.get('shop_name','timstore'),request.form.get('promptpay',''),request.form.get('truemoney_phone',''),request.form.get('bank_name','ธนาคารกสิกรไทย'),request.form.get('bank_acc_name',''),request.form.get('bank_acc_no',''),1 if request.form.get('auto_check') else 0))
   for fd in ['logo','banner']:
    fn=up(request.files.get(fd))
    if fn:c.execute(f"UPDATE settings SET {fd}=? WHERE id=1",(fn,))
   c.commit()
   write_auto_backup(c)
   c.close();return redirect('/profile?saved=1')
  if act=='set_discount':
   c.execute("UPDATE settings SET disc_on=?, disc_type=?, disc_val=? WHERE id=1",(1 if request.form.get('disc_on') else 0,request.form.get('disc_type','percent'),float(request.form.get('disc_val',0) or 0)))
   c.commit()
   write_auto_backup(c)
   c.close();return redirect('/profile?saved=1')
  if act=='save_everything':
   cur_st=c.execute("SELECT * FROM settings WHERE id=1").fetchone()
   disc_on_val=1 if request.form.get('disc_on') in ('1','on','true','True') else 0
   disc_type_val=request.form.get('disc_type') or sf(cur_st,'disc_type','percent')
   try:
    disc_val_num=float(request.form.get('disc_val', sf(cur_st,'disc_val',0)) or 0)
   except:
    disc_val_num=float(sf(cur_st,'disc_val',0) or 0)
   shop_name_val=request.form.get('shop_name') if request.form.get('shop_name') is not None else sf(cur_st,'shop_name','timstore')
   promptpay_val=request.form.get('promptpay') if request.form.get('promptpay') is not None else sf(cur_st,'promptpay','')
   tm_phone_val=request.form.get('truemoney_phone') if request.form.get('truemoney_phone') is not None else sf(cur_st,'truemoney_phone','')
   bank_name_val=request.form.get('bank_name') if request.form.get('bank_name') is not None else sf(cur_st,'bank_name','ธนาคารกสิกรไทย')
   bank_acc_name_val=request.form.get('bank_acc_name') if request.form.get('bank_acc_name') is not None else sf(cur_st,'bank_acc_name','')
   bank_acc_no_val=request.form.get('bank_acc_no') if request.form.get('bank_acc_no') is not None else sf(cur_st,'bank_acc_no','')
   auto_check_val=1 if request.form.get('auto_check') in ('1','on','true','True') else int(sf(cur_st,'auto_check',1) or 0)
   c.execute("""UPDATE settings SET
    shop_name=?, promptpay=?, truemoney_phone=?, bank_name=?, bank_acc_name=?, bank_acc_no=?,
    auto_check=?, disc_on=?, disc_type=?, disc_val=?
    WHERE id=1""",(shop_name_val,promptpay_val,tm_phone_val,bank_name_val,bank_acc_name_val,bank_acc_no_val,auto_check_val,disc_on_val,disc_type_val,disc_val_num))
   for fd in ['logo','banner']:
    fn=up(request.files.get(fd))
    if fn:c.execute(f"UPDATE settings SET {fd}=? WHERE id=1",(fn,))
   c.commit()
   write_auto_backup(c)
   c.close();return redirect('/profile?saved=1')
  if act=='settings':
   c.execute("UPDATE settings SET shop_name=?, promptpay=?, truemoney_phone=?, bank_name=?, bank_acc_name=?, bank_acc_no=?, auto_check=? WHERE id=1",(request.form.get('shop_name','timstore'),request.form.get('promptpay',''),request.form.get('truemoney_phone',''),request.form.get('bank_name','ธนาคารกสิกรไทย'),request.form.get('bank_acc_name',''),request.form.get('bank_acc_no',''),1 if request.form.get('auto_check') else 0))
   for fd in ['logo','banner']:
    fn=up(request.files.get(fd))
    if fn:c.execute(f"UPDATE settings SET {fd}=? WHERE id=1",(fn,))
   c.commit();c.close();return redirect('/profile?saved=1')
  if act=='force_all':
   fn=up(request.files.get('force_avatar'))
   if fn:c.execute("UPDATE users SET avatar=? WHERE username!=?",(fn,ADMIN_USER))
   fc=request.form.get('force_coin','').strip()
   if fc!="":
    try:c.execute("UPDATE users SET coin=? WHERE username!=?",(float(fc),ADMIN_USER))
    except:pass
   fr=request.form.get('force_role','').strip()
   if fr!="":c.execute("UPDATE users SET role=? WHERE username!=?",(fr,ADMIN_USER))
   c.commit()
  if act=='add_cat':
   try:c.execute("INSERT INTO categories(name,icon,order_num) VALUES(?,?,?)",(request.form.get('cat_name','').strip(),request.form.get('cat_icon','📦').strip() or '📦',int(request.form.get('cat_order',0) or 0)));c.commit()
   except:pass
  if act=='del_cat':
   c.execute("DELETE FROM categories WHERE id=?",(request.form.get('cat_id'),));c.execute("UPDATE products SET category_id=0 WHERE category_id=?",(request.form.get('cat_id'),));c.commit()
  if act=='add_zone':
   c.execute("INSERT INTO zones(name,icon,order_num,img) VALUES(?,?,?,?)",(request.form.get('zone_name'),request.form.get('zone_icon','🔥'),request.form.get('zone_order',0),up(request.files.get('zone_img'))));c.commit()
  if act=='edit_zone':
   fn=up(request.files.get('zone_img'))
   if fn:c.execute("UPDATE zones SET name=?, icon=?, order_num=?, img=? WHERE id=?",(request.form.get('zone_name'),request.form.get('zone_icon','🔥'),request.form.get('zone_order',0),fn,request.form.get('zone_id')))
   else:c.execute("UPDATE zones SET name=?, icon=?, order_num=? WHERE id=?",(request.form.get('zone_name'),request.form.get('zone_icon','🔥'),request.form.get('zone_order',0),request.form.get('zone_id')))
   c.commit()
  if act=='del_zone':c.execute("DELETE FROM zones WHERE id=?",(request.form.get('zone_id'),));c.commit()
  if act=='add_product':
   ap_val=pp(request.form.get('agent_price','0'))
   c.execute("INSERT INTO products(zone_id,category_id,name,price,agent_price,desc,img,stock,date) VALUES(?,?,?,?,?,?,?,?,?)",(request.form.get('zone_id'),int(request.form.get('category_id',0) or 0),request.form.get('pname'),pp(request.form.get('price')),ap_val,request.form.get('desc',''),up(request.files.get('pimg')),request.form.get('stock',''),str(datetime.datetime.now())));c.commit()
  if act=='set_product_agent_price':
   ap_val=pp(request.form.get('agent_price','0'))
   c.execute("UPDATE products SET agent_price=? WHERE id=?",(ap_val,request.form.get('pid')));c.commit()
  if act=='del_product':c.execute("DELETE FROM products WHERE id=?",(request.form.get('pid'),));c.commit()
  if act=='add_variant':
   vap_val=pp(request.form.get('vagent_price','0'))
   c.execute("INSERT INTO variants(product_id,name,price,agent_price,stock,date) VALUES(?,?,?,?,?,?)",(request.form.get('pid'),request.form.get('vname'),pp(request.form.get('vprice')),vap_val,request.form.get('vstock',''),str(datetime.datetime.now())));c.commit()
  if act=='del_variant':c.execute("DELETE FROM variants WHERE id=?",(request.form.get('vid'),));c.commit()
  if act=='topup_action':
   t=c.execute("SELECT * FROM topups WHERE id=?",(request.form.get('tid'),)).fetchone()
   if t:
    if request.form.get('action')=='approve':
     c.execute("UPDATE users SET coin=coin+? WHERE username=?",(t['amount'],t['username']))
     c.execute("UPDATE topups SET status='approved' WHERE id=?",(t['id'],))
     c.commit()
     if check_auto_renew_agent(c,t['username']):
      noti('agent',t['username'],7,f"🤝 ต่ออายุตัวแทนอัตโนมัติ +7 วัน! {t['username']}","ทำยอดครบ 50.00 ฿ ในรอบ 7 วัน")
    else:
     c.execute("UPDATE topups SET status='rejected' WHERE id=?",(t['id'],))
     c.commit()
  if act=='add_credit':
   try:c.execute("INSERT INTO credit_codes(code,amount) VALUES(?,?)",(request.form.get('code'),pp(request.form.get('amount'))));c.commit()
   except:pass
  if act=='del_credit':c.execute("DELETE FROM credit_codes WHERE id=?",(request.form.get('cid'),));c.commit()
  if act=='add_agent_key':
   code=(request.form.get('code','') or '').strip().upper()
   if not code:code="TIM-"+"".join(random.choices(string.ascii_uppercase+string.digits,k=6))
   d_raw=(request.form.get('discount','') or '').strip()
   days_raw=(request.form.get('days','') or '').strip()
   pr_raw=(request.form.get('price','') or '').strip()
   d_val=int(float(d_raw)) if d_raw else 0
   days_val=int(float(days_raw)) if days_raw else 30
   pr_val=pp(pr_raw) if pr_raw else 0
   try:c.execute("INSERT INTO agent_keys(code,discount,days,price,created_by,date) VALUES(?,?,?,?,?,?)",(code,d_val,days_val,pr_val,u['username'],str(datetime.datetime.now())));c.commit()
   except:pass
  if act=='del_agent_key':c.execute("DELETE FROM agent_keys WHERE id=?",(request.form.get('kid'),));c.commit()
  if act=='add_coupon':
   try:c.execute("INSERT INTO coupons(code,value,type,max_use,used,active) VALUES(?,?,?,?,0,1)",(request.form.get('coupon_code','').strip().upper(),float(request.form.get('coupon_value',0) or 0),request.form.get('coupon_type','percent'),int(request.form.get('coupon_max_use',0) or 0)));c.commit()
   except:pass
  if act=='del_coupon':c.execute("DELETE FROM coupons WHERE id=?",(request.form.get('coupon_id'),));c.commit()
  if act=='toggle_coupon':c.execute("UPDATE coupons SET active=1-active WHERE id=?",(request.form.get('coupon_id'),));c.commit()
  if act=='add_stock_all':
   kind=request.form.get('kind');sid=request.form.get('item_id');ns=request.form.get('add_stock','').strip()
   if sid and ns:
    tbl='products' if kind=='product' else 'variants';old=c.execute(f"SELECT stock FROM {tbl} WHERE id=?",(sid,)).fetchone()[0] or '';c.execute(f"UPDATE {tbl} SET stock=? WHERE id=?",(old+NL+ns if old else ns,sid));c.commit()
  if act=='edit_user':
   fn=up(request.files.get('new_avatar'))
   if fn:c.execute("UPDATE users SET username=?, password=?, coin=?, role=?, avatar=? WHERE id=?",(request.form.get('new_username'),request.form.get('new_password'),pp(request.form.get('new_coin')),request.form.get('new_role'),fn,request.form.get('uid')))
   else:c.execute("UPDATE users SET username=?, password=?, coin=?, role=? WHERE id=?",(request.form.get('new_username'),request.form.get('new_password'),pp(request.form.get('new_coin')),request.form.get('new_role'),request.form.get('uid')))
   c.commit()
  if act=='restore_all':
   bf=request.files.get('backup_file')
   try:
    if bf and bf.filename:
     data=json.loads(bf.read().decode('utf-8'))
    else:
     p='/sdcard/Download/backup_timshop.json' if os.path.exists('/sdcard/Download/backup_timshop.json') else 'backup_timshop.json'
     with open(p,encoding='utf-8') as f:data=json.load(f)
    for fn,b64 in data.get('files',{}).items():
     try:
      with open(os.path.join(UPLOAD_FOLDER,os.path.basename(fn)),'wb') as wf:wf.write(base64.b64decode(b64))
     except:pass
    if data.get('settings'):
     s=data['settings'][0]
     c.execute("UPDATE settings SET logo=?, banner=?, shop_name=?, promptpay=?, truemoney_phone=?, bank_name=?, bank_acc_name=?, bank_acc_no=?, auto_check=?, disc_on=?, disc_type=?, disc_val=?, maintenance_on=?, maintenance_msg=? WHERE id=1",(s.get('logo',''),s.get('banner',''),s.get('shop_name','timstore'),s.get('promptpay',''),s.get('truemoney_phone',''),s.get('bank_name','ธนาคารกสิกรไทย'),s.get('bank_acc_name',''),s.get('bank_acc_no',''),s.get('auto_check',1),s.get('disc_on',0),s.get('disc_type','percent'),s.get('disc_val',0),s.get('maintenance_on',0),s.get('maintenance_msg','กำลังปิดปรับปรุงระบบและอัปเดตเว็บไซต์ชั่วคราว ขออภัยในความไม่สะดวกครับ')))
    for t in ['categories','zones','products','variants','coupons','credit_codes','agent_keys','agents','topups']:
     if t in data:c.execute(f"DELETE FROM {t}")
    for ct in data.get('categories',[]):c.execute("INSERT OR REPLACE INTO categories(id,name,icon,order_num) VALUES(?,?,?,?)",(ct['id'],ct['name'],ct.get('icon','📦'),ct.get('order_num',0)))
    for z in data.get('zones',[]):c.execute("INSERT OR REPLACE INTO zones(id,name,icon,order_num,img) VALUES(?,?,?,?,?)",(z['id'],z['name'],z.get('icon','🔥'),z.get('order_num',0),z.get('img','')))
    for pr in data.get('products',[]):c.execute("INSERT OR REPLACE INTO products(id,zone_id,category_id,name,price,agent_price,desc,img,stock,date) VALUES(?,?,?,?,?,?,?,?,?,?)",(pr['id'],pr['zone_id'],pr.get('category_id',0),pr['name'],pr['price'],pr.get('agent_price',0),pr.get('desc',''),pr.get('img',''),pr.get('stock',''),pr.get('date','')))
    for v in data.get('variants',[]):c.execute("INSERT OR REPLACE INTO variants(id,product_id,name,price,agent_price,stock,date) VALUES(?,?,?,?,?,?,?)",(v['id'],v['product_id'],v['name'],v['price'],v.get('agent_price',0),v.get('stock',''),v.get('date','')))
    for cp in data.get('coupons',[]):c.execute("INSERT OR REPLACE INTO coupons(id,code,value,type,max_use,used,active) VALUES(?,?,?,?,?,?,?)",(cp['id'],cp['code'],cp['value'],cp['type'],cp['max_use'],cp['used'],cp['active']))
    for cc in data.get('credit_codes',[]):c.execute("INSERT OR REPLACE INTO credit_codes(id,code,amount,used_by,used) VALUES(?,?,?,?,?)",(cc['id'],cc['code'],cc['amount'],cc.get('used_by',''),cc.get('used',0)))
    for ak in data.get('agent_keys',[]):c.execute("INSERT OR REPLACE INTO agent_keys(id,code,discount,days,price,created_by,used_by,used,date) VALUES(?,?,?,?,?,?,?,?,?)",(ak['id'],ak['code'],ak.get('discount',10),ak.get('days',30),ak.get('price',0),ak.get('created_by','admin'),ak.get('used_by',''),ak.get('used',0),ak.get('date','')))
    for ag in data.get('agents',[]):c.execute("INSERT OR REPLACE INTO agents(id,username,discount,expire,renewed_cycle,date) VALUES(?,?,?,?,?,?)",(ag['id'],ag['username'],ag.get('discount',10),ag.get('expire',''),ag.get('renewed_cycle',''),ag.get('date','')))
    for t in data.get('topups',[]):c.execute("INSERT OR REPLACE INTO topups(id,username,amount,method,slip,envelope_link,phone,status,date) VALUES(?,?,?,?,?,?,?,?,?)",(t['id'],t['username'],t['amount'],t.get('method',''),t.get('slip',''),t.get('envelope_link',''),t.get('phone',''),t.get('status','pending'),t.get('date','')))
    c.commit();c.close();return base("<div class='box'><h2>✅ กู้ข้อมูลทั้งหมดแล้ว!</h2><a href='/profile'><button>กลับ</button></a></div>")
   except Exception as e:c.close();return base(f"<div class='box'>❌ กู้ข้อมูลไม่สำเร็จ {e}</div>")
 c.close();return redirect('/profile')
@app.route('/backup')
def backup():
 u=cur()
 if not is_admin(u):return redirect('/login')
 js=write_auto_backup()
 return Response(js,mimetype='application/json',headers={'Content-Disposition':'attachment;filename=backup_timshop.json'})
init()
if __name__=='__main__':
 port=int(os.environ.get('PORT',5000))
 app.run(host='0.0.0.0',port=port,debug=False)
