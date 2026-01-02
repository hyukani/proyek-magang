import pandas as pd
from flask import Flask, render_template, jsonify, request
import os
import glob
import sys

app = Flask(__name__)

# --- KONFIGURASI ---
EXCEL_FILE = 'data_dashboard_internet.xlsx'
MASTER_DATA = None
LOAD_STATUS = {"status": "init", "message": "Menunggu proses loading...", "details": []}

def log_status(msg):
    print(msg)
    LOAD_STATUS["details"].append(msg)

def load_data():
    global MASTER_DATA
    log_status(f"--- MEMULAI PROSES LOADING DATA ---")
    log_status(f"Current Directory: {os.getcwd()}")
    log_status(f"Files: {os.listdir('.')}")
    
    all_dfs = []
    target_years = [2022, 2023, 2024, 2025]
    
    # Mapping nama kolom agar seragam
    col_mapping_base = {
        'kab/kota': 'city',
        'Pilar Infrastruktur dan Ekosistem': 'infra',
        'Pilar Keterampilan Digital': 'skill',
        'Pilar Pemberdayaan': 'empowerment',
        'Pilar Pekerjaan': 'job'
    }

    # 1. COBA BACA EXCEL LANGSUNG (Prioritas Utama)
    if os.path.exists(EXCEL_FILE):
        log_status(f"[OK] File Excel ditemukan: {EXCEL_FILE}")
        try:
            xl = pd.ExcelFile(EXCEL_FILE)
            sheet_names = xl.sheet_names
            log_status(f"[INFO] Sheet ditemukan: {sheet_names}")
            
            for sheet in sheet_names:
                # Cek apakah nama sheet mengandung tahun target
                year = None
                for y in target_years:
                    if str(y) in sheet:
                        year = y
                        break
                
                if year:
                    try:
                        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
                        # Bersihkan nama kolom
                        df.columns = [str(c).strip() for c in df.columns]
                        
                        # Rename kolom sesuai mapping
                        new_cols = {}
                        for col in df.columns:
                            for k, v in col_mapping_base.items():
                                if k.lower() in col.lower():
                                    new_cols[col] = v
                        df.rename(columns=new_cols, inplace=True)
                        
                        df['year'] = year
                        
                        # Kolom skor biasanya bernama tahun (misal '2025')
                        if str(year) in df.columns:
                            df['score'] = df[str(year)]
                        elif 'score' not in df.columns:
                            # Fallback: hitung rata-rata pilar jika ada
                            pilar_cols = [c for c in ['infra', 'skill', 'empowerment', 'job'] if c in df.columns]
                            if pilar_cols:
                                df['score'] = df[pilar_cols].mean(axis=1)
                            else:
                                df['score'] = 0
                        
                        if 'city' in df.columns:
                            all_dfs.append(df)
                            log_status(f"[SUKSES] Data Excel tahun {year} dimuat dari sheet '{sheet}'")
                    except Exception as e:
                        log_status(f"[ERROR] Gagal baca sheet {sheet}: {e}")
        except Exception as e:
            log_status(f"[ERROR] Gagal membuka file Excel: {e}")
    else:
        log_status(f"[INFO] File {EXCEL_FILE} tidak ditemukan, beralih ke CSV...")

    # 2. COBA BACA CSV (Fallback / Alternatif jika Excel dipecah)
    # Sistem mungkin memecah Excel menjadi: "data_dashboard_internet.xlsx - IMDI 2025.csv"
    if len(all_dfs) < len(target_years):
        csv_files = glob.glob("*.csv")
        log_status(f"[INFO] File CSV ditemukan: {csv_files}")
        
        for year in target_years:
            # Skip jika tahun ini sudah didapat dari Excel
            if any(not d.empty and d['year'].iloc[0] == year for d in all_dfs):
                continue
                
            # Cari file yang mengandung tahun tersebut
            # Case insensitive search
            matching = [f for f in csv_files if str(year) in f and "IMDI" in f]
            if not matching: 
                 matching = [f for f in csv_files if str(year) in f] # Coba pencarian lebih luas
            
            if matching:
                fname = matching[0]
                try:
                    df = pd.read_csv(fname)
                    # Bersihkan nama kolom
                    df.columns = [str(c).strip() for c in df.columns]
                    
                    # Rename
                    new_cols = {}
                    for col in df.columns:
                        for k, v in col_mapping_base.items():
                            if k.lower() in col.lower():
                                new_cols[col] = v
                    df.rename(columns=new_cols, inplace=True)
                    
                    if 'city' not in df.columns:
                        log_status(f"[SKIP] File {fname} tidak memiliki kolom kota.")
                        continue

                    df['year'] = year
                    
                    # Skor
                    if str(year) in df.columns:
                        df['score'] = df[str(year)]
                    else:
                        pilar_cols = [c for c in ['infra', 'skill', 'empowerment', 'job'] if c in df.columns]
                        if pilar_cols:
                            df['score'] = df[pilar_cols].mean(axis=1)
                        else:
                            df['score'] = 0
                    
                    all_dfs.append(df)
                    log_status(f"[SUKSES] Data CSV tahun {year} dimuat dari file: {fname}")
                except Exception as e:
                    log_status(f"[ERROR] Gagal baca CSV {fname}: {e}")
            else:
                log_status(f"[WARNING] Tidak ditemukan file data untuk tahun {year}")

    # 3. GABUNGKAN SEMUA
    if all_dfs:
        try:
            MASTER_DATA = pd.concat(all_dfs, ignore_index=True)
            
            # Konversi Tipe Data
            numeric_cols = ['score', 'infra', 'skill', 'empowerment', 'job']
            for col in numeric_cols:
                if col in MASTER_DATA.columns:
                    MASTER_DATA[col] = pd.to_numeric(MASTER_DATA[col], errors='coerce').fillna(0)
            
            # Standardisasi Nama Kota
            MASTER_DATA['city'] = MASTER_DATA['city'].astype(str).str.upper().str.strip()
            
            # Hitung Growth (YoY)
            MASTER_DATA.sort_values(by=['city', 'year'], inplace=True)
            MASTER_DATA['growth'] = MASTER_DATA.groupby('city')['score'].pct_change() * 100
            MASTER_DATA['growth'] = MASTER_DATA['growth'].fillna(0).round(2)
            
            LOAD_STATUS["status"] = "success"
            LOAD_STATUS["message"] = f"Berhasil memuat {len(MASTER_DATA)} baris data."
            log_status("[FINAL] Data berhasil digabungkan dan siap digunakan.")
        except Exception as e:
            LOAD_STATUS["status"] = "error"
            LOAD_STATUS["message"] = f"Error penggabungan data: {e}"
    else:
        LOAD_STATUS["status"] = "error"
        LOAD_STATUS["message"] = "Tidak ada data yang berhasil dimuat dari Excel maupun CSV."

