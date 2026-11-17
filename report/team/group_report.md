# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: motminh (nhóm 1 người: tôi, Vũ Đình Huy, 2A202603985)
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): f8ba782

## 2. Mục tiêu và cách tiếp cận

Tôi hiểu bài toán là xử lý claim hoàn phí của LogiX-VN bằng bốn kiến trúc, rồi chọn kiến trúc ít tự chủ nhất mà vẫn đạt. Ranh giới chính: số tiền, approval và chống ghi trùng do code (`compute_compensation`, `durability.issue_refund`) quyết; model chỉ soạn chữ. Vì làm một mình nên tôi làm tuần tự: cài môi trường và đọc contract, viết helper chung `early()` / `settle()` (đặt trong `workflow.py`), rồi workflow → single → orchestrator, sau đó thêm test, chạy crash suite, benchmark và viết báo cáo. Swarm có sẵn nên tôi dùng để đối chứng.

## 3. Giải pháp

Phần dùng chung: `src/lab8/shapes/workflow.py` có `early()` (needs_info, escalated, failed; không ghi ledger) và `settle()` (quote = 0 → `denied`; quote > 0 → `issue_refund` với quote đầy đủ, map kết quả host sang `resolved` / `denied` / `failed`). `InjectedCrash` được ghi trace rồi ném lại, không bắt.

- **workflow:** các bước cố định: `get_claim_view` → `lookup_order` → `compute_compensation` từ order row (bỏ qua số ngày trễ trong ticket) → `settle`. MockLLM chỉ soạn câu trả lời.
- **single:** `run_react` tối đa 8 bước; `decide` chỉ chọn tool đọc (get_claim_view, lookup_order, compute_compensation). Sau vòng lặp code của shape gọi `issue_refund`. Trace ghi tên tool và status từng bước, không ghi observation thô.
- **orchestrator:** orchestrator dựng handoff bằng `make_handoff` (allowlist, chỉ tool đọc, `facts` rỗng), `run_readonly_investigators` chạy tool, orchestrator quote và là bên duy nhất gọi `issue_refund`. Trace ghi handoff đã sanitize, không ghi parent context.

Trace chỉ ghi các view đã allowlist (claim: found và có order_id hay không; order: các field của `lookup_order`), quote, kết quả host và decision. Không ghi ticket, principal_id, parent_secret, SĐT, địa chỉ.

## 4. Kết quả

Nguồn: `src/reports/benchmark.json` (4 shape × 14 claim × 5 seed, MockLLM, giá mô phỏng).

| Shape | Pass rate | pass^5 | Seed min–max | Variance | Cost/success (VND) | Steps mean / p95 |
| --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 28.79 | 4.43 / 5.0 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 30.45 | 8.14 / 9.0 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 57.58 | 5.36 / 6.0 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3.0 |

Crash safety: 20/20 (`src/reports/crash.json`). Swarm fail một trial duy nhất, C-002 seed 55 (tin delay trong ticket). Tôi chưa có `student_drop/` nên chưa tự kiểm trên hidden.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

- Tôi chạy trên Python 3.14, ngoài khoảng 3.11–3.13 đề khuyến nghị; smoke, pytest và benchmark vẫn chạy bình thường.
- `run_react` chỉ truyền lại kết quả tool cuối, nên tôi cho `single` giữ state (claim, order) trong closure của `decide`.
- Để T12 thấy crash thật, tôi truyền `crash_at` xuống `issue_refund` và `InjectedCrash` không bị bắt (tôi chỉ ghi trace rồi ném lại).

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/2A202603985_VuDinhHuy.md`. Tôi (Vũ Đình Huy) làm toàn bộ.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Pass 1.000 chỉ trên 14 claim public; hidden set có thể có tình huống mới. Tôi sẽ đổi quyết định chọn workflow nếu hidden claim cần đọc hiểu ngôn ngữ tự nhiên mà luật cố định không bao quát, hoặc nếu giá model/tool đổi làm chênh lệch cost không còn đáng kể. Hướng cải thiện của tôi: thêm test cho các nhánh approval và đơn đã hoàn đủ ở cả 3 shape.

## 8. Tài liệu tham khảo

- Đề bài và tài liệu lab: `README.md`, `docs/business_rules.md`, `docs/contracts.md`, `docs/metrics.md`.
- EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* (thư viện tham khảo của lớp, câu R4; tôi chưa có URL gốc).
