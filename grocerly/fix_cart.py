import re

filepath = 'd:/proj/my_github/grocerly_ecom/grocerly/core/views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

helper = '''
def safe_float(val, default=0.0):
    try:
        return float(str(val).replace(',', ''))
    except (ValueError, TypeError):
        return default

def safe_int(val, default=1):
    try:
        return int(float(str(val).replace(',', '')))
    except (ValueError, TypeError):
        return default
'''

if 'def safe_float' not in content:
    # insert after imports
    parts = content.split('from userauths.models import Profile', 1)
    content = parts[0] + 'from userauths.models import Profile\n\n' + helper + parts[1]

content = content.replace("int(item['qty'])", "safe_int(item.get('qty'))")
content = content.replace("float(item['qty'])", "float(safe_int(item.get('qty')))")
content = content.replace("float(item['price'])", "safe_float(item.get('price'))")
content = content.replace("price=item['price']", "price=safe_float(item.get('price'))")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
