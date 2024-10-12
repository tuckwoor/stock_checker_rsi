from stock_checker_rsi import StockRSIAnalyzer
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

load_dotenv()

def send_email(subject, body, attachment_path=None):
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.example.com')
    
    if smtp_server == 'smtp.example.com':
        print("\nSMTP server is set to default. Email will not be sent.")
        print("Here's what would have been sent:")
        print("=" * 50)
        print(f"Subject: {subject}")
        print("-" * 50)
        print(body)
        print("-" * 50)
        if attachment_path:
            print(f"Attachment: {attachment_path}")
        print("=" * 50)
        return False

    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    sender_email = os.getenv('SENDER_EMAIL')
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEApplication(attachment.read(), Name=os.path.basename(attachment_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        message.attach(part)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(message)

    return True  # Indicate that email was sent successfully

def analyze_stocks(tickers, generate_pdf=True):
    results = []
    analyzers = {}
    styles = getSampleStyleSheet()
    email_body = "Stock Alert: Recent Crossovers Detected\n\n"
    alert_stocks = []

    for ticker in tickers:
        analyzer = StockRSIAnalyzer(ticker, rsi_window=100, smoothing_window=200, method='ema')
        if analyzer.data is not None and not analyzer.data.empty:
            result = analyzer.get_analysis_summary()
            results.append(result)
            analyzers[ticker] = analyzer

            if result['recent_crossover'] and result['trend'] in ['Strengthening', 'Weakening']:
                alert_stocks.append(result)

    # Sort results by current RSI value (if available)
    sorted_results = sorted(results, key=lambda x: x['current_rsi'] if x['current_rsi'] is not None else -1, reverse=True)
    
    pdf_elements = []

    # Print sorted results and generate PDF content
    for index, result in enumerate(sorted_results):
        ticker = result['ticker']
        print(f"Stock: {result['stock_name']} ({ticker})")
        if result['current_rsi'] is not None:
            print(f"Current RSI: {result['current_rsi']:.2f} ({result['rsi_status']})")
            print(f"Signal: {result['signal']}")
        else:
            print("No data available for analysis")
        print("---")

        if generate_pdf:
            analyzer = analyzers[ticker]
            # Add stock analysis text to PDF
            pdf_elements.append(Paragraph(analyzer.get_analysis_text().replace('\n', '<br/>'), styles['Normal']))
            pdf_elements.append(Spacer(1, 0.1*inch))
            
            # Add stock graph to PDF
            img_buffer = analyzer.plot_stock_rsi()
            if img_buffer:
                img = Image(img_buffer, width=5*inch, height=3.33*inch)  # Adjusted size
                pdf_elements.append(img)
            
            # Add space between stocks
            pdf_elements.append(Spacer(1, 0.2*inch))
            
            # Add a page break after every second stock (except for the last page)
            if (index + 1) % 2 == 0 and index < len(sorted_results) - 1:
                pdf_elements.append(PageBreak())

    # Generate PDF
    pdf_path = "stock_analysis.pdf"
    if generate_pdf:
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        doc.build(pdf_elements)
        print("PDF report generated: stock_analysis.pdf")

    # Prepare email body for alert stocks
    if alert_stocks:
        email_body += "The following stocks have shown significant changes:\n\n"
        for stock in alert_stocks:
            email_body += f"Stock: {stock['stock_name']} ({stock['ticker']})\n"
            email_body += f"Current RSI: {stock['current_rsi']:.2f} ({stock['rsi_status']})\n"
            email_body += f"Current Smoothed RSI: {stock['current_smoothed_rsi']:.2f}\n"
            email_body += f"Current Double Smoothed RSI: {stock['current_double_smoothed_rsi']:.2f}\n"
            email_body += f"Trend: {stock['trend']}\n"
            email_body += f"Signal: {stock['signal']}\n\n"

        email_body += "Please find the full analysis report attached.\n"

        # Attempt to send email with attachment
        subject = "Stock Alert: Recent Crossovers Detected"
        email_sent = send_email(subject, email_body, pdf_path)
        
        if email_sent:
            print("Email alert sent for recent crossovers with PDF attachment.")
        else:
            print("Email alert not sent due to default SMTP settings. Content displayed above.")
    else:
        print("No recent crossovers detected. No email content generated.")

# List of tickers to analyze
tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "RR.L"]

# Set generate_pdf to True to generate the PDF report
analyze_stocks(tickers, generate_pdf=True)

