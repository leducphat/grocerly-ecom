import os
import google.generativeai as genai
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.models import Product, Category
from store_api.serializers import ProductSerializer, CategorySerializer

class ProductListAPI(generics.ListAPIView):
    queryset = Product.objects.filter(status=True, in_stock=True)
    serializer_class = ProductSerializer

class CategoryListAPI(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

# ================= AI CHAT CONFIGURATION ================= #

def search_products(query: str) -> list[dict]:
    """Search for products in the grocery store based on a text query.
    Call this whenever the user asks about product availability, price, details, or stock.
    Returns a list of matching products.
    """
    products = Product.objects.filter(title__icontains=query, status=True, in_stock=True)[:5]
    if not products.exists():
        return [{"message": "No matching products found."}]
        
    results = []
    for p in products:
        results.append({
            "title": p.title,
            "price": f"{float(p.price)} VND",
            "stock_count": p.stock_count,
            "weight_volume": p.weight_volume,
            "product_url_id": p.p_id
        })
    return results

def request_add_to_cart(product_url_id: str, qty: int = 1):
    """Call this function when the user asks to add an item to their cart or wants to buy an item.
    Do not just tell them it's added; you MUST call this function so the system can confirm it.
    Provide the exact product_url_id from the search results, and how many they want (qty).
    """
    pass

def request_checkout():
    """Call this function when the user asks to checkout, pay, or place their order."""
    pass

def get_bestsellers() -> list[dict]:
    """Get the bestselling and featured products of the store.
    Call this when the user asks what is popular or what to buy.
    """
    products = Product.objects.filter(featured=True, status=True, in_stock=True)[:5]
    results = []
    for p in products:
        results.append({
            "title": p.title,
            "price": f"{float(p.price)} VND"
        })
    return results

api_key = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=api_key)

try:
    # Initialize the model with tools and system instruction
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash-latest',
        tools=[search_products, get_bestsellers, request_add_to_cart, request_checkout],
        system_instruction=(
            "You are Grocerly Assistant, the AI shopping assistant for Grocerly E-commerce. "
            "You are polite, helpful, and concise. "
            "Always use the provided tools to search for products when the user asks about them. "
            "If quoting a price, mention the VND currency clearly. "
            "If a user wants to buy something, or add to cart, YOU MUST use the request_add_to_cart tool! "
            "If they ask to checkout, use the request_checkout tool."
        )
    )
    # create a global conversation history placeholder or start chat
    # To support multiple users effectively, we should let the frontend pass history,
    # but for this MVP, we will instantiate a new chat per request and pass history.
except Exception as e:
    model = None
    print(f"Failed to initialize Gemini Model: {e}")

@api_view(['POST'])
def ai_chat(request):
    if not model or not api_key:
        return Response({
            "reply": "System Error: Gemini API Key is missing or invalid. Please configure it in .env."
        }, status=200) # Returns 200 so UI doesn't crash, but shows warning.
        
    user_message = request.data.get('message', '')
    history_data = request.data.get('history', [])
    
    if not user_message:
        return Response({"error": "Empty message"}, status=400)

    try:
        # Convert frontend history to gemini history format
        formatted_history = []
        for msg in history_data:
            role = 'model' if msg.get('role') == 'assistant' else 'user'
            formatted_history.append({"role": role, "parts": [msg.get('content', '')]})

        # Initialize chat with history (disabling automatic function calling)
        chat = model.start_chat(history=formatted_history)
        
        response = chat.send_message(user_message)
        
        # Manual loop to process function calls (max 3 loops to prevent recursion)
        for _ in range(3):
            if not response.parts:
                break
                
            # Collect all function calls from the response
            function_calls_to_execute = []
            for part in response.parts:
                if part.function_call:
                    function_calls_to_execute.append(part.function_call)
                    
            if not function_calls_to_execute:
                break
                
            # We process the first function call for simplicity
            fc = function_calls_to_execute[0]
            name = fc.name
            args = {k: v for k, v in fc.args.items()} if hasattr(fc.args, 'items') else dict(fc.args)
            
            if name == "request_add_to_cart":
                p_id = args.get('product_url_id')
                # Handle possible float representation from JSON
                try:
                    qty = int(float(args.get('qty', 1)))
                except Exception:
                    qty = 1

                p = Product.objects.filter(p_id=p_id).first()
                if p:
                    # Interrupt conversation to ask for UI confirmation
                    return Response({
                        "reply": f"Would you like to add **{qty}x {p.title}** to your cart?",
                        "action": "confirm_add_cart",
                        "product": {
                            "id": str(p.id),
                            "pid": p.p_id,
                            "title": p.title,
                            "qty": qty,
                            "price": str(p.price),
                            "image": p.image.url if p.image else ""
                        }
                    })
                else:
                    response = chat.send_message([{
                        "function_response": {
                            "name": name,
                            "response": {"error": "Product not found"}
                        }
                    }])
                    continue

            elif name == "request_checkout":
                return Response({
                    "reply": "You can review your items and complete your order at the checkout page.",
                    "action": "confirm_checkout"
                })

            elif name == "search_products":
                query_val = args.get('query', '')
                results = search_products(query_val)
                response = chat.send_message([{
                    "function_response": {
                        "name": name,
                        "response": {"result": results}
                    }
                }])
                return Response({
                    "reply": response.text,
                    "hidden_context": f"(SYSTEM CONTEXT - DO NOT MENTION: Latest Search Results: {results})"
                })
                
            elif name == "get_bestsellers":
                results = get_bestsellers()
                response = chat.send_message([{
                    "function_response": {
                        "name": name,
                        "response": {"result": results}
                    }
                }])
                return Response({
                    "reply": response.text,
                    "hidden_context": f"(SYSTEM CONTEXT - DO NOT MENTION: Latest Bestsellers: {results})"
                })
                
            else:
                break
        
        return Response({
            "reply": response.text
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if "429" in error_msg or "Quota" in error_msg:
            return Response({"reply": "Hệ thống AI đang quá tải do giới hạn miễn phí (Rate Limit). Vui lòng đợi khoảng 15-30 giây rồi thử lại nhé!"}, status=200)
        return Response({"reply": "I am having trouble connecting to my brain right now. Try again later!"}, status=200)
