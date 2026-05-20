import os
import re

directories_to_scan = ['templates', 'store_api']
regex_trans = re.compile(r'{%\s*trans\s+[\'\"]([^\'\"]+)[\'\"]\s*%}')
regex_gettext = re.compile(r'_\([\'\"]([^\'\"]+)[\'\"]\)')

strings = set()

for d in directories_to_scan:
    if not os.path.exists(d):
        continue
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith('.html') or file.endswith('.py'):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    strings.update(regex_trans.findall(content))
                    strings.update(regex_gettext.findall(content))

po_header = r"""msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2024-05-20 10:00+0000\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"Language: \n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"

"""

def write_po(lang):
    os.makedirs(f'locale/{lang}/LC_MESSAGES', exist_ok=True)
    with open(f'locale/{lang}/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
        f.write(po_header)
        for s in sorted(strings):
            f.write(f'msgid "{s}"\n')
            f.write('msgstr ""\n\n')

write_po('vi')
write_po('en')

print(f"Extracted {len(strings)} strings.")
