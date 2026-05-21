import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "grocerly.settings")
django.setup()
sys.stdout.reconfigure(encoding='utf-8')

from taggit.models import Tag, TaggedItem

def clean_broken_tags():
    # Tìm các tag bị tách từng chữ (ví dụ độ dài <= 2 hoặc rỗng) 
    # Hoặc các tag do lỗi tách chữ sinh ra
    broken_tags = Tag.objects.filter(name__iregex=r'^.{1,2}$')
    
    count = 0
    for tag in broken_tags:
        # Lấy danh sách liên kết giữa Tag này và các Sản phẩm
        tagged_items = TaggedItem.objects.filter(tag=tag)
        
        # Xóa liên kết an toàn
        tagged_items.delete()
        
        # Sau khi không còn sản phẩm nào dùng tag này, xóa tag đi
        print(f"Deleting broken tag: '{tag.name}' (slug: {tag.slug})")
        tag.delete()
        count += 1
        
    print(f"\nDa xoa thanh cong {count} tag loi!")

if __name__ == "__main__":
    clean_broken_tags()
