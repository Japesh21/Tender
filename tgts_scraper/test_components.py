"""
Test/Example scripts for TGTS Tender Scraper
Run these to test individual components
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_database():
    """Test database creation and operations"""
    print("\n=== Testing Database ===")

    from database.db_manager import TenderDatabase
    from config import DATABASE_FILE

    db = TenderDatabase(DATABASE_FILE)

    # Insert test tender
    test_tender = {
        'tender_id': 'TEST-001',
        'title': 'Test Tender - Network',
        'department': 'IT',
        'published_date': '2024-01-15',
        'closing_date': '2024-02-15',
        'emd': 50000,
        'tender_value': 5000000,
        'document_link': 'http://example.com/doc',
        'pdf_link': 'http://example.com/pdf',
        'status': 'Active'
    }

    inserted = db.insert_tender(test_tender)
    print(f"✓ Insert test tender: {inserted}")

    # Retrieve tender
    tender = db.get_tender('TEST-001')
    print(f"✓ Retrieved tender: {tender['title'] if tender else 'Not found'}")

    # Get all tenders
    all_tenders = db.get_all_tenders(department='IT')
    print(f"✓ Found {len(all_tenders)} IT tenders")

    # Get stats
    stats = db.get_database_stats()
    print(f"✓ Database stats: {stats}")

    print("✓ Database tests passed!")


def test_output_generator():
    """Test CSV and Excel generation"""
    print("\n=== Testing Output Generator ===")

    from output.generator import OutputGenerator
    from config import OUTPUT_DIR

    generator = OutputGenerator(OUTPUT_DIR)

    # Test data
    test_tenders = [
        {
            'tender_id': 'TEN-001',
            'title': 'Network Infrastructure',
            'department': 'IT',
            'published_date': '2024-01-15',
            'closing_date': '2024-02-15',
            'emd': 50000,
            'tender_value': 5000000,
            'status': 'Active',
            'document_link': 'http://example.com/doc',
            'pdf_link': 'http://example.com/pdf'
        },
        {
            'tender_id': 'TEN-002',
            'title': 'Database Management',
            'department': 'IT',
            'published_date': '2024-01-20',
            'closing_date': '2024-03-01',
            'emd': 75000,
            'tender_value': 7000000,
            'status': 'Active',
            'document_link': 'http://example.com/doc2',
            'pdf_link': 'http://example.com/pdf2'
        }
    ]

    # Generate CSV
    csv_path = generator.generate_csv(test_tenders, 'test_tenders.csv')
    print(f"✓ CSV generated: {csv_path}")

    # Generate Excel
    excel_path = generator.generate_excel(test_tenders, 'test_tenders.xlsx')
    print(f"✓ Excel generated: {excel_path}")

    # Generate HTML
    html_path = generator.generate_html_report(test_tenders, 'test_report.html')
    print(f"✓ HTML report generated: {html_path}")

    print("✓ Output generator tests passed!")


def test_filters():
    """Test tender filtering"""
    print("\n=== Testing Filters ===")

    from scraper.filters import TenderFilter

    test_tenders = [
        {
            'tender_id': 'TEN-001',
            'title': 'Network',
            'department': 'IT Services',
            'closing_date': '2024-02-15',
            'tender_value': 5000000,
            'status': 'Active'
        },
        {
            'tender_id': 'TEN-002',
            'title': 'Database',
            'department': 'Finance',
            'closing_date': '2024-02-20',
            'tender_value': 3000000,
            'status': 'Active'
        },
        {
            'tender_id': 'TEN-003',
            'title': 'Servers',
            'department': 'IT',
            'closing_date': '2024-01-20',
            'tender_value': 7000000,
            'status': 'Closed'
        }
    ]

    # Filter by department
    it_tenders = TenderFilter.filter_by_department(test_tenders, ['IT'])
    print(f"✓ IT tenders: {len(it_tenders)}")

    # Filter by status
    active = TenderFilter.filter_by_status(test_tenders, ['Active'])
    print(f"✓ Active tenders: {len(active)}")

    # Filter by minimum value
    high_value = TenderFilter.filter_by_minimum_value(test_tenders, 5000000)
    print(f"✓ High-value tenders: {len(high_value)}")

    # Remove duplicates
    unique = TenderFilter.remove_duplicates(test_tenders)
    print(f"✓ Unique tenders: {len(unique)}")

    print("✓ Filter tests passed!")


def test_email_notifier():
    """Test email notifier (without sending)"""
    print("\n=== Testing Email Notifier ===")

    from notifications.email_notifier import EmailNotifier

    notifier = EmailNotifier(
        smtp_server='smtp.gmail.com',
        smtp_port=587,
        sender_email='test@gmail.com',
        sender_password='test_password'
    )

    # Test message building
    test_tenders = [
        {
            'tender_id': 'TEN-001',
            'title': 'Network Infrastructure',
            'department': 'IT',
            'closing_date': '2024-02-15',
            'tender_value': 5000000,
            'pdf_link': 'http://example.com'
        }
    ]

    body = notifier._build_tender_email_body(test_tenders, "NEW")
    print(f"✓ Email body generated: {len(body)} characters")

    stats = {'total_tenders': 10, 'new_tenders': 2, 'by_status': {'Active': 8, 'Closed': 2}}
    formatted = notifier._format_status_stats(stats['by_status'])
    print(f"✓ Status stats formatted: {formatted}")

    print("✓ Email notifier tests passed!")


def test_whatsapp_notifier():
    """Test WhatsApp notifier (without sending)"""
    print("\n=== Testing WhatsApp Notifier ===")

    from notifications.whatsapp_notifier import WhatsAppNotifier

    notifier = WhatsAppNotifier(
        account_sid='test_sid',
        auth_token='test_token',
        from_phone='+1234567890'
    )

    # Test message building
    test_tenders = [
        {
            'tender_id': 'TEN-001',
            'title': 'Network Infrastructure',
            'department': 'IT',
            'closing_date': '2024-02-15',
            'tender_value': 5000000,
            'pdf_link': 'http://example.com'
        }
    ]

    message = notifier._build_tender_message(test_tenders, "NEW")
    print(f"✓ WhatsApp message built: {len(message)} characters")

    # Test phone formatting
    phone = notifier._format_phone('+91-9876543210')
    print(f"✓ Phone formatted: {phone}")

    phone2 = notifier._format_phone('9876543210')
    print(f"✓ Phone formatted (no country): {phone2}")

    print("✓ WhatsApp notifier tests passed!")


def test_fetcher():
    """Test tender fetcher setup"""
    print("\n=== Testing Tender Fetcher ===")

    from scraper.fetch_tenders import TenderFetcher

    with TenderFetcher('https://example.com') as fetcher:
        print(f"✓ Fetcher session created")
        print(f"✓ User-Agent: {fetcher.session.headers.get('User-Agent')}")

    print("✓ Tender fetcher tests passed!")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("TGTS Tender Scraper - Component Tests")
    print("=" * 50)

    try:
        test_database()
        test_output_generator()
        test_filters()
        test_email_notifier()
        test_whatsapp_notifier()
        test_fetcher()

        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50 + "\n")
        return True

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
