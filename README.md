# Othello AI — Adversarial Search

Implementasi permainan Othello (Reversi) untuk membandingkan **Alpha-Beta
Pruning** dan **Monte Carlo Tree Search (MCTS)**. Proyek menyediakan permainan
interaktif melalui Streamlit, pengujian aturan dan algoritma, serta eksperimen
waktu, memori, dan kemampuan bermain.

## Fitur

- Papan Othello 8×8 dengan penanda langkah legal, skor, pass, dan pemenang.
- Mode Human vs Human, Human vs AI, dan AI vs AI.
- Konfigurasi algoritma, depth Alpha-Beta, iterations MCTS, dan seed.
- Halaman eksperimen dengan tabel, grafik, statistik pencarian, dan unduhan CSV.
- Benchmark serial dan tournament dengan pertukaran warna melalui GUI atau CLI.
- Skenario opening, midgame, dan endgame yang dibentuk dari langkah legal.

## Instalasi dan menjalankan aplikasi

Gunakan **Python 3.11 atau lebih baru**. Jalankan perintah dari root proyek.
Contoh berikut menggunakan PowerShell di Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Jika aktivasi virtual environment tidak tersedia, gunakan interpreter-nya
secara langsung, misalnya:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Pada macOS/Linux, aktivasi environment menggunakan `source .venv/bin/activate`.

## Struktur proyek

```text
.
├── app.py                       # Navigasi dan antarmuka permainan
├── game/
│   ├── board.py                 # Representasi dan pembuatan papan
│   └── engine.py                # Legalitas, flip, pass, skor, terminal
├── algorithms/
│   ├── alphabeta.py             # Minimax dengan Alpha-Beta Pruning
│   ├── evaluation.py            # Heuristik posisi dan nilai terminal
│   └── mcts.py                  # UCT, rollout, dan backpropagation
├── experiments/
│   ├── common.py                # Pemanggilan AI melalui API bersama
│   ├── benchmark.py             # Pengukuran waktu/memori dan ekspor CSV
│   ├── tournament.py            # Pertandingan otomatis dan ekspor CSV
│   ├── scenarios.py             # Posisi uji dengan riwayat langkah
│   └── ui.py                    # Halaman eksperimen Streamlit
├── results/                     # CSV dan metadata eksperimen
├── tests/                       # Unit test dan pengujian integrasi/UI
├── requirements.txt
└── LAPORAN.md                   # Teori, implementasi, hasil, dan analisis
```

## Memainkan Othello

Di sidebar, pilih **Permainan**, lalu Human vs Human, Human vs AI, atau AI vs AI.
Atur algoritma dan parameter
masing-masing warna, lalu klik **New Game**. Manusia menekan kotak bertanda
hijau. Klik **Jalankan giliran AI** untuk setiap giliran AI, termasuk AI vs AI.
Pencarian hanya dijalankan oleh tombol tersebut sehingga rerun Streamlit tidak
mengulang pencarian. Pass otomatis ditangani melalui API engine. **Reset**
mengulang papan dengan konfigurasi aktif; **New Game** menerapkan pengaturan baru.

## Eksperimen

### Melalui aplikasi

Di sidebar aplikasi, pilih **Eksperimen**, lalu buka tab **Benchmark** atau
**Tournament**. Atur konfigurasi dan tekan tombol jalankan. Benchmark dapat
membandingkan kedua algoritma pada skenario yang sama; hasilnya mencakup
tabel, grafik waktu/memori, statistik pencarian, dan unduhan CSV. Tournament
menampilkan jumlah menang/seri, skor, durasi, serta unduhan CSV.

Hasil dan konfigurasi terakhir disimpan selama sesi Streamlit. Pindah halaman,
mengubah input, atau mengunduh CSV tidak menjalankan eksperimen ulang. Papan
permainan tetap tersimpan saat berpindah halaman. Hasil dari UI tidak menimpa
file di `results/`; gunakan tombol unduh untuk menyimpan CSV.

### Melalui terminal

Contoh benchmark kedua algoritma pada skenario midgame yang sama:

