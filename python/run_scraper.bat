@echo off
cd /d "%~dp0"
echo ==================================================== >> pipeline_log.txt
echo [%DATE% %TIME%] Starting Pipeline... >> pipeline_log.txt

echo 1. Scraping latest data... >> pipeline_log.txt
"C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" scraper.py >> pipeline_log.txt 2>&1

echo 2. Transforming and computing metrics... >> pipeline_log.txt
"C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" transform_data.py >> pipeline_log.txt 2>&1

echo 3. Loading to SQL Server... >> pipeline_log.txt
"C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe" load_to_sql.py >> pipeline_log.txt 2>&1

echo [%DATE% %TIME%] Pipeline completed successfully. >> pipeline_log.txt
