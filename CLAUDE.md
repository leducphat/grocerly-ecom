# CLAUDE.md

Chỉ dẫn cho [Claude Code](https://claude.com/claude-code) khi làm việc trong repo này.

Toàn bộ nội dung dùng chung cho mọi AI agent được đặt ở `AGENTS.md` và import bên dưới,
để tránh tình trạng nhiều file chỉ dẫn lệch nhau theo thời gian.

@AGENTS.md

## Riêng cho Claude Code

**Môi trường**: Windows 11. Shell mặc định là PowerShell; Bash tool dùng Git Bash
(cú pháp POSIX). Đường dẫn dự án dùng dấu `\` khi thao tác qua PowerShell.

**Bộ quy tắc ECC** (`.claude/rules/ecc/`, `.claude/skills/`, `.claude/agents/`) chỉ tồn
tại ở máy local và **đã được gitignore** — xem ADR-0004 trong [docs/DECISIONS.md](docs/DECISIONS.md).
Không giả định người khác clone repo về sẽ có chúng.

**Ưu tiên công cụ**: Grep/Glob thay cho `Select-String`/`Get-ChildItem -Recurse`;
Read thay cho `Get-Content`; Edit/Write thay cho `Set-Content`.

**Chạy lệnh Django**: nhớ `cd grocerly` trước. Thư mục làm việc của Bash tool giữ nguyên
giữa các lần gọi, nhưng nên dùng đường dẫn tuyệt đối cho chắc.

**Khi được hỏi về trạng thái một chức năng**: luôn `grep` kiểm chứng trong code trước khi
trả lời, kể cả khi bản báo cáo mô tả rõ ràng rằng chức năng đó tồn tại. Danh sách các
chức năng "có trong báo cáo, không có trong code" ở [docs/SPEC-GAPS.md](docs/SPEC-GAPS.md).
