import os
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    # Fix dynamic product links
    content = re.sub(r'<h2><a href="shop-product-right\.html">({{ p\.title }})</a></h2>', r'<h2><a href="{% url \'core:product-detail\' p.pid %}">\1</a></h2>', content)

    # Fix dynamic product image links
    content = re.sub(r'<a href="shop-product-right\.html">\s*(<img class="default-img" src="{{ p\.image\.url }}" alt="" />)\s*(<img class="hover-img" src="{{ p\.image\.url }}" alt="" />)\s*</a>', r'<a href="{% url \'core:product-detail\' p.pid %}">\n                                            \1\n                                            \2\n                                        </a>', content)

    # Replace remaining shop-product-right.html with coming-soon
    content = content.replace('"shop-product-right.html"', '"{% url \'core:coming-soon\' %}"')
    content = content.replace('"vendor-details-1.html"', '"{% url \'core:coming-soon\' %}"')
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")

for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            fix_file(os.path.join(root, file))

print('Done')
