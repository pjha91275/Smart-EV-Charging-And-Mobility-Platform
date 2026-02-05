@echo off
REM Quick setup script for Smart EV Charging - Gemini API Configuration

echo.
echo ========================================
echo Smart EV Charging - Gemini API Setup
echo ========================================
echo.

REM Check if .env file exists
if exist .env (
    echo ✅ .env file found
) else (
    echo ⚠️ .env file not found
    echo Creating .env from .env.example...
    
    if exist .env.example (
        copy .env.example .env
        echo ✅ .env created successfully
        echo.
        echo 📝 IMPORTANT: Edit .env and add your Gemini API key:
        echo    GEMINI_API_KEY=your-api-key-here
    ) else (
        echo ❌ .env.example not found
    )
)

echo.
echo Checking Python dependencies...
pip install -q python-dotenv 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ python-dotenv installed
) else (
    echo ⚠️ Could not install python-dotenv
    echo   Run: pip install python-dotenv
)

echo.
echo Verifying Gemini API Key...
python -c "import os; from dotenv import load_dotenv; load_dotenv(); api_key = os.getenv('GEMINI_API_KEY', ''); status = '✅' if api_key and api_key.startswith('AIza') else '⚠️'; masked = api_key[:10] + '...' if len(api_key) > 10 else 'Not set'; print(f'{status} API Key: {masked}')" 2>nul

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your Gemini API key
echo 2. Run: python app.py
echo 3. Visit: http://localhost:5000/user/chat
echo.
pause
