# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R4 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* (theo thư viện tham khảo của lớp, slide 68–69). Tôi chưa có URL gốc và chưa đọc bản đầy đủ. Loại bằng chứng: paper benchmark |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | So sánh hiệu quả giữa các hệ multi-agent dễ bị nhiễu bởi prompt, tool và seed; muốn kết luận về topology phải cố định các biến này. (Tôi chỉ dựa vào tiêu đề và mô tả của lớp, chưa đọc bản đầy đủ.) |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận của paper không áp dụng trực tiếp cho lab: lab dùng MockLLM, 14 claim public, bảng giá mô phỏng. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Đổi workflow → orchestrator (thêm investigator) không đổi pass rate vì quote do code tính, nhưng cost/success tăng khoảng gấp 2 (nhiều tool call và model call hơn). |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, cùng tool đọc, seed 11,22,33,44,55, 14 claim public, pricing.yaml, cùng grader, SQLite mới cho mỗi trial. Biến thay đổi duy nhất: topology (workflow, single, orchestrator, swarm). |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: tin số ngày trễ trong ticket thay vì order row (swarm, seed chia hết cho 5). Đo bằng pass rate, pass^5, variance và cost/success. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: src/reports/benchmark.json (ví dụ R-workflow-C-001-s11, R-swarm-C-002-s55)
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Đúng. Tôi thấy pass rate của workflow, single, orchestrator đều 1.000; cost/success lần lượt 28.79, 30.45, 57.58 (orchestrator gấp 2.0 lần workflow). Chỉ swarm lệch: pass 0.986, pass^5 0.929, fail duy nhất là C-002 seed 55 (`resolved != denied`), đúng lỗi dự kiến. Do seed, corpus, giá và tool được giữ cố định nên chênh lệch quy cho topology; tôi chưa tách riêng được ảnh hưởng của prompt vì MockLLM không dùng prompt thật.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
