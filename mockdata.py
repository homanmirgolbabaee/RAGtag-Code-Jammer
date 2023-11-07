import pandas as pd
from fpdf import FPDF

# Define a simple set of FAQs as an example
faq_data = {
    "Question": [
        "How can I reset my password?",
        "Where can I find the user manual?",
        "What is the refund policy?",
        "How do I track my order?",
        "What are the warranty terms?"
    ],
    "Answer": [
        "To reset your password, go to the settings page and click on 'Forgot Password'.",
        "The user manual can be found on the product page under the 'Documentation' section.",
        "Our refund policy lasts 30 days. If 30 days have gone by since your purchase, unfortunately, we cannot offer you a refund or exchange.",
        "You can track your order by logging into your account and visiting the 'Orders' section.",
        "Our products come with a one year warranty. For more details, please visit the warranty section on our website."
    ],
    "Category": [
        "Account Issues",
        "Product Information",
        "Returns and Refunds",
        "Order Management",
        "Warranty and Repairs"
    ],
    "Keywords": [
        "password, reset, account",
        "manual, user guide, instructions",
        "refund, policy, money back",
        "track order, delivery, status",
        "warranty, guarantee, terms"
    ]
}

# Convert to DataFrame
df = pd.DataFrame(faq_data)

# Export to CSV
df.to_csv('faq_data.csv', index=False)

# For PDF, you will need an additional library, like FPDF, to generate a PDF
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Customer Service FAQ Data', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

pdf = PDF()
pdf.add_page()
pdf.set_font('Arial', '', 12)

for i in range(len(df)):
    for col in df.columns:
        pdf.cell(0, 10, f'{col}: {df[col][i]}', 0, 1)
    pdf.cell(0, 10, '', 0, 1)  # Add an empty line

pdf.output('faq_data.pdf')




