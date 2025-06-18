import unittest
from fastapi.testclient import TestClient
from metrics_handler.src.main import app
import json

class TestWebSocketEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.valid_token = "token1"
        self.invalid_token = "invalid"

    def test_agent_rejects_invalid_token(self):
        with self.client.websocket_connect("/ws/agent") as websocket:
            websocket.send_text(self.invalid_token)
            message = websocket.receive()
            self.assertEqual(message["type"], "websocket.close")
            self.assertEqual(message["code"], 1008)

    def test_client_rejects_invalid_token(self):
        with self.client.websocket_connect("/ws/get_data") as websocket:
            websocket.send_text(self.invalid_token)
            message = websocket.receive()
            self.assertEqual(message["type"], "websocket.close")
            self.assertEqual(message["code"], 1008)

    def test_valid_agent_and_client_communication(self):
        agent = self.client.websocket_connect("/ws/agent")
        client = self.client.websocket_connect("/ws/get_data")

        agent.__enter__()
        client.__enter__()

        agent.send_text(self.valid_token)
        client.send_text(self.valid_token)

        # Simulate valid data
        valid_payload = {
        "message_type": "system",
        "host": "agent1",
        "timestamp": "2025-06-18T12:00:00Z",
        "data": {
            "total_memory": 16000,
            "used_memory": 8000,
            "total_swap": 2000,
            "used_swap": 500,
            "cpu_usage": 23.5,
            "load_avg": [0.12, 0.34, 0.56],
            "uptime": 123456
            }
        }       
        agent.send_text(json.dumps(valid_payload))
        # Client should receive it
        msg = client.receive_text()
        parsed = json.loads(msg)

        self.assertEqual(parsed["message_type"],"system")
        self.assertEqual(parsed["host"], "agent1")

        agent.__exit__(None, None, None)
        client.__exit__(None, None, None)

if __name__ == "__main__":
    unittest.main()

