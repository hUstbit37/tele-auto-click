# Hướng dẫn tạo script Telegram Daily Check-in tự động trên Windows 11

Tài liệu này hướng dẫn từ đầu đến cuối cách tạo một script Python dùng Telethon để tự động bấm nút **Daily Check-in** trong một bot/chat Telegram, sau đó cấu hình Windows Task Scheduler để chạy hằng ngày.

> Lưu ý: Chỉ nên dùng cho tài khoản cá nhân của bạn, chạy 1 lần/ngày. Không dùng để spam, farm nhiều tài khoản, vượt captcha hoặc bypass cơ chế chống bot.

---

## 1. Mục tiêu

Sau khi hoàn thành, máy Windows 11 sẽ có project dạng:

```text
D:\Tele-Daily-Checkin
├── .venv/
├── .env
├── telegram_session.session
├── list_chats.py
├── daily_checkin.py
├── run_checkin.bat
└── checkin.log
```

Script sẽ:

1. Đăng nhập Telegram bằng tài khoản của bạn.
2. Tìm đúng bot/chat Telegram.
3. Tìm nút `Daily Check-in`.
4. Click nút đó.
5. Ghi log vào file `checkin.log`.
6. Được Windows tự chạy mỗi ngày qua Task Scheduler.

---

## 2. Chuẩn bị

Cần có:

- Windows 11
- VS Code
- Python đã cài trên máy
- Tài khoản Telegram
- `api_id` và `api_hash` từ Telegram Developer

Kiểm tra Python:

```powershell
python --version
```

Nếu có kết quả kiểu:

```text
Python 3.x.x
```

là được.

---

## 3. Tạo project trong VS Code

Tạo thư mục:

```text
D:\Tele-Daily-Checkin
```

Mở VS Code, chọn:

```text
File > Open Folder > D:\Tele-Daily-Checkin
```

Mở terminal trong VS Code:

```text
Terminal > New Terminal
```

---

## 4. Tạo môi trường ảo Python

Trong terminal VS Code, chạy:

```powershell
python -m venv .venv
```

Kích hoạt môi trường ảo:

```powershell
.venv\Scripts\activate
```

Nếu thành công, terminal sẽ có dạng:

```text
(.venv) PS D:\Tele-Daily-Checkin>
```

Cài thư viện cần dùng:

```powershell
pip install telethon python-dotenv
```

---

## 5. Lấy `api_id` và `api_hash`

Vào trang:

```text
https://my.telegram.org
```

Đăng nhập bằng số điện thoại Telegram của bạn.

Vào:

```text
API development tools
```

Tạo app mới. Sau đó bạn sẽ nhận được:

```text
api_id
api_hash
```

Không chia sẻ `api_hash` cho người khác.

---

## 6. Tạo file `.env`

Trong thư mục `D:\Tele-Daily-Checkin`, tạo file:

```text
.env
```

Nội dung ban đầu:

```env
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
TG_PHONE=+84xxxxxxxxx
TARGET_CHAT=8604751086
```

Ví dụ:

```env
TG_API_ID=12345678
TG_API_HASH=abcdef1234567890abcdef1234567890
TG_PHONE=+84901234567
TARGET_CHAT=8604751086
```

Trong đó:

- `TG_API_ID`: lấy từ Telegram Developer.
- `TG_API_HASH`: lấy từ Telegram Developer.
- `TG_PHONE`: số điện thoại Telegram của bạn, có mã quốc gia `+84`.
- `TARGET_CHAT`: ID bot/chat cần check-in.

Nếu chưa biết `TARGET_CHAT`, làm tiếp bước bên dưới để lấy danh sách chat.

---

## 7. Tạo file `list_chats.py` để lấy ID chat

Tạo file:

```text
list_chats.py
```

Nội dung:

```python
import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
phone = os.getenv("TG_PHONE")

client = TelegramClient("telegram_session", api_id, api_hash)


async def main():
    await client.start(phone=phone)

    dialogs = await client.get_dialogs(limit=200)

    print("Recent chats:")
    for dialog in dialogs:
        print(f"{dialog.id} | {dialog.name}")


if __name__ == "__main__":
    asyncio.run(main())
```

Chạy:

```powershell
python list_chats.py
```

Lần đầu chạy, Telethon sẽ hỏi mã xác nhận Telegram:

```text
Please enter the code you received:
```

Nhập code Telegram gửi về app. Nếu tài khoản bật 2FA, nhập thêm password 2FA.

Sau khi chạy xong, bạn sẽ thấy danh sách kiểu:

```text
777000 | Telegram
-1002574080903 | MMOVN Community
-1003870268511 | TQA Solution 👨‍💻👩‍💻
-1003724230322 | Team交流群
-1001227549557 | J2TEAM Community Chat
2079264817 | Xì Ta Poi
8604751086 | 公益Plus/Team机器人
```

Với ví dụ trên, chat cần check-in là:

```text
8604751086 | 公益Plus/Team机器人
```

Sửa file `.env`:

```env
TARGET_CHAT=8604751086
```

---

## 8. Tạo file `daily_checkin.py`

Tạo file:

```text
daily_checkin.py
```

Nội dung:

```python
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
phone = os.getenv("TG_PHONE")
target_chat = os.getenv("TARGET_CHAT")

client = TelegramClient("telegram_session", api_id, api_hash)


def is_checkin_button(text: str) -> bool:
    if not text:
        return False

    text = text.lower()

    keywords = [
        "daily check-in",
        "daily checkin",
        "daily check in",
        "check-in",
        "check in",
        "checkin",
        "daily",
        "签到",
        "簽到",
    ]

    return any(keyword in text for keyword in keywords)


async def get_target_entity():
    if not target_chat:
        raise ValueError("Missing TARGET_CHAT in .env file")

    raw = target_chat.strip()

    # Load dialogs first so Telethon can get full entity/access_hash
    dialogs = await client.get_dialogs(limit=200)

    # If TARGET_CHAT is an ID
    if raw.lstrip("-").isdigit():
        target_id = int(raw)

        for dialog in dialogs:
            if dialog.id == target_id:
                print(f"Found chat: {dialog.name} | ID: {dialog.id}")
                return dialog.entity

        print("Cannot find target ID in dialogs.")
        print("Available chats:")

        for dialog in dialogs:
            print(f"{dialog.id} | {dialog.name}")

        raise ValueError(f"Cannot find chat id: {target_id}")

    # If TARGET_CHAT is display name
    for dialog in dialogs:
        if dialog.name == raw:
            print(f"Found chat by name: {dialog.name} | ID: {dialog.id}")
            return dialog.entity

    # If TARGET_CHAT is @username
    return await client.get_entity(raw)


async def main():
    await client.start(phone=phone)

    entity = await get_target_entity()

    print(f"[{datetime.now()}] Finding check-in button...")

    async for message in client.iter_messages(entity, limit=100):
        if not message.buttons:
            continue

        for row_index, row in enumerate(message.buttons):
            for button_index, button in enumerate(row):
                button_text = button.text or ""
                print(f"Found button: {button_text}")

                if is_checkin_button(button_text):
                    print(f"Click button: {button_text}")
                    await message.click(row_index, button_index)
                    print("Clicked successfully.")
                    return

    print("Cannot find Daily Check-in button in latest 100 messages.")


if __name__ == "__main__":
    asyncio.run(main())
```

Chạy thử:

```powershell
python daily_checkin.py
```

Nếu thành công, terminal sẽ có dạng:

```text
Found chat: 公益Plus/Team机器人 | ID: 8604751086
[2026-06-01 09:10:00] Finding check-in button...
Found button: Daily Check-in
Click button: Daily Check-in
Clicked successfully.
```

---

## 9. Tạo file `run_checkin.bat`

Tạo file:

```text
run_checkin.bat
```

Nội dung:

```bat
@echo off
chcp 65001 > nul
cd /d D:\Tele-Daily-Checkin

echo =============================== >> checkin.log
echo Run at %date% %time% >> checkin.log

call .venv\Scripts\activate
set PYTHONIOENCODING=utf-8

python daily_checkin.py >> checkin.log 2>&1

echo Finished at %date% %time% >> checkin.log
echo. >> checkin.log
```

Chạy thử:

```powershell
.\run_checkin.bat
```

Sau đó mở file:

```text
checkin.log
```

Nếu thấy:

```text
Clicked successfully.
```

là script đã chạy thành công.

---

## 10. Tạo lịch chạy hằng ngày bằng Task Scheduler

Mở Windows Start, tìm:

```text
Task Scheduler
```

Mở app **Task Scheduler**.

Ở cột bên phải, chọn:

```text
Create Basic Task...
```

Cấu hình:

```text
Name: Telegram Daily Checkin
```

Chọn:

```text
Trigger: Daily
```

Chọn giờ chạy, ví dụ:

```text
09:00 AM
```

Ở bước Action, chọn:

```text
Start a program
```

Phần Program/script chọn file:

```text
D:\Tele-Daily-Checkin\run_checkin.bat
```

Nếu có ô **Start in**, nhập:

```text
D:\Tele-Daily-Checkin
```

Bấm **Finish**.

---

## 11. Tìm và chạy thử task

Trong Task Scheduler, nhìn cột bên trái, bấm:

```text
Task Scheduler Library
```

Ở khung giữa, tìm task:

```text
Telegram Daily Checkin
```

Nếu không thấy, bấm **Refresh** bên phải.

Khi thấy task:

- Chuột phải > **Run** để chạy thử ngay.
- Chuột phải > **Properties** để chỉnh cấu hình.
- Chuột phải > **Disable** để tắt tạm thời.
- Chuột phải > **Delete** để xóa task.

Sau khi bấm **Run**, mở file:

```text
D:\Tele-Daily-Checkin\checkin.log
```

Nếu có log mới và thấy:

```text
Clicked successfully.
```

