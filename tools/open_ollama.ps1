# 設定 ollama 監聽的連接埠 OLLAMA_HOST = 0.0.0.0
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0", "User")

# 開啟防火牆
New-NetFirewallRule -DisplayName "Ollama VPN Access" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow

# 移除環境變數 
[Environment]::SetEnvironmentVariable("VariableName", $null, "User")

# 移除防火牆規則
Remove-NetFirewallRule -DisplayName "Ollama VPN Access"