```powershell
python -m experiments.benchmark alphabeta --parameter 4 --scenario midgame --repetitions 30 --output results/benchmark-alphabeta-midgame.csv
python -m experiments.benchmark mcts --parameter 500 --scenario midgame --repetitions 30 --seed 42 --output results/benchmark-mcts-midgame.csv
```

Parameter `--parameter` berarti depth untuk `alphabeta` dan iterations untuk
`mcts`. Ganti `--scenario` dengan `opening`, `midgame`, atau `endgame`.

Contoh tournament dua pasangan, yaitu empat pertandingan:

```powershell
python -m experiments.tournament --pairs 2 --depth 4 --iterations 500 --seed 42 --output results/tournament-baru.csv
```

Untuk melihat seluruh opsi:

```powershell
python -m experiments.benchmark --help
python -m experiments.tournament --help
```

### Metode pengukuran dan seed

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

### Hasil dan dokumentasi

- `results/benchmark.csv`: dataset benchmark yang dipakai dalam laporan.
- `results/tournament.csv`: hasil pertandingan yang dipakai dalam laporan.
- `results/experiment_metadata.json`: catatan eksekusi ulang dataset laporan,
  meliputi hardware, versi library, konfigurasi, waktu, dan hash kode/CSV.
- [LAPORAN.md](LAPORAN.md): pembahasan teori, implementasi, hasil, dan batasan
  kesimpulan berdasarkan data yang tersedia.

Metadata tersebut merupakan catatan eksekusi tertentu, bukan file yang otomatis
diperbarui oleh setiap pemanggilan CLI atau GUI. Jika dataset diganti, catat
kembali lingkungan dan konfigurasi agar metadata tetap sesuai dengan hasil.

## Algoritma dan API

Alpha-Beta memakai Minimax dengan batas depth, heuristik nonterminal
`H = 25C + 5M + D`, serta evaluasi terminal terpisah. `C` adalah selisih sudut,
`M` selisih mobilitas, dan `D` selisih bidak dari perspektif pemain pencari.
Pass tidak mengurangi sisa depth penempatan.

MCTS memakai UCT dengan konstanta `sqrt(2)`, rollout acak uniform hingga
terminal, dan reward menang/seri/kalah sebesar `1.0/0.5/0.0`. Seed menggunakan
generator lokal agar hasil dapat diulang tanpa mengubah global random state.

API pencarian mengembalikan `(move, stats)`:

```python
from game.board import create_board
from algorithms.alphabeta import get_best_move as alphabeta
from algorithms.mcts import get_best_move as mcts

board = create_board()
move_ab, stats_ab = alphabeta(board, player=1, depth=4)
move_mcts, stats_mcts = mcts(board, player=1, iterations=500, seed=42)
```

Papan untuk API fungsional berupa `list[list[int]]`: kosong `0`, hitam `1`,
putih `-1`. Koordinat langkah berbentuk `(row, col)` dengan indeks 0–7;
`None` menandakan tidak ada langkah legal. Fungsi pencarian dan API fungsional
engine mempertahankan papan input. Kelas `Board` dan `GameEngine` juga tersedia
untuk pengelolaan permainan melalui instance.

Statistik bersama adalah `nodes_visited`, `nodes_expanded`, dan
`max_depth_reached`. Alpha-Beta menambahkan `pruned_branches`; MCTS menambahkan
`simulations` dan `tree_size`.

## Pengujian

```powershell
python -m pytest
```

Tes mencakup aturan Othello, salinan papan, langkah ilegal, pass dan terminal,
evaluasi, determinisme AI, UCT, benchmark, CSV, replay skenario, pertandingan
penuh, serta UI menggunakan fasilitas pengujian Streamlit. Tes layar
dependensi belum tersedia dilewati ketika seluruh modul sudah terintegrasi.

## Batasan perbandingan

Depth dan iterations bukan anggaran komputasi yang setara. Bandingkan waktu,
memori, dan hasil pertandingan pada konfigurasi yang dicatat; jangan menyamakan
jumlah node kedua algoritma sebagai biaya kerja yang identik. Hasil pada satu
posisi atau sedikit pertandingan belum mewakili seluruh kemungkinan permainan.
