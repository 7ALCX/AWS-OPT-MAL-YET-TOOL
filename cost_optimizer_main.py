import boto3
import pandas as pd
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Attempt to initialize AWS Cost Explorer client
try:
    # boto3 automatically looks for AWS credentials in environment variables or ~/.aws/credentials file.
    ce_client = boto3.client('ce', region_name='us-east-1')
    print("AWS Cost Explorer client successfully initialized. Ready for real data fetching.")
except Exception as e:
    print(f"Error: Could not initialize AWS client. Please check credentials or region. Detail: {e}")
    print("This might occur if your AWS account is new or credentials are not properly configured.")
    ce_client = None # Set client to None if initialization fails

def get_cost_and_usage_data(client, start_date, end_date):
    """
    Fetches daily cost and usage data from AWS Cost Explorer API for a specified date range.
    Groups data by service and uses 'UnblendedCost' metric.
    """
    if client is None:
        print("AWS client is not available. Cannot fetch real data.")
        return []

    results = []
    next_page_token = None

    print(f"\nAttempting to fetch real AWS cost data for period: {start_date} - {end_date}")

    while True:
        try:
            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Granularity': 'DAILY',
                'Metrics': ['UnblendedCost'],
                'GroupBy': [
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            }
            if next_page_token:
                params['NextPageToken'] = next_page_token

            response = client.get_cost_and_usage(**params)
            results.extend(response['ResultsByTime'])
            next_page_token = response.get('NextPageToken')

            if not next_page_token:
                break
        except client.exceptions.DataUnavailableException:
            print(f"No data found or not yet available for: {start_date} - {end_date}. Cost Explorer data usually appears after 24-48 hours.")
            return []
        except Exception as e:
            print(f"Error occurred during AWS API call: {e}")
            print("Please check your IAM permissions (e.g., AWSCostExplorerReadOnlyAccess).")
            return []

    processed_data = []
    for result_by_time in results:
        date = result_by_time['TimePeriod']['Start']
        for group in result_by_time['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            unit = group['Metrics']['UnblendedCost']['Unit']
            processed_data.append({
                'Date': date,
                'Service': service,
                'Cost': cost,
                'Unit': unit
            })
    return processed_data

# --- Main Workflow ---

# Define date range to fetch cost data for the last 30 days
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

# Attempt to fetch real data from AWS
aws_costs = get_cost_and_usage_data(ce_client, start_date, end_date)

# Fallback to simulated data if real data could not be fetched
if not aws_costs:
    print("Real AWS cost data not available or empty. Using simulated data for analysis and demonstration...")
    try:
        with open('mock_aws_costs.json', 'r') as f:
            aws_costs = json.load(f)
    except FileNotFoundError:
        print("Error: 'mock_aws_costs.json' not found. Please ensure the file exists.")
        exit("Program terminated. Data source unavailable.")

# Convert loaded data to Pandas DataFrame
df = pd.DataFrame(aws_costs)

# Convert 'Date' column to datetime objects
df['Date'] = pd.to_datetime(df['Date'])

print("\n--- AWS Cost Data Sample (First 5 Rows) ---")
print(df.head().to_string())
print("\n")

# --- Data Processing and Analysis ---

# a) Calculate daily total costs
daily_total_cost = df.groupby('Date')['Cost'].sum().reset_index()
print("--- Daily Total Costs ---")
print(daily_total_cost.to_string(index=False))
print("\n")

# b) Calculate total costs by service
service_total_cost = df.groupby('Service')['Cost'].sum().reset_index()
print("--- Total Costs by Service ---")
print(service_total_cost.sort_values(by='Cost', ascending=False).to_string(index=False))
print("\n")

# --- Basic Optimization Recommendation Logic ---

df['DayServiceCost'] = df.groupby(['Date', 'Service'])['Cost'].transform('sum')
high_cost_per_service_per_day = df[df['DayServiceCost'] > 10].drop_duplicates(subset=['Date', 'Service'])

if not high_cost_per_service_per_day.empty:
    print("**Optimization Recommendations:**")
    for index, row in high_cost_per_service_per_day.iterrows():
        print(f"- On {row['Date'].strftime('%Y-%m-%d')}, '{row['Service']}' cost {row['Cost']:.2f} {row['Unit']}. Consider reviewing its usage!")
else:
    print("Costs appear to be under control; no prominent optimization recommendations at this time.")
print("\n")

# --- Data Visualization ---

plt.style.use('ggplot')

# Plot for Daily Cost Trend
plt.figure(figsize=(12, 6))
sns.lineplot(x='Date', y='Cost', data=daily_total_cost, marker='o', color='skyblue')
plt.title('Daily Total AWS Cost Trend', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Cost (USD)', fontsize=12)
plt.grid(True)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('daily_cost_trend.png', dpi=300)

# Plot for Service-wise Cost Distribution
plt.figure(figsize=(12, 7))
sns.barplot(x='Service', y='Cost', data=service_total_cost.sort_values(by='Cost', ascending=False), palette='viridis')
plt.title('AWS Cost Distribution by Service', fontsize=16)
plt.xlabel('AWS Service', fontsize=12)
plt.ylabel('Total Cost (USD)', fontsize=12)
plt.xticks(rotation=60, ha='right')
plt.tight_layout()
plt.savefig('service_cost_distribution.png', dpi=300)

print("\nCost analysis and visualization completed. Graphs saved as 'daily_cost_trend.png' and 'service_cost_distribution.png'.")