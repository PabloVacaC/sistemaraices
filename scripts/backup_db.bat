@echo off
REM =============================================================================
REM Script de Respaldo Automatizado de Base de Datos para Windows (Docker)
REM Sistemas Raíces
REM =============================================================================

set CONTAINER_NAME=raices_db
set DB_NAME=sistemraices_db
set DB_USER=postgres
set BACKUP_DIR=backups

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

set BACKUP_FILE=%BACKUP_DIR%\backup_%DB_NAME%_%TIMESTAMP%.sql

echo [%date% %time%] Creando respaldo de %DB_NAME% desde %CONTAINER_NAME%...
docker exec %CONTAINER_NAME% pg_dump -U %DB_USER% -d %DB_NAME% > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] Respaldo generado con exito: %BACKUP_FILE%
) else (
    echo [ERROR] No se pudo generar el respaldo. Verifique que el contenedor Docker este corriendo.
)

