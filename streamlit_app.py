"""
🗺️ GEOCODING WEB APP - IMPROVED WITH DEBUG
==========================================

FIXED ISSUES:
- Better error handling
- More retries
- Detailed logging
- Fallback mechanisms
- Rate limit optimization
"""

import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import re

# Page config
st.set_page_config(
    page_title="Geocoding Tool - Free",
    page_icon="🗺️",
    layout="wide"
)

class ImprovedGeocoder:
    """Improved geocoder with better error handling"""
    
    def __init__(self, max_workers=2):  # Reduced to 2 for better rate limit
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.stats = {
            'success': 0,
            'not_found': 0,
            'error': 0,
            'timeout': 0,
            'rate_limit': 0
        }
        self.last_request = 0
    
    def rate_limit_wait(self):
        """Enforce 1 second delay between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request
        
        if time_since_last < 1.2:  # 1.2 seconds to be safe
            time.sleep(1.2 - time_since_last)
        
        self.last_request = time.time()
    
    def test_connection(self):
        """Test if Nominatim is accessible"""
        try:
            response = self.session.get(
                'https://nominatim.openstreetmap.org/reverse',
                params={
                    'lat': -6.2088,
                    'lon': 106.8456,
                    'format': 'json'
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def geocode_nominatim(self, lat, lon, retry=0):
        """Geocode with Nominatim with retries"""
        
        # Rate limit
        self.rate_limit_wait()
        
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 18,
            'accept-language': 'id'
        }
        
        try:
            response = self.session.get(
                'https://nominatim.openstreetmap.org/reverse',
                params=params,
                timeout=15  # Longer timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data and 'address' in data:
                    return data, None
                else:
                    return None, 'no_result'
            
            elif response.status_code == 429:
                # Rate limited
                self.stats['rate_limit'] += 1
                if retry < 2:
                    time.sleep(3)  # Wait longer
                    return self.geocode_nominatim(lat, lon, retry + 1)
                return None, 'rate_limit'
            
            else:
                return None, f'http_{response.status_code}'
        
        except requests.Timeout:
            self.stats['timeout'] += 1
            if retry < 2:
                time.sleep(2)
                return self.geocode_nominatim(lat, lon, retry + 1)
            return None, 'timeout'
        
        except Exception as e:
            return None, str(e)[:50]
    
    def geocode_coordinate(self, lat, lon, kelurahan=None):
        """Geocode single coordinate"""
        
        data, error = self.geocode_nominatim(lat, lon)
        
        if data:
            address = data.get('address', {})
            
            road = address.get('road', '')
            suburb = address.get('suburb') or address.get('village') or address.get('neighbourhood', '')
            district = address.get('city_district') or address.get('municipality', '')
            city = address.get('city') or address.get('town', '')
            province = address.get('state', '')
            
            self.stats['success'] += 1
            
            return {
                'Nama_Jalan': road or 'Tidak ada',
                'Kelurahan': suburb,
                'Kecamatan': district,
                'Kota': city,
                'Provinsi': province,
                'Alamat_Lengkap': data.get('display_name', ''),
                'Status': 'OK',
                'Source': 'nominatim',
                'Error': None
            }
        else:
            self.stats['not_found'] += 1
            return {
                'Nama_Jalan': 'NOT_FOUND',
                'Kelurahan': '',
                'Kecamatan': '',
                'Kota': '',
                'Provinsi': '',
                'Alamat_Lengkap': '',
                'Status': 'NOT_FOUND',
                'Source': 'None',
                'Error': error or 'unknown'
            }


def create_template():
    """Create template"""
    return pd.DataFrame({
        'latitude': [-6.2088, -6.1751, -6.2146, -6.1969, -6.1703],
        'longitude': [106.8456, 106.8650, 106.8451, 106.7685, 106.8143],
        'kelurahan': ['Menteng', 'Gambir', 'Tanah Abang', 'Kebon Jeruk', 'Petojo'],
        'kecamatan': ['Menteng', 'Gambir', 'Tanah Abang', 'Kebon Jeruk', 'Gambir']
    })


def main():
    st.title("🗺️ Geocoding Tool - Improved")
    
    st.info("⚠️ **Important:** Set workers to 1-2 max for Nominatim. Too many workers = all NOT_FOUND!")
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Settings")
        max_workers = st.slider("Workers", 1, 2, 1, 
                               help="RECOMMENDED: 1 worker. More = rate limit!")
        
        st.warning("⚠️ **Use 1 worker** to avoid rate limiting!")
        
        st.markdown("---")
        st.markdown("### Debug Info")
        if st.button("Test Nominatim Connection"):
            geocoder = ImprovedGeocoder()
            if geocoder.test_connection():
                st.success("✅ Nominatim is accessible!")
            else:
                st.error("❌ Cannot reach Nominatim!")
    
    # Tabs
    tab1, tab2 = st.tabs(["📤 Upload & Process", "ℹ️ Help"])
    
    with tab1:
        # Download template
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("### 📥 Download Template")
            template_df = create_template()
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                template_df.to_excel(writer, index=False)
            excel_data = output.getvalue()
            
            st.download_button(
                label="⬇️ Download Template",
                data=excel_data,
                file_name="template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.markdown("---")
        
        # Upload
        st.markdown("### 📤 Upload Your Data")
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'])
        
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Loaded {len(df)} rows")
            
            # Detect columns
            lat_col = None
            lon_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if col_lower in ['latitude', 'lat', 'y']:
                    lat_col = col
                if col_lower in ['longitude', 'lon', 'lng', 'x']:
                    lon_col = col
            
            if not lat_col or not lon_col:
                st.error("❌ Cannot find latitude/longitude columns!")
                return
            
            st.info(f"📍 Using: {lat_col}, {lon_col}")
            
            with st.expander("👀 Preview Data"):
                st.dataframe(df.head(10))
            
            # Estimate
            est_time = len(df) * 1.5 / max_workers
            st.warning(f"⏱️ Estimated time: ~{est_time/60:.1f} minutes ({est_time:.0f} seconds)")
            
            if len(df) > 50:
                st.error(f"⚠️ {len(df)} rows is A LOT for web app! Consider testing with 10-20 rows first!")
            
            # Process button
            if st.button("🚀 Start Geocoding", type="primary"):
                st.markdown("---")
                st.markdown("### 🔄 Processing...")
                
                # Normalize
                df['latitude'] = df[lat_col]
                df['longitude'] = df[lon_col]
                df['kelurahan'] = df.get('kelurahan', '')
                
                # Initialize
                geocoder = ImprovedGeocoder(max_workers=max_workers)
                
                # Test first
                st.info("🔍 Testing connection...")
                if not geocoder.test_connection():
                    st.error("❌ Cannot reach Nominatim! Check internet or try later.")
                    return
                st.success("✅ Connection OK!")
                
                # Progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                start_time = time.time()
                
                # Process sequentially for better rate limit control
                for idx, row in df.iterrows():
                    result = geocoder.geocode_coordinate(
                        row['latitude'],
                        row['longitude'],
                        row.get('kelurahan')
                    )
                    
                    result['Latitude'] = row['latitude']
                    result['Longitude'] = row['longitude']
                    result['Kelurahan_Original'] = row.get('kelurahan', '')
                    
                    results.append(result)
                    
                    progress = (idx + 1) / len(df)
                    progress_bar.progress(progress)
                    status_text.text(f"Processed: {idx+1}/{len(df)} ({progress*100:.1f}%)")
                
                elapsed = time.time() - start_time
                
                # Results
                df_result = pd.DataFrame(results)
                
                st.success(f"✅ Completed in {elapsed/60:.1f} minutes!")
                
                # Stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", len(df))
                with col2:
                    st.metric("Success", geocoder.stats['success'],
                             delta=f"{geocoder.stats['success']/len(df)*100:.1f}%")
                with col3:
                    st.metric("Not Found", geocoder.stats['not_found'])
                with col4:
                    st.metric("Speed", f"{len(df)/elapsed:.2f} coord/sec")
                
                # Debug stats
                with st.expander("🔍 Debug Information"):
                    st.json({
                        'Timeouts': geocoder.stats['timeout'],
                        'Rate Limits': geocoder.stats['rate_limit'],
                        'Errors': geocoder.stats['error']
                    })
                
                # Show results
                st.markdown("### 📊 Results")
                st.dataframe(df_result)
                
                # Show errors if many NOT_FOUND
                if geocoder.stats['not_found'] > len(df) * 0.5:
                    st.error("⚠️ More than 50% NOT_FOUND! Possible issues:")
                    st.markdown("""
                    - **Rate limiting**: Try with 1 worker only
                    - **Network issues**: Check connection
                    - **Invalid coordinates**: Verify data
                    - **Nominatim down**: Try again later
                    """)
                
                # Download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_result.to_excel(writer, index=False)
                excel_data = output.getvalue()
                
                st.download_button(
                    label="⬇️ Download Results",
                    data=excel_data,
                    file_name=f"hasil_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
    
    with tab2:
        st.markdown("""
        ### ℹ️ Important Notes
        
        **Why 100% NOT_FOUND?**
        1. **Too many workers**: Nominatim blocks if too many concurrent requests
        2. **Rate limiting**: Nominatim has strict 1 req/sec limit
        3. **Network issues**: Streamlit Cloud IP might be rate limited
        
        **Solutions:**
        1. **Use 1 worker only** (MOST IMPORTANT!)
        2. Test with small data (10-20 rows) first
        3. If still fails, try later (Nominatim might be busy)
        
        **For large data (>50 rows):**
        - Use desktop scripts instead
        - Or process in small batches
        """)


if __name__ == "__main__":
    main()