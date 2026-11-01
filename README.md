# Othello — bagian anggota 4

Implementasi UI Streamlit, benchmark serial, tournament seimbang, skenario yang
dapat direplay, dan pengujian integrasi. Python 3.11+; jalankan dari root proyek.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m pytest
```

## Ketergantungan integrasi

Saat implementasi ini dibuat, file `game/` dan `algorithms/` masih kosong.
Anggota 1–3 harus menyediakan API sesuai spesifikasi: `create_board`, fungsi
engine, dan `get_best_move` kedua algoritma. Implementasi ini tidak mengganti
pekerjaan anggota lain. UI menampilkan pesan apabila dependensi belum siap;
pengujian engine/AI nyata dilewati dengan alasan yang jelas sampai API tersedia.
Pengujian infrastruktur dengan test doubles tetap dijalankan.

Validasi saat penyerahan bagian anggota 4: **13 passed, 2 skipped** pada
Python 3.13.5. Tes mencakup ketiga mode UI memakai engine/AI pengganti,
Reset, tidak mengulang pencarian saat rerun, benchmark, CSV, seed, dan
penukaran warna. Dua tes yang dilewati adalah replay skenario dengan AI
asli dan pertandingan penuh dengan engine/AI asli; keduanya aktif otomatis
setelah API anggota 1–3 tersedia. Hasil ini belum membuktikan permainan
Othello penuh dengan implementasi asli.

## Pemakaian UI

Pilih Human vs Human, Human vs AI, atau AI vs AI; atur algoritma dan parameter
masing-masing warna, lalu klik **New Game**. Manusia menekan kotak bertanda
hijau. Klik **Jalankan giliran AI** untuk setiap giliran AI, termasuk AI vs AI.
Pencarian hanya dijalankan oleh tombol tersebut sehingga rerun Streamlit tidak
mengulang pencarian. Pass otomatis ditangani melalui API engine. **Reset**
mengulang papan dengan konfigurasi aktif; **New Game** menerapkan pengaturan baru.

## Eksperimen

Di sidebar aplikasi, pilih **Eksperimen**, lalu buka tab **Benchmark** atau
**Tournament**. Atur konfigurasi dan tekan tombol jalankan. Benchmark dapat
membandingkan kedua algoritma pada skenario yang sama; hasilnya mencakup
tabel, grafik waktu/memori, statistik pencarian, dan unduhan CSV. Tournament
menampilkan jumlah menang/seri, skor, durasi, serta unduhan CSV.

Hasil dan konfigurasi terakhir disimpan selama sesi Streamlit. Pindah halaman,
mengubah input, atau mengunduh CSV tidak menjalankan eksperimen ulang. Papan
permainan tetap tersimpan saat berpindah halaman. Hasil dari UI tidak menimpa
file di `results/`; gunakan tombol unduh untuk menyimpan CSV. Eksperimen juga
tetap bisa dijalankan melalui terminal:

```powershell
python -m experiments.benchmark alphabeta --parameter 4 --scenario opening --repetitions 30 --output results/ab-opening.csv
python -m experiments.benchmark mcts --parameter 500 --scenario midgame --repetitions 30 --seed 42 --output results/mcts-midgame.csv
python -m experiments.tournament --pairs 2 --depth 4 --iterations 500 --seed 42 --output results/tournament.csv
```

Benchmark mendukung opening, midgame, endgame; setiap pengulangan memakai
salinan papan identik dan seed MCTS `seed + repetition`. Waktu memakai
`perf_counter_ns`; peak memory memakai sesi `tracemalloc` baru setiap panggilan.
Angka tersebut adalah alokasi Python terlacak, bukan resident memory proses.
Tracing menambah overhead waktu; bandingkan pada perangkat, versi Python,
dan metode pengukuran yang sama. Nodes visited kedua AI tidak sepenuhnya setara.
CSV menyertakan statistik khusus algoritma dan parameter; nama output yang sama
akan ditimpa. Benchmark dijalankan serial, tanpa GUI.

Tournament memainkan dua pertandingan per pasangan, menukar warna. Seed dasar
kedua game dalam pasangan sama: `seed + pair_index * 1000`. Setiap keputusan
MCTS memakai `game_seed + mcts_decision_index` (indeks mulai nol). CSV mencatat
seed, konfigurasi, warna, pemenang, skor, jumlah penempatan bidak (pass tidak
dihitung), dan durasi. Ulangi konfigurasi tetap sebelum eksperimen tambahan.

`get_scenarios()` membentuk posisi dari langkah legal terkecil secara
leksikografis: opening 0, midgame 24, endgame 50 penempatan. Setiap hasil
berisi `board`, `player`, dan `moves`, yaitu daftar `(player, (row, col))`.
Giliran yang sama dua kali menandakan lawan pass. Tidak ada posisi acak.