là task đã chạy đúng.

---

## 12. Cấu hình thêm trong Task Scheduler

Chuột phải vào task:

```text
Telegram Daily Checkin
```

Chọn:

```text
Properties
```

### Tab General

Nếu máy thường mở và đăng nhập Windows, chọn:

```text
Run only when user is logged on
```

Nếu muốn chạy cả khi chưa đăng nhập, có thể chọn:

```text
Run whether user is logged on or not
```

Tùy chọn này có thể yêu cầu nhập mật khẩu Windows.

### Tab Conditions

Nếu dùng laptop và vẫn muốn chạy khi dùng pin, bỏ tick:

```text
Start the task only if the computer is on AC power
```

### Tab Settings

Nên bật:

```text
Run task as soon as possible after a scheduled start is missed
```

Có thể bật retry:

```text
If the task fails, restart every: 10 minutes
Attempt to restart up to: 3 times
```

---

## 13. Các lỗi thường gặp

### Lỗi 1: Cannot find any entity corresponding to "tên chat"

Ví dụ:

```text
ValueError: Cannot find any entity corresponding to "公益Plus/Team机器人"
```

Nguyên nhân: bạn dùng tên hiển thị của chat trong `.env`, Telethon không resolve được.

Cách sửa:

1. Chạy:

```powershell
python list_chats.py
```

2. Lấy ID thật.
3. Sửa `.env`:

```env
TARGET_CHAT=8604751086
```

---

### Lỗi 2: Could not find input entity for PeerUser

Ví dụ:

```text
ValueError: Could not find the input entity for PeerUser(user_id=8604751086)
```

Nguyên nhân: truyền ID trực tiếp vào `iter_messages()`, Telethon thiếu `access_hash`.

Cách sửa: dùng hàm `get_target_entity()` như trong file `daily_checkin.py` ở trên. Hàm này load dialogs trước, sau đó trả về `dialog.entity` đầy đủ.

---

### Lỗi 3: UnicodeEncodeError khi chạy `.bat`

Ví dụ:

```text
UnicodeEncodeError: 'charmap' codec can't encode character
```

Nguyên nhân: Windows `.bat` đang dùng encoding không hỗ trợ tiếng Việt hoặc tiếng Trung.

Cách sửa: trong `run_checkin.bat` cần có:

```bat
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
```

Ngoài ra, trong Python nên dùng log tiếng Anh không dấu để tránh lỗi.

---

### Lỗi 4: Không thấy task trong Task Scheduler

Cách kiểm tra:

1. Mở Task Scheduler.
2. Bấm trực tiếp vào dòng:

```text
Task Scheduler Library
```

3. Nhìn khung giữa.
4. Bấm **Refresh**.
5. Nếu vẫn không thấy, tạo lại bằng **Create Basic Task...**.

---

### Lỗi 5: Không tìm thấy nút Daily Check-in

Nếu log báo:

```text
Cannot find Daily Check-in button in latest 100 messages.
```

Có thể do:

- Bot đổi tên button.
- Button nằm quá xa 100 tin gần nhất.
- Button chỉ xuất hiện sau khi gửi lệnh nào đó.
- Bạn đã check-in rồi nên button không còn active.

Cách xử lý:

- Tăng `limit=100` lên `limit=200` trong `daily_checkin.py`.
- Kiểm tra lại button thật bằng debug script.
- Thêm keyword vào hàm `is_checkin_button()`.

---

## 14. Lưu ý bảo mật

Không chia sẻ các file sau:

```text
.env
telegram_session.session
```

Vì:

- `.env` chứa `api_hash` và số điện thoại.
- `telegram_session.session` chứa session đăng nhập Telegram.

Nếu nghi ngờ session bị lộ, hãy vào Telegram:

```text
Settings > Devices
```

Sau đó đăng xuất các phiên lạ.

---

## 15. Checklist hoàn thành

- [ ] Tạo project `D:\Tele-Daily-Checkin`
- [ ] Tạo `.venv`
- [ ] Cài `telethon` và `python-dotenv`
- [ ] Tạo `.env`
- [ ] Lấy `api_id` và `api_hash`
- [ ] Chạy `list_chats.py`
- [ ] Lấy đúng `TARGET_CHAT`
- [ ] Chạy `daily_checkin.py` thành công
- [ ] Tạo `run_checkin.bat`
- [ ] Chạy `.bat` thành công
- [ ] Tạo task `Telegram Daily Checkin`
- [ ] Chạy thử task trong Task Scheduler
- [ ] Kiểm tra `checkin.log`

---

## 16. Lệnh chạy nhanh

Kích hoạt môi trường ảo:

```powershell
.venv\Scripts\activate
```

Chạy lấy danh sách chat:

```powershell
python list_chats.py
```

Chạy check-in thủ công:

```powershell
python daily_checkin.py
```

Chạy qua file `.bat`:

```powershell
.\run_checkin.bat
```

Xem log:

```powershell
notepad checkin.log
```
