import auth
print("Testing registration...")
res = auth.user_register("test_user", "test@test.com", "password")
print(res)
print("Testing login...")
res2 = auth.user_login("test_user", "password")
print(res2)
