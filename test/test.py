#单元测试
from app.models.db import init_db
from app.models.user import UserRepository

init_db()
print("Create:",UserRepository.create_user("rexyang","123456"))
print("verity right:",UserRepository.verify_user("rexyang","123456"))
print("verity wrong1:",UserRepository.verify_user("rexyan","123456"))
print("verity wrong2:",UserRepository.verify_user("rexyang","1234567"))