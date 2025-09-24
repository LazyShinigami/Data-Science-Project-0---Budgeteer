import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

url = os.getenv("SUPABASE_URL")
api_key = os.getenv("SUPABASE_KEY")
supabase_db = create_client(url, api_key)
print("Checkpoint 0 === ", supabase_db)


class CRUD:
    def createRecord(self, data:  dict): # accepting a dictionary (map) as parameter to add to the table
        try: 
            response = supabase_db.table('transactions').select('*').execute()
            print("Added Record Successfully === ", response)
            return response.data
        except Exception as e:
            print('Got an error while adding record! ===', e)
            return 'E-R-R-O-R'
    
    def readRecord(self):
        try:
            response = supabase_db.table('transactions').select('*').execute()
            print("Added Record Successfully === ", response)
            return response.data
            
        except Exception as e:
            print('Got an error while adding record! ===', e)
            return 'E-R-R-O-R'


