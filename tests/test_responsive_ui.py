import os
from pathlib import Path


def test_mobile_responsive_rules_exist():
    css = Path('static/css/tailwind.css').read_text(encoding='utf-8')
    assert '@media (max-width: 768px)' in css
    assert 'table{display:block' in css
