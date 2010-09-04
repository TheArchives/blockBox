@echo off
cls
echo.
:loop
set choice=
set /p choice=Enter in the name of the map without the .dat: 
java -Xms512M -Xmx512M -cp minecraft-server.jar; OrigFormat load %choice%.dat %choice%
echo Done converting!
goto loop