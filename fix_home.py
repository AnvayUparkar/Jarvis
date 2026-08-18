import re

with open('www/home.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add IDs to register form
content = content.replace(
    '<form action="#">',
    '<form action="#" id="registerForm">'
)
content = content.replace(
    '<input type="text" required>',
    '<input type="text" id="registerUsername" required>'
)
content = content.replace(
    '<input type="email" required>',
    '<input type="email" id="registerEmail" required>'
)
content = content.replace(
    '<input type="password" required>',
    '<input type="password" id="registerPassword" required>'
)

# 2. Add registerForm JS variable
content = content.replace(
    "const loginForm = document.getElementById('loginForm');",
    "const loginForm = document.getElementById('loginForm');\n    const registerForm = document.getElementById('registerForm');"
)

# 3. Replace login logic and add register logic
# We'll use regex to find the loginForm event listener and replace it entirely.
pattern = r"loginForm\.addEventListener\('submit', async \(e\) => \{.*?\n    \}\);"
replacement = """loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const email = document.getElementById('loginUsername').value.trim();
      const password = document.getElementById('loginPassword').value;

      if (!email || !password) {
        showLoginMessage('Please enter both email and password', 'error');
        return;
      }

      showLoginMessage('Logging in...', 'loading');

      try {
        if (typeof eel !== 'undefined') {
          eel.user_login(email, password)(async function (result) {
            if (result.success) {
              await eel.set_authenticated_user(result.user_name, result.user_email)();
              showLoginMessage(
                `Login successful! Welcome ${result.user_name}.`,
                'success'
              );
              
              document.getElementById('loginUsername').value = '';
              document.getElementById('loginPassword').value = '';

              setTimeout(() => {
                loginModal.classList.remove('show');
                loginMessage.classList.remove('show');
                displayUserInfo(result.user_name);
              }, 1500);
            } else {
              showLoginMessage(result.message, 'error');
            }
          });
        }
      } catch (error) {
        console.error('Login error:', error);
        showLoginMessage('An error occurred during authentication.', 'error');
      }
    });

    // ===== REGISTRATION =====
    if (registerForm) {
      registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('registerUsername').value.trim();
        const email = document.getElementById('registerEmail').value.trim();
        const password = document.getElementById('registerPassword').value;

        if (!username || !email || !password) {
          showLoginMessage('Please fill all fields', 'error');
          return;
        }

        showLoginMessage('Registering...', 'loading');

        try {
          if (typeof eel !== 'undefined') {
            eel.user_register(username, email, password)(function (result) {
              if (result.success) {
                showLoginMessage('Registration successful! Please sign in.', 'success');
                // Switch to login tab
                setTimeout(() => {
                  authWrapper.classList.remove('toggled');
                  document.getElementById('loginUsername').value = email;
                  registerForm.reset();
                }, 1500);
              } else {
                showLoginMessage(result.message, 'error');
              }
            });
          }
        } catch (error) {
          console.error('Register error:', error);
          showLoginMessage('An error occurred during registration.', 'error');
        }
      });
    }"""

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('www/home.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done updating home.html")
