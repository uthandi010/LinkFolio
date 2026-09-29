import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRequest, ApiError, getToken, setToken } from "../client";

describe("apiRequest", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("does not send an Authorization header when there is no token", async () => {
    setToken(null);
    fetch.mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));

    await apiRequest("/api/anything");

    const [, init] = fetch.mock.calls[0];
    expect(init.headers.Authorization).toBeUndefined();
  });

  it("attaches a Bearer Authorization header when a token is stored", async () => {
    setToken("test-token-123");
    fetch.mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));

    await apiRequest("/api/anything");

    const [, init] = fetch.mock.calls[0];
    expect(init.headers.Authorization).toBe("Bearer test-token-123");
  });

  it("returns the parsed JSON body on success", async () => {
    fetch.mockResolvedValue(new Response(JSON.stringify({ id: 1, title: "GitHub" }), { status: 200 }));

    const result = await apiRequest("/api/links/1");

    expect(result).toEqual({ id: 1, title: "GitHub" });
  });

  it("returns undefined for a 204 No Content response", async () => {
    fetch.mockResolvedValue(new Response(null, { status: 204 }));

    const result = await apiRequest("/api/links/1", { method: "DELETE" });

    expect(result).toBeUndefined();
  });

  it("extracts a plain string HTTPException detail as the error message", async () => {
    fetch.mockResolvedValue(
      new Response(JSON.stringify({ detail: "Invalid email or password." }), { status: 401 })
    );

    await expect(apiRequest("/api/auth/login", { method: "POST" })).rejects.toMatchObject({
      message: "Invalid email or password.",
      status: 401,
    });
  });

  it("extracts the first message from a FastAPI validation error list", async () => {
    fetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: [{ loc: ["body", "password"], msg: "password must be at least 8 characters", type: "value_error" }],
        }),
        { status: 422 }
      )
    );

    await expect(apiRequest("/api/auth/register", { method: "POST" })).rejects.toMatchObject({
      message: "password must be at least 8 characters",
    });
  });

  it("falls back to a generic message when the server sends nothing usable", async () => {
    fetch.mockResolvedValue(new Response("", { status: 500 }));

    await expect(apiRequest("/api/anything")).rejects.toBeInstanceOf(ApiError);
  });

  it("round-trips the token through localStorage", () => {
    setToken("abc123");
    expect(getToken()).toBe("abc123");
    setToken(null);
    expect(getToken()).toBeNull();
  });
});