# Load data saat aplikasi start
load_data()

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/debug_status')
def debug_status():
    """Endpoint untuk mengecek log loading data"""
    return jsonify(LOAD_STATUS)

@app.route('/api/dashboard_analysis')
def get_dashboard_analysis():
    if MASTER_DATA is None or MASTER_DATA.empty:
        return jsonify({
            'error': True, 
            'message': LOAD_STATUS['message'],
            'details': LOAD_STATUS['details']
        })

    try:
        year_param = int(request.args.get('year', 2025))
        
        # Filter data tahun ini
        df_curr = MASTER_DATA[MASTER_DATA['year'] == year_param].copy()
        
        if df_curr.empty:
            # Jika tahun 2025 belum ada, gunakan tahun terakhir yang tersedia
            max_year = int(MASTER_DATA['year'].max())
            df_curr = MASTER_DATA[MASTER_DATA['year'] == max_year].copy()
            year_param = max_year # Update year param agar UI tahu
        
        # Statistik
        avg_score = df_curr['score'].mean()
        max_score = df_curr['score'].max()
        min_score = df_curr['score'].min()
        gap = max_score - min_score
        
        # Top & Bottom
        # Gunakan nlargest/nsmallest
        top_5 = df_curr.nlargest(5, 'score')[['city', 'score', 'growth']].to_dict(orient='records')
        bottom_5 = df_curr.nsmallest(5, 'score')[['city', 'score', 'growth']].to_dict(orient='records')
        
        # Data Kuadran
        quadrant_data = []
        for _, row in df_curr.iterrows():
            hc = (row.get('skill', 0) + row.get('empowerment', 0)) / 2
            quadrant_data.append({
                'city': row['city'],
                'x': row.get('infra', 0),
                'y': hc,
                'r': row['score'] / 5
            })
            
        # Watchlist (Growth Negatif)
        declining = df_curr[df_curr['growth'] < 0][['city', 'growth', 'score']].to_dict(orient='records')

        return jsonify({
            'year': year_param,
            'stats': {
                'avg': round(avg_score, 2),
                'gap': round(gap, 2),
                'highest': top_5[0]['city'] if top_5 else '-',
                'lowest': bottom_5[0]['city'] if bottom_5 else '-'
            },
            'top_5': top_5,
            'bottom_5': bottom_5,
            'declining': declining,
            'quadrant': quadrant_data
        })
    except Exception as e:
        return jsonify({'error': True, 'message': f"Runtime Error: {str(e)}"})

@app.route('/api/simulation_data')
def get_simulation_data():
    if MASTER_DATA is None or MASTER_DATA.empty: return jsonify([])
    cities = sorted(MASTER_DATA['city'].unique().tolist())
    return jsonify(cities)

@app.route('/api/analyze_city')
def analyze_city():
    city = request.args.get('city', '').upper()
    if MASTER_DATA is None or MASTER_DATA.empty: return jsonify({'error': 'No Data'})
    
    df_city = MASTER_DATA[MASTER_DATA['city'] == city].sort_values('year')
    if df_city.empty: return jsonify({'found': False})
    
    latest = df_city.iloc[-1]
    curr_year = latest['year']
    
    df_prov = MASTER_DATA[MASTER_DATA['year'] == curr_year]
    prov_avg = df_prov[['score', 'infra', 'skill', 'empowerment', 'job']].mean()
    
    comparison = {
        'score_diff': latest['score'] - prov_avg['score'],
        'infra_diff': latest['infra'] - prov_avg['infra'],
        'skill_diff': latest['skill'] - prov_avg['skill'],
        'empowerment_diff': latest['empowerment'] - prov_avg['empowerment'],
        'job_diff': latest['job'] - prov_avg['job']
    }
    
    recommendations = []
    if comparison['infra_diff'] < -5:
        recommendations.append("🚨 KRITIS: Infrastruktur tertinggal. Prioritaskan akses internet.")
    if comparison['skill_diff'] < 0:
        recommendations.append("⚠️ Skill Digital di bawah rata-rata. Perbanyak pelatihan.")
    if comparison['empowerment_diff'] < 0:
        recommendations.append("💡 Pemberdayaan rendah. Dorong adopsi digital UMKM.")
        
    if not recommendations: recommendations.append("✅ Kinerja Baik. Pertahankan.")

    return jsonify({
        'found': True,
        'city': city,
        'latest_data': latest.to_dict(),
        'prov_avg': prov_avg.to_dict(),
        'comparison': comparison,
        'recommendations': recommendations
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)