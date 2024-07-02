import os
import glob
import re
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image
from PIL.ExifTags import TAGS
import datetime

# 默认文件类型
default_file_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.mp4', '*.avi', '*.mov', '*.mkv', '*.heic']

def sanitize_folder_name(folder_name):
    # 使用正则表达式只保留中文字符和字母
    sanitized_name = re.sub(r'[^a-zA-Z\u4e00-\u9fa5]', '', folder_name)
    return sanitized_name

def get_creation_time(file_path):
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == 'DateTimeOriginal':
                    # 将时间字符串转换为时间对象
                    return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        print(f"无法读取文件 {file_path} 的创建时间: {e}")
    # 如果无法获取EXIF数据或没有DateTimeOriginal标签，则使用文件的修改时间
    return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

def extract_sequence_number(file_name, folder_name):
    match = re.match(rf"{folder_name}_(\d+)", file_name)
    if match:
        return int(match.group(1))
    return None

def rename_files_in_directory(directory, file_extensions):
    # 获取当前文件夹的名称并进行清理
    folder_name = os.path.basename(directory)
    sanitized_folder_name = sanitize_folder_name(folder_name)

    # 收集所有文件及其创建时间
    files_with_dates = []
    for extension in file_extensions:
        for file_path in glob.glob(os.path.join(directory, extension)):
            creation_time = get_creation_time(file_path)
            files_with_dates.append((file_path, creation_time))

    # 按创建时间排序
    files_with_dates.sort(key=lambda x: x[1])

    modified_count = 0
    unmodified_count = 0

    # 提取现有文件的序号
    existing_files = {}
    for file_path, _ in files_with_dates:
        file_name = os.path.basename(file_path)
        seq_num = extract_sequence_number(file_name, sanitized_folder_name)
        if seq_num is not None:
            existing_files[seq_num] = file_path

    # 确保序号连贯
    sorted_seq_nums = sorted(existing_files.keys())
    next_seq_num = 1
    for seq_num in sorted_seq_nums:
        if seq_num != next_seq_num:
            old_path = existing_files[seq_num]
            file_extension = os.path.splitext(old_path)[1]
            new_file_name = f"{sanitized_folder_name}_{next_seq_num:03d}{file_extension}"
            new_file_path = os.path.join(directory, new_file_name)
            os.rename(old_path, new_file_path)
            modified_count += 1
        else:
            unmodified_count += 1
        next_seq_num += 1

    # 重命名新文件
    for file_path, _ in files_with_dates:
        file_name = os.path.basename(file_path)
        seq_num = extract_sequence_number(file_name, sanitized_folder_name)
        if seq_num is None:
            file_extension = os.path.splitext(file_path)[1]
            new_file_name = f"{sanitized_folder_name}_{next_seq_num:03d}{file_extension}"
            new_file_path = os.path.join(directory, new_file_name)
            os.rename(file_path, new_file_path)
            modified_count += 1
            next_seq_num += 1

    return modified_count, unmodified_count

def rename_files_recursively(root_directory, file_extensions):
    total_modified = 0
    total_unmodified = 0

    for dirpath, _, _ in os.walk(root_directory):
        modified_count, unmodified_count = rename_files_in_directory(dirpath, file_extensions)
        total_modified += modified_count
        total_unmodified += unmodified_count

    return total_modified, total_unmodified

def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        modified_count, unmodified_count = rename_files_recursively(folder_selected, file_extensions)
        messagebox.showinfo("完成",
                            f"{modified_count} 项修改成功，{unmodified_count} 项未修改。")

def configure_file_types():
    global file_extensions
    current_types = ', '.join([ext.lstrip('*.') for ext in file_extensions])
    input_types = simpledialog.askstring("文件类型配置",
                                         f"当前文件类型: {current_types}\n\n请输入新的文件类型（用逗号分隔）：\n例如：jpg, png, mp4\n注意：不要输入点号和星号，支持英文逗号和中文逗号。", initialvalue=current_types)
    if input_types:
        # 处理输入，去除空格，处理大小写，支持中英文逗号
        input_types = re.sub(r'\s+', '', input_types)  # 去除所有空格
        input_types = input_types.replace('，', ',')    # 将中文逗号替换为英文逗号
        # 仅保留英文字符和逗号
        input_types = re.sub(r'[^a-zA-Z,]', '', input_types)
        file_extensions = [f"*.{ext.strip().lower()}" for ext in input_types.split(',') if ext.strip()]
        messagebox.showinfo("文件类型配置", f"文件类型已更新为: {', '.join(file_extensions)}")

# 初始化文件类型
file_extensions = default_file_extensions.copy()

# 创建主窗口
root = tk.Tk()
root.title("文件重命名工具")

# 创建说明标签
instructions = tk.Label(root,
                        text="使用方法：\n1. 点击“选择文件夹”按钮。\n2. 选择包含需要更名文件的文件夹。\n3. 程序将自动重命名文件夹中的所有指定格式文件。\n\n功能：\n- 支持自定义修改格式\n（默认jpg,jpeg,png,gif,bmp,mp4,avi,mov,mkv,heic）\n- 文件名格式为“当前目录文件夹名_001”。",
                        justify=tk.LEFT, padx=10, pady=10)
instructions.pack()

# 创建选择文件夹按钮
select_button = tk.Button(root, text="选择文件夹", command=select_folder)
select_button.pack(pady=10)

# 创建配置文件类型按钮
configure_button = tk.Button(root, text="配置文件类型", command=configure_file_types)
configure_button.pack(pady=10)

# 运行应用程序
root.mainloop()
