import hashlib
import sys

def calculate_sha256(file_path):
    # 创建一个SHA-256哈希对象
    sha256_hash = hashlib.sha256()

    # 打开文件以进行二进制读取
    with open(file_path, "rb") as file:
        # 逐块读取文件并更新哈希值
        for chunk in iter(lambda: file.read(4096), b""):
            sha256_hash.update(chunk)

    # 返回SHA-256哈希值的十六进制表示
    return sha256_hash.hexdigest()


for path in sys.argv[1:]:
    sha256 = calculate_sha256(path)
    print(f"SHA-256 {path}: {sha256}")
