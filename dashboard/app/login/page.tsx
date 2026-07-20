"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function Login() {
  const router = useRouter();
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const data = new FormData(event.currentTarget);
    const response = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: data.get("email"), password: data.get("password") }) });
    if (!response.ok) { setError("Email or password is incorrect."); return; }
    router.push("/"); router.refresh();
  }
  return <div className="login"><form className="card" onSubmit={submit}>
    <h1>Nicer Homes</h1><p className="muted">Sign in to pricing operations.</p>
    <label className="field">Email<input name="email" type="email" required autoComplete="username" /></label>
    <label className="field">Password<input name="password" type="password" required autoComplete="current-password" /></label>
    {error && <p className="error">{error}</p>}<button className="button" type="submit">Sign in</button>
  </form></div>;
}

