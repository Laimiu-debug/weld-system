import os, sys, json, secrets
from pathlib import Path
from datetime import datetime,timedelta
sys.path.insert(0,str(Path('backend').resolve()))
from app.core.config import settings
from sqlalchemy import create_engine,text
schema='qa_business_f06_f11_20260905'
url=settings.DATABASE_URL
engine=create_engine(url,echo=False)
with engine.begin() as c:
 exists=c.execute(text('SELECT 1 FROM pg_namespace WHERE nspname=:name'),{'name':schema}).scalar()
 if not exists: c.execute(text('CREATE SCHEMA '+schema))
 else:
  count=c.execute(text('SELECT count(*) FROM pg_tables WHERE schemaname=:name'),{'name':schema}).scalar()
  if count: raise RuntimeError('Test schema is not empty')
os.environ['PGOPTIONS']='-c search_path='+schema
os.environ['DEBUG']='false'
from app.core.database import Base,engine as scoped_engine,SessionLocal
from sqlalchemy import event
@event.listens_for(scoped_engine, 'connect')
def set_schema(connection, record):
 old=connection.autocommit
 connection.autocommit=True
 with connection.cursor() as cursor: cursor.execute('SET SESSION search_path TO '+schema)
 connection.autocommit=old
with scoped_engine.connect() as c:
 assert c.execute(text('SELECT current_schema()')).scalar()==schema
from app.scripts.bootstrap_schema import import_all_models
import_all_models()
Base.metadata.create_all(scoped_engine)
from app.models.user import User
from app.models.company import Company,CompanyEmployee,Factory
from app.core.security import get_password_hash
password=secrets.token_urlsafe(24)
with SessionLocal() as db:
 users=[]
 for name,tier in [('f06_personal','personal_flagship'),('f06_enterprise','enterprise'),('f06_outsider','personal_flagship')]:
  user=User(username=name,email=name+'@example.com',hashed_password=get_password_hash(password),full_name='F06 专用测试账号',is_active=True,is_verified=True,member_tier=tier,membership_type='enterprise' if tier=='enterprise' else 'personal',subscription_status='active',subscription_end_date=datetime.utcnow()+timedelta(days=7))
  db.add(user);db.flush();users.append(user)
 company=Company(name='F06 焊材验收测试企业',owner_id=users[1].id,membership_tier='enterprise',is_active=True)
 db.add(company);db.flush()
 factory=Factory(name='F06 测试工厂',code='F06-FACTORY',company_id=company.id)
 db.add(factory);db.flush()
 db.add(CompanyEmployee(company_id=company.id,user_id=users[1].id,role='admin',status='active',factory_id=factory.id))
 db.commit()
 result={'schema':schema,'password':password,'accounts':[{'id':u.id,'email':u.email} for u in users],'company_id':company.id,'factory_id':factory.id}
 path=Path(os.environ['TEMP'])/'weld-f06-credentials.json'
 path.write_text(json.dumps(result),encoding='utf-8')
 print({'schema':schema,'accounts_created':len(users),'credentials_path':str(path)})
