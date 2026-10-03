import snowflake.connector
from pathlib import Path

conn = snowflake.connector.connect(
    account='DWZZADX-GJ83412',
    user='NAVAMSAK',
    authenticator='snowflake',
    role='ACCOUNTADMIN',
    warehouse='COMPUTE_WH',
    database='CARE360_DB',
    password='Iloveicecre@m23',
    schema='PUBLIC',
)

cur = conn.cursor()
cur.execute("""
    SELECT GET_PRESIGNED_URL(
        @CARE360_DB.PUBLIC.CARE360_COPILOT,
        'streamlit_app.py',
        3600
    )
""")
url = cur.fetchone()[0]
print(f"URL: {url}")

import urllib.request
urllib.request.urlretrieve(url, r'streamlit\streamlit_app.py')
print("Downloaded streamlit_app.py")
conn.close()
