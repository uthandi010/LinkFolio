import { useEffect, useState } from "react";
import { Plus, Trash2, ArrowUp, ArrowDown, ExternalLink } from "lucide-react";
import { NavBar } from "../components/NavBar";
import { useAuth } from "../auth/AuthContext";
import * as linksApi from "../api/links";
import * as authApi from "../api/auth";
import { ApiError } from "../api/client";

export function DashboardPage() {
  const { user, updateProfile } = useAuth();
  const [links, setLinks] = useState(null);
  const [error, setError] = useState(null);

  const [newTitle, setNewTitle] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [creating, setCreating] = useState(false);

  const [bio, setBio] = useState("");
  const [bioSaved, setBioSaved] = useState(false);

  useEffect(() => {
    linksApi
      .listLinks()
      .then(setLinks)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load your links."));
  }, []);

  useEffect(() => {
    authApi
      .getMe()
      .then((me) => setBio(me.bio ?? ""))
      .catch(() => {});
  }, []);

  async function handleCreate(event) {
    event.preventDefault();
    if (!newTitle.trim() || !newUrl.trim()) return;

    setCreating(true);
    setError(null);
    try {
      const link = await linksApi.createLink(newTitle.trim(), newUrl.trim());
      setLinks((current) => [...current, link]);
      setNewTitle("");
      setNewUrl("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create that link.");
    } finally {
      setCreating(false);
    }
  }

  async function handleToggleActive(link) {
    try {
      const updated = await linksApi.updateLink(link.id, { active: !link.active });
      setLinks((current) => current.map((l) => (l.id === link.id ? updated : l)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update that link.");
    }
  }

  async function handleDelete(linkId) {
    try {
      await linksApi.deleteLink(linkId);
      setLinks((current) => current.filter((l) => l.id !== linkId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete that link.");
    }
  }

  async function handleMove(index, direction) {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= links.length) return;

    const reordered = [...links];
    [reordered[index], reordered[targetIndex]] = [reordered[targetIndex], reordered[index]];
    setLinks(reordered);

    try {
      const saved = await linksApi.reorderLinks(reordered.map((l) => l.id));
      setLinks(saved);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save the new order.");
    }
  }

  async function handleSaveBio(event) {
    event.preventDefault();
    setBioSaved(false);
    try {
      await authApi.updateMe({ bio });
      updateProfile({ bio });
      setBioSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your bio.");
    }
  }

  return (
    <div>
      <NavBar />
      <main className="page-content">
        <div className="page-header">
          <h1>Your links</h1>
          <p>
            Your public page: <code>/u/{user.username}</code>
          </p>
        </div>

        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}

        <section className="bio-panel">
          <form onSubmit={handleSaveBio}>
            <label className="field">
              <span>Bio</span>
              <textarea
                value={bio}
                onChange={(e) => {
                  setBio(e.target.value);
                  setBioSaved(false);
                }}
                rows={2}
                maxLength={280}
                placeholder="A short line about you, shown on your public page."
              />
            </label>
            <button type="submit" className="btn btn-secondary">
              Save bio
            </button>
            {bioSaved && <span className="saved-hint">Saved.</span>}
          </form>
        </section>

        <form className="inline-form" onSubmit={handleCreate}>
          <input type="text" placeholder="Title" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} />
          <input
            type="url"
            placeholder="https://..."
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
          />
          <button type="submit" className="btn btn-primary" disabled={creating}>
            <Plus size={16} />
            Add link
          </button>
        </form>

        {links === null ? (
          <p className="muted">Loading your links...</p>
        ) : links.length === 0 ? (
          <p className="muted">No links yet. Add your first one above.</p>
        ) : (
          <ul className="link-list">
            {links.map((link, index) => (
              <li key={link.id} className={link.active ? "" : "inactive"}>
                <div className="link-order-buttons">
                  <button
                    type="button"
                    className="icon-button"
                    disabled={index === 0}
                    onClick={() => handleMove(index, -1)}
                    aria-label="Move up"
                  >
                    <ArrowUp size={14} />
                  </button>
                  <button
                    type="button"
                    className="icon-button"
                    disabled={index === links.length - 1}
                    onClick={() => handleMove(index, 1)}
                    aria-label="Move down"
                  >
                    <ArrowDown size={14} />
                  </button>
                </div>

                <div className="link-info">
                  <strong>{link.title}</strong>
                  <a href={link.url} target="_blank" rel="noopener noreferrer">
                    {link.url} <ExternalLink size={12} />
                  </a>
                </div>

                <div className="link-actions">
                  <button type="button" className="btn btn-ghost" onClick={() => handleToggleActive(link)}>
                    {link.active ? "Active" : "Hidden"}
                  </button>
                  <button
                    type="button"
                    className="btn btn-danger"
                    onClick={() => handleDelete(link.id)}
                    aria-label="Delete link"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
