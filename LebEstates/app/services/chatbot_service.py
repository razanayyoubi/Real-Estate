import json
import requests
from flask import current_app
from app.models.base import db
from app.models.users import Users, SupportSession, SupportMessage
from app.models.property import Property
from app.models.operations import Visit, Consultation, Transaction
from app.models.customer import Customer

class GeminiChatbotService:
    @staticmethod
    def get_ai_user():
        """Retrieve or resolve the System AI User."""
        return Users.query.filter_by(email='ai@lebestates.com').first()

    @staticmethod
    def search_properties(location=None, price_min=None, price_max=None, property_type=None, listing_type=None, rooms=None):
        """Search published properties matching criteria."""
        try:
            query = Property.query.filter_by(status='Published')
            if location:
                query = query.filter(Property.location.ilike(f'%{location}%'))
            if price_min:
                query = query.filter(Property.price >= float(price_min))
            if price_max:
                query = query.filter(Property.price <= float(price_max))
            if property_type:
                query = query.filter(Property.propertyType.ilike(f'%{property_type}%'))
            if listing_type:
                query = query.filter(Property.listingType.ilike(f'%{listing_type}%'))
            if rooms:
                query = query.filter(Property.rooms == int(rooms))
            
            properties = query.order_by(Property.createdAt.desc()).limit(8).all()
            results = []
            for p in properties:
                results.append({
                    'propertyID': p.propertyID,
                    'title': p.title,
                    'description': p.description or '',
                    'propertyType': p.propertyType,
                    'listingType': p.listingType,
                    'location': p.location,
                    'price': float(p.price),
                    'area': float(p.area),
                    'rooms': p.rooms,
                    'bathrooms': p.bathrooms,
                    'parkingAvailable': p.parkingAvailable
                })
            return {'properties': results}
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def get_my_profile(customer_id):
        """Get profile details of the customer."""
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return {'error': 'Customer not found.'}
            return {
                'fullName': customer.user.fullName,
                'email': customer.user.email,
                'phoneNumber': customer.user.phoneNumber or 'N/A',
                'address': customer.address or 'N/A',
                'nationalID': customer.nationalID or 'N/A',
                'documents': [
                    {'documentType': doc.documentType, 'status': doc.status} for doc in customer.documents
                ]
            }
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def get_my_active_operations(customer_id):
        """Get active visits, active consultations, and transactions for the customer."""
        try:
            visits = Visit.query.filter_by(customerID=customer_id).filter(Visit.status != 'Cancelled').all()
            consultations = Consultation.query.filter_by(customerID=customer_id).filter(Consultation.status != 'Cancelled').all()
            transactions = Transaction.query.filter_by(customerID=customer_id).all()
            
            visits_list = []
            for v in visits:
                visits_list.append({
                    'visitID': v.visitID,
                    'propertyTitle': v.property_obj.title,
                    'date': v.visitDate.strftime('%Y-%m-%d'),
                    'time': v.visitTime.strftime('%H:%M'),
                    'status': v.status,
                    'notes': v.notes or ''
                })
                
            cons_list = []
            for c in consultations:
                cons_list.append({
                    'consultationID': c.consultationID,
                    'type': c.consultationType,
                    'method': c.preferredMethod,
                    'status': c.status,
                    'date': c.scheduledDate.strftime('%Y-%m-%d') if c.scheduledDate else 'TBD',
                    'time': c.scheduledTime.strftime('%H:%M') if c.scheduledTime else 'TBD',
                    'notes': c.notes or ''
                })
                
            trans_list = []
            for t in transactions:
                trans_list.append({
                    'transactionID': t.transactionID,
                    'propertyTitle': t.property_obj.title,
                    'type': t.transactionType,
                    'finalPrice': float(t.finalPrice),
                    'amountPaid': float(t.amountPaid),
                    'paymentStatus': t.paymentStatus,
                    'nextDueDate': t.nextDueDate.strftime('%Y-%m-%d') if t.nextDueDate else 'N/A'
                })
                
            return {
                'active_visits': visits_list,
                'active_consultations': cons_list,
                'transactions': trans_list
            }
        except Exception as e:
            return {'error': str(e)}

    @staticmethod
    def escalate_to_human(session_id=None):
        """Escalate session to customer support, assigning it to human queue."""
        return {'success': True, 'message': 'escalate_to_human triggered'}

    @staticmethod
    def get_website_guide():
        """Provide instructions on how to use the website."""
        return {
            'how_to_schedule_visit': 'To request a property visit: navigate to the details page of any property, scroll to the "Schedule a Visit" section, select your preferred date/time, and click "Submit Visit Request". An agent will be assigned to assist you.',
            'how_to_request_consultation': 'To book a consultation: click on "Consultations" in the navigation bar, click the "New Request" button, specify the consultation type, preferred contact method (Phone, Office, Video Call), write your message, and submit.',
            'how_to_add_favorites': 'To save properties: browse the property catalog at "/properties" and click the heart icon on any property card or details page. View them later under your profile menu at "Favorite Properties" ("/favorites").',
            'how_to_upload_verification_docs': 'To upload identification: navigate to your Profile page, scroll to "Verification Documents", upload the front and back of the document, and submit for verification.'
        }

    @classmethod
    def execute_tool(cls, name, args, session_id, customer_id):
        """Local router to execute python functions called by Gemini."""
        if name == 'search_properties':
            return cls.search_properties(**args)
        elif name == 'get_my_profile':
            return cls.get_my_profile(customer_id)
        elif name == 'get_my_active_operations':
            return cls.get_my_active_operations(customer_id)
        elif name == 'escalate_to_human':
            return cls.escalate_to_human()
        elif name == 'get_website_guide':
            return cls.get_website_guide()
        return {'error': f'Tool {name} not found.'}

    @classmethod
    def generate_chatbot_response(cls, user_message, history, customer_id):
        """Invoke Gemini Content Generation API, executing the tool loop if needed."""
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            return "I apologize, but my AI system is currently disabled. Please escalate to a human agent."

        # Format history
        contents = []
        for item in history:
            role = 'model' if item.get('role') == 'model' else 'user'
            contents.append({
                'role': role,
                'parts': [{'text': item.get('text', '')}]
            })
            
        # Append current user message
        contents.append({
            'role': 'user',
            'parts': [{'text': user_message}]
        })

        # Define tools / functions schema
        tools = [
            {
                'functionDeclarations': [
                    {
                        'name': 'search_properties',
                        'description': 'Search published real estate properties based on criteria such as location, price bounds, property type (Apartment, Villa), listing type (Sell, Rent), or rooms count.',
                        'parameters': {
                            'type': 'OBJECT',
                            'properties': {
                                'location': {'type': 'STRING', 'description': 'The city or area name in Lebanon.'},
                                'price_min': {'type': 'NUMBER', 'description': 'Minimum price in USD.'},
                                'price_max': {'type': 'NUMBER', 'description': 'Maximum price in USD.'},
                                'property_type': {'type': 'STRING', 'description': 'e.g., Apartment, Villa.'},
                                'listing_type': {'type': 'STRING', 'description': 'Either "Sell" or "Rent".'},
                                'rooms': {'type': 'INTEGER', 'description': 'Number of rooms.'}
                            }
                        }
                    },
                    {
                        'name': 'get_my_profile',
                        'description': 'Retrieve profile details of the logged-in customer (Full Name, email, phone number, address, and verification status of documents).',
                        'parameters': {
                            'type': 'OBJECT',
                            'properties': {}
                        }
                    },
                    {
                        'name': 'get_my_active_operations',
                        'description': 'Retrieve the logged-in customer\'s current operations: active visits, consultations, and transactions details (prices, due dates, statuses).',
                        'parameters': {
                            'type': 'OBJECT',
                            'properties': {}
                        }
                    },
                    {
                        'name': 'escalate_to_human',
                        'description': 'Transfer this support chat session to customer support representatives. Use this if the customer explicitly requests human support or if their inquiry is complex.',
                        'parameters': {
                            'type': 'OBJECT',
                            'properties': {}
                        }
                    },
                    {
                        'name': 'get_website_guide',
                        'description': 'Get official guides and navigation instructions on how to use the website (e.g. scheduling visits, requesting consultations, uploading verification documents, adding favorites).',
                        'parameters': {
                            'type': 'OBJECT',
                            'properties': {}
                        }
                    }
                ]
            }
        ]

        system_instruction = {
            'parts': [
                {
                    'text': (
                        "ROLE: You represent 'LebEstates' as a helpful, intelligent customer support AI. "
                        "STRICT RULES:\n"
                        "- YOU CANNOT write or modify database records other than via the provided escalate_to_human tool.\n"
                        "- You are friendly and concise. Prioritize answering based on real-time data retrieved from tools.\n"
                        "- Enforce user security. Only answer about properties, active visits, and transactions retrieved from the active tools.\n"
                        "- If the user requests to talk to a human agent, or if you cannot help them, immediately call the 'escalate_to_human' tool.\n"
                        "- Always suggest 'Did this answer your question? If you need a human agent, just say so or click the Escalate button.'"
                    )
                }
            ]
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}

        # Tool calling loop (max 5 iterations)
        for _ in range(5):
            body = {
                'contents': contents,
                'tools': tools,
                'systemInstruction': system_instruction
            }
            
            try:
                response = requests.post(url, json=body, headers=headers, timeout=15)
                if response.status_code != 200:
                    current_app.logger.error(f"Gemini API returned error {response.status_code}: {response.text}")
                    return "I apologize, but I am unable to process your request at the moment. Please try again later or escalate to support."
                
                res_data = response.json()
                candidate = res_data.get('candidates', [{}])[0]
                content = candidate.get('content', {})
                parts = content.get('parts', [])
                
                # Check for function call
                func_call = None
                text_response = ""
                for part in parts:
                    if 'functionCall' in part:
                        func_call = part['functionCall']
                    if 'text' in part:
                        text_response += part['text']
                
                if func_call:
                    name = func_call['name']
                    args = func_call.get('args', {})
                    
                    # Execute tool locally
                    tool_result = cls.execute_tool(name, args, None, customer_id)
                    
                    # Append full model content directly to preserve parts and thoughtSignature
                    contents.append(content)
                    
                    # Append function response part to contents history
                    contents.append({
                        'role': 'function',
                        'parts': [
                            {
                                'functionResponse': {
                                    'name': name,
                                    'response': tool_result
                                }
                            }
                        ]
                    })
                    
                    # If we escalated to a human, we should immediately return the transfer message
                    if name == 'escalate_to_human' and tool_result.get('success'):
                        return "I am transferring this chat to our customer support representatives. A human agent will join shortly. Please wait."
                else:
                    return text_response or "I apologize, I received an empty response. Please try again."
            except Exception as e:
                current_app.logger.error(f"Error calling Gemini: {e}")
                return "I apologize, but an error occurred while generating a response. Please try again later."
        
        return "I apologize, but the request exceeded processing steps. Please speak to a human support agent."
