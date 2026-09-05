import os,sys
from pathlib import Path
sys.path.insert(0,str(Path('backend').resolve()))
os.environ['DEBUG']='false'
os.environ['DEVELOPMENT']='true'
from app.core.database import engine
from sqlalchemy import event,text
@event.listens_for(engine,'connect')
def select_schema(connection, record):
 old=connection.autocommit;connection.autocommit=True
 with connection.cursor() as cursor: cursor.execute('SET SESSION search_path TO qa_materials_f05_20260905')
 connection.autocommit=old
with engine.connect() as c:
 assert c.execute(text('SELECT current_schema()')).scalar()=='qa_materials_f05_20260905'
from app.main import app
import uvicorn
uvicorn.run(app,host='127.0.0.1',port=8000,log_level='warning')
