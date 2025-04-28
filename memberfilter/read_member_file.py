import re

# Đọc file member_raw.txt
with open('D:/UIT SUBJECTS/Nam 1 - hoc ki 2 - Cau truc du lieu va giai thuat/Big Task 1/memberfilter/member_raw.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Danh sách lưu các tên trích xuất được
names_before_remove = []

# Duyệt qua từng dòng và tìm các tên đứng trước "remove"
for line in lines:
    # Tìm tất cả các từ đứng trước "remove"
    match = re.search(r'(\S+)\s+Remove', line)
    if match:
        # Lấy tên đứng trước "remove"
        names_before_remove.append(match.group(1))

# Xuất kết quả vào file output.txt
with open('output.txt', 'w', encoding='utf-8') as output_file:
    for name in names_before_remove:
        output_file.write(name + '\n')

print("Đã trích xuất xong và lưu vào file output.txt")
