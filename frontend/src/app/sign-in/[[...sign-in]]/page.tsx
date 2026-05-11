import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="auth-page">
      <div className="auth-page__header">
        <h1>Welcome back</h1>
        <p>Sign in to access your music library.</p>
      </div>
      <SignIn />
    </div>
  );
}
