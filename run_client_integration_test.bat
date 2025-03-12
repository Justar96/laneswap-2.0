@echo off
REM Run the client integration test
REM Usage: run_client_integration_test.bat <mongodb_uri>

if "%1"=="" (
    echo MongoDB URI is required
    echo Usage: run_client_integration_test.bat ^<mongodb_uri^>
    exit /b 1
)

python run_client_integration_test.py --mongodb-uri=%1 