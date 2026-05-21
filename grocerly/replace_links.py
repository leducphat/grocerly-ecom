import os
import glob

def replace_in_files(directory, old_str, new_str):
    for filepath in glob.glob(os.path.join(directory, '**/*.html'), recursive=True):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_str in content:
            content = content.replace(old_str, new_str)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filepath}")

if __name__ == "__main__":
    templates_dir = r"d:\proj\my_github\grocerly_ecom\grocerly\templates"
    replace_in_files(templates_dir, 'shop-wishlist.html', "{% url 'core:wishlist' %}")
    print("Done replacing.")
