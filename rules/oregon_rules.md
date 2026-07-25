# Oregon Cross Analysis Rule v2

## Daftar Pasaran Oregon

Sistem hanya memiliki 4 target Oregon:

- Oregon 03
- Oregon 06
- Oregon 09
- Oregon 12


## Target Selection

User memilih salah satu target:

Oregon Target


## Source Selection

Gunakan tiga Oregon lainnya sebagai sumber.

Formula:

Source = Semua Oregon - Oregon Target


Contoh:

Target:
Oregon 03

Source:
Oregon 06
Oregon 09
Oregon 12


Target:
Oregon 06

Source:
Oregon 03
Oregon 09
Oregon 12


Target:
Oregon 09

Source:
Oregon 03
Oregon 06
Oregon 12


Target:
Oregon 12

Source:
Oregon 03
Oregon 06
Oregon 09


---

## Analisa Digit

Ambil result dari semua source.

Pecah setiap result menjadi digit.

Hitung jumlah kemunculan setiap digit.


---

## Kandidat Digit

Urutkan digit berdasarkan frekuensi terbesar.


Jika hasil lebih dari 6 digit:

Lakukan eliminasi.


---

## Eliminasi

Gunakan history Oregon target sendiri.

Ambil history 7 hari terakhir.

Jika suatu digit:

- terlalu sering muncul sebagai result target
- terlalu dominan pada history terbaru

maka turunkan prioritas atau eliminasi.


---

## Output Akhir

Hasil:

5 digit utama

+

1 digit cadangan


Cadangan:

Digit yang memiliki hubungan statistik dengan source,
tetapi frekuensinya lebih rendah dari kandidat utama.