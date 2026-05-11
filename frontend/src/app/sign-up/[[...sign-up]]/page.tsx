import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="auth-page">
      <div className="auth-page__header">
        <h1>Create your library</h1>
        <p>Sign up to upload, tag, and search your music.</p>
      </div>
      <SignUp />
    </div>
  );
}
