import re
import sys

def extract_order_details(text):
    phone_pattern = r'(?:\+88|88)?01[3-9]\d{8}'
    phone_match = re.search(phone_pattern, text)
    details = {'phone': None, 'address': None}
    
    # Extract phone
    if phone_match:
        details['phone'] = phone_match.group(0)
    
    # Extract address
    address_indicators = ['address', 'ঠিকানা', 'dhaka', 'road', 'house', 'block', 'sector']
    if any(ind in text.lower() for ind in address_indicators):
        clean_address = text
        if details['phone']:
            clean_address = clean_address.replace(details['phone'], '')
        
        clean_address = re.sub(r'address|phone|mobile|delivery|to|:|ঠিকানা|মোবাইল|নাম্বার', '', clean_address, flags=re.IGNORECASE).strip()
        
        if len(clean_address) > 5:
            details['address'] = clean_address
            
    return details

# Test cases
test_cases = [
    "01609132361",
    "green model town dhaka 1214",
    "my phone is 01609132361 and address is green model town dhaka 1214",
    "House 12, Road 5, Block B, Dhaka",
    "ঠিকানা: গ্রিন মডেল টাউন",
]

for tc in test_cases:
    print(f"Input: {tc}")
    print(f"Output: {extract_order_details(tc)}")
    print("-" * 20)
