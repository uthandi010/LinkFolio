import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../api/client";

function slugify(value) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [usernameEdited, setUsernameEdited] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function handleNameChange(value) {
    setName(value);
    if (!usernameEdited) {
      setUsername(slugify(value));
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);

    if (!name.trim() || !email.trim() || !username.trim() || !password) {
      setError("Name, email, username, and password are all required.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setSubmitting(true);
    try {
      await register(name.trim(), email.trim(), username.trim(), password);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" noValidate onSubmit={handleSubmit}>
        <h1>Create your LinkFolio</h1>
        <p className="auth-subtitle">One link, all your links - with click analytics built in.</p>

        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}

        <label className="field">
          <span>Name</span>
          <input type="text" value={name} onChange={(e) => handleNameChange(e.target.value)} autoComplete="name" />
        </label>

        <label className="field">
          <span>Email</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
        </label>

        <label className="field">
          <span>Username</span>
          <input
            type="text"
            value={username}
            onChange={(e) => {
              setUsernameEdited(true);
              setUsername(e.target.value);
            }}
          />
          <small>Your page will live at linkfolio.example/u/{username || "yourname"}</small>
        </label>

        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
          />
          <small>At least 8 characters.</small>
        </label>

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Creating account..." : "Create account"}
        </button>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
