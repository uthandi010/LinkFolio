import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "../AuthContext";
import { getToken } from "../../api/client";

vi.mock("../../api/auth", () => ({
  login: vi.fn(async (email) => ({ token: "test-token", user_id: 1, name: "Test User", email, username: "test" })),
  register: vi.fn(async (name, email, username) => ({
    token: "test-token",
    user_id: 2,
    name,
    email,
    username,
  })),
}));

function Probe() {
  const { user, isAuthenticated, login, logout } = useAuth();
  return (
    <div>
      <p data-testid="status">{isAuthenticated ? "signed-in" : "signed-out"}</p>
      <p data-testid="username">{user?.username ?? "none"}</p>
      <button onClick={() => login("person@example.com", "Password123!")}>Log in</button>
      <button onClick={logout}>Log out</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("starts signed out when there is no stored token", () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    expect(screen.getByTestId("status")).toHaveTextContent("signed-out");
  });

  it("stores the token and user after a successful login", async () => {
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await act(async () => {
      await user.click(screen.getByText("Log in"));
    });

    expect(screen.getByTestId("status")).toHaveTextContent("signed-in");
    expect(screen.getByTestId("username")).toHaveTextContent("test");
    expect(getToken()).toBe("test-token");
  });

  it("clears the token and user on logout", async () => {
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>
    );

    await act(async () => {
      await user.click(screen.getByText("Log in"));
    });
    await act(async () => {
      await user.click(screen.getByText("Log out"));
    });

    expect(screen.getByTestId("status")).toHaveTextContent("signed-out");
    expect(getToken()).toBeNull();
  });
});
