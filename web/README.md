# Job Radar - web

Static prototype: tong hop tin tuyen dung Viet Nam, so sanh luong gross va net truoc khi ung tuyen.

## Serve

- python3 -m http.server 8080 --directory web
- Mo http://localhost:8080/ trong trinh duyet.

## API va demo data

- API mac dinh http://localhost:8000, doi qua query api hoac window.JOB_RADAR_API_BASE. Endpoints: /api/jobs, /api/jobs/id, /api/filters, /api/redirect/id.
- Khi API khong toi duoc, trang dung assets/sample-jobs.json (14 tin mau) va hien ghi chu demo. Tim kiem va bo loc chay o ca hai che do.

## Pages

- index.html: hero, tim kiem, bo loc thanh pho, nganh, lam viec tu xa, luong, luoi tin dang.
- job.html: chi tiet tin, doc id tu query string, luong gross kem uoc tinh net, nut ve trang goc qua API redirect.
- tools.html: doi gross sang net, tro cap that nghiep, bao hiem xa hoi.
- pricing.html: goi token.
- companies.html: danh ba cong ty tu du lieu mau.

## Salary rates

- Muc theo brief w-a-4, giong worker 3: giam tru ban than 11 trieu, phu thuoc 4,4 trieu; thue 7 bac luy tien; BHXH 8%, BHYT 1,5%, BHTN 1%.
- Tran BHXH/BHYT 46,8 trieu (20 x luong co so 2,34 trieu). Tran BHTN 99,2 trieu (20 x luong toi thieu vung I 4,96 trieu).
- Tro cap that nghiep: 60% luong binh quan 6 thang gan nhat, toi da 5 x luong toi thieu vung I (24,8 trieu). Huong 3 thang neu dong 12-35 thang, +1 thang cho moi 12 thang them sau 36 thang, toi da 12 thang.
- Trang tools ghi ngay ap dung muc: 2026-11-14.
- Lich su: ban nhap truoc dung muc luat 2026 (giam tru 15,5 trieu, thue 5 bac) da tra ve muc brief de khop voi salary service.

## Verify

- node --check assets/salary.js
- node --check assets/app.js
- node /tmp/check-salary.js va node /tmp/check-salary2.js, doi chieu: net 30 trieu 1 phu thuoc 25.882.500, net 30 trieu 0 phu thuoc 25.222.500, net 100 trieu 75.165.300, tro cap 24 thang dong 3 thang x 12 trieu.
