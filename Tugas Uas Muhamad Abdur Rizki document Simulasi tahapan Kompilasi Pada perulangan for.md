# Dokumentasi Tugas uas teknik Kompilasi: Simulasi Tahapan Kompilasi pada Perulangan (For Loop)

## 1. Kenapa Pilih For Loop

Dari beberapa pilihan konstruksi yang ditawarkan di soal (looping, kondisi, error handler, deklarasi fungsi), saya memilih **perulangan `for`**. Alasannya sederhana: struktur `for` punya empat bagian yang berbeda perannya (inisialisasi, kondisi, body, dan update), jadi enak dipakai buat nunjukkin bagaimana tiap tahap kompilasi memproses bagian-bagian itu dengan cara yang berbeda-beda. Kalau pilih `if-else` rasanya terlalu mirip contoh yang sudah dikasih di soal.

## 2. Pola / Grammar (BNF)

Aturan sintaksisnya saya tulis begini:

```
<for_stmt>   ::= "for" "(" <assign> ";" <condition> ";" <assign> ")" "{" <body> "}"
<assign>     ::= <identifier> "=" <expr>
<expr>       ::= <operand> | <operand> <operator> <operand>
<condition>  ::= <operand> <rel_op> <operand>
<operand>    ::= <identifier> | <number>
<body>       ::= <assign> { <assign> }
<operator>   ::= "+" | "-" | "*" | "/"
<rel_op>     ::= "<" | ">" | "<=" | ">=" | "==" | "!="
```

Kalimat sumber yang saya pakai sebagai contoh dan sudah cocok sama grammar di atas: `for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }`. Ini kira-kira representasi dari perulangan yang menjumlahkan angka 0 sampai 4 ke variabel `sum`.

## 3. Cara Kerja Programnya

Programnya saya tulis pakai Python biasa, tanpa library tambahan, dan saya bagi jadi empat bagian mengikuti urutan tahap kompilasi yang diminta.

### 3.1 Tahap Leksikal

Bagian ini tugasnya cuma satu: mengubah teks source code jadi kumpulan token. Saya pakai `re` dengan satu regex besar yang isinya gabungan semua pola token (angka, identifier, operator, tanda kurung, dst), jadi begitu ketemu sebuah karakter atau kata, langsung ketahuan itu masuk kategori token apa. Spasi dan baris baru diabaikan saja karena tidak berarti apa-apa secara sintaksis.

Kalau source-nya `for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }`, hasil tokenisasinya jadi deretan token mulai dari `<KEYWORD:for>`, `<LPAREN:(>`, `<IDENT:i>`, `<ASSIGN:=>`, `<NUMBER:0>`, dan seterusnya sampai `<RBRACE:}>` di akhir.

### 3.2 Tahap Sintaksis (bikin AST)

Di sinilah bedanya sama contoh di soal — kalau di contoh AST-nya cuma hasil potong-potong string, di punya saya beneran dibentuk jadi objek: ada kelas `ForNode` (mewakili keseluruhan struktur for), `AssignNode` (untuk statement `x = ...`), dan `BinOpNode` (untuk ekspresi kayak `i + 1` atau `i < 5`).

Parsernya jenis *recursive descent*, jadi urutan pembacaannya persis ngikutin grammar: baca `for`, baca kurung buka, parse bagian init, titik koma, parse condition, titik koma lagi, parse update, kurung tutup, lalu kurung kurawal buka baru parse isi body. Kalau di tengah jalan ada token yang tidak sesuai yang diharapkan (misal lupa titik koma), parser langsung berhenti dan melempar error — jadi validasi struktur otomatis kejadian selama proses parsing, bukan dicek belakangan.

Hasil AST-nya kira-kira begini bentuknya:

```
ForNode(
  init=Assign(i = 0),
  condition=(i < 5),
  update=Assign(i = (i + 1)),
  body=[Assign(sum = (sum + i))]
)
```

### 3.3 Tahap Semantik

Nah, tahap ini yang menurut saya paling penting buat ditunjukkan bukan cuma formalitas. Fungsi `semantic_analysis()` menerima AST plus sebuah *symbol table* (semacam daftar variabel yang sudah "dikenal" beserta tipenya). Variabel `i` dari bagian init otomatis dianggap baru dideklarasikan. Setelah itu, setiap variabel yang dipakai di condition, update, maupun body dicek satu-satu: kalau bukan angka dan belum ada di symbol table, program langsung berhenti dengan error.

Supaya kelihatan pengecekan ini beneran jalan (bukan cuma kode yang ditulis tapi tidak pernah ketemu kasusnya), saya sengaja tambahkan satu percobaan yang memang dibuat gagal: `for ( j = 0 ; j < 3 ; j = j + 1 ) { total = total + j }`, di mana variabel `total` belum pernah dideklarasikan sebelumnya. Waktu dijalankan, hasilnya persis seperti yang diharapkan — muncul pesan `Variabel 'total' belum dideklarasikan.` dan proses berhenti sebelum sempat lanjut ke tahap pembuatan kode.

### 3.4 Tahap Generasi Kode (Three-Address Code)

Bagian terakhir ini yang mengubah AST jadi TAC. Pola yang saya pakai untuk loop `for` adalah pola standar yang biasa dipakai di buku kompilator:

```
<init>
L1:
ifFalse <condition> goto L2
<body>
<update>
goto L1
L2:
```

Setiap kali ketemu ekspresi yang punya operator (misalnya `sum + i` atau `i + 1`), saya buat variabel sementara (`t1`, `t2`, dan seterusnya) buat nampung hasilnya, sesuai aturan TAC bahwa satu baris instruksi maksimal cuma boleh ada satu operator.

## 4. Hasil Akhirnya

Untuk source `for ( i = 0 ; i < 5 ; i = i + 1 ) { sum = sum + i }`, kode TAC yang keluar dari program adalah:

```
i = 0
L1:
ifFalse i < 5 goto L2
t1 = sum + i
sum = t1
t2 = i + 1
i = t2
goto L1
L2:
```

Kalau dicek satu-satu, ini sudah masuk akal: variabel `i` diinisialisasi dulu, lalu tiap kali sebelum masuk body, kondisi `i < 5` dicek — kalau salah, langsung lompat ke `L2` alias keluar loop. Kalau kondisinya benar, body dijalankan (nambah `i` ke `sum` lewat variabel sementara `t1`), baru `i` di-update lewat `t2`, dan proses lompat balik ke `L1` buat ngecek kondisi lagi. Persis kelakuan loop `for` yang aslinya.

## 5. Kesimpulan

Dari tugas ini saya jadi lebih paham kenapa proses kompilasi itu dipecah jadi beberapa tahap terpisah: leksikal buat mengenali "kata-kata" dasar dari kode, sintaksis buat memahami strukturnya, semantik buat mastiin kodenya masuk akal secara logika (bukan cuma benar tata bahasanya), dan baru di tahap generasi kode hasil akhirnya diterjemahkan ke bentuk yang lebih sederhana (TAC) yang nantinya bisa dipakai lagi buat tahap optimasi atau diubah jadi kode mesin.