# Orphan Market Slot Positions

File ini adalah referensi posisi slot orphan result di `data_harian/`.

## Format

Setiap file `data_harian/DD-MM-YYYY-Luna.md` punya struktur tetap:

```
<NAMED_MARKET> POOL
<result>
[PERIODE : N]
Play Now
```

Setelah beberapa `POOL` market tertentu, ada slot orphan result
(hasil tanpa nama market) dengan pola:

```
labelthumbnail
(blank)
<RESULT>
(blank)
Play Now
btn_live
```

Atau (untuk live draw popup):

```
thumbnail
<RESULT>
<WAKTU>
btn_live
```

## Slot Mapping (Berdasarkan Posisi)

Setelah KING KONG 4D POOL:
  orphan #0 → **HOKIdraw**
  orphan #1 → **huahin0100**

Setelah KENTUCKYEVE POOL:
  orphan #0 → **cambodialotto**

Setelah BULLSEYE POOL:
  orphan #0 → **poipet12**

Setelah OREGON12 POOL (tipe thumbnail):
  orphan #0 → **sydneylotto**

Setelah CHELSEA 15 POOL:
  orphan #0 → **poipet15**
  orphan #1 → **totomali1530**
  orphan #2 → **huahin1630**

Setelah CHELSEA 19 POOL:
  orphan #0 → **poipet19**

Setelah PCSO POOL:
  orphan #0 → **totomali2030**
  orphan #1 → **huahin2100**

Setelah BRUNEI 21 POOL:
  orphan #0 → **poipet22**
  orphan #1 → **hongkonglotto** (tipe thumbnail)
  orphan #2 → **totomali2330**

## Total

14 orphan markets.

## Aturan

- Mapping berdasarkan **posisi**, bukan nilai result.
- Urutan slot TIDAK BOLEH berubah.
- Kalau ada market baru, tambah entry di `config/orphan_markets.json`.
- Jangan ubah urutan yang sudah ada.
