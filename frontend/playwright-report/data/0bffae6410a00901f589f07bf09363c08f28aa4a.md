# Page snapshot

```yaml
- heading "Welcome back" [level=3]
- paragraph: Sign in to your StruMind account
- text: Login failed Email
- textbox "Email": invalid@email.com
- text: Password
- textbox "Password": wrongpassword
- checkbox "Remember me"
- text: Remember me
- link "Forgot password?":
  - /url: /auth/forgot-password
- button "Sign in"
- paragraph:
  - text: Don't have an account?
  - link "Sign up":
    - /url: /auth/register
- text: Or continue with
- button "Google":
  - img
  - text: Google
- button "GitHub":
  - img
  - text: GitHub
- region "Notifications (F8)":
  - list
- button "Open Tanstack query devtools":
  - img
- alert
```