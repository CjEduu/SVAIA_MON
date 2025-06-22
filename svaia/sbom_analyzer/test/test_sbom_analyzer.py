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
        
    def test_correct_sbom_parses_and_gives_correct_results(self):
        # Ill pass it the correct little sbom i have that should only have 1 CVE
        response = self.client.post("/analizar_sbom",json= {
                  "bomFormat": "CycloneDX",
                  "specVersion": "1.2",
                  "serialNumber": "urn:uuid:1f860713-54b9-4253-ba5a-9554851904af",
                  "version": 1,
                  "metadata": {
                    "timestamp": "2020-08-03T03:20:53.771Z",
                    "tools": [
                      {
                        "vendor": "CycloneDX",
                        "name": "Node.js module",
                        "version": "2.0.0"
                      }
                    ],
                    "component": {
                      "type": "library",
                      "bom-ref": "pkg:npm/juice-shop@11.1.2",
                      "name": "juice-shop",
                      "version": "11.1.2",
                      "description": "Probably the most modern and sophisticated insecure web application",
                      "licenses": [
                        {
                          "license": {
                            "id": "MIT"
                          }
                        }
                      ],
                      "purl": "pkg:npm/juice-shop@11.1.2",
                      "externalReferences": [
                        {
                          "type": "website",
                          "url": "https://owasp-juice.shop"
                        },
                        {
                          "type": "issue-tracker",
                          "url": "https://github.com/bkimminich/juice-shop/issues"
                        },
                        {
                          "type": "vcs",
                          "url": "git+https://github.com/bkimminich/juice-shop.git"
                        }
                      ]
                    }
                  },
                  "components": [
                    {
                      "type": "library",
                      "bom-ref": "pkg:npm/body-parser@1.19.0",
                      "name": "body-parser",
                      "version": "1.19.0",
                      "description": "Node.js body parsing middleware",
                      "hashes": [
                        {
                          "alg": "SHA-1",
                          "content": "96b2709e57c9c4e09a6fd66a8fd979844f69f08a"
                        }
                      ],
                      "licenses": [
                        {
                          "license": {
                            "id": "MIT"
                          }
                        }
                      ],
                      "purl": "pkg:npm/body-parser@1.19.0",
                      "externalReferences": [
                        {
                          "type": "website",
                          "url": "https://github.com/expressjs/body-parser#readme"
                        },
                        {
                          "type": "issue-tracker",
                          "url": "https://github.com/expressjs/body-parser/issues"
                        },
                        {
                          "type": "vcs",
                          "url": "git+https://github.com/expressjs/body-parser.git"
                        }
                      ]
                    }
                  ]
                })

        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["CVES"][0]["id"], "CVE-2024-45590")

<<<<<<< HEAD
    def test_unsupported_sbom_format(self):
        response = self.client.post("/analizar_sbom", json={"bomFormat": "SPDX", "specVersion": "3.0.1"})
        self.assertIn(response.status_code, (400, 422))

    def test_malicious_sbom_content(self):
        malicious_sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.2",
            "serialNumber": "urn:uuid:malicious",
            "version": 1,
            "metadata": {
                "timestamp": "2020-08-03T03:20:53.771Z",
                "tools": [{"vendor": "<script>alert(1)</script>", "name": "X", "version": "1.0"}],
                "component": {"type": "library", "bom-ref": "pkg:npm/x", "name": "<img src=x onerror=alert(1)>", "version": "1.0"}
            }
        }
        response = self.client.post("/analizar_sbom", json=malicious_sbom)
        self.assertIn(response.status_code, (200, 400, 422))  # Should not crash

    def test_rate_limiting(self):
        for _ in range(10):
            response = self.client.post("/analizar_sbom", json={"bomFormat": "CycloneDX"})
            self.assertIn(response.status_code, (200, 400, 422))

=======
>>>>>>> ddb9f5b88c0198c24a781439214a720dd9b7b5c2
if __name__ == "__main__":
    unittest.main()
