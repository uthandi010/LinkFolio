import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import * as publicApi from "../api/public";
import { ApiError } from "../api/client";

export function PublicProfilePage() {
  const { username } = useParams();
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    publicApi
      .getPublicProfile(username)
      .then(setProfile)
      .catch((err) => setError(err instanceof ApiError ? err.message : "This profile could not be found."));
  }, [username]);

  if (error) {
    return (
      <div className="public-page">
        <div className="form-error" role="alert">
          {error}
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="public-page">
        <p className="muted">Loading...</p>
      </div>
    );
  }

  return (
    <div className="public-page">
      <div className="public-card">
        <div className="public-avatar">{profile.name.charAt(0).toUpperCase()}</div>
        <h1>{profile.name}</h1>
        <p className="public-username">@{profile.username}</p>
        {profile.bio && <p className="public-bio">{profile.bio}</p>}

        <div className="public-links">
          {profile.links.length === 0 ? (
            <p className="muted">No links yet.</p>
          ) : (
            profile.links.map((link) => (
              <a key={link.id} href={publicApi.clickUrl(link.id)} className="public-link-button">
                {link.title}
              </a>
            ))
          )}
        </div>

        <p className="public-footer">Made with LinkFolio</p>
      </div>
    </div>
  );
}
