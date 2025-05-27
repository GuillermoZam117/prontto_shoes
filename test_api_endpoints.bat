@echo off
echo Testing Reportes Avanzados API Endpoints

echo.
echo === Testing Connection to Server ===
curl -s -o nul -w "Status: %%{http_code}\n" http://127.0.0.1:8000/

echo.
echo === Testing Reportes Dashboard ===
curl -s -o nul -w "Status: %%{http_code}\n" http://127.0.0.1:8000/reportes/

echo.
echo === Testing API Reportes Personalizados ===
curl -s -o nul -w "Status: %%{http_code}\n" http://127.0.0.1:8000/api/reportes_personalizados/

echo.
echo === Testing API Schema ===
curl -s -o nul -w "Status: %%{http_code}\n" http://127.0.0.1:8000/api/schema/

echo.
echo === Testing Reportes Avanzados Endpoint ===
curl -s -o nul -w "Status: %%{http_code}\n" http://127.0.0.1:8000/reportes/api/avanzados/

echo.
echo Tests completed!
