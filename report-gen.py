#!/usr/bin/env python3
"""
Daily Reports Generator
Generates daily GMV, gross revenue, and booking count reports with histograms in PDF format.
"""

import requests
from datetime import datetime, timedelta
import argparse
import json
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import os

class ReportGenerator:
    def __init__(self, api_key: str = None):
        """Initialize API connection."""
        self.base_url = "https://api.flowtheroom.com"
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def get_date_range(self, start_date: str, end_date: str) -> List[str]:
        """Generate list of dates between start and end date (inclusive)."""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        date_list = []
        current = start
        while current <= end:
            date_list.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        return date_list
    
    def fetch_data(self, space_id: str, start_date: str, end_date: str) -> Dict[str, Dict[str, Any]]:
        """Fetch data from backend API."""
        # Construct the API endpoint URL
        endpoint = f"{self.base_url}/internal/report/hotel/revenue-and-count"
        
        # Prepare request parameters
        params = {
            'space_id': space_id,
            'start_date': start_date,
            'end_date': end_date
        }
        
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle the response structure based on your backend
            if data.get('Success'):
                return data.get('Data', {})
            else:
                print(f"❌ API Error: {data.get('message', 'Unknown error')}")
                return {}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ JSON Decode Error: {e}")
            return {}
    
    def generate_reports(self, space_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate all three reports with zero-filling for missing dates."""
        # Get the complete date range
        date_range = self.get_date_range(start_date, end_date)
        
        # Fetch data from API
        db_data = self.fetch_data(space_id, start_date, end_date)
        
        # Initialize reports with zero values for all dates
        reports = {
            'daily_gmv': {},
            'daily_gross_revenue': {},
            'daily_booking_count': {}
        }
        
        # Fill in data for all dates
        for date in date_range:
            if date in db_data:
                # Use actual data from API
                reports['daily_gmv'][date] = float(db_data[date].get('total_book_price', 0))
                reports['daily_gross_revenue'][date] = float(db_data[date].get('gross', 0))
                reports['daily_booking_count'][date] = int(db_data[date].get('no_of_booking', 0))
            else:
                # Fill with zeros for missing dates
                reports['daily_gmv'][date] = 0.0
                reports['daily_gross_revenue'][date] = 0.0
                reports['daily_booking_count'][date] = 0
        
        return reports
    
    def create_histogram(self, data: Dict[str, float], title: str, ylabel: str, filename: str):
        """Create a histogram chart and save it as an image."""
        plt.figure(figsize=(12, 6))
        
        # Convert dates to datetime objects for proper x-axis formatting
        dates = [datetime.strptime(date, '%Y-%m-%d') for date in data.keys()]
        values = list(data.values())
        
        # Create bar chart (histogram-like)
        plt.bar(dates, values, width=0.8, alpha=0.7, color='skyblue', edgecolor='navy')
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.xticks(rotation=45, ha='right')
        
        # Add labels and title
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # Add value labels on bars (only for non-zero values)
        for i, (date, value) in enumerate(zip(dates, values)):
            if value > 0:
                plt.text(date, value + max(values) * 0.01, f'{value:,.0f}', 
                        ha='center', va='bottom', fontsize=8, rotation=0)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def create_summary_table(self, reports: Dict[str, Any]) -> List[List[str]]:
        """Create a summary table for the PDF."""
        table_data = [
            ['Metric', 'Total', 'Average', 'Max', 'Min', 'Days with Data']
        ]
        
        for report_name, data in reports.items():
            values = list(data.values())
            non_zero_values = [v for v in values if v > 0]
            
            total = sum(values)
            avg = sum(values) / len(values) if values else 0
            max_val = max(values) if values else 0
            min_val = min(values) if values else 0
            days_with_data = len(non_zero_values)
            
            # Format based on data type
            if 'booking' in report_name:
                total_str = f"{total:,}"
                avg_str = f"{avg:.1f}"
                max_str = f"{max_val:,}"
                min_str = f"{min_val:,}"
            else:
                total_str = f"${total:,.2f}"
                avg_str = f"${avg:.2f}"
                max_str = f"${max_val:,.2f}"
                min_str = f"${min_val:,.2f}"
            
            table_data.append([
                report_name.replace('_', ' ').title(),
                total_str,
                avg_str,
                max_str,
                min_str,
                f"{days_with_data}"
            ])
        
        return table_data
    
    def generate_pdf_report(self, reports: Dict[str, Any], start_date: str, end_date: str, 
                          space_id: str, output_filename: str):
        """Generate a comprehensive PDF report with all charts and data."""
        doc = SimpleDocTemplate(output_filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(f"Daily Reports Summary", title_style))
        story.append(Spacer(1, 20))
        
        # Report info
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20
        )
        story.append(Paragraph(f"<b>Space ID:</b> {space_id}", info_style))
        story.append(Paragraph(f"<b>Period:</b> {start_date} to {end_date}", info_style))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Spacer(1, 30))
        
        # Summary table
        summary_data = self.create_summary_table(reports)
        summary_table = Table(summary_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(Paragraph("<b>Summary Statistics</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Create charts
        chart_files = []
        
        # Daily GMV Chart
        gmv_chart = self.create_histogram(
            reports['daily_gmv'],
            'Daily GMV (Total Book Price)',
            'Amount ($)',
            'gmv_chart.png'
        )
        chart_files.append(('gmv_chart.png', 'Daily GMV (Total Book Price)'))
        
        # Daily Gross Revenue Chart
        gross_chart = self.create_histogram(
            reports['daily_gross_revenue'],
            'Daily Gross Revenue',
            'Amount ($)',
            'gross_chart.png'
        )
        chart_files.append(('gross_chart.png', 'Daily Gross Revenue') )
        
        # Daily Booking Count Chart
        booking_chart = self.create_histogram(
            reports['daily_booking_count'],
            'Daily Booking Count',
            'Number of Bookings',
            'booking_chart.png'
        )
        chart_files.append(('booking_chart.png', 'Daily Booking Count'))
        
        # Add charts to PDF
        for chart_file, title in chart_files:
            story.append(Paragraph(f"<b>{title}</b>", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Add chart image
            img = Image(chart_file, width=7*inch, height=3.5*inch)
            story.append(img)
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        # Clean up chart files
        for chart_file, _ in chart_files:
            if os.path.exists(chart_file):
                os.remove(chart_file)
        
        print(f"✅ PDF report generated: {output_filename}")
    
    def print_reports(self, reports: Dict[str, Any], start_date: str, end_date: str):
        """Print formatted reports to console."""
        print(f"\n{'='*60}")
        print(f"DAILY REPORTS: {start_date} to {end_date}")
        print(f"{'='*60}")
        
        # Daily GMV Report
        print(f"\n📊 DAILY GMV (Total Book Price)")
        print(f"{'-'*40}")
        total_gmv = 0
        for date, value in reports['daily_gmv'].items():
            print(f"{date}: ${value:,.2f}")
            total_gmv += value
        print(f"{'-'*40}")
        print(f"TOTAL GMV: ${total_gmv:,.2f}")
        
        # Daily Gross Revenue Report
        print(f"\n💰 DAILY GROSS REVENUE")
        print(f"{'-'*40}")
        total_gross = 0
        for date, value in reports['daily_gross_revenue'].items():
            print(f"{date}: ${value:,.2f}")
            total_gross += value
        print(f"{'-'*40}")
        print(f"TOTAL GROSS REVENUE: ${total_gross:,.2f}")
        
        # Daily Booking Count Report
        print(f"\n📅 DAILY BOOKING COUNT")
        print(f"{'-'*40}")
        total_bookings = 0
        for date, value in reports['daily_booking_count'].items():
            print(f"{date}: {value:,} bookings")
            total_bookings += value
        print(f"{'-'*40}")
        print(f"TOTAL BOOKINGS: {total_bookings:,}")
        
        print(f"\n{'='*60}")
    
    def save_reports_to_file(self, reports: Dict[str, Any], filename: str):
        """Save reports to JSON file."""
        with open(filename, 'w') as f:
            json.dump(reports, f, indent=2)
        print(f"\n✅ Reports saved to: {filename}")
    
    def close(self):
        """Close session."""
        self.session.close()

def main():
    parser = argparse.ArgumentParser(description='Generate daily reports for GMV, gross revenue, and booking count with PDF output')
    parser.add_argument('--space-id', type=str, required=True, help='Space ID')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', help='Output JSON file (optional)')
    parser.add_argument('--pdf', help='Output PDF file (optional)')
    
    args = parser.parse_args()
    
    try:
        # Initialize report generator with the secret
        generator = ReportGenerator(
            api_key="XBGfP2cjHu9XTqPhk81CwrYNDxCZS="
        )
        
        # Generate reports
        reports = generator.generate_reports(
            space_id=args.space_id,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        # Print reports to console
        generator.print_reports(reports, args.start_date, args.end_date)
        
        # Save to JSON file if specified
        if args.output:
            generator.save_reports_to_file(reports, args.output)
        
        # Generate PDF report if specified
        if args.pdf:
            generator.generate_pdf_report(
                reports=reports,
                start_date=args.start_date,
                end_date=args.end_date,
                space_id=args.space_id,
                output_filename=args.pdf
            )
        
        generator.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
