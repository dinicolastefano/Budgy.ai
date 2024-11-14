import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import calendar
import json

class RetailDataProcessor:
    def __init__(self):
        self.raw_data = None
        self.processed_data = None
        self.closed_days = set()
        self.special_dates = set()
        
    def load_data(self, file):
        """Load and process the CSV data"""
        # Read CSV with specific Italian column names
        self.raw_data = pd.read_csv(file, parse_dates=['Data'])
        
        # Rename columns to English for consistency
        column_mapping = {
            'Data': 'date',
            'Incasso totale': 'total_sales',
            'N. Scontrini': 'num_receipts',
            'Pezzi per scontrino': 'items_per_receipt',
            'Presenze': 'visitors',
            'Pezzi venduti': 'items_sold',
            'Margine': 'margin',
            'Sconto medio': 'avg_discount'
        }
        
        # Add category columns mapping
        for i in range(1, 6):
            column_mapping.update({
                f'Incasso (cat {i})': f'sales_cat_{i}',
                f'Margine (cat {i})': f'margin_cat_{i}',
                f'N. pezzi (cat {i})': f'items_cat_{i}',
                f'Sconto medio (cat {i})': f'discount_cat_{i}'
            })
        
        # Rename columns
        self.processed_data = self.raw_data.rename(columns=column_mapping)
        
        # Convert percentage strings to floats
        percentage_columns = [col for col in self.processed_data.columns if 'margin' in col or 'discount' in col]
        for col in percentage_columns:
            self.processed_data[col] = self.processed_data[col].str.rstrip('%').astype('float') / 100
            
        # Add time-based features
        self.processed_data['year'] = self.processed_data['date'].dt.year
        self.processed_data['quarter'] = self.processed_data['date'].dt.quarter
        self.processed_data['month'] = self.processed_data['date'].dt.month
        self.processed_data['week'] = self.processed_data['date'].dt.isocalendar().week
        self.processed_data['weekday'] = self.processed_data['date'].dt.weekday
        
        return self.processed_data

    def set_closed_days(self, days):
        """Set days when store is closed"""
        self.closed_days = set(days)
        
    def set_special_dates(self, dates):
        """Set special dates (holidays, events, etc.)"""
        self.special_dates = set(pd.to_datetime(dates))
        
    def calculate_daily_weights(self):
        """Calculate weights for each day based on historical patterns"""
        # Group by week number and weekday
        weekly_patterns = self.processed_data.groupby(['week', 'weekday'])['total_sales'].mean()
        
        # Calculate special dates patterns
        special_patterns = self.processed_data[
            self.processed_data['date'].isin(self.special_dates)
        ]['total_sales'].mean()
        
        return weekly_patterns, special_patterns

class ForecastingEngine:
    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.yearly_budget = None
        self.forecasts = None
        
    def generate_forecast(self, base_year=None):
        """Generate forecast based on historical data"""
        data = self.data_processor.processed_data
        if base_year:
            data = data[data['year'] == base_year]
            
        # Calculate basic trend
        x = np.arange(len(data))
        y = data['total_sales'].values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Apply seasonality
        weekly_pattern, special_pattern = self.data_processor.calculate_daily_weights()
        
        # Calculate forecast
        forecast = pd.DataFrame()
        forecast['date'] = pd.date_range(
            start=data['date'].max() + timedelta(days=1),
            periods=365
        )
        forecast['sales_forecast'] = slope * (len(data) + np.arange(365)) + intercept
        
        # Adjust for weekly patterns and special dates
        forecast['week'] = forecast['date'].dt.isocalendar().week
        forecast['weekday'] = forecast['date'].dt.weekday
        
        # Apply weekly patterns
        for (week, weekday), weight in weekly_pattern.items():
            mask = (forecast['week'] == week) & (forecast['weekday'] == weekday)
            forecast.loc[mask, 'sales_forecast'] *= weight / weekly_pattern.mean()
            
        # Adjust for special dates
        for date in self.data_processor.special_dates:
            if date in forecast['date'].values:
                forecast.loc[forecast['date'] == date, 'sales_forecast'] *= (
                    special_pattern / forecast['sales_forecast'].mean()
                )
                
        return forecast
    
    def distribute_budget(self, yearly_budget):
        """Distribute yearly budget across different time periods"""
        self.yearly_budget = yearly_budget
        forecast = self.generate_forecast()
        
        # Calculate distribution ratios
        total_forecast = forecast['sales_forecast'].sum()
        daily_ratios = forecast['sales_forecast'] / total_forecast
        
        # Distribute budget
        forecast['daily_budget'] = yearly_budget * daily_ratios
        
        # Calculate additional metrics
        historical_avg = self.data_processor.processed_data.groupby('date').agg({
            'num_receipts': 'mean',
            'items_per_receipt': 'mean',
            'margin': 'mean'
        }).mean()
        
        forecast['target_receipts'] = (forecast['daily_budget'] / 
                                     self.data_processor.processed_data['total_sales'].mean() * 
                                     historical_avg['num_receipts'])
        
        forecast['target_items'] = forecast['target_receipts'] * historical_avg['items_per_receipt']
        
        return forecast

