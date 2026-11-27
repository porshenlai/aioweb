# aioweb

## Web Server based on Python Asynchornouse I/O Modules

### Linux or Windows WSL
* (BOURNE SHELL)
	- &gt; ./play.sh

### Windows
* (POWER SHELL)
	- [WIN+r] powershell &crarr;
	- &gt; Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser
	- &gt; play.ps1

* (FIREWALL)
	- (Add firewall rule)
	- &gt; New-NetFirewallRule -DisplayName "AIO Web Server" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow
	- (Delete firewall rule)
	- &gt; Remove-NetFirewallRule -DisplayName "AIO Web Server"

## Configuration
* Location: etc/*.json
* Sample: play.sh etc/ollama.json
* Sample: play.ps1 etc/ollama.json
