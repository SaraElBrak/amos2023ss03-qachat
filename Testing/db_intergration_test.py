import unittest
from QAChat.db_interface import DBInterface
import os


class DatabaseIntegrationTest(unittest.TestCase):

    def test_init(self):
        try:
            db = DBInterface()
            print("SUPABASE_URL: ", os.environ['SUPABASE_URL'])
        except ConnectionError as e:
            print("Connection Error:", e)
      

if __name__ == '__main__':
    unittest.main()