def create_dashboard():
    st.title("Retail Analytics and Forecasting Dashboard")
    
    # Initialize session state
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = RetailDataProcessor()
    if 'forecasting_engine' not in st.session_state:
        st.session_state.forecasting_engine = ForecastingEngine(st.session_state.data_processor)
    
    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        
        # Data upload
        uploaded_file = st.file_uploader("Upload Sales Data (CSV)", type=['csv'])
        
        # Closed days selection
        st.subheader("Store Closure Days")
        closed_days = []
        for day in range(7):
            if st.checkbox(calendar.day_name[day]):
                closed_days.append(day)
                
        # Special dates input
        st.subheader("Special Dates")
        special_date = st.date_input("Add special date")
        if st.button("Add Special Date"):
            if 'special_dates' not in st.session_state:
                st.session_state.special_dates = set()
            st.session_state.special_dates.add(special_date)
            
        # Budget input
        st.subheader("Budget Planning")
        yearly_budget = st.number_input("Yearly Budget Target", min_value=0.0)
        
    # Main dashboard area
    if uploaded_file:
        # Load and process data
        data = st.session_state.data_processor.load_data(uploaded_file)
        st.session_state.data_processor.set_closed_days(closed_days)
        if 'special_dates' in st.session_state:
            st.session_state.data_processor.set_special_dates(st.session_state.special_dates)
            
        # Generate forecasts and budgets
        if yearly_budget > 0:
            forecast_data = st.session_state.forecasting_engine.distribute_budget(yearly_budget)
            
            # Display KPIs
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Daily Sales Target",
                    f"€{forecast_data['daily_budget'].mean():,.2f}",
                    f"{((forecast_data['daily_budget'].mean() - data['total_sales'].mean()) / data['total_sales'].mean() * 100):,.1f}%"
                )
                
            with col2:
                st.metric(
                    "Target Daily Receipts",
                    f"{forecast_data['target_receipts'].mean():,.1f}",
                    f"{((forecast_data['target_receipts'].mean() - data['num_receipts'].mean()) / data['num_receipts'].mean() * 100):,.1f}%"
                )
                
            with col3:
                st.metric(
                    "Average Margin",
                    f"{data['margin'].mean()*100:,.1f}%"
                )
                
            with col4:
                st.metric(
                    "Items per Receipt",
                    f"{data['items_per_receipt'].mean():,.1f}"
                )
            
            # Forecast visualization
            st.subheader("Sales Forecast and Budget Distribution")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=forecast_data['date'],
                y=forecast_data['daily_budget'],
                name="Budget Target"
            ))
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data['total_sales'],
                name="Historical Sales"
            ))
            st.plotly_chart(fig)
            
            # Category performance
            st.subheader("Category Performance")
            category_cols = [col for col in data.columns if 'cat' in col]
            category_metrics = data[category_cols].mean()
            st.bar_chart(category_metrics)
            
        # Data entry section
        st.subheader("Enter New Daily Data")
        col1, col2 = st.columns(2)
        
        with col1:
            new_date = st.date_input("Select Date")
            
        with col2:
            if st.button("Enter New Data"):
                st.session_state.show_entry_form = True
                
        if 'show_entry_form' in st.session_state and st.session_state.show_entry_form:
            with st.form("new_data_entry"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_sales = st.number_input("Total Sales")
                    new_receipts = st.number_input("Number of Receipts")
                    new_items = st.number_input("Items Sold")
                    
                with col2:
                    new_margin = st.number_input("Margin (%)")
                    new_discount = st.number_input("Average Discount (%)")
                    
                if st.form_submit_button("Save"):
                    # Update data logic here
                    st.success(f"Data for {new_date} saved successfully!")
                    st.session_state.show_entry_form = False

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    create_dashboard()
