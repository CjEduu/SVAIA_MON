import unittest 
from fastapi.testclient import TestClient
from sbom_analyzer.src.main import app


class TestSbomAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # Just to test correct functionality of the test
    def test_ping(self):
        response = self.client.get("/ping")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "pong"})


    def test_if_empty_sbom_doesnt_parse(self):
        response= self.client.post("/analizar_sbom")
        self.assertEqual(response.status_code,422) # 422 = Unprocesable Entity 

    def test_if_wrong_sbom_doesnt_parse(self):
        # Formato necesario visible en src/cycloneDX.py
        # Just a little SBOM that does not have all the required parameters
        response = self.client.post("/analizar_sbom",
                                    json={"BomFormat":"CycloneDX"} )
        self.assertEqual(response.status_code,422)

        # Missing serialNumber
        response = self.client.post("/analizar_sbom",json=
                                    {
                                        "bomFormat": "CycloneDX",
                                        "specVersion": "1.2",
                                        "version": 1,
                                        "metadata": {
                                            "timestamp": "2020-08-03T03:20:53.771Z",
                                            "tools": [
                                                {
                                                    "vendor": "oneDX",
                                                    "name": "Node.js module",
                                                    "version": "2.0.0"
                                                }
                                            ],
                                            "component": {
                                                "type": "library",
                                                "bom-ref": "pkg:npm/juice-shop@11.1.2",
                                                "name": "juice-shop",
                                                "version": "11.1.2",
                                                "description": "Probably the most modern and sophisticated insecure web application"
                                            }
                                        }
                                    }
                                )
        self.assertEqual(response.status_code,422)
        

if __name__ == "__main__":
    unittest.main()
