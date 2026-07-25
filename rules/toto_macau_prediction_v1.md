# Luna Rule Engine
# Toto Macau Prediction Logic v1

## Nama Rule

Toto Macau Cross Result Similarity Analysis


---

# Tujuan

Menganalisa kandidat digit berdasarkan kesamaan angka dari beberapa pasaran referensi.

Rule ini menggunakan penyamaan digit antar pasaran sebagai dasar analisis.


---

# Target

Target:

Toto Macau 4D


Prediksi dibuat berdasarkan pasaran referensi yang telah ditentukan.


---

# STEP 1 - Sumber Data

Gunakan 5 pasaran referensi:


1. Huahin 0100

2. Bangkok 0130

3. Kentucky Mid

4. New York Mid

5. Florida Mid


Sumber:

- huahin_0100_pool.md
- bangkok_0130_pool.md
- kentuckymid_pool.md
- newyorkmid_pool.md
- floridamid_pool.md


---

# STEP 2 - Ambil Result Terbaru

Dari setiap pasaran:

Ambil hanya result terbaru 4 digit.


Contoh:


Huahin:

0008


Bangkok:

1541


Kentucky:

3922


New York:

6145


Florida:

4934


---

# STEP 3 - Pecah Digit

Setiap result diubah menjadi digit individu.


Contoh:


1541


Menjadi:


1

5

4

1


Lakukan untuk semua pasaran sumber.


---

# STEP 4 - Analisa Kesamaan Digit

Cari digit yang muncul pada beberapa pasaran.


Prioritas:


## Level 1

Digit yang muncul di semua 5 pasaran.


## Level 2

Jika tidak tersedia:

Cari digit yang muncul di 4 dari 5 pasaran.


## Level 3

Jika masih tidak tersedia:

Cari digit yang muncul di 3 dari 5 pasaran.


## Level 4

Jika tidak ada pola:

Gunakan digit dengan frekuensi kemunculan tertinggi.


---

# STEP 5 - Perhitungan Frekuensi

Hitung jumlah kemunculan setiap digit dari seluruh sumber.


Contoh:


Digit:

4 = 5 kali

1 = 4 kali

9 = 3 kali

5 = 2 kali


Urutkan dari frekuensi terbesar.


---

# STEP 6 - Membuat Kandidat Utama

Ambil digit dengan hubungan paling kuat.


Prioritas:


1. Muncul di banyak pasaran.

2. Frekuensi tertinggi.

3. Konsisten pada result terbaru.


Jangan langsung membatasi sebelum proses ranking selesai.


---

# STEP 7 - Kandidat Lebih Dari 5 Digit

Jika hasil analisa menghasilkan lebih dari 5 digit:


Lakukan filter:


1. Prioritaskan digit dengan frekuensi tertinggi.

2. Buang digit dengan kemunculan paling rendah.

3. Sisakan:


5 digit utama


+

1 digit cadangan


---

# STEP 8 - Digit Cadangan


Cadangan adalah:

Digit yang masih memiliki hubungan statistik,
tetapi berada setelah kandidat utama.


Prioritas cadangan:


1. Muncul pada beberapa pasaran.

2. Frekuensi mendekati kandidat utama.

3. Tidak termasuk digit terlemah.


---

# STEP 9 - Output

AI harus memberikan:


## Analisa Toto Macau


Sumber:

- Huahin
- Bangkok
- Kentucky
- New York
- Florida


## Hasil Frekuensi Digit


Digit | Jumlah


## Kandidat Utama


5 Digit:


X X X X X


## Cadangan


X


## Penjelasan

Jelaskan:

- digit yang dipilih
- jumlah kemunculan
- pasaran sumber
- alasan digit masuk kandidat


---

# Aturan Wajib AI


Selalu:


1. Ambil 5 sumber.
2. Ambil result terbaru.
3. Pecah digit.
4. Cari kesamaan.
5. Hitung frekuensi.
6. Ranking digit.
7. Ambil 5 utama + 1 cadangan.


Jangan:


- memakai data lama sebelum result terbaru
- memilih digit tanpa sumber
- mengabaikan frekuensi
- langsung membuat angka 4D tanpa proses analisa


---

# Status

Rule aktif:

Toto Macau Prediction v1
