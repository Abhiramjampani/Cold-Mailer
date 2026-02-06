"""
Script to create a sample Excel file with HR contacts
Run this once to create the template
"""

import pandas as pd

# Sample data
sample_data = {
    'Email': [
        'hr.example@google.com',
        'recruitment@microsoft.com',
        'careers@amazon.com',
        'talent@flipkart.com',
        'hr@razorpay.com'
    ],
    'HR Name': [
        'Priya Sharma',
        'John Smith',
        'Rahul Verma',
        'Sneha Patel',
        'Amit Kumar'
    ],
    'Company Name': [
        'Google',
        'Microsoft',
        'Amazon',
        'Flipkart',
        'Razorpay'
    ]
}

df = pd.DataFrame(sample_data)
df.to_excel('sample_contacts.xlsx', index=False)
print("✅ Created sample_contacts.xlsx")
print("\nSample contents:")
print(df.to_string(index=False))
