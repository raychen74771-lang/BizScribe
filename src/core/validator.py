import re
class QualityGate:
    @staticmethod
    def needs_repair(text: str) -> bool:
        if not text or len(text) < 10: return True
        punc = len(re.findall(r'[.,;!?，。；！？]', text))
        if punc / len(text) < 0.01: return True
        return False
