from datetime import datetime, timedelta, timezone
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

url = os.getenv("SUPABASE_URL")
api_key = os.getenv("SUPABASE_KEY")
supabase_db = create_client(url, api_key)
# print("Checkpoint 0 === ", supabase_db)


class CRUD:
    def createRecord(self, data:  dict): # accepting a dictionary (map) as parameter to add to the table
        try: 
            response = supabase_db.table('transactions').select('*').execute()
            # print("Added Record Successfully === ", response)
            return response.data
        except Exception as e:
            print(f'Got an error while adding record! === {e}')
            return str(e)
    
    def readAllRecords(self,userID = None):
        try:
            query = supabase_db.table('transactions').select('*').eq('userID', userID)

           

            response = query.execute()
            return response.data
            
        except Exception as e:
            print('Got an error while reading record! ===', e)
            return f'E-R-R-O-R ===> {e}'

    def readRecordByDateFilter(self, userID = None,date_filter = None):
            try:
                query = supabase_db.table('transactions').select('*').eq('userID', userID)
                if date_filter:
                    today = datetime.now(timezone.utc).date()
                    # print(today)
                    past_date = today - timedelta(days=date_filter)
                    query = query.gte("date", past_date.isoformat())

                response = query.execute()
                return response.data
                
            except Exception as e:
                print('Got an error while reading record! ===', e)
                return f'E-R-R-O-R ===> {e}'

