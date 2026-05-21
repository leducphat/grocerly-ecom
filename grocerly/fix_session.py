filepath = 'd:/proj/my_github/grocerly_ecom/grocerly/core/views.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("""    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'price': request.GET['price'],
        'image': request.GET['image'],
        'pid': request.GET['pid'],
    }""", """    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': safe_int(request.GET.get('qty')),
        'price': safe_float(request.GET.get('price')),
        'image': request.GET['image'],
        'pid': request.GET['pid'],
    }""")

loop_target = """        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += safe_int(item.get('qty')) * safe_float(item.get('price'))"""

loop_replacement = """        for p_id, item in request.session['cart_data_obj'].items():
            item['qty'] = safe_int(item.get('qty'))
            item['price'] = safe_float(item.get('price'))
            cart_total_amount += item['qty'] * item['price']
        request.session.modified = True"""

content = content.replace(loop_target, loop_replacement)

content = content.replace("cart_data[str(request.GET['id'])]['qty'] = product_qty", "cart_data[str(request.GET['id'])]['qty'] = safe_int(product_qty)")
content = content.replace("cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])", "cart_data[str(request.GET['id'])]['qty'] = safe_int(cart_product[str(request.GET['id'])]['qty'])")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
