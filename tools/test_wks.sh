IP="172.20.187.116"
curl -X POST http://${IP}:8080/__API__/WKS/commit \
  -H "Content-Type: application/json" \
  -d '{"sensor_id": "temp_01", "temperature": 24.5, "status": "active"}'
