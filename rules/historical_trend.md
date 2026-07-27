# Historical Trend Engine — Prediction Rules

## Core Concept
Analisis frekuensi historis dan tren untuk memprediksi digit yang paling mungkin muncul.
Engine ini bekerja untuk SEMUA market (universal), tidak terbatas pada market tertentu.

## Algorithm Steps

### 1. Overall Digit Frequency
Hitung frekuensi kemunculan setiap digit (0-9) di seluruh history market.

### 2. Positional Frequency
Hitung frekuensi digit per posisi (posisi 1, 2, 3, 4 dari kiri). Ini menangkap bias posisi — misalnya digit '0' jarang muncul di posisi pertama tapi sering di posisi keempat.

### 3. Recent Trend
Hitung frekuensi digit di N hasil terakhir (default 10). Bandingkan dengan frekuensi overall untuk mendeteksi tren:
- **Hot**: frekuensi recent > frekuensi overall (digit sedang naik)
- **Cold**: frekuensi recent < frekuensi overall (digit sedang turun)
- **Neutral**: frekuensi recent ≈ frekuensi overall (stabil)

### 4. Combined Scoring
Ranking digit berdasarkan 3 komponen:
- **Frequency Score (30%)**: frekuensi overall yang dinormalisasi
- **Positional Score (40%)**: rata-rata normalized frequency di 4 posisi
- **Trend Score (30%)**: recent_trend / overall_trend, di-capped 3x

### 5. Selection
- Top 5 digit → main prediction
- Next digit → backup

## Confidence Calculation
- **Data Score (30%)**: seberapa banyak history (capped di 20 records)
- **Pattern Score (40%)**: diversity (berapa digit unik) + trend strength
- **Position Score (30%)**: seberapa kuat positional bias

## Notes
- Engine tidak memerlukan source market lain — cukup history target market sendiri
- Semakin banyak history, semakin akurat analisis
- Minimum 5 records untuk prediksi bermakna
- Trend analysis memerlukan minimal 10 records untuk hasil optimal
