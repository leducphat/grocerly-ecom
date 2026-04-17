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
        model_name='gemini-2.5-flash',
        tools=[search_products, get_bestsellers],
        system_instruction=(
            "You are Grocerly Assistant, the AI shopping assistant for Grocerly E-commerce. "
            "You are polite, helpful, and concise. "
            "Always use the provided tools to search for products when the user asks about them. "
            "If quoting a price, mention the VND currency clearly. "
            "If a user wants to buy something, provide them the product title and its price based on the search_products tool output."
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

        # Initialize chat with history and enable auto-calling
        chat = model.start_chat(
            history=formatted_history, 
            enable_automatic_function_calling=True
        )
        
        response = chat.send_message(user_message)
        
        return Response({
            "reply": response.text
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"reply": "I am having trouble connecting to my brain right now. Try again later!"}, status=200)
