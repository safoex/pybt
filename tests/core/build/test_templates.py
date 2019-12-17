from unittest import TestCase
from src.core.build.yaml.templates import Templates
from src.core.memory.memory import Memory

class TestTemplates(TestCase):
    def setUp(self) -> None:
        self.memory = Memory()
        self.templates = Templates(self.memory)

    def test_load(self):
        tmplt = """
        nodes:
        """
        self.templates.load_template()