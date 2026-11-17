# Team

## Thông tin nhóm

- Tên nhóm: motminh
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-motminh-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/VNno1TH/K5-L3B-DAY08-motminh-FromWorkflowsToAgents, nhánh `main`, commit chốt: d1a917c

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Vũ Đình Huy | 2A202603985 | huyvudinh1608@gmail.com | VNno1TH | Nhóm 1 người: integration, workflow, single, orchestrator, ledger/crash, eval/report |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Vũ Đình Huy | Toàn bộ | d1a917c | `src/tests/test_team_shapes.py` (24 test mới) |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603985_VuDinhHuy

### Phần việc phụ trách

- Toàn bộ đồ án (nhóm 1 người): triển khai 3 shape (workflow, single, orchestrator), helper dùng chung `early()` / `settle()` (trong `workflow.py`), kiểm thử đơn vị & hệ thống, crash safety test, benchmark và báo cáo kỹ thuật.

### Đóng góp cụ thể

- Cài đặt đầy đủ 3 kiến trúc theo đúng contracts và business rules.
- Tách `early()` / `settle()` (trong `workflow.py`) tối ưu xử lý quote, idempotency và trace.
- Viết bộ kiểm thử mở rộng `src/tests/test_team_shapes.py` gồm 24 test kiểm tra ranh giới bảo mật, step cap, và handling bất thường.
- Thực hiện đo benchmark 4 shape trên 5 seed và kiểm thử độ bền bỉ crash 20/20.

### Bằng chứng

- Chi tiết xem file cá nhân: [report/team/2A202603985_VuDinhHuy.md](report/team/2A202603985_VuDinhHuy.md).
