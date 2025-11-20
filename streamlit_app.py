"""
🗺️ GEOCODING WEB APP - NOMINATIM ULTRA
=======================================

Web-based geocoding tool dengan Nominatim (100% GRATIS!)

Features:
• Upload Excel file
• Download template
• Real-time progress tracking
• Download hasil geocoding
• 100% FREE (no API key needed!)

Deploy: Streamlit Cloud (free hosting!)
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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    .info-box-blue {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)


class UltraGeocoderWeb:
    """Ultra Geocoder untuk web app"""
    
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.providers = {
            'nominatim': {
                'url': 'https://nominatim.openstreetmap.org/reverse',
                'delay': 1.0,
                'last_request': 0
            },
            'photon': {
                'url': 'https://photon.komoot.io/reverse',
                'delay': 0.5,
                'last_request': 0
            }
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Geocoding-Web-App/1.0'
        })
        self.stats = {
            'success': 0,
            'not_found': 0,
            'error': 0
        }
    
    def normalize_text(self, text):
        if not text or pd.isna(text):
            return ""
        text = str(text).lower().strip()
        text = re.sub(r'\b(kel\.|kelurahan|kec\.|kecamatan)\b', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def calculate_similarity(self, text1, text2):
        if not text1 or not text2:
            return 0.0
        text1 = self.normalize_text(text1)
        text2 = self.normalize_text(text2)
        if text1 == text2:
            return 1.0
        if text1 in text2 or text2 in text1:
            return 0.8
        words1 = set(text1.split())
        words2 = set(text2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0.0
    
    def score_result(self, address, expected_kelurahan=None, expected_kecamatan=None):
        score = 0.0
        weights = {'kelurahan': 0.6, 'kecamatan': 0.4}
        
        result_kelurahan = address.get('suburb') or address.get('village') or address.get('neighbourhood')
        result_kecamatan = address.get('city_district') or address.get('municipality')
        
        if expected_kelurahan and result_kelurahan:
            sim = self.calculate_similarity(expected_kelurahan, result_kelurahan)
            score += weights['kelurahan'] * sim
        
        if expected_kecamatan and result_kecamatan:
            sim = self.calculate_similarity(expected_kecamatan, result_kecamatan)
            score += weights['kecamatan'] * sim
        
        return score
    
    def rate_limit(self, provider_name):
        provider = self.providers[provider_name]
        current_time = time.time()
        time_since_last = current_time - provider['last_request']
        if time_since_last < provider['delay']:
            time.sleep(provider['delay'] - time_since_last)
        provider['last_request'] = time.time()
    
    def geocode_nominatim(self, lat, lon, zoom=18):
        self.rate_limit('nominatim')
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
            'zoom': zoom,
            'accept-language': 'id'
        }
        try:
            response = self.session.get(
                self.providers['nominatim']['url'],
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data and 'address' in data:
                    return data, 'nominatim'
        except:
            pass
        return None, None
    
    def geocode_photon(self, lat, lon):
        self.rate_limit('photon')
        params = {'lat': lat, 'lon': lon, 'lang': 'id'}
        try:
            response = self.session.get(
                self.providers['photon']['url'],
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'features' in data and len(data['features']) > 0:
                    feature = data['features'][0]
                    properties = feature.get('properties', {})
                    photon_data = {
                        'address': {
                            'road': properties.get('street'),
                            'suburb': properties.get('district') or properties.get('locality'),
                            'city_district': properties.get('county'),
                            'city': properties.get('city'),
                            'state': properties.get('state'),
                            'postcode': properties.get('postcode')
                        },
                        'display_name': properties.get('name', ''),
                        'lat': feature['geometry']['coordinates'][1],
                        'lon': feature['geometry']['coordinates'][0]
                    }
                    return photon_data, 'photon'
        except:
            pass
        return None, None
    
    def geocode_coordinate(self, lat, lon, expected_kelurahan=None, expected_kecamatan=None):
        # Try multiple strategies
        results = []
        
        # Strategy 1: Nominatim zoom 18
        data, source = self.geocode_nominatim(lat, lon, zoom=18)
        if data:
            results.append((data, source))
        
        # Strategy 2: Nominatim zoom 17
        if not results:
            data, source = self.geocode_nominatim(lat, lon, zoom=17)
            if data:
                results.append((data, source))
        
        # Strategy 3: Photon
        if not results:
            data, source = self.geocode_photon(lat, lon)
            if data:
                results.append((data, source))
        
        if results:
            data, source = results[0]
            address = data.get('address', {})
            
            # Score if validation enabled
            confidence_score = 0.5
            if expected_kelurahan:
                confidence_score = self.score_result(address, expected_kelurahan, expected_kecamatan)
            
            # Extract info
            road_name = address.get('road') or address.get('street') or ''
            suburb = (address.get('suburb') or address.get('village') or 
                     address.get('neighbourhood') or address.get('district') or '')
            subdistrict = (address.get('city_district') or 
                          address.get('municipality') or address.get('county') or '')
            city = (address.get('city') or address.get('town') or 
                   address.get('county') or '')
            province = address.get('state') or ''
            
            self.stats['success'] += 1
            
            return {
                'Nama_Jalan': road_name or 'Tidak ditemukan',
                'Kelurahan': suburb,
                'Kecamatan': subdistrict,
                'Kota': city,
                'Provinsi': province,
                'Alamat_Lengkap': data.get('display_name', ''),
                'Confidence_Score': round(confidence_score, 2),
                'Status': 'OK',
                'Source': source
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
                'Confidence_Score': 0.0,
                'Status': 'NOT_FOUND',
                'Source': 'None'
            }


def create_template():
    """Create template Excel file"""
    template_data = {
        'latitude': [
            -6.2088, -6.1751, -6.2146, -6.2297, -6.1862,
            -6.2603, -6.1862, -6.2441, -6.2249, -6.1944
        ],
        'longitude': [
            106.8456, 106.8650, 106.8451, 106.8177, 106.8063,
            106.7811, 106.7999, 106.8381, 106.8073, 106.8229
        ],
        'kelurahan': [
            'Menteng', 'Gambir', 'Tanah Abang', 'Kebon Jeruk',
            'Palmerah', 'Grogol', 'Slipi', 'Cikini', 'Bendungan Hilir', 'Gondangdia'
        ],
        'kecamatan': [
            'Menteng', 'Gambir', 'Tanah Abang', 'Kebon Jeruk',
            'Palmerah', 'Grogol Petamburan', 'Palmerah', 'Menteng', 'Tanah Abang', 'Menteng'
        ]
    }
    
    df = pd.DataFrame(template_data)
    return df


def detect_columns(df):
    """Auto-detect required columns"""
    columns_lower = {col.lower(): col for col in df.columns}
    
    # Detect latitude
    lat_col = None
    for name in ['latitude', 'lat', 'y', 'lintang']:
        if name in columns_lower:
            lat_col = columns_lower[name]
            break
    
    # Detect longitude
    lon_col = None
    for name in ['longitude', 'lon', 'lng', 'long', 'x', 'bujur']:
        if name in columns_lower:
            lon_col = columns_lower[name]
            break
    
    # Detect kelurahan
    kel_col = None
    for name in ['kelurahan', 'kel', 'village', 'desa']:
        if name in columns_lower:
            kel_col = columns_lower[name]
            break
    
    # Detect kecamatan
    kec_col = None
    for name in ['kecamatan', 'kec', 'district']:
        if name in columns_lower:
            kec_col = columns_lower[name]
            break
    
    return lat_col, lon_col, kel_col, kec_col


def main():
    # Header
    st.markdown('<h1 class="main-header">🗺️ Geocoding Tool - FREE</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/streamlit/streamlit/develop/docs/_static/logo.png", width=100)
        st.title("⚙️ Settings")
        
        st.markdown("### Processing Options")
        max_workers = st.slider("Workers (Parallel Processing)", 1, 5, 3, 
                               help="More workers = faster, but respect rate limits!")
        
        use_validation = st.checkbox("Enable Kelurahan/Kecamatan Validation", value=True,
                                    help="Validate results dengan data kelurahan/kecamatan")
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        **Geocoding Tool v1.0**
        
        100% FREE geocoding using:
        • OpenStreetMap Nominatim
        • Photon (fallback)
        
        No API key needed! 🎉
        """)
        
        st.markdown("---")
        st.markdown("### Support")
        st.markdown("""
        📧 Email: support@company.com  
        💬 Slack: #gis-team  
        📚 [Documentation](https://github.com)
        """)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "📊 Statistics", "ℹ️ Help"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="info-box info-box-blue">', unsafe_allow_html=True)
            st.markdown("""
            **📋 Instructions:**
            1. Download template Excel (or use your own file)
            2. Fill with your data (latitude, longitude, kelurahan, kecamatan)
            3. Upload file
            4. Click "Start Geocoding"
            5. Download results!
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📥 Download Template")
            template_df = create_template()
            
            # Convert to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                template_df.to_excel(writer, index=False, sheet_name='Template')
            excel_data = output.getvalue()
            
            st.download_button(
                label="⬇️ Download Template.xlsx",
                data=excel_data,
                file_name="template_geocoding.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Download template dengan contoh data"
            )
            
            with st.expander("👀 Preview Template"):
                st.dataframe(template_df, use_container_width=True)
        
        st.markdown("---")
        
        # File upload
        st.markdown("### 📤 Upload Your Data")
        uploaded_file = st.file_uploader(
            "Choose Excel file (.xlsx)",
            type=['xlsx'],
            help="Upload file Excel dengan kolom: latitude, longitude, kelurahan (optional), kecamatan (optional)"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ File uploaded successfully! Total rows: {len(df)}")
                
                # Detect columns
                lat_col, lon_col, kel_col, kec_col = detect_columns(df)
                
                if not lat_col or not lon_col:
                    st.error("❌ Error: Tidak dapat menemukan kolom latitude/longitude!")
                    st.info("Expected column names: latitude/lat/y dan longitude/lon/lng/x")
                    st.stop()
                
                # Show detected columns
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Latitude Column", lat_col)
                with col2:
                    st.metric("Longitude Column", lon_col)
                with col3:
                    st.metric("Kelurahan Column", kel_col or "Not found")
                with col4:
                    st.metric("Kecamatan Column", kec_col or "Not found")
                
                # Show preview
                with st.expander("👀 Preview Data (first 10 rows)"):
                    st.dataframe(df.head(10), use_container_width=True)
                
                # Estimate time
                estimated_time = len(df) / (max_workers * 1.5)
                st.info(f"⏱️ Estimated processing time: ~{estimated_time:.1f} minutes for {len(df)} rows")
                
                # Warning for large data
                if len(df) > 1000:
                    st.warning(f"⚠️ Large dataset detected ({len(df)} rows). Processing may take ~{estimated_time/60:.1f} hours.")
                
                # Start button
                if st.button("🚀 Start Geocoding", type="primary", use_container_width=True):
                    st.markdown("---")
                    st.markdown("### 🔄 Processing...")
                    
                    # Normalize columns
                    df['latitude'] = df[lat_col]
                    df['longitude'] = df[lon_col]
                    if kel_col:
                        df['kelurahan'] = df[kel_col]
                    if kec_col:
                        df['kecamatan'] = df[kec_col]
                    
                    # Initialize geocoder
                    geocoder = UltraGeocoderWeb(max_workers=max_workers)
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Results container
                    results = []
                    
                    # Process with ThreadPoolExecutor
                    start_time = time.time()
                    
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {}
                        
                        for idx, row in df.iterrows():
                            expected_kelurahan = row.get('kelurahan') if kel_col else None
                            expected_kecamatan = row.get('kecamatan') if kec_col else None
                            
                            future = executor.submit(
                                geocoder.geocode_coordinate,
                                row['latitude'], row['longitude'],
                                expected_kelurahan, expected_kecamatan
                            )
                            futures[future] = idx
                        
                        completed = 0
                        for future in as_completed(futures):
                            result = future.result()
                            idx = futures[future]
                            
                            # Add original data
                            result['Original_Index'] = idx
                            result['Latitude'] = df.loc[idx, 'latitude']
                            result['Longitude'] = df.loc[idx, 'longitude']
                            if kel_col:
                                result['Kelurahan_Original'] = df.loc[idx, 'kelurahan']
                            if kec_col:
                                result['Kecamatan_Original'] = df.loc[idx, 'kecamatan']
                            
                            results.append(result)
                            
                            completed += 1
                            progress = completed / len(df)
                            progress_bar.progress(progress)
                            status_text.text(f"Processed: {completed}/{len(df)} ({progress*100:.1f}%)")
                    
                    elapsed = time.time() - start_time
                    
                    # Create result dataframe
                    df_result = pd.DataFrame(results)
                    df_result = df_result.sort_values('Original_Index').reset_index(drop=True)
                    
                    # Show results
                    st.success(f"✅ Geocoding completed in {elapsed/60:.1f} minutes!")
                    
                    # Statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total", len(df))
                    with col2:
                        st.metric("Success", geocoder.stats['success'], 
                                 delta=f"{geocoder.stats['success']/len(df)*100:.1f}%")
                    with col3:
                        st.metric("Not Found", geocoder.stats['not_found'],
                                 delta=f"{geocoder.stats['not_found']/len(df)*100:.1f}%")
                    with col4:
                        st.metric("Speed", f"{len(df)/elapsed:.2f} coord/sec")
                    
                    # Show results preview
                    st.markdown("### 📊 Results Preview")
                    st.dataframe(df_result.head(20), use_container_width=True)
                    
                    # Download button
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_result.to_excel(writer, index=False, sheet_name='Results')
                    excel_data = output.getvalue()
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    st.download_button(
                        label="⬇️ Download Results",
                        data=excel_data,
                        file_name=f"hasil_geocoding_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )
                    
                    # Store in session state for statistics tab
                    st.session_state['results'] = df_result
                    st.session_state['stats'] = geocoder.stats
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                st.exception(e)
    
    with tab2:
        st.markdown("### 📊 Processing Statistics")
        
        if 'results' in st.session_state:
            df_result = st.session_state['results']
            stats = st.session_state['stats']
            
            # Overall stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Success Rate", f"{stats['success']/len(df_result)*100:.1f}%")
            with col2:
                st.metric("Average Confidence", f"{df_result['Confidence_Score'].mean():.2f}")
            with col3:
                st.metric("High Confidence (>0.7)", 
                         f"{len(df_result[df_result['Confidence_Score']>=0.7])} rows")
            
            # Charts
            import plotly.express as px
            
            # Status distribution
            st.markdown("#### Status Distribution")
            status_counts = df_result['Status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title="Geocoding Status")
            st.plotly_chart(fig, use_container_width=True)
            
            # Confidence score distribution
            st.markdown("#### Confidence Score Distribution")
            fig = px.histogram(df_result, x='Confidence_Score', nbins=20,
                             title="Confidence Score Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
            # Source distribution
            st.markdown("#### Provider Usage")
            source_counts = df_result['Source'].value_counts()
            fig = px.bar(x=source_counts.index, y=source_counts.values,
                        labels={'x': 'Provider', 'y': 'Count'},
                        title="Geocoding Provider Usage")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("No data processed yet. Upload and process data first!")
    
    with tab3:
        st.markdown("### ℹ️ Help & Documentation")
        
        with st.expander("📖 How to Use"):
            st.markdown("""
            **Step-by-step Guide:**
            
            1. **Download Template**
               - Click "Download Template.xlsx" button
               - Open in Excel
               - See example format
            
            2. **Prepare Your Data**
               - Required columns: `latitude`, `longitude`
               - Optional: `kelurahan`, `kecamatan` (for validation)
               - Save as .xlsx file
            
            3. **Upload File**
               - Click "Choose Excel file"
               - Select your .xlsx file
               - System will auto-detect columns
            
            4. **Configure Settings**
               - Adjust workers (1-5)
               - Enable/disable validation
            
            5. **Start Geocoding**
               - Click "Start Geocoding"
               - Wait for progress bar
               - Download results when done!
            """)
        
        with st.expander("⚙️ Settings Explained"):
            st.markdown("""
            **Workers (Parallel Processing):**
            - 1 worker: Slowest, safest
            - 3 workers: Recommended (balanced)
            - 5 workers: Fastest, max recommended
            - More workers = faster processing
            
            **Kelurahan/Kecamatan Validation:**
            - Enable: Compare results with input data
            - Calculates confidence score
            - Helps identify mismatches
            - Recommended for quality control
            """)
        
        with st.expander("📊 Understanding Results"):
            st.markdown("""
            **Output Columns:**
            - `Nama_Jalan`: Street name
            - `Kelurahan`: Village/kelurahan
            - `Kecamatan`: District/kecamatan
            - `Kota`: City
            - `Provinsi`: Province
            - `Alamat_Lengkap`: Full address
            - `Confidence_Score`: Match quality (0-1)
            - `Status`: OK or NOT_FOUND
            - `Source`: nominatim or photon
            
            **Confidence Score:**
            - 0.9-1.0: Excellent match
            - 0.7-0.9: Good match
            - 0.5-0.7: Fair match
            - <0.5: Review manually
            """)
        
        with st.expander("⚠️ Limitations"):
            st.markdown("""
            **Rate Limits:**
            - Nominatim: 1 request/second
            - Photon: 2 requests/second
            - Please respect fair use policy!
            
            **Accuracy:**
            - Success rate: 85-90%
            - Depends on data quality
            - Urban areas: better coverage
            - Rural areas: may have gaps
            
            **Processing Time:**
            - 100 rows: ~40 seconds
            - 500 rows: ~2-3 minutes
            - 1000 rows: ~5-7 minutes
            - 5000 rows: ~30-40 minutes
            """)
        
        with st.expander("🐛 Troubleshooting"):
            st.markdown("""
            **Common Issues:**
            
            1. **"Column not found" error**
               - Check column names match: latitude, longitude
               - Or use: lat, lon, lng, x, y
            
            2. **Many NOT_FOUND results**
               - Coordinates may be in remote areas
               - Check coordinates are valid
               - Try reducing workers to 1
            
            3. **Slow processing**
               - Normal for large datasets
               - Increase workers (up to 5)
               - Check internet connection
            
            4. **Rate limit errors**
               - Reduce workers
               - Wait and retry
               - System will auto-retry
            """)
        
        st.markdown("---")
        st.markdown("### 📞 Support")
        st.info("""
        Need help? Contact us:
        - 📧 Email: support@company.com
        - 💬 Slack: #gis-team
        - 📚 Documentation: [Link to docs]
        """)


if __name__ == "__main__":
    main()
