from dotenv import load_dotenv
import os
load_dotenv()



print("Key Store path: ", os.getenv("KEYSTORE_PATH"))

