# Daily Reports Generator

This Python script generates three daily reports by fetching data from your backend API and creates beautiful PDF reports with histograms:

1. **Daily GMV** (Gross Merchandise Value) - using `total_book_price`
2. **Daily Gross Revenue** - using `gross` calculation
3. **Daily Booking Count** - using `no_of_booking`

## Features

- ✅ **Zero-filling**: Missing dates are filled with 0 values to ensure no gaps in reports
- ✅ **HTTP API integration**: Fetches data from your backend API endpoint
- ✅ **Console output**: Beautifully formatted reports displayed in terminal
- ✅ **JSON export**: Option to save reports to JSON file
- ✅ **PDF reports**: Generate professional PDF reports with histograms
- ✅ **Histogram charts**: Visual representation of daily data trends
- ✅ **Summary statistics**: Comprehensive statistics table in PDF
- ✅ **Error handling**: Comprehensive error handling for API requests
- ✅ **Authentication support**: Optional API key authentication

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage (Console Output Only)

```bash
python report-gen.py \
  --space-id 123 \
  --start-date 2024-01-01 \
  --end-date 2024-01-31
```

### Generate PDF Report

```bash
python report-gen.py \
  --space-id 123 \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --pdf daily_reports.pdf
```

### Complete Usage (Console + JSON + PDF)

```bash
python report-gen.py \
  --space-id 123 \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --output reports.json \
  --pdf daily_reports.pdf
```

### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--space-id` | Yes | Space ID to generate reports for | `123` |
| `--start-date` | Yes | Start date in YYYY-MM-DD format | `2024-01-01` |
| `--end-date` | Yes | End date in YYYY-MM-DD format | `2024-01-31` |
| `--output` | No | Output JSON file path | `reports.json` |
| `--pdf` | No | Output PDF file path | `daily_reports.pdf` |

## PDF Report Features

The generated PDF report includes:

### 📊 **Summary Statistics Table**
- Total, Average, Maximum, Minimum values for each metric
- Number of days with actual data (non-zero values)
- Professional formatting with color-coded headers

### 📈 **Histogram Charts**
- **Daily GMV Chart**: Bar chart showing daily total book price
- **Daily Gross Revenue Chart**: Bar chart showing daily gross revenue
- **Daily Booking Count Chart**: Bar chart showing daily booking numbers
- Value labels on bars for easy reading
- Proper date formatting on x-axis
- Grid lines for better readability

### 📋 **Report Information**
- Space ID and date range
- Generation timestamp
- Professional title and formatting

## API Endpoint

The script expects your backend API to have an endpoint that returns data in this format:

**Request:**
```
GET /report/hotel/revenue-and-count?space_id=123&start_date=2024-01-01&end_date=2024-01-31
```

**Expected Response:**
```json
{
  "Success": true,
  "Data": {
    "2024-01-01": {
      "no_of_booking": 5,
      "total_book_price": 1250.0,
      "gross": 1100.0
    },
    "2024-01-02": {
      "no_of_booking": 0,
      "total_book_price": 0.0,
      "gross": 0.0
    }
  }
}
```

## Example Output

### Console Output
```
============================================================
DAILY REPORTS: 2024-01-01 to 2024-01-31
============================================================

📊 DAILY GMV (Total Book Price)
----------------------------------------
2024-01-01: $1,250.00
2024-01-02: $0.00
2024-01-03: $2,100.50
...
----------------------------------------
TOTAL GMV: $45,250.00

💰 DAILY GROSS REVENUE
----------------------------------------
2024-01-01: $1,100.00
2024-01-02: $0.00
2024-01-03: $1,850.25
...
----------------------------------------
TOTAL GROSS REVENUE: $40,125.50

📅 DAILY BOOKING COUNT
----------------------------------------
2024-01-01: 5 bookings
2024-01-02: 0 bookings
2024-01-03: 8 bookings
...
----------------------------------------
TOTAL BOOKINGS: 125
============================================================
```

### PDF Report Structure
1. **Title Page**: Report title and generation info
2. **Summary Table**: Statistics for all metrics
3. **Daily GMV Histogram**: Visual chart of GMV trends
4. **Daily Gross Revenue Histogram**: Visual chart of revenue trends
5. **Daily Booking Count Histogram**: Visual chart of booking trends

## JSON Output Format

When using `--output`, the script creates a JSON file with this structure:

```json
{
  "daily_gmv": {
    "2024-01-01": 1250.0,
    "2024-01-02": 0.0,
    "2024-01-03": 2100.5
  },
  "daily_gross_revenue": {
    "2024-01-01": 1100.0,
    "2024-01-02": 0.0,
    "2024-01-03": 1850.25
  },
  "daily_booking_count": {
    "2024-01-01": 5,
    "2024-01-02": 0,
    "2024-01-03": 8
  }
}
```

## Backend Integration

The script expects your backend to implement an endpoint that:

1. Accepts `space_id`, `start_date`, and `end_date` parameters
2. Returns data in the format shown above
3. Handles the same business logic as your original backend code
4. Returns `Success: true` and `Data: {}` structure

## Error Handling

The script handles various error scenarios:
- Network connection failures
- API authentication errors
- Invalid response formats
- HTTP status errors
- Chart generation errors
- PDF creation errors

Error messages are displayed with clear descriptions to help troubleshoot issues.

## Security Notes

- Store API keys securely
- Use HTTPS for all API communications
- Consider using environment variables for sensitive data
- Implement proper rate limiting on your API endpoint 