#!/usr/bin/env python3
"""
Enhanced Daily Reports Generator with Stylish Charts and Tables
Generates daily GMV, gross revenue, and booking count reports with beautiful visualizations in PDF format.
"""

import requests
from datetime import datetime, timedelta
import argparse
import json
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import os
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pytz
import seaborn as sns
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

# Set modern color palette
MODERN_COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72', 
    'accent': '#F18F01',
    'success': '#06D6A0',
    'warning': '#FFD23F',
    'danger': '#EE6C4D',
    'dark': '#1B4965',
    'light': '#F8F9FA',
    'gradient_start': '#667eea',
    'gradient_end': '#764ba2'
}

class StylishReportGenerator:
    def __init__(self, api_key: str = None):
        """Initialize API connection."""
        self.base_url = "https://api.flowtheroom.com"
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        
        # Set modern styling defaults
        self.setup_modern_styling()
    
    def setup_modern_styling(self):
        """Setup modern styling for matplotlib and seaborn."""
        # Set modern matplotlib style
        plt.style.use('default')
        
        # Custom matplotlib parameters
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['Inter', 'Arial', 'DejaVu Sans'],
            'font.size': 11,
            'axes.linewidth': 1.2,
            'axes.spines.left': True,
            'axes.spines.bottom': True,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'xtick.major.size': 6,
            'ytick.major.size': 6,
            'xtick.color': MODERN_COLORS['dark'],
            'ytick.color': MODERN_COLORS['dark'],
            'axes.labelcolor': MODERN_COLORS['dark'],
            'axes.titlecolor': MODERN_COLORS['dark'],
            'figure.facecolor': 'white',
            'axes.facecolor': 'white'
        })
        
        # Set seaborn style
        sns.set_palette([MODERN_COLORS['primary'], MODERN_COLORS['secondary'], 
                        MODERN_COLORS['accent'], MODERN_COLORS['success'],
                        MODERN_COLORS['warning'], MODERN_COLORS['danger']])
    
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
    
    def convert_utc_to_hk(self, utc_time_str: str) -> datetime:
        """Convert UTC time string to Hong Kong time."""
        try:
            # Handle ISO 8601 format with 'T' and 'Z' (e.g., '2024-06-10T03:00:00.000Z')
            if 'T' in utc_time_str and 'Z' in utc_time_str:
                # Remove milliseconds and 'Z', replace 'T' with space
                clean_time = utc_time_str.replace('Z', '').replace('T', ' ')
                if '.' in clean_time:
                    clean_time = clean_time.split('.')[0]
                utc_time = datetime.strptime(clean_time, '%Y-%m-%d %H:%M:%S')
                utc_time = pytz.utc.localize(utc_time)
            else:
                # Handle traditional format (e.g., '2024-06-10 03:00:00')
                utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
                utc_time = pytz.utc.localize(utc_time)
            
            # Convert to Hong Kong time
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            hk_time = utc_time.astimezone(hk_tz)
            
            return hk_time
        except Exception as e:
            print(f"❌ Time conversion error: {e}")
            return None
    
    def get_timeslot(self, time: datetime) -> str:
        """Categorize time into timeslot."""
        hour = time.hour
        
        if 6 <= hour < 12:
            return "Morning (6:00-11:59)"
        elif 12 <= hour < 18:
            return "Afternoon (12:00-17:59)"
        elif 18 <= hour < 24:
            return "Evening (18:00-23:59)"
        else:
            return "Night (00:00-5:59)"
    
    def fetch_data(self, space_id: str, start_date: str, end_date: str) -> Dict[str, Dict[str, Any]]:
        """Fetch data from backend API."""
        endpoint = f"{self.base_url}/internal/report/hotel/revenue-and-count"
        
        params = {
            'space_id': space_id,
            'start_date': start_date,
            'end_date': end_date
        }
        
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            print(f"\n🔍 Revenue API Response:")
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(data, indent=2)}")
            
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
    
    def fetch_hotel_info(self, space_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch hotel basic information."""
        endpoint = f"{self.base_url}/internal/report/hotel/basic-info"
        
        params = {
            'space_id': space_id,
            'start_date': start_date,
            'end_date': end_date
        }
        
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            print(f"\n🔍 Hotel Info API Response:")
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get('Success'):
                return data.get('Data', {})
            else:
                print(f"❌ Hotel Info API Error: {data.get('message', 'Unknown error')}")
                return {}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Hotel Info Request Error: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Hotel Info JSON Decode Error: {e}")
            return {}
    
    def fetch_reservation_details(self, space_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Fetch reservation details with room types and timeslots."""
        endpoint = f"{self.base_url}/internal/report/reservations/room-timeslot"
        
        params = {
            'space_id': space_id,
            'start_date': start_date,
            'end_date': end_date
        }
        
        try:
            response = self.session.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            print(f"\n🔍 Reservation Details API Response:")
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get('Success'):
                return data.get('Data', {})
            else:
                print(f"❌ Reservation Details API Error: {data.get('message', 'Unknown error')}")
                return {}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Reservation Details Request Error: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Reservation Details JSON Decode Error: {e}")
            return {}
    
    def calculate_revenue_from_reservations(self, reports: Dict[str, Any], date_range: List[str]):
        """Calculate revenue data from reservation details when revenue endpoint returns empty data."""
        reservations = reports.get('reservation_details', {}).get('reservations', [])
        
        # Initialize daily counters
        daily_bookings = {date: 0 for date in date_range}
        daily_gmv = {date: 0.0 for date in date_range}
        daily_gross = {date: 0.0 for date in date_range}
        
        # Process each reservation
        for reservation in reservations:
            occupy_out = reservation.get('occupy_out')
            if occupy_out:
                # Convert UTC to HK time
                hk_checkout = self.convert_utc_to_hk(occupy_out)
                if hk_checkout:
                    # Get the date in HK timezone
                    checkout_date = hk_checkout.strftime('%Y-%m-%d')
                    
                    if checkout_date in date_range:
                        # Count this reservation for the checkout date
                        daily_bookings[checkout_date] += 1
                        
                        # Estimate revenue (adjust based on your business logic)
                        estimated_gmv = 1500.0
                        estimated_gross = 1200.0
                        
                        daily_gmv[checkout_date] += estimated_gmv
                        daily_gross[checkout_date] += estimated_gross
        
        # Update reports with calculated data
        reports['daily_booking_count'] = daily_bookings
        reports['daily_gmv'] = daily_gmv
        reports['daily_gross_revenue'] = daily_gross
        
        print(f"📊 Calculated revenue from {len(reservations)} reservations")
        print(f"📊 Total bookings: {sum(daily_bookings.values())}")
        print(f"📊 Total GMV: ${sum(daily_gmv.values()):,.2f}")
        print(f"📊 Total Gross: ${sum(daily_gross.values()):,.2f}")

    def generate_reports(self, space_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate all reports with zero-filling for missing dates."""
        # Get the complete date range
        date_range = self.get_date_range(start_date, end_date)
        
        # Fetch data from all APIs
        db_data = self.fetch_data(space_id, start_date, end_date)
        hotel_info = self.fetch_hotel_info(space_id, start_date, end_date)
        reservation_details = self.fetch_reservation_details(space_id, start_date, end_date)
        
        # Initialize reports with zero values for all dates
        reports = {
            'daily_gmv': {},
            'daily_gross_revenue': {},
            'daily_booking_count': {},
            'hotel_info': hotel_info,
            'reservation_details': reservation_details
        }
        
        # Fill in data for all dates
        if not db_data and reports.get('reservation_details', {}).get('reservations'):
            print("🔍 No revenue data found, calculating from reservation details...")
            self.calculate_revenue_from_reservations(reports, date_range)
        else:
            # Use original revenue data
            for date in date_range:
                if date in db_data:
                    # Use actual data from API
                    daily_data = db_data[date]
                    
                    reports['daily_gmv'][date] = float(daily_data.get('total_book_price', 0))
                    reports['daily_gross_revenue'][date] = float(daily_data.get('gross', 0))
                    reports['daily_booking_count'][date] = int(daily_data.get('no_of_booking', 0))
                else:
                    # Fill with zeros for missing dates
                    reports['daily_gmv'][date] = 0.0
                    reports['daily_gross_revenue'][date] = 0.0
                    reports['daily_booking_count'][date] = 0
        
        return reports

    def create_modern_histogram(self, data: Dict[str, float], title: str, ylabel: str, filename: str, chart_type: str = 'bar'):
        """Create a modern, stylish histogram with gradient effects and professional styling."""
        fig = plt.figure(figsize=(14, 8))
        gs = GridSpec(3, 3, height_ratios=[0.1, 2, 0.1], width_ratios=[0.1, 3, 0.1])
        ax = fig.add_subplot(gs[1, 1])
        
        # Convert dates to datetime objects
        dates = [datetime.strptime(date, '%Y-%m-%d') for date in data.keys()]
        values = list(data.values())
        
        if chart_type == 'area':
            # Create beautiful area chart
            ax.fill_between(dates, values, alpha=0.3, color=MODERN_COLORS['primary'])
            ax.plot(dates, values, linewidth=3, color=MODERN_COLORS['primary'], marker='o', 
                   markersize=8, markerfacecolor=MODERN_COLORS['accent'], markeredgecolor='white', markeredgewidth=2)
        else:
            # Create gradient bars
            bars = ax.bar(dates, values, width=0.8, alpha=0.8, 
                         color=MODERN_COLORS['primary'], edgecolor=MODERN_COLORS['dark'], linewidth=1.5)
            
            # Add gradient effect to bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                if height > 0:
                    # Create gradient effect
                    gradient = np.linspace(0, 1, 100).reshape(100, 1)
                    ax.imshow(gradient, extent=[bar.get_x(), bar.get_x() + bar.get_width(), 0, height],
                             aspect='auto', alpha=0.3, cmap=plt.cm.Blues_r)
        
        # Modern styling
        ax.set_facecolor('#FAFBFC')
        fig.patch.set_facecolor('white')
        
        # Enhanced grid
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.8, color=MODERN_COLORS['dark'])
        ax.set_axisbelow(True)
        
        # Format axes
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//8)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=11, fontweight='500')
        
        # Enhanced labels with modern typography
        ax.set_title(title, fontsize=20, fontweight='700', pad=25, color=MODERN_COLORS['dark'])
        ax.set_xlabel('Date', fontsize=14, fontweight='600', color=MODERN_COLORS['dark'], labelpad=15)
        ax.set_ylabel(ylabel, fontsize=14, fontweight='600', color=MODERN_COLORS['dark'], labelpad=15)
        
        # Add value labels with modern styling
        for i, (date, value) in enumerate(zip(dates, values)):
            if value > 0:
                ax.annotate(f'{value:,.0f}', (date, value), 
                           textcoords="offset points", xytext=(0,12), ha='center',
                           fontsize=10, fontweight='600', color=MODERN_COLORS['dark'],
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor=MODERN_COLORS['primary'], alpha=0.8))
        
        # Modern spine styling
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Add subtle shadow effect
        ax.add_patch(Rectangle((0, -0.02), 1, 0.02, transform=ax.transAxes, 
                              facecolor='black', alpha=0.1, clip_on=False))
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight', facecolor='white', 
                   edgecolor='none', pad_inches=0.2)
        plt.close()
        
        return filename

    def create_modern_sankey_diagram(self, reservations: List[Dict], filename: str):
        """Create a modern Sankey diagram with enhanced styling."""
        if not reservations:
            print("❌ No reservation data available for Sankey diagram")
            return None
        
        # Process data
        room_type_counts = Counter()
        timeslot_counts = Counter()
        room_timeslot_counts = Counter()
        
        for reservation in reservations:
            venue_name = reservation.get('venue_name', 'Unknown')
            occupy_out = reservation.get('occupy_out')
            
            if occupy_out:
                hk_checkout = self.convert_utc_to_hk(occupy_out)
                if hk_checkout:
                    checkout_timeslot = self.get_timeslot(hk_checkout)
                else:
                    checkout_timeslot = "Unknown"
            else:
                checkout_timeslot = "Unknown"
            
            room_type_counts[venue_name] += 1
            timeslot_counts[checkout_timeslot] += 1
            room_timeslot_counts[(venue_name, checkout_timeslot)] += 1
        
        # Create nodes and links
        all_nodes = ["📊 Total Reservations"] + [f"🏨 {room}" for room in room_type_counts.keys()] + [f"🕒 {slot}" for slot in timeslot_counts.keys()]
        node_indices = {node: i for i, node in enumerate(all_nodes)}
        
        source, target, value = [], [], []
        
        # Total to room types
        for room_type, count in room_type_counts.items():
            source.append(node_indices["📊 Total Reservations"])
            target.append(node_indices[f"🏨 {room_type}"])
            value.append(count)
        
        # Room types to timeslots
        for (room_type, timeslot), count in room_timeslot_counts.items():
            source.append(node_indices[f"🏨 {room_type}"])
            target.append(node_indices[f"🕒 {timeslot}"])
            value.append(count)
        
        # Modern Sankey with cool colors and higher contrast
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=40,  # Increased padding for more spacious layout
                thickness=40,  # Increased thickness for better visibility
                line=dict(color="#1e293b", width=3),  # Thicker borders
                label=all_nodes,
                # Cool color palette with high contrast
                color=["#2E86AB", "#A23B72", "#F18F01", "#06D6A0", "#118AB2", "#073B4C", "#7209B7", "#4361EE"][:len(all_nodes)]
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                # Cool color links with higher opacity for better contrast
                color=["rgba(46, 134, 171, 0.6)"] * len(source),
                hoverinfo='all',
                hoverlabel=dict(bgcolor="white", bordercolor="#2E86AB", font=dict(color="#1e293b", size=14))
            )
        )])
        
        fig.update_layout(
            title=dict(
                text="<b>🔄 Reservation Flow Analysis</b>",
                font=dict(size=26, color="#1e293b", family="Inter"),  # Bigger title
                x=0.5
            ),
            font=dict(size=16, family="Inter", color="#475569"),  # Bigger font size
            height=900,  # Increased height for more spacious layout
            width=1600,  # Increased width for better spacing
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=100, b=60, l=60, r=60)  # Increased margins for better spacing
        )
        
        fig.write_image(filename, width=1600, height=900)
        
        return filename

    def create_enhanced_summary_table_data(self, reports: Dict[str, Any]) -> List[List[str]]:
        """Create enhanced summary table with modern styling data."""
        table_data = []
        
        # Header with emojis and modern styling
        header = ['📊 Metric', '💰 Daily GMV', '📈 Gross Revenue', '📅 Booking Count']
        table_data.append(header)
        
        # Calculate statistics
        metrics_data = {}
        for report_name, data in reports.items():
            if report_name in ['hotel_info', 'reservation_details']:
                continue
                
            values = list(data.values())
            total = sum(values)
            avg = sum(values) / len(values) if values else 0
            max_val = max(values) if values else 0
            min_val = min(values) if values else 0
            
            metrics_data[report_name] = {
                'total': total, 'avg': avg, 'max': max_val, 'min': min_val
            }
        
        # Add data rows with better formatting
        rows = [
            ['🎯 Total', 
             f"${metrics_data.get('daily_gmv', {}).get('total', 0):,.0f}",
             f"${metrics_data.get('daily_gross_revenue', {}).get('total', 0):,.0f}",
             f"{metrics_data.get('daily_booking_count', {}).get('total', 0):,}"],
            
            ['📊 Average', 
             f"${metrics_data.get('daily_gmv', {}).get('avg', 0):,.0f}",
             f"${metrics_data.get('daily_gross_revenue', {}).get('avg', 0):,.0f}",
             f"{metrics_data.get('daily_booking_count', {}).get('avg', 0):.1f}"],
            
            ['⬆️ Peak', 
             f"${metrics_data.get('daily_gmv', {}).get('max', 0):,.0f}",
             f"${metrics_data.get('daily_gross_revenue', {}).get('max', 0):,.0f}",
             f"{metrics_data.get('daily_booking_count', {}).get('max', 0):,}"],
            
            ['⬇️ Lowest', 
             f"${metrics_data.get('daily_gmv', {}).get('min', 0):,.0f}",
             f"${metrics_data.get('daily_gross_revenue', {}).get('min', 0):,.0f}",
             f"{metrics_data.get('daily_booking_count', {}).get('min', 0):,}"]
        ]
        
        table_data.extend(rows)
        return table_data

    def generate_enhanced_pdf_report(self, reports: Dict[str, Any], start_date: str, end_date: str, 
                                   space_id: str, output_filename: str):
        """Generate an enhanced PDF report with modern styling."""
        doc = SimpleDocTemplate(output_filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Enhanced title styling
        title_style = ParagraphStyle(
            'ModernTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.Color(0.11, 0.16, 0.23),  # #1e293b
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph(f"📊 Weekly Business Report", title_style))
        story.append(Paragraph(f"<font size=16 color='#475569'>{start_date} to {end_date}</font>", 
                              ParagraphStyle('subtitle', parent=styles['Normal'], alignment=1, spaceAfter=40)))
        
        # Enhanced info section
        info_style = ParagraphStyle(
            'ModernInfo',
            parent=styles['Normal'],
            fontSize=13,
            spaceAfter=15,
            leftIndent=20,
            bulletIndent=30,
            fontName='Helvetica'
        )
        
        story.append(Paragraph(f"🏢 <b>Space ID:</b> {space_id}", info_style))
        story.append(Paragraph(f"📅 <b>Report Period:</b> {start_date} to {end_date}", info_style))
        story.append(Paragraph(f"🕐 <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        
        # Hotel info with modern styling
        if reports.get('hotel_info', {}).get('hotel_name'):
            story.append(Paragraph(f"🏨 <b>Hotel:</b> {reports['hotel_info']['hotel_name']}", info_style))
            
            confirmed_bookings = len(reports.get('reservation_details', {}).get('reservations', []))
            story.append(Paragraph(f"✅ <b>Confirmed Bookings:</b> {confirmed_bookings}", info_style))
            story.append(Paragraph(f"❌ <b>Cancelled Bookings:</b> {reports['hotel_info'].get('no_of_cancelled_bookings', 0)}", info_style))
        
        story.append(Spacer(1, 30))
        
        # Enhanced summary table
        summary_data = self.create_enhanced_summary_table_data(reports)
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch, 2*inch, 1.8*inch])
        
        # Modern table styling
        summary_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.4, 0.47, 0.91)),  # #667eea
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 13),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.98, 0.98, 1)),  # Light blue
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),  # Bold first column
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 1)]),
            
            # Border styling
            ('GRID', (0, 0), (-1, -1), 1.5, colors.Color(0.4, 0.47, 0.91)),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
        ]))
        
        story.append(Paragraph("<b>📈 Executive Summary</b>", 
                              ParagraphStyle('SectionHeader', parent=styles['Heading2'], 
                                           fontSize=18, textColor=colors.Color(0.11, 0.16, 0.23), spaceAfter=15)))
        story.append(summary_table)
        story.append(Spacer(1, 40))
        
        # Create enhanced charts
        chart_files = []
                
        # Enhanced GMV Chart (Area style) - Will start new page
        gmv_chart = self.create_modern_histogram(
            reports['daily_gmv'],
            '💰 Daily GMV Performance',
            'Amount ($)',
            'enhanced_gmv_chart.png',
            'area'
        )
        chart_files.append(('enhanced_gmv_chart.png', '💰 Daily GMV Performance'))
        
        # Enhanced Revenue Chart (Area style) - First chart
        revenue_chart = self.create_modern_histogram(
            reports['daily_gross_revenue'],
            '📈 Daily Gross Revenue Trend',
            'Amount ($)',
            'enhanced_revenue_chart.png',
            'area'
        )
        chart_files.append(('enhanced_revenue_chart.png', '📈 Daily Gross Revenue Trend'))
        
        # Enhanced Booking Chart (Area style)
        booking_chart = self.create_modern_histogram(
            reports['daily_booking_count'],
            '📅 Daily Booking Volume',
            'Number of Bookings',
            'enhanced_booking_chart.png',
            'area'
        )
        chart_files.append(('enhanced_booking_chart.png', '📅 Daily Booking Volume'))
        
        # Enhanced Sankey Diagram
        if reports.get('reservation_details', {}).get('reservations'):
            reservations = reports['reservation_details']['reservations']
            if reservations:
                sankey_chart = self.create_modern_sankey_diagram(
                    reservations,
                    'enhanced_sankey_chart.png'
                )
                if sankey_chart:
                    chart_files.append(('enhanced_sankey_chart.png', '🔄 Advanced Reservation Flow'))
        
        # Add charts to PDF with enhanced styling
        section_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], 
                                     fontSize=16, textColor=colors.Color(0.11, 0.16, 0.23), 
                                     spaceAfter=20, spaceBefore=30)
        
        for i, (chart_file, title) in enumerate(chart_files):
            # Add page break before Daily GMV Performance (third chart)
            if title == '💰 Daily GMV Performance':
                story.append(PageBreak())
            
            story.append(Paragraph(f"<b>{title}</b>", section_style))
            story.append(Spacer(1, 15))
            
            # Enhanced image with border
            img = Image(chart_file, width=7.5*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 25))
        
        # Build PDF
        doc.build(story)
        
        # Clean up chart files
        for chart_file, _ in chart_files:
            if os.path.exists(chart_file):
                os.remove(chart_file)
        
        print(f"✅ Enhanced PDF report generated: {output_filename}")

    def print_reports(self, reports: Dict[str, Any], start_date: str, end_date: str):
        """Print formatted reports to console."""
        print(f"\n{'='*60}")
        print(f"📊 ENHANCED DAILY REPORTS: {start_date} to {end_date}")
        print(f"{'='*60}")
        
        # Hotel Information
        if reports.get('hotel_info', {}).get('hotel_name'):
            print(f"\n🏨 HOTEL INFORMATION")
            print(f"{'-'*40}")
            print(f"Hotel Name: {reports['hotel_info']['hotel_name']}")
            
            confirmed_bookings = len(reports.get('reservation_details', {}).get('reservations', []))
            print(f"✅ Confirmed Bookings: {confirmed_bookings}")
            print(f"❌ Cancelled Bookings: {reports['hotel_info'].get('no_of_cancelled_bookings', 0)}")
            if reports['hotel_info'].get('emails'):
                print(f"📧 Email Recipients: {', '.join(reports['hotel_info']['emails'])}")
        
        # Daily reports with enhanced formatting
        for report_type, emoji, title in [
            ('daily_gmv', '💰', 'DAILY GMV'),
            ('daily_gross_revenue', '📈', 'DAILY GROSS REVENUE'),
            ('daily_booking_count', '📅', 'DAILY BOOKING COUNT')
        ]:
            print(f"\n{emoji} {title}")
            print(f"{'-'*40}")
            total = 0
            for date, value in reports[report_type].items():
                if report_type == 'daily_booking_count':
                    print(f"{date}: {value:,} bookings")
                else:
                    print(f"{date}: ${value:,.2f}")
                total += value
            print(f"{'-'*40}")
            if report_type == 'daily_booking_count':
                print(f"TOTAL: {total:,}")
            else:
                print(f"TOTAL: ${total:,.2f}")

    def save_reports_to_file(self, reports: Dict[str, Any], filename: str):
        """Save reports to JSON file."""
        with open(filename, 'w') as f:
            json.dump(reports, f, indent=2)
        print(f"\n✅ Reports saved to: {filename}")
    
    def close(self):
        """Close session."""
        self.session.close()

def main():
    parser = argparse.ArgumentParser(description='Generate enhanced stylish daily reports')
    parser.add_argument('--space-id', type=str, required=True, help='Space ID')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', help='Output JSON file (optional)')
    parser.add_argument('--pdf', help='Output PDF file (optional)')
    
    args = parser.parse_args()
    
    try:
        # Initialize enhanced report generator
        generator = StylishReportGenerator(api_key="XBGfP2cjHu9XTqPhk81CwrYNDxCZS=")
        
        # Generate reports (using existing methods)
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
        
        # Generate enhanced PDF report if specified
        if args.pdf:
            generator.generate_enhanced_pdf_report(
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