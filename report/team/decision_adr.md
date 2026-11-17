# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: f8ba782
- Run id dẫn chứng: R-workflow-C-001-s11 (toàn bộ 70 trial trong src/reports/benchmark.json)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000
- Cost per success (mô phỏng, VND): 28.79
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 (trace test và test host đều xanh)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Trên cùng 14 claim public × 5 seed (70 trial mỗi shape), cùng bảng giá mô phỏng và MockLLM, workflow, single và orchestrator đều pass 1.000 và pass^5 1.000 với variance 0. Vì pass ngang nhau, tôi chọn workflow vì nó thắng ở chi phí: 28.79 VND/success, so với single 30.45 (8.14 bước trung bình), orchestrator 57.58 và swarm 49.57. Task này là quy trình tuần tự có luật rõ (thiếu order → hỏi thêm, không thấy đơn → escalate, quote từ order row, host ghi refund), nên không có chỗ nào cần model tự quyết định. Tôi chọn kiến trúc ít tự chủ nhất mà vẫn làm được việc.

## Có đáng đổi lấy multi-agent không

Với tôi là không. Multi-agent (orchestrator, swarm) không cho pass cao hơn workflow mà cost gấp 1.7–2 lần; swarm còn thua ở C-002 seed 55 vì tin số ngày trễ trong ticket (pass^5 = 0.929, variance 0.0008). Tôi sẽ đổi quyết định nếu hidden set có claim mà luật cố định không bao quát (ví dụ ticket mơ hồ cần đọc hiểu ngôn ngữ tự nhiên để phân loại), khiến pass rate workflow rơi dưới 0.75 trong khi shape có model vẫn giữ được, hoặc nếu giá model/tool thay đổi làm chênh lệch cost không còn đáng kể.

## Trace và bằng chứng

Trace của tôi (lab8.trace.Trace, ghi vào traces/<run_id>.json) có các event: `claim` (found, có order_id hay không), `order` (view đã allowlist qua lookup_order), `handoff` (đã qua make_handoff, chỉ ở orchestrator), `investigator`, `step` (chỉ ở single), `quote`, `host` (ok, reason), `crash`, `decision`. Tôi cố ý không ghi: ticket, principal_id, parent_secret, header, SĐT, địa chỉ, ghi chú nội bộ, tên hàng, vì claim row và order row thô chứa các field đó. Mọi trace đều nằm cùng thư mục traces/ nên scanner quét được; ngoài ra tôi viết test_team_shapes.py để kiểm tra không có `CANARY_SECRET_` trong trace và RunResult của cả 3 shape trên toàn bộ claim public.

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Tôi không sửa JSON cho đủ 0.75. Pass 1.000 là trên 14 claim public; hidden set (40 claim × 5 seed) có thể có tình huống khác, nên kết quả public không đảm bảo điểm hidden.
