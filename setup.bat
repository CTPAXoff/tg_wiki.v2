@echo off
echo Setting up Telegram Parser...

REM Create .env file if it doesn't exist
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please edit it with your Telegram API credentials.
)

REM Setup backend
echo Setting up backend...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r ..\requirements.txt

REM Setup frontend
echo Setting up frontend...
cd ..\frontend
npm install

echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your Telegram API credentials
echo 2. Run backend: cd backend ^&^& venv\Scripts\activate ^&^& python run.py
echo 3. Run frontend: cd frontend ^&^& npm run dev
echo 4. Open http://localhost:5173 in your browser

pause